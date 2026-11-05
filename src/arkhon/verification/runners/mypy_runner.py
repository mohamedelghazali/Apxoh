"""Mypy runner — strict static type checking."""

from __future__ import annotations

import hashlib
import shutil
import subprocess
from pathlib import Path

from arkhon.core.logging import get_logger
from arkhon.verification.runners.base import Runner, RunnerOutcome, RunnerResult

logger = get_logger("verification.runners.mypy")


class MypyRunner(Runner):
    def __init__(self, timeout_seconds: int = 600) -> None:
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        self._timeout = timeout_seconds

    @property
    def name(self) -> str:
        return "mypy"

    def run(self, project_root: Path) -> RunnerResult:
        binary = shutil.which("mypy")
        if binary is None:
            return RunnerResult(
                runner=self.name,
                outcome=RunnerOutcome.BLOCKED,
                reason="mypy not found on PATH",
            )
        root = project_root.resolve()
        source = root / "src"
        target_path = source if source.is_dir() else root
        command = [binary, "--strict", "--no-incremental", str(target_path)]
        try:
            result = subprocess.run(  # noqa: S603 - resolved mypy executable and fixed arguments
                command,
                cwd=root,
                capture_output=True,
                text=True,
                timeout=self._timeout,
                check=False,
            )
        except subprocess.TimeoutExpired:
            return RunnerResult(
                runner=self.name,
                outcome=RunnerOutcome.BLOCKED,
                reason=f"mypy timed out after {self._timeout}s",
            )
        except OSError as exc:
            return RunnerResult(
                runner=self.name,
                outcome=RunnerOutcome.BLOCKED,
                reason=f"mypy failed to start: {exc}",
            )
        output = (result.stdout or "") + (result.stderr or "")
        target_dir = root / ".arkhon" / "evidence" / "code-quality"
        try:
            target_dir.mkdir(parents=True, exist_ok=True)
            payload = output.encode("utf-8")
            digest = hashlib.sha256(payload).hexdigest()
            target = target_dir / f"mypy-{digest}.txt"
            if target.is_symlink():
                raise OSError("refusing symlinked content-addressed Mypy evidence")
            try:
                with target.open("xb") as stream:
                    stream.write(payload)
            except FileExistsError:
                if target.read_bytes() != payload:
                    raise OSError("content-addressed Mypy evidence does not match its digest")
        except OSError as exc:
            return RunnerResult(
                runner=self.name,
                outcome=RunnerOutcome.BLOCKED,
                reason=f"cannot persist mypy evidence: {exc}",
            )
        if result.returncode == 0:
            return RunnerResult(runner=self.name, outcome=RunnerOutcome.PASS, artifacts=[target])
        if result.returncode == 1:
            return RunnerResult(
                runner=self.name,
                outcome=RunnerOutcome.FAIL,
                reason="mypy reported type errors",
                artifacts=[target],
            )
        return RunnerResult(
            runner=self.name,
            outcome=RunnerOutcome.BLOCKED,
            reason=f"mypy could not complete (exit={result.returncode})",
            artifacts=[target],
        )
