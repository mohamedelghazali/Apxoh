"""Provider-neutral multi-agent runtime adapters and capability detection."""

from __future__ import annotations

import abc
import os
import shutil
import subprocess
import sys
import threading
import time
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from gencode_gov.security_audit.sandbox import (
    SandboxExecutor,
    _snapshot_tree_digests,
    promote_agent_artifacts,
    validate_agent_id,
)
from gencode_gov.security_audit.validators import _read_regular_json


def _utc_now() -> str:
    return datetime.now(UTC).isoformat()


def _pythonpath_for_worker() -> str:
    src_root = str(Path(__file__).resolve().parents[2])
    existing = os.environ.get("PYTHONPATH", "")
    return f"{src_root}{os.pathsep}{existing}" if existing else src_root


@dataclass(frozen=True)
class RuntimeDescriptor:
    """Truthful capability metadata for an external or isolated subprocess agent runtime."""

    runtime_id: str
    provider: str
    available: bool
    executable_path: str | None
    isolated_process: bool
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "runtime_id": self.runtime_id,
            "provider": self.provider,
            "available": self.available,
            "executable_path": self.executable_path,
            "isolated_process": self.isolated_process,
            "reason": self.reason,
        }


@dataclass(frozen=True)
class AgentTaskSpec:
    """Immutable task specification passed across process boundary to one agent session."""

    task_id: str
    action: str
    audit_run_id: str
    commit_sha: str
    role: str
    agent_id: str
    wave: int
    attempt: int
    project_root: str
    output_filename: str
    payload: dict[str, Any]
    timeout_seconds: float = 30.0
    depends_on: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not validate_agent_id(self.agent_id):
            raise ValueError(f"invalid canonical agent_id: {self.agent_id!r}")
        if self.wave < 1 or self.attempt < 1:
            raise ValueError("wave and attempt must be >= 1")

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "action": self.action,
            "audit_run_id": self.audit_run_id,
            "commit_sha": self.commit_sha,
            "role": self.role,
            "agent_id": self.agent_id,
            "wave": self.wave,
            "attempt": self.attempt,
            "project_root": self.project_root,
            "output_filename": self.output_filename,
            "payload": self.payload,
            "timeout_seconds": self.timeout_seconds,
            "depends_on": list(self.depends_on),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AgentTaskSpec:
        return cls(
            task_id=str(data["task_id"]),
            action=str(data["action"]),
            audit_run_id=str(data["audit_run_id"]),
            commit_sha=str(data["commit_sha"]),
            role=str(data["role"]),
            agent_id=str(data["agent_id"]),
            wave=int(data["wave"]),
            attempt=int(data["attempt"]),
            project_root=str(data["project_root"]),
            output_filename=str(data["output_filename"]),
            payload=dict(data["payload"]),
            timeout_seconds=float(data.get("timeout_seconds", 30.0)),
            depends_on=tuple(str(x) for x in data.get("depends_on", ())),
        )


@dataclass(frozen=True)
class AgentSessionResult:
    """Verified outcome and OS process provenance of one isolated agent session."""

    task_id: str
    session_id: str
    agent_id: str
    role: str
    runtime_id: str
    pid: int
    isolated_process: bool
    status: str
    exit_code: int | None
    started_at: str
    completed_at: str
    promoted_artifact: str | None
    output_data: dict[str, Any] | None
    error: str | None = None

    def to_session_record(self, wave: int) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "agent_id": self.agent_id,
            "role": self.role,
            "runtime_id": self.runtime_id,
            "pid": self.pid,
            "wave": wave,
            "status": self.status,
        }


class AgentRuntimeAdapter(abc.ABC):
    """Provider-neutral interface for launching isolated security audit agent sessions."""

    runtime_id: str

    @abc.abstractmethod
    def probe(self) -> RuntimeDescriptor:
        """Detect whether this runtime is genuinely executable on the current host."""

    @abc.abstractmethod
    def execute_session(
        self,
        task: AgentTaskSpec,
        *,
        audit_dir: Path,
        cancel_event: threading.Event | None = None,
    ) -> AgentSessionResult:
        """Execute task in an isolated child process and promote its regular-file output."""


def _execute_isolated_child_session(
    *,
    runtime_id: str,
    build_argv: Any,
    task: AgentTaskSpec,
    audit_dir: Path,
    extra_env: dict[str, str] | None = None,
    cancel_event: threading.Event | None = None,
) -> AgentSessionResult:
    """Spawn an isolated OS child process with per-agent scratch dir and O_NOFOLLOW promotion."""
    import json

    started = _utc_now()
    session_id = f"sess-{uuid.uuid4().hex[:12]}"
    sandbox = SandboxExecutor(audit_dir)
    scratch_dir, artifacts_dir = sandbox.prepare_agent_dirs(task.agent_id)
    if cancel_event is not None and cancel_event.is_set():
        return AgentSessionResult(
            task_id=task.task_id,
            session_id=session_id,
            agent_id=task.agent_id,
            role=task.role,
            runtime_id=runtime_id,
            pid=os.getpid(),
            isolated_process=False,
            status="cancelled",
            exit_code=None,
            started_at=started,
            completed_at=_utc_now(),
            promoted_artifact=None,
            output_data=None,
            error="session cancelled before launch",
        )

    envelope = {
        "session_id": session_id,
        "runtime_id": runtime_id,
        "scratch_dir": str(scratch_dir),
        "output_path": str(scratch_dir / task.output_filename),
        "task": task.to_dict(),
    }
    task_file = scratch_dir / "task.json"
    task_file.write_text(json.dumps(envelope, indent=2) + "\n", encoding="utf-8")

    env = sandbox.build_allowlisted_env(scratch_dir, extra_env)
    env["GENCODE_GOV_AGENT_SESSION_ID"] = session_id
    env["GENCODE_GOV_TASK_FILE"] = str(task_file)

    project_path = Path(task.project_root).resolve()
    before_digests = _snapshot_tree_digests(project_path)
    argv: list[str] = build_argv(task_file)

    try:
        proc = subprocess.Popen(  # noqa: S603 - fixed runtime binary and task.json path
            argv,
            cwd=scratch_dir,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
    except OSError as exc:
        return AgentSessionResult(
            task_id=task.task_id,
            session_id=session_id,
            agent_id=task.agent_id,
            role=task.role,
            runtime_id=runtime_id,
            pid=os.getpid(),
            isolated_process=False,
            status="blocked",
            exit_code=None,
            started_at=started,
            completed_at=_utc_now(),
            promoted_artifact=None,
            output_data=None,
            error=f"failed to spawn agent runtime process: {exc}",
        )

    child_pid = proc.pid
    deadline = time.monotonic() + task.timeout_seconds
    timed_out = False
    cancelled = False
    while proc.poll() is None:
        if cancel_event is not None and cancel_event.is_set():
            cancelled = True
            proc.kill()
            break
        if time.monotonic() >= deadline:
            timed_out = True
            proc.kill()
            break
        time.sleep(0.01)

    _stdout, stderr = proc.communicate()
    after_digests = _snapshot_tree_digests(project_path)
    if before_digests != after_digests:
        return AgentSessionResult(
            task_id=task.task_id,
            session_id=session_id,
            agent_id=task.agent_id,
            role=task.role,
            runtime_id=runtime_id,
            pid=child_pid,
            isolated_process=True,
            status="blocked",
            exit_code=proc.returncode,
            started_at=started,
            completed_at=_utc_now(),
            promoted_artifact=None,
            output_data=None,
            error="target source tree was modified during agent session",
        )

    if cancelled:
        return AgentSessionResult(
            task_id=task.task_id,
            session_id=session_id,
            agent_id=task.agent_id,
            role=task.role,
            runtime_id=runtime_id,
            pid=child_pid,
            isolated_process=True,
            status="cancelled",
            exit_code=proc.returncode,
            started_at=started,
            completed_at=_utc_now(),
            promoted_artifact=None,
            output_data=None,
            error="agent session cancelled during execution",
        )

    if timed_out:
        return AgentSessionResult(
            task_id=task.task_id,
            session_id=session_id,
            agent_id=task.agent_id,
            role=task.role,
            runtime_id=runtime_id,
            pid=child_pid,
            isolated_process=True,
            status="timed_out",
            exit_code=proc.returncode,
            started_at=started,
            completed_at=_utc_now(),
            promoted_artifact=None,
            output_data=None,
            error=f"agent session exceeded timeout ({task.timeout_seconds}s)",
        )

    if proc.returncode != 0:
        return AgentSessionResult(
            task_id=task.task_id,
            session_id=session_id,
            agent_id=task.agent_id,
            role=task.role,
            runtime_id=runtime_id,
            pid=child_pid,
            isolated_process=True,
            status="failed",
            exit_code=proc.returncode,
            started_at=started,
            completed_at=_utc_now(),
            promoted_artifact=None,
            output_data=None,
            error=(stderr or "").strip()[:512] or f"session exited with code {proc.returncode}",
        )

    promo = promote_agent_artifacts(
        scratch_dir=scratch_dir,
        artifacts_dir=artifacts_dir,
        allowlisted_files=(task.output_filename,),
    )
    if task.output_filename not in promo.promoted:
        reason = promo.rejected[0][1] if promo.rejected else "missing session output artifact"
        return AgentSessionResult(
            task_id=task.task_id,
            session_id=session_id,
            agent_id=task.agent_id,
            role=task.role,
            runtime_id=runtime_id,
            pid=child_pid,
            isolated_process=True,
            status="failed",
            exit_code=proc.returncode,
            started_at=started,
            completed_at=_utc_now(),
            promoted_artifact=None,
            output_data=None,
            error=f"artifact promotion rejected: {reason}",
        )

    promoted_file = artifacts_dir / task.output_filename
    parsed, read_errs = _read_regular_json(promoted_file)
    if read_errs or not isinstance(parsed, dict):
        detail = "; ".join(read_errs) if read_errs else "session output must be a JSON object"
        return AgentSessionResult(
            task_id=task.task_id,
            session_id=session_id,
            agent_id=task.agent_id,
            role=task.role,
            runtime_id=runtime_id,
            pid=child_pid,
            isolated_process=True,
            status="failed",
            exit_code=proc.returncode,
            started_at=started,
            completed_at=_utc_now(),
            promoted_artifact=None,
            output_data=None,
            error=f"invalid session output JSON: {detail}",
        )

    rel_promoted = f"agents/{task.agent_id}/artifacts/{task.output_filename}"
    return AgentSessionResult(
        task_id=task.task_id,
        session_id=session_id,
        agent_id=task.agent_id,
        role=task.role,
        runtime_id=runtime_id,
        pid=child_pid,
        isolated_process=True,
        status="completed",
        exit_code=0,
        started_at=started,
        completed_at=_utc_now(),
        promoted_artifact=rel_promoted,
        output_data=parsed,
        error=None,
    )


class IsolatedSubprocessWorkerRuntime(AgentRuntimeAdapter):
    """Spawns genuinely independent OS Python worker processes per audit session."""

    runtime_id = "python-isolated-worker"

    def __init__(self, *, python_executable: str | None = None) -> None:
        self._python = python_executable or sys.executable

    def probe(self) -> RuntimeDescriptor:
        exe = Path(self._python)
        ok = exe.is_file() and os.access(exe, os.X_OK)
        return RuntimeDescriptor(
            runtime_id=self.runtime_id,
            provider="gencode-gov-isolated-subprocess",
            available=ok,
            executable_path=str(exe) if ok else None,
            isolated_process=True,
            reason="Available isolated OS subprocess worker" if ok else "Python binary missing",
        )

    def execute_session(
        self,
        task: AgentTaskSpec,
        *,
        audit_dir: Path,
        cancel_event: threading.Event | None = None,
    ) -> AgentSessionResult:
        desc = self.probe()
        if not desc.available or desc.executable_path is None:
            return AgentSessionResult(
                task_id=task.task_id,
                session_id=f"sess-blocked-{uuid.uuid4().hex[:8]}",
                agent_id=task.agent_id,
                role=task.role,
                runtime_id=self.runtime_id,
                pid=os.getpid(),
                isolated_process=False,
                status="blocked",
                exit_code=None,
                started_at=_utc_now(),
                completed_at=_utc_now(),
                promoted_artifact=None,
                output_data=None,
                error=desc.reason,
            )
        exe_path = desc.executable_path
        return _execute_isolated_child_session(
            runtime_id=self.runtime_id,
            build_argv=lambda tf: [
                exe_path,
                "-c",
                (
                    "import sys; from gencode_gov.security_audit.worker_entry import main; "
                    "raise SystemExit(main(sys.argv[1:]))"
                ),
                str(tf),
            ],
            task=task,
            audit_dir=audit_dir,
            extra_env={"PYTHONPATH": _pythonpath_for_worker()},
            cancel_event=cancel_event,
        )


class ExternalCliAgentRuntime(AgentRuntimeAdapter):
    """Adapter for external CLI agent runtimes (claude, codex, gemini, or custom command)."""

    def __init__(
        self,
        *,
        runtime_id: str,
        provider: str,
        binary_name: str | None = None,
        explicit_executable: str | None = None,
        extra_args: tuple[str, ...] = (),
        which_fn: Any = shutil.which,
    ) -> None:
        self.runtime_id = runtime_id
        self.provider = provider
        self._binary_name = binary_name
        self._explicit_executable = explicit_executable
        self._extra_args = extra_args
        self._which_fn = which_fn

    def probe(self) -> RuntimeDescriptor:
        candidate = self._explicit_executable or (
            self._which_fn(self._binary_name) if self._binary_name else None
        )
        if not candidate:
            label = self._explicit_executable or self._binary_name or self.runtime_id
            return RuntimeDescriptor(
                runtime_id=self.runtime_id,
                provider=self.provider,
                available=False,
                executable_path=None,
                isolated_process=True,
                reason=f"External runtime executable not found: {label}",
            )
        exe = Path(candidate)
        is_py_script = exe.suffix.lower() == ".py"
        usable = exe.is_file() and (
            os.access(exe, os.R_OK) if is_py_script else os.access(exe, os.X_OK)
        )
        if not usable:
            return RuntimeDescriptor(
                runtime_id=self.runtime_id,
                provider=self.provider,
                available=False,
                executable_path=None,
                isolated_process=True,
                reason=f"External runtime path is not an executable file: {candidate}",
            )
        return RuntimeDescriptor(
            runtime_id=self.runtime_id,
            provider=self.provider,
            available=True,
            executable_path=str(exe.resolve()),
            isolated_process=True,
            reason=f"Detected executable external runtime at {exe.resolve()}",
        )

    def execute_session(
        self,
        task: AgentTaskSpec,
        *,
        audit_dir: Path,
        cancel_event: threading.Event | None = None,
    ) -> AgentSessionResult:
        desc = self.probe()
        if not desc.available or desc.executable_path is None:
            return AgentSessionResult(
                task_id=task.task_id,
                session_id=f"sess-blocked-{uuid.uuid4().hex[:8]}",
                agent_id=task.agent_id,
                role=task.role,
                runtime_id=self.runtime_id,
                pid=os.getpid(),
                isolated_process=False,
                status="blocked",
                exit_code=None,
                started_at=_utc_now(),
                completed_at=_utc_now(),
                promoted_artifact=None,
                output_data=None,
                error=desc.reason,
            )
        exe_path = desc.executable_path
        prefix = [sys.executable, exe_path] if exe_path.lower().endswith(".py") else [exe_path]
        return _execute_isolated_child_session(
            runtime_id=self.runtime_id,
            build_argv=lambda tf: [*prefix, *self._extra_args, str(tf)],
            task=task,
            audit_dir=audit_dir,
            extra_env={"PYTHONPATH": _pythonpath_for_worker()},
            cancel_event=cancel_event,
        )


def detect_available_runtimes(
    *,
    agent_cmd: str | None = None,
    which_fn: Any = shutil.which,
) -> list[RuntimeDescriptor]:
    """Probe all supported external CLI and isolated subprocess agent runtimes truthfully."""
    cmd_target = agent_cmd or (os.environ.get("GENCODE_GOV_AGENT_CMD"))
    adapters: list[AgentRuntimeAdapter] = [
        ExternalCliAgentRuntime(
            runtime_id="claude-cli",
            provider="anthropic",
            binary_name="claude",
            which_fn=which_fn,
        ),
        ExternalCliAgentRuntime(
            runtime_id="codex-cli",
            provider="openai",
            binary_name="codex",
            which_fn=which_fn,
        ),
        ExternalCliAgentRuntime(
            runtime_id="gemini-cli",
            provider="google",
            binary_name="gemini",
            which_fn=which_fn,
        ),
        ExternalCliAgentRuntime(
            runtime_id="command",
            provider="external-command",
            explicit_executable=cmd_target,
            which_fn=which_fn,
        ),
        IsolatedSubprocessWorkerRuntime(),
    ]
    return [adapter.probe() for adapter in adapters]


def resolve_runtime_adapter(
    runtime_name: str = "auto",
    *,
    agent_cmd: str | None = None,
    which_fn: Any = shutil.which,
) -> AgentRuntimeAdapter:
    """Resolve a requested runtime adapter without silently substituting unavailable ones."""
    cmd_target = agent_cmd or (os.environ.get("GENCODE_GOV_AGENT_CMD"))
    if runtime_name == "command" or (runtime_name == "auto" and cmd_target):
        return ExternalCliAgentRuntime(
            runtime_id="command",
            provider="external-command",
            explicit_executable=cmd_target,
            which_fn=which_fn,
        )
    if runtime_name == "claude-cli":
        return ExternalCliAgentRuntime(
            runtime_id="claude-cli",
            provider="anthropic",
            binary_name="claude",
            which_fn=which_fn,
        )
    if runtime_name == "codex-cli":
        return ExternalCliAgentRuntime(
            runtime_id="codex-cli",
            provider="openai",
            binary_name="codex",
            which_fn=which_fn,
        )
    if runtime_name == "gemini-cli":
        return ExternalCliAgentRuntime(
            runtime_id="gemini-cli",
            provider="google",
            binary_name="gemini",
            which_fn=which_fn,
        )
    if runtime_name in {"auto", "python-isolated-worker"}:
        return IsolatedSubprocessWorkerRuntime()
    raise ValueError(f"unsupported security audit runtime: {runtime_name!r}")
