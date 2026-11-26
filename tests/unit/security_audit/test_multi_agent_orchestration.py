"""Unit and integration tests for genuine Multi-Agent Security Audit Orchestration."""

from __future__ import annotations

import concurrent.futures
import json
import os
import shutil
import stat
import subprocess
import sys
import threading
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

from arkhon.cli import main as cli_main
from arkhon.security_audit.coverage import (
    CoverageCheck,
    CoverageLedger,
    CoverageUnit,
    LockedCoverageLedgerStore,
    build_canonical_coverage_id,
)
from arkhon.security_audit.dispatcher import AuditRole, SecurityAuditTaskDispatcher
from arkhon.security_audit.findings import (
    DiscoveryProvenance,
    FindingsCollection,
    LocationRef,
    SecurityFinding,
    TraceStep,
    VerificationProvenance,
    compute_finding_fingerprint,
    finding_id_from_fingerprint,
)
from arkhon.security_audit.orchestrator import (
    MultiAgentAuditOrchestrator,
    OrchestrationConfig,
)
from arkhon.security_audit.runtime import (
    AgentRuntimeAdapter,
    AgentSessionResult,
    AgentTaskSpec,
    ExternalCliAgentRuntime,
    IsolatedSubprocessWorkerRuntime,
    RuntimeDescriptor,
    resolve_runtime_adapter,
)
from arkhon.security_audit.validators import (
    validate_audit_directory,
    validate_coverage_ledger_data,
    validate_findings_data,
)
from arkhon.security_audit.worker_entry import execute_worker_envelope
from arkhon.security_audit.worker_entry import main as worker_main

_GIT = shutil.which("git") or "/usr/bin/git"
SHA = "e" * 40


def _init_vuln_git_repo(root: Path) -> tuple[Path, str]:
    proj = root / "multi_agent_target"
    (proj / "src" / "web").mkdir(parents=True)
    (proj / "src" / "auth").mkdir(parents=True)
    (proj / "src" / "web" / "routes.py").write_text(
        "from fastapi import FastAPI\n"
        "app = FastAPI()\n"
        "def run_cmd(user_input: str):\n"
        "    return eval(user_input)\n",
        encoding="utf-8",
    )
    (proj / "src" / "auth" / "crypto.py").write_text(
        "import hashlib\n"
        "def weak_hash(pw: str) -> str:\n"
        "    return hashlib.md5(pw.encode()).hexdigest()\n",
        encoding="utf-8",
    )
    subprocess.run([_GIT, "init"], cwd=proj, check=True, capture_output=True)  # noqa: S603
    subprocess.run(  # noqa: S603
        [_GIT, "config", "user.email", "ma@example.com"], cwd=proj, check=True
    )
    subprocess.run([_GIT, "config", "user.name", "MA"], cwd=proj, check=True)  # noqa: S603
    subprocess.run([_GIT, "add", "."], cwd=proj, check=True)  # noqa: S603
    subprocess.run(  # noqa: S603
        [_GIT, "commit", "-m", "initial target repo"],
        cwd=proj,
        check=True,
        capture_output=True,
    )
    sha = subprocess.run(  # noqa: S603
        [_GIT, "rev-parse", "HEAD"],
        cwd=proj,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    return proj, sha


def test_real_multi_process_orchestration_session_isolation_and_cli(
    tmp_path: Path,
) -> None:
    proj, sha = _init_vuln_git_repo(tmp_path)
    out_dir = tmp_path / "ma_audit"

    # CLI runtimes discovery
    assert cli_main(["audit", "runtimes", "--json"]) == 0
    assert cli_main(["audit", "runtimes"]) == 0

    # Real multi-agent audit run via CLI using python-isolated-worker child OS processes
    rc = cli_main(
        [
            "audit",
            "run",
            str(proj),
            "--execution-mode",
            "multi_agent_independent_sessions",
            "--runtime",
            "python-isolated-worker",
            "--max-workers",
            "3",
            "--output-dir",
            str(out_dir),
            "--record-evidence",
            "--json",
        ]
    )
    # Vulnerable target produces confirmed high/critical finding -> exit 1 (FAIL gate)
    assert rc == 1
    assert validate_audit_directory(out_dir).ok is True

    ledger = CoverageLedger.load(out_dir / "coverage-ledger.json")
    findings = FindingsCollection.load(out_dir / "findings.json")
    report = json.loads((out_dir / "security-audit-report.json").read_text(encoding="utf-8"))
    md_text = (out_dir / "SECURITY-AUDIT-REPORT.md").read_text(encoding="utf-8")

    assert ledger.execution_mode == "multi_agent_independent_sessions"
    assert ledger.orchestration is not None
    assert ledger.orchestration["independent_sessions_verified"] is True
    assert ledger.orchestration["distinct_session_ids"] >= 4
    assert ledger.orchestration["distinct_pids"] >= 2
    assert "Multi-Agent Runtime" in md_text
    assert report["orchestration_summary"]["independent_sessions_verified"] is True

    # Verify every session ran in a genuinely separate OS process (pid != parent pid)
    parent_pid = os.getpid()
    for sess in ledger.orchestration["sessions"]:
        assert int(sess["pid"]) != parent_pid
        agent_scratch = out_dir / "agents" / sess["agent_id"] / "scratch"
        assert agent_scratch.is_dir()
        if os.name == "posix":
            assert (stat.S_IMODE(agent_scratch.stat().st_mode) & 0o777) == 0o700

    # Verify strict discovery vs verification session & agent independence on every finding
    assert len(findings.records) >= 2
    for rec in findings.records:
        dp = rec.discovery_provenance
        vp = rec.verification_provenance
        assert vp is not None
        assert dp.session_id is not None
        assert vp.session_id is not None
        assert dp.agent_id != vp.verifier_id
        assert dp.session_id != vp.session_id
        assert vp.record_verifier_id is not None
        assert vp.record_verifier_id not in {dp.agent_id, vp.verifier_id}
        assert vp.record_verifier_session_id not in {dp.session_id, vp.session_id}


def test_external_command_runtime_adapter_and_fail_closed_unavailable_runtimes(
    tmp_path: Path,
) -> None:
    proj, _sha = _init_vuln_git_repo(tmp_path)

    # Create a real executable external agent CLI script wrapping worker_entry
    ext_bin = tmp_path / "custom_external_agent.py"
    src_root = str(Path(__file__).resolve().parents[3] / "src")
    ext_bin.write_text(
        f"#!{sys.executable}\n"
        "import sys\n"
        f"sys.path.insert(0, {src_root!r})\n"
        "from arkhon.security_audit.worker_entry import main\n"
        "raise SystemExit(main(sys.argv[1:]))\n",
        encoding="utf-8",
    )
    ext_bin.chmod(0o755)

    ext_out = tmp_path / "ext_cmd_audit"
    rc_ext = cli_main(
        [
            "audit",
            "run",
            str(proj),
            "--execution-mode",
            "auto",
            "--runtime",
            "auto",
            "--agent-cmd",
            str(ext_bin),
            "--max-workers",
            "2",
            "--output-dir",
            str(ext_out),
        ]
    )
    assert rc_ext == 1
    assert validate_audit_directory(ext_out).ok is True
    ext_ledger = CoverageLedger.load(ext_out / "coverage-ledger.json")
    assert ext_ledger.orchestration is not None
    assert ext_ledger.orchestration["runtime_id"] == "command"

    # Unavailable external vendor CLI runtimes must fail closed (BLOCKED) without faking sessions
    for vendor_rt in ("claude-cli", "codex-cli", "gemini-cli"):
        adapter = resolve_runtime_adapter(vendor_rt, which_fn=lambda _: None)
        assert adapter.probe().available is False
        blocked_res = adapter.execute_session(
            AgentTaskSpec(
                task_id="t1",
                action="reconnaissance",
                audit_run_id="AUDIT-BLK1",
                commit_sha=SHA,
                role="security-reconnaissance-agent",
                agent_id="recon-01",
                wave=1,
                attempt=1,
                project_root=str(proj),
                output_filename="recon.json",
                payload={},
            ),
            audit_dir=tmp_path / f"blk_{vendor_rt}",
        )
        assert blocked_res.status == "blocked"
        assert blocked_res.isolated_process is False

    # CLI fails closed when --runtime command has a missing or non-executable file
    non_exec = tmp_path / ("not_exec.txt" if os.name == "posix" else "missing_exec_dir")
    if os.name == "posix":
        non_exec.write_text("nope\n", encoding="utf-8")
        non_exec.chmod(0o600)
    else:
        non_exec.mkdir()
    assert (
        cli_main(
            [
                "audit",
                "run",
                str(proj),
                "--execution-mode",
                "multi_agent_independent_sessions",
                "--runtime",
                "command",
                "--agent-cmd",
                str(non_exec),
                "--output-dir",
                str(tmp_path / "blk_cli"),
            ]
        )
        == 1
    )
    with pytest.raises(ValueError, match="unsupported security audit runtime"):
        resolve_runtime_adapter("nonexistent-runtime")

    # IsolatedSubprocessWorkerRuntime with missing python binary fails closed
    bad_py = IsolatedSubprocessWorkerRuntime(python_executable=str(tmp_path / "missing_py"))
    assert bad_py.probe().available is False
    bad_py_out = MultiAgentAuditOrchestrator(
        project_root=proj,
        audit_dir=tmp_path / "bad_py_aud",
        audit_run_id="AUDIT-BADPY",
        commit_sha=SHA,
        runtime=bad_py,
    ).run()
    assert bad_py_out.status == "blocked"
    assert bad_py_out.execution_mode == "single_process_deterministic"

def test_concurrent_locked_coverage_ledger_store_and_lock_contention(
    tmp_path: Path,
) -> None:
    units = [
        CoverageUnit(
            coverage_id=build_canonical_coverage_id(
                entry_point=f"ep-{i}",
                trust_boundary="ext->app",
                component="src/app",
                attack_class="api-security",
            ),
            component="src/app",
            attack_class="api-security",
            trust_boundary="ext->app",
            entry_point=f"ep-{i}",
            interface="internal",
            starting_paths=[f"src/app/m{i}.py"],
        )
        for i in range(8)
    ]
    ledger = CoverageLedger(
        ledger_id="LEDGER-CONC",
        audit_run_id="AUDIT-CONC",
        project="conc",
        commit_sha=SHA,
        profile="standard",
        audit_status="initiated",
        execution_mode="single_process_deterministic",
        scope_paths=[],
        units=units,
    )
    store = LockedCoverageLedgerStore(tmp_path / "coverage-ledger.json", lock_timeout_seconds=5.0)
    store.initialize(ledger)

    def _concurrent_worker(idx: int) -> None:
        cid = units[idx].coverage_id
        hid = f"hunter-{idx + 1:02d}"
        claimed = store.claim_unit(cid, hid)
        claimed.reviewed_paths = list(claimed.starting_paths)
        claimed.checks = [
            CoverageCheck(
                investigator_id=hid,
                method="source",
                reviewed_paths=tuple(claimed.starting_paths),
                invariant="inv",
                result="ok",
                evidence_refs=tuple(claimed.starting_paths),
                artifact_path=None,
                timestamp="2026-11-26T00:00:00Z",
                session_id=f"sess-{idx + 1:02d}",
                runtime_id="python-isolated-worker",
            )
        ]
        claimed.status = "partially_examined"
        claimed.limitations = ["wave 1 partial"]
        store.apply_unit_outcome(claimed)
        new_wave = store.archive_and_reassign_unit(cid, "wave 2 completion")
        assert new_wave == 2
        hid2 = f"hunter-w2-{idx + 1:02d}"
        claimed2 = store.claim_unit(cid, hid2)
        claimed2.reviewed_paths = list(claimed2.starting_paths)
        claimed2.checks = [
            CoverageCheck(
                investigator_id=hid2,
                method="source",
                reviewed_paths=tuple(claimed2.starting_paths),
                invariant="inv",
                result="complete",
                evidence_refs=tuple(claimed2.starting_paths),
                artifact_path=None,
                timestamp="2026-11-26T00:01:00Z",
                session_id=f"sess-w2-{idx + 1:02d}",
                runtime_id="python-isolated-worker",
            )
        ]
        claimed2.status = "examined"
        claimed2.limitations = []
        store.apply_unit_outcome(claimed2)

    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        futs = [pool.submit(_concurrent_worker, i) for i in range(8)]
        for f in futs:
            f.result()

    final_led = store.read()
    comp = final_led.compute_completeness()
    assert comp["examined"] == 8
    assert comp["is_complete"] is True
    assert all(len(u.attempts) == 1 and u.wave == 2 for u in final_led.units)

    # Error branches: double claim, unknown coverage_id, lock timeout
    with pytest.raises(ValueError, match="cannot claim"):
        store.claim_unit(units[0].coverage_id, "hunter-99")
    with pytest.raises(KeyError, match="unknown coverage_id"):
        store.claim_unit("missing-cid", "hunter-99")
    dummy = CoverageUnit("missing-cid", "c", "a", "b", "e", "i", ["x.py"])
    with pytest.raises(KeyError, match="unknown coverage_id"):
        store.apply_unit_outcome(dummy)
    with pytest.raises(KeyError, match="unknown coverage_id"):
        store.archive_and_reassign_unit("missing-cid", "reason")

    contended_path = tmp_path / "contended" / "coverage-ledger.json"
    contended_path.parent.mkdir()
    ledger.save(contended_path)
    (contended_path.with_suffix(".json.lock")).write_text("99999\n", encoding="utf-8")
    fast_store = LockedCoverageLedgerStore(contended_path, lock_timeout_seconds=0.03)
    with pytest.raises(TimeoutError, match="timed out acquiring"):
        fast_store.read()


def test_timeouts_retries_tamper_interruption_and_checkpoint_resumption(
    tmp_path: Path,
) -> None:
    proj, sha = _init_vuln_git_repo(tmp_path)

    # Config validation
    with pytest.raises(ValueError, match="max_workers"):
        OrchestrationConfig(max_workers=0)
    with pytest.raises(ValueError, match="task_timeout_seconds"):
        OrchestrationConfig(task_timeout_seconds=0)
    with pytest.raises(ValueError, match="max_retries"):
        OrchestrationConfig(max_retries=-1)
    with pytest.raises(ValueError, match="invalid canonical agent_id"):
        AgentTaskSpec("t", "reconnaissance", "AUDIT-1", sha, "r", "CON", 1, 1, ".", "o.json", {})
    with pytest.raises(ValueError, match="wave and attempt"):
        AgentTaskSpec("t", "reconnaissance", "AUDIT-1", sha, "r", "a-1", 0, 1, ".", "o.json", {})

    # 1. Runtime child process edge cases: cancel, timeout, exit!=0, bad JSON, symlink, tamper
    pre_cancel = threading.Event()
    pre_cancel.set()
    rt = IsolatedSubprocessWorkerRuntime()
    spec_base = AgentTaskSpec(
        task_id="t-edge",
        action="reconnaissance",
        audit_run_id="AUDIT-EDGE",
        commit_sha=sha,
        role="security-reconnaissance-agent",
        agent_id="recon-01",
        wave=1,
        attempt=1,
        project_root=str(proj),
        output_filename="out.json",
        payload={},
        timeout_seconds=0.08,
    )
    assert (
        rt.execute_session(spec_base, audit_dir=tmp_path / "e1", cancel_event=pre_cancel).status
        == "cancelled"
    )

    def _make_script(name: str, body: str) -> ExternalCliAgentRuntime:
        sc = tmp_path / name
        sc.write_text(f"#!{sys.executable}\n{body}\n", encoding="utf-8")
        sc.chmod(0o755)
        return ExternalCliAgentRuntime(
            runtime_id="command",
            provider="external-command",
            explicit_executable=str(sc),
        )

    # Timeout child
    sleep_rt = _make_script("sleep_agent.py", "import time\ntime.sleep(5)")
    assert sleep_rt.execute_session(spec_base, audit_dir=tmp_path / "e_to").status == "timed_out"

    # Mid-execution cancel child
    mid_cancel = threading.Event()
    threading.Timer(0.03, mid_cancel.set).start()
    slow_spec = AgentTaskSpec(
        task_id="t-cancel",
        action="reconnaissance",
        audit_run_id="AUDIT-EDGE",
        commit_sha=sha,
        role="security-reconnaissance-agent",
        agent_id="recon-02",
        wave=1,
        attempt=1,
        project_root=str(proj),
        output_filename="out.json",
        payload={},
        timeout_seconds=5.0,
    )
    assert (
        sleep_rt.execute_session(
            slow_spec, audit_dir=tmp_path / "e_can", cancel_event=mid_cancel
        ).status
        == "cancelled"
    )

    # Exit non-zero child
    fail_rt = _make_script(
        "fail_agent.py", "import sys\nsys.stderr.write('boom')\nraise SystemExit(3)"
    )
    assert fail_rt.execute_session(slow_spec, audit_dir=tmp_path / "e_fail").status == "failed"

    # Symlink output rejected by promote_agent_artifacts
    sym_rt = _make_script(
        "sym_agent.py",
        "import json, os, pathlib, sys\n"
        "env = json.loads(pathlib.Path(sys.argv[1]).read_text())\n"
        "out = pathlib.Path(env['output_path'])\n"
        "real = out.parent / 'real.txt'\n"
        "real.write_text('{}')\n"
        "out.symlink_to(real)\n",
    )
    res_sym = sym_rt.execute_session(slow_spec, audit_dir=tmp_path / "e_sym")
    assert res_sym.status == "failed"
    assert "promotion rejected" in (res_sym.error or "")

    # Non-dict JSON output rejected
    arr_rt = _make_script(
        "arr_agent.py",
        "import json, pathlib, sys\n"
        "env = json.loads(pathlib.Path(sys.argv[1]).read_text())\n"
        "pathlib.Path(env['output_path']).write_text('[1, 2, 3]')\n",
    )
    res_arr = arr_rt.execute_session(slow_spec, audit_dir=tmp_path / "e_arr")
    assert res_arr.status == "failed"
    assert "JSON object" in (res_arr.error or "")

    # Spawn OSError fails closed to blocked
    with patch("subprocess.Popen", side_effect=OSError("spawn blocked")):
        assert rt.execute_session(slow_spec, audit_dir=tmp_path / "e_os").status == "blocked"

    # Source tree tamper detection fails closed to blocked
    tamper_copy, t_sha = _init_vuln_git_repo(tmp_path / "tamper_wrap")
    tamper_rt = _make_script(
        "tamper_agent.py",
        "import json, pathlib, sys\n"
        "env = json.loads(pathlib.Path(sys.argv[1]).read_text())\n"
        "proj = pathlib.Path(env['task']['project_root'])\n"
        "(proj / 'src' / 'web' / 'routes.py').write_text('# tampered\\n')\n"
        "pathlib.Path(env['output_path']).write_text('{}')\n",
    )
    t_spec = AgentTaskSpec(
        task_id="t-tamper",
        action="reconnaissance",
        audit_run_id="AUDIT-TAMP",
        commit_sha=t_sha,
        role="security-reconnaissance-agent",
        agent_id="recon-03",
        wave=1,
        attempt=1,
        project_root=str(tamper_copy),
        output_filename="out.json",
        payload={},
    )
    assert tamper_rt.execute_session(t_spec, audit_dir=tmp_path / "e_tamp").status == "blocked"

    # 2. Bounded retry recovery + safe interruption + CLI resume!
    flaky_marker = tmp_path / "flaky_once.flag"
    src_root = str(Path(__file__).resolve().parents[3] / "src")
    flaky_rt = _make_script(
        "flaky_agent.py",
        "import json, pathlib, sys\n"
        f"sys.path.insert(0, {src_root!r})\n"
        f"flag = pathlib.Path({str(flaky_marker)!r})\n"
        "env = json.loads(pathlib.Path(sys.argv[1]).read_text())\n"
        "if env['task']['action'] == 'hunt_unit' and not flag.exists():\n"
        "    flag.write_text('1')\n"
        "    raise SystemExit(2)\n"
        "from arkhon.security_audit.worker_entry import main\n"
        "raise SystemExit(main(sys.argv[1:]))\n",
    )

    # Interrupt right after hunting stage by wrapping execute_session
    interrupt_dir = tmp_path / "interrupted_audit"
    stop_ev = threading.Event()

    class _InterruptBeforeVerifyAdapter(AgentRuntimeAdapter):
        runtime_id = "command"

        def probe(self) -> RuntimeDescriptor:
            return flaky_rt.probe()

        def execute_session(
            self,
            task: AgentTaskSpec,
            *,
            audit_dir: Path,
            cancel_event: threading.Event | None = None,
        ) -> AgentSessionResult:
            if task.action == "verify_candidate" and cancel_event is not None:
                cancel_event.set()
            return flaky_rt.execute_session(
                task, audit_dir=audit_dir, cancel_event=cancel_event
            )

    orch_int = MultiAgentAuditOrchestrator(
        project_root=proj,
        audit_dir=interrupt_dir,
        audit_run_id="AUDIT-INTRES1",
        commit_sha=sha,
        runtime=_InterruptBeforeVerifyAdapter(),
        config=OrchestrationConfig(max_workers=2, max_retries=1, max_units=3),
    )
    int_outcome = orch_int.run(cancel_event=stop_ev)
    assert int_outcome.status == "interrupted"
    ckpt = json.loads((interrupt_dir / "orchestration-state.json").read_text(encoding="utf-8"))
    assert ckpt["interrupted"] is True
    assert ckpt["retried_tasks"] >= 1

    # Reject resuming against a mismatched commit SHA
    with pytest.raises(ValueError, match="different Git commit SHA"):
        MultiAgentAuditOrchestrator(
            project_root=proj,
            audit_dir=interrupt_dir,
            audit_run_id="AUDIT-INTRES1",
            commit_sha="a" * 40,
            runtime=rt,
        ).run(resume=True)

    # CLI resume error checks + successful resume completion!
    assert cli_main(["audit", "resume", str(proj)]) == 1
    assert cli_main(["audit", "resume", str(proj), "--audit-dir", str(tmp_path / "empty")]) == 1
    rc_resumed = cli_main(
        [
            "audit",
            "resume",
            str(proj),
            "--audit-dir",
            str(interrupt_dir),
            "--runtime",
            "python-isolated-worker",
            "--record-evidence",
        ]
    )
    assert rc_resumed == 1  # confirmed findings -> FAIL gate, status == completed
    resumed_ledger = CoverageLedger.load(interrupt_dir / "coverage-ledger.json")
    assert resumed_ledger.orchestration is not None
    assert resumed_ledger.orchestration["resumed"] is True
    assert validate_audit_directory(interrupt_dir).ok is True


def test_in_process_worker_entry_validator_session_guards_and_edge_branches(
    tmp_path: Path,
) -> None:
    proj, sha = _init_vuln_git_repo(tmp_path)

    # Direct in-process coverage of worker_entry.py (all 5 actions + separation violations + CLI)
    assert worker_main([]) == 2
    bad_task = tmp_path / "bad_task.json"
    bad_task.write_text("{not-json", encoding="utf-8")
    assert worker_main([str(bad_task)]) == 1

    recon_task_file = tmp_path / "recon_task.json"
    recon_out_file = tmp_path / "recon_out.json"
    recon_env = {
        "session_id": "sess-recon-01",
        "runtime_id": "python-isolated-worker",
        "output_path": str(recon_out_file),
        "task": AgentTaskSpec(
            task_id="t-recon",
            action="reconnaissance",
            audit_run_id="AUDIT-WK01",
            commit_sha=sha,
            role="security-reconnaissance-agent",
            agent_id="recon-01",
            wave=1,
            attempt=1,
            project_root=str(proj),
            output_filename="recon.json",
            payload={"profile": "standard", "scope_paths": ["src/web"]},
        ).to_dict(),
    }
    recon_task_file.write_text(json.dumps(recon_env), encoding="utf-8")
    assert worker_main([str(recon_task_file)]) == 0
    recon_data = json.loads(recon_out_file.read_text(encoding="utf-8"))

    led_dict = recon_data["ledger"]
    active_unit = next(
        u
        for u in led_dict["units"]
        if u["status"] == "planned" and u["attack_class"] == "injection-input-handling"
    )
    hunt_res = execute_worker_envelope(
        {
            "session_id": "sess-hunt-01",
            "runtime_id": "python-isolated-worker",
            "output_path": str(tmp_path / "h.json"),
            "task": AgentTaskSpec(
                task_id="t-hunt",
                action="hunt_unit",
                audit_run_id="AUDIT-WK01",
                commit_sha=sha,
                role="security-hunter",
                agent_id="hunter-01",
                wave=1,
                attempt=1,
                project_root=str(proj),
                output_filename="h.json",
                payload={"unit": active_unit},
            ).to_dict(),
        }
    )
    cand_dict = hunt_res["candidates"][0]

    # Critic action with a partially_examined unit triggers reassignable_unit_ids
    partial_unit = dict(hunt_res["unit"])
    partial_unit["status"] = "partially_examined"
    partial_unit["limitations"] = ["needs wave 2"]
    led_dict["units"][0] = partial_unit
    critic_res = execute_worker_envelope(
        {
            "session_id": "sess-critic-01",
            "runtime_id": "python-isolated-worker",
            "output_path": str(tmp_path / "c.json"),
            "task": AgentTaskSpec(
                task_id="t-critic",
                action="coverage_critic",
                audit_run_id="AUDIT-WK01",
                commit_sha=sha,
                role="coverage-analyst",
                agent_id="critic-01",
                wave=1,
                attempt=1,
                project_root=str(proj),
                output_filename="c.json",
                payload={"ledger": led_dict},
            ).to_dict(),
        }
    )
    assert critic_res["reassignable_unit_ids"] == [partial_unit["coverage_id"]]

    # Candidate verifier rejects same agent_id AND same session_id
    with pytest.raises(ValueError, match="separation-of-duties"):
        execute_worker_envelope(
            {
                "session_id": "sess-ver-other",
                "runtime_id": "python-isolated-worker",
                "output_path": str(tmp_path / "v.json"),
                "task": AgentTaskSpec(
                    task_id="t-ver",
                    action="verify_candidate",
                    audit_run_id="AUDIT-WK01",
                    commit_sha=sha,
                    role="independent-finding-verifier",
                    agent_id="hunter-01",
                    wave=1,
                    attempt=1,
                    project_root=str(proj),
                    output_filename="v.json",
                    payload={"candidate": cand_dict},
                ).to_dict(),
            }
        )
    with pytest.raises(ValueError, match="session isolation"):
        execute_worker_envelope(
            {
                "session_id": "sess-hunt-01",
                "runtime_id": "python-isolated-worker",
                "output_path": str(tmp_path / "v.json"),
                "task": AgentTaskSpec(
                    task_id="t-ver",
                    action="verify_candidate",
                    audit_run_id="AUDIT-WK01",
                    commit_sha=sha,
                    role="independent-finding-verifier",
                    agent_id="verifier-01",
                    wave=1,
                    attempt=1,
                    project_root=str(proj),
                    output_filename="v.json",
                    payload={"candidate": cand_dict},
                ).to_dict(),
            }
        )

    ver_res = execute_worker_envelope(
        {
            "session_id": "sess-ver-01",
            "runtime_id": "python-isolated-worker",
            "output_path": str(tmp_path / "v.json"),
            "task": AgentTaskSpec(
                task_id="t-ver",
                action="verify_candidate",
                audit_run_id="AUDIT-WK01",
                commit_sha=sha,
                role="independent-finding-verifier",
                agent_id="verifier-01",
                wave=1,
                attempt=1,
                project_root=str(proj),
                output_filename="v.json",
                payload={"candidate": cand_dict},
            ).to_dict(),
        }
    )
    ver_finding = ver_res["finding"]

    # Phase 5 record verifier rejects reused session_id and detects material replacement
    with pytest.raises(ValueError, match="Phase 5 record verifier session"):
        execute_worker_envelope(
            {
                "session_id": "sess-ver-01",
                "runtime_id": "python-isolated-worker",
                "output_path": str(tmp_path / "rv.json"),
                "task": AgentTaskSpec(
                    task_id="t-rv",
                    action="verify_record",
                    audit_run_id="AUDIT-WK01",
                    commit_sha=sha,
                    role="independent-finding-verifier",
                    agent_id="record-v1",
                    wave=1,
                    attempt=1,
                    project_root=str(proj),
                    output_filename="rv.json",
                    payload={"finding": ver_finding},
                ).to_dict(),
            }
        )

    drifted_finding = json.loads(json.dumps(ver_finding))
    drifted_finding["trace"][0]["line"] = 999
    rv_res = execute_worker_envelope(
        {
            "session_id": "sess-rv-01",
            "runtime_id": "python-isolated-worker",
            "output_path": str(tmp_path / "rv.json"),
            "task": AgentTaskSpec(
                task_id="t-rv",
                action="verify_record",
                audit_run_id="AUDIT-WK01",
                commit_sha=sha,
                role="independent-finding-verifier",
                agent_id="record-v1",
                wave=1,
                attempt=1,
                project_root=str(proj),
                output_filename="rv.json",
                payload={"finding": drifted_finding},
            ).to_dict(),
        }
    )
    assert rv_res["materially_changed"] is True

    with pytest.raises(ValueError, match="unsupported worker task action"):
        execute_worker_envelope(
            {
                "session_id": "sess-x",
                "runtime_id": "python-isolated-worker",
                "output_path": str(tmp_path / "x.json"),
                "task": AgentTaskSpec(
                    task_id="t-x",
                    action="unknown_action",
                    audit_run_id="AUDIT-WK01",
                    commit_sha=sha,
                    role="security-hunter",
                    agent_id="hunter-99",
                    wave=1,
                    attempt=1,
                    project_root=str(proj),
                    output_filename="x.json",
                    payload={},
                ).to_dict(),
            }
        )

    # Dispatcher & Finding & Validator multi-agent provenance rejection tests
    disp = SecurityAuditTaskDispatcher(
        audit_dir=tmp_path / "d_test", execution_mode="multi_agent_independent_sessions"
    )
    with pytest.raises(ValueError, match="session_id and canonical agent_id"):
        disp.register_external_session(
            session_id="",
            agent_id="hunter-01",
            role=AuditRole.HUNTER,
            runtime_id="r",
            pid=12345,
        )
    disp.register_discovery("fp:s", "hunter-01", session_id="sess-same")
    with pytest.raises(ValueError, match="cannot verify its own discovery"):
        disp.assert_independent_verifier("fp:s", "verifier-01", verifier_session_id="sess-same")

    # SecurityFinding policy invariant rejects identical discovery/verification session_id
    sf = SecurityFinding.from_dict(ver_finding)
    sf.verification_provenance = VerificationProvenance(
        verifier_id="verifier-01",
        role="independent-finding-verifier",
        run_id="AUDIT-WK01",
        timestamp="2026-11-26T00:00:00Z",
        method="independent_source_review",
        supporting_evidence=("ok",),
        contradictory_evidence=(),
        disprove_attempts=("checked",),
        session_id=sf.discovery_provenance.session_id,
    )
    with pytest.raises(ValueError, match="discovering session"):
        sf.to_dict()

    # Validator rejects fake multi_agent_independent_sessions without >=2 distinct sessions
    fake_led = CoverageLedger.from_dict(recon_data["ledger"])
    assert not validate_coverage_ledger_data(fake_led.to_dict()).ok
    fake_led.orchestration = {
        "runtime_id": "python-isolated-worker",
        "independent_sessions_verified": True,
        "max_workers": 2,
        "session_count": 1,
        "distinct_session_ids": 1,
        "distinct_pids": 1,
        "sessions": [
            {
                "session_id": "sess-only-1",
                "agent_id": "recon-01",
                "role": "security-reconnaissance-agent",
                "runtime_id": "python-isolated-worker",
                "pid": 99999,
                "wave": 1,
                "status": "completed",
            }
        ],
    }
    assert not validate_coverage_ledger_data(fake_led.to_dict()).ok

    # Validator rejects findings payload with same session_id on discovery & verification
    bad_rec_raw = json.loads(json.dumps(ver_finding))
    bad_rec_raw["verification_provenance"]["session_id"] = (
        bad_rec_raw["discovery_provenance"]["session_id"]
    )
    assert not validate_findings_data(
        {
            "schema_version": "1.0.0",
            "audit_run_id": "AUDIT-WK01",
            "commit_sha": sha,
            "records": [bad_rec_raw],
        }
    ).ok


def test_orchestrator_exhaustive_failure_cancel_critic_and_reverify_branches(
    tmp_path: Path,
) -> None:
    # 1. Clean repo CLI multi-agent run -> exit 0 (cli_dispatch.py:243 & zero candidates)
    clean_proj = tmp_path / "clean_ma"
    (clean_proj / "src").mkdir(parents=True)
    (clean_proj / "src" / "pure.py").write_text(
        "def inc(x: int) -> int:\n    return x + 1\n", encoding="utf-8"
    )
    subprocess.run([_GIT, "init"], cwd=clean_proj, check=True, capture_output=True)  # noqa: S603
    subprocess.run(  # noqa: S603
        [_GIT, "config", "user.email", "c@example.com"], cwd=clean_proj, check=True
    )
    subprocess.run(  # noqa: S603
        [_GIT, "config", "user.name", "C"], cwd=clean_proj, check=True
    )
    subprocess.run([_GIT, "add", "."], cwd=clean_proj, check=True)  # noqa: S603
    subprocess.run(  # noqa: S603
        [_GIT, "commit", "-m", "clean"], cwd=clean_proj, check=True, capture_output=True
    )
    clean_sha = subprocess.run(  # noqa: S603
        [_GIT, "rev-parse", "HEAD"],
        cwd=clean_proj,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()

    clean_out = tmp_path / "clean_ma_out"
    assert (
        cli_main(
            [
                "audit",
                "run",
                str(clean_proj),
                "--execution-mode",
                "multi_agent_independent_sessions",
                "--runtime",
                "python-isolated-worker",
                "--output-dir",
                str(clean_out),
            ]
        )
        == 0
    )

    # 2. runtime.py missing python execute_session, dispatcher provenance_summary, worker_entry L142
    bad_py = IsolatedSubprocessWorkerRuntime(python_executable=str(tmp_path / "no_py"))
    sample_spec = AgentTaskSpec(
        task_id="t1",
        action="reconnaissance",
        audit_run_id="AUDIT-1",
        commit_sha=clean_sha,
        role="security-reconnaissance-agent",
        agent_id="recon-01",
        wave=1,
        attempt=1,
        project_root=str(clean_proj),
        output_filename="r.json",
        payload={},
    )
    assert bad_py.execute_session(sample_spec, audit_dir=tmp_path / "bp").status == "blocked"

    disp = SecurityAuditTaskDispatcher(
        audit_dir=tmp_path / "dp", execution_mode="multi_agent_independent_sessions"
    )
    assert disp.provenance_summary()["multi_agent_independent_sessions"] is False

    # worker_entry verify_record when verification_provenance is None (candidate status)
    fp = compute_finding_fingerprint(
        component="src",
        attack_class="injection-input-handling",
        primary_file="src/pure.py",
        symbol="inc",
        invariant_key="k",
    )
    cand_unv = SecurityFinding(
        finding_id=finding_id_from_fingerprint(fp),
        fingerprint=fp,
        title="t",
        description="d",
        attack_class="injection-input-handling",
        component="src",
        affected_locations=[LocationRef("src/pure.py", 1, "inc")],
        trace=[TraceStep("sink", "src/pure.py", 1, "inc", "s")],
        trust_boundary="b",
        entry_point="e",
        affected_principal_or_resource="p",
        preconditions=[],
        scenario_summary="s",
        reproduction_steps=[],
        security_impact="i",
        evidence_refs=["src/pure.py:1"],
        discovery_provenance=DiscoveryProvenance(
            "hunter-01", "security-hunter", "AUDIT-1", "2026-11-26T00:00:00Z", "static_ast"
        ),
        verification_provenance=None,
        verification_status="not_verified",
        lifecycle_state="candidate",
        confidence_score="low",
        confidence_reason="r",
        uncertainty_notes=[],
        severity=None,
        root_cause=None,
        claimed_root_cause="c",
        remediation=None,
        unresolved_blockers=[],
        validation_plan=None,
        rejection_reason=None,
        related_rules=["SE-SEC-003"],
        related_requirements=[],
        commit_sha=clean_sha,
        first_seen_run="AUDIT-1",
        last_seen_run="AUDIT-1",
        first_seen_commit=clean_sha,
        last_seen_commit=clean_sha,
        state_history=[
            {
                "state": "candidate",
                "run_id": "AUDIT-1",
                "commit_sha": clean_sha,
                "actor": "hunter-01",
                "reason": "init",
            }
        ],
    )
    rv_unv = execute_worker_envelope(
        {
            "session_id": "sess-rv-unv",
            "runtime_id": "python-isolated-worker",
            "output_path": str(tmp_path / "rv_u.json"),
            "task": AgentTaskSpec(
                task_id="t-rvu",
                action="verify_record",
                audit_run_id="AUDIT-1",
                commit_sha=clean_sha,
                role="independent-finding-verifier",
                agent_id="record-v9",
                wave=1,
                attempt=1,
                project_root=str(clean_proj),
                output_filename="rv_u.json",
                payload={"finding": cand_unv.to_dict()},
            ).to_dict(),
        }
    )
    assert rv_unv["finding"]["verification_status"] == "not_verified"

    # 3. Cross-artifact multi-agent validator checks (479, 487-488, 502)
    vuln_proj, vuln_sha = _init_vuln_git_repo(tmp_path / "v_wrap")
    val_ma_dir = tmp_path / "val_ma_dir"
    cli_main(
        [
            "audit",
            "run",
            str(vuln_proj),
            "--execution-mode",
            "multi_agent_independent_sessions",
            "--runtime",
            "python-isolated-worker",
            "--output-dir",
            str(val_ma_dir),
        ]
    )
    f_json = json.loads((val_ma_dir / "findings.json").read_text(encoding="utf-8"))
    # Mark first record lacking discovery session_id & add a remediated record
    rem_copy = json.loads(json.dumps(f_json["records"][0]))
    rem_copy["fingerprint"] = "rem:fp:01"
    rem_copy["finding_id"] = finding_id_from_fingerprint("rem:fp:01")
    rem_copy["lifecycle_state"] = "remediated"
    rem_copy["state_history"].append(
        {
            "state": "remediated",
            "run_id": f_json["audit_run_id"],
            "commit_sha": vuln_sha,
            "actor": "rem-1",
            "reason": "fixed",
        }
    )
    f_json["records"][0]["discovery_provenance"].pop("session_id", None)
    f_json["records"].append(rem_copy)
    f_json["records"].sort(key=lambda x: x["fingerprint"])
    (val_ma_dir / "findings.json").write_text(json.dumps(f_json), encoding="utf-8")

    r_json = json.loads((val_ma_dir / "security-audit-report.json").read_text(encoding="utf-8"))
    r_json["execution_mode"] = "single_process_deterministic"
    (val_ma_dir / "security-audit-report.json").write_text(json.dumps(r_json), encoding="utf-8")
    v_res = validate_audit_directory(val_ma_dir)
    assert not v_res.ok
    assert any("lacks distinct multi-agent" in e for e in v_res.errors)
    assert any("report execution_mode disagrees" in e for e in v_res.errors)

    # 4. Orchestrator deterministic mock adapter covering recon fail, wave cancel, critic wave 2,
    # hunter/verifier retry exhaustion -> blocked, Phase 5 material re-verify, and post-val failure!
    seq = {"n": 0}

    def _next_sess(
        task: AgentTaskSpec,
        status: str,
        data: dict[str, Any] | None = None,
        *,
        pid: int = 90001,
        err: str | None = None,
    ) -> AgentSessionResult:
        seq["n"] += 1
        return AgentSessionResult(
            task_id=task.task_id,
            session_id=f"mock-sess-{seq['n']}",
            agent_id=task.agent_id,
            role=task.role,
            runtime_id="mock-rt",
            pid=pid if pid == os.getpid() else pid + seq["n"],
            isolated_process=(pid != os.getpid()),
            status=status,
            exit_code=0 if status == "completed" else 1,
            started_at="2026-11-26T00:00:00Z",
            completed_at="2026-11-26T00:00:01Z",
            promoted_artifact=None,
            output_data=data,
            error=err,
        )

    # 4a. Recon timeout -> blocked
    class _ReconTimeoutAdapter(AgentRuntimeAdapter):
        runtime_id = "mock-rt"

        def probe(self) -> RuntimeDescriptor:
            return RuntimeDescriptor("mock-rt", "mock", True, "/bin/true", True, "ok")

        def execute_session(
            self,
            task: AgentTaskSpec,
            *,
            audit_dir: Path,
            cancel_event: threading.Event | None = None,
        ) -> AgentSessionResult:
            return _next_sess(task, "timed_out", err="recon timed out")

    out_rt = MultiAgentAuditOrchestrator(
        project_root=vuln_proj,
        audit_dir=tmp_path / "o_recon_to",
        audit_run_id="AUDIT-RTO",
        commit_sha=vuln_sha,
        runtime=_ReconTimeoutAdapter(),
        config=OrchestrationConfig(max_retries=0),
    ).run()
    assert out_rt.status == "blocked"

    # 4b. Cancel during Wave 1 hunt (with 0 completed sessions -> single_process_deterministic)
    ev_w1 = threading.Event()

    class _CancelWave1Adapter(AgentRuntimeAdapter):
        runtime_id = "mock-rt"

        def probe(self) -> RuntimeDescriptor:
            return RuntimeDescriptor("mock-rt", "mock", True, "/bin/true", True, "ok")

        def execute_session(
            self,
            task: AgentTaskSpec,
            *,
            audit_dir: Path,
            cancel_event: threading.Event | None = None,
        ) -> AgentSessionResult:
            if task.action == "reconnaissance":
                out = execute_worker_envelope(
                    {
                        "session_id": "s-r1",
                        "runtime_id": "mock-rt",
                        "output_path": str(audit_dir / "r.json"),
                        "task": task.to_dict(),
                    }
                )
                return _next_sess(task, "completed", out)
            if task.action == "hunt_unit":
                if seq["n"] == 2:
                    out_h = execute_worker_envelope(
                        {
                            "session_id": "s-h1",
                            "runtime_id": "mock-rt",
                            "output_path": str(audit_dir / "h.json"),
                            "task": task.to_dict(),
                        }
                    )
                    return _next_sess(task, "completed", out_h, pid=os.getpid())
                if cancel_event is not None:
                    cancel_event.set()
                return _next_sess(task, "cancelled", err="cancelled")
            return _next_sess(task, "cancelled")

    out_cw1 = MultiAgentAuditOrchestrator(
        project_root=vuln_proj,
        audit_dir=tmp_path / "o_cw1",
        audit_run_id="AUDIT-CW1",
        commit_sha=vuln_sha,
        runtime=_CancelWave1Adapter(),
        config=OrchestrationConfig(max_workers=1, max_retries=0),
    ).run(cancel_event=ev_w1)
    assert out_cw1.status == "interrupted"
    assert out_cw1.execution_mode == "single_process_deterministic"

    # 4c. Critic Wave 2 reassignment + hunter/verifier retry exhaustion -> blocked
    # + Phase 5 material change re-verify!
    critic_ran = {"done": False}
    rv_calls = {"count": 0}

    class _FullScenarioAdapter(AgentRuntimeAdapter):
        runtime_id = "mock-rt"

        def probe(self) -> RuntimeDescriptor:
            return RuntimeDescriptor("mock-rt", "mock", True, "/bin/true", True, "ok")

        def execute_session(
            self,
            task: AgentTaskSpec,
            *,
            audit_dir: Path,
            cancel_event: threading.Event | None = None,
        ) -> AgentSessionResult:
            sid = f"s-full-{seq['n'] + 1}"
            if task.action == "hunt_unit":
                u_data = task.payload["unit"]
                # Make authn-authz-boundaries fail permanently -> blocked unit
                if u_data["attack_class"] == "authn-authz-boundaries":
                    return _next_sess(task, "failed", err="simulated hunter crash")
                out_h = execute_worker_envelope(
                    {
                        "session_id": sid,
                        "runtime_id": "mock-rt",
                        "output_path": str(audit_dir / "h.json"),
                        "task": task.to_dict(),
                    }
                )
                # First wave cryptographic-implementation -> partially_examined so critic reassigns!
                if u_data["attack_class"] == "cryptographic-implementation" and task.wave == 1:
                    out_h["unit"]["status"] = "partially_examined"
                    out_h["unit"]["limitations"] = ["needs wave 2 deep check"]
                return _next_sess(task, "completed", out_h)

            if task.action == "coverage_critic":
                critic_ran["done"] = True
                out_c = execute_worker_envelope(
                    {
                        "session_id": sid,
                        "runtime_id": "mock-rt",
                        "output_path": str(audit_dir / "c.json"),
                        "task": task.to_dict(),
                    }
                )
                return _next_sess(task, "completed", out_c)

            if task.action == "verify_candidate":
                cand = task.payload["candidate"]
                if cand["attack_class"] == "cryptographic-implementation":
                    return _next_sess(task, "failed", err="verifier crashed")
                out_v = execute_worker_envelope(
                    {
                        "session_id": sid,
                        "runtime_id": "mock-rt",
                        "output_path": str(audit_dir / "v.json"),
                        "task": task.to_dict(),
                    }
                )
                return _next_sess(task, "completed", out_v)

            if task.action == "verify_record":
                rv_calls["count"] += 1
                out_rv = execute_worker_envelope(
                    {
                        "session_id": sid,
                        "runtime_id": "mock-rt",
                        "output_path": str(audit_dir / "rv.json"),
                        "task": task.to_dict(),
                    }
                )
                if rv_calls["count"] == 1:
                    out_rv["materially_changed"] = True
                return _next_sess(task, "completed", out_rv)

            out_r = execute_worker_envelope(
                {
                    "session_id": sid,
                    "runtime_id": "mock-rt",
                    "output_path": str(audit_dir / "r.json"),
                    "task": task.to_dict(),
                }
            )
            return _next_sess(task, "completed", out_r)

    full_dir = tmp_path / "o_full"
    out_full = MultiAgentAuditOrchestrator(
        project_root=vuln_proj,
        audit_dir=full_dir,
        audit_run_id="AUDIT-FULL1",
        commit_sha=vuln_sha,
        runtime=_FullScenarioAdapter(),
        config=OrchestrationConfig(max_workers=2, max_retries=0),
    ).run()
    assert critic_ran["done"] is True
    assert rv_calls["count"] >= 2
    assert out_full.status == "blocked"
    assert out_full.governance_gate_status == "FAIL"


    # 4d. Cancel after critic & cancel during record verification + post-validation failure
    ev_c2 = threading.Event()

    class _CancelAfterCriticAdapter(_FullScenarioAdapter):
        def execute_session(
            self,
            task: AgentTaskSpec,
            *,
            audit_dir: Path,
            cancel_event: threading.Event | None = None,
        ) -> AgentSessionResult:
            res = super().execute_session(task, audit_dir=audit_dir, cancel_event=cancel_event)
            if task.action == "coverage_critic" and cancel_event is not None:
                cancel_event.set()
            return res

    assert (
        MultiAgentAuditOrchestrator(
            project_root=clean_proj,
            audit_dir=tmp_path / "o_cac",
            audit_run_id="AUDIT-CAC",
            commit_sha=clean_sha,
            runtime=_CancelAfterCriticAdapter(),
            config=OrchestrationConfig(max_workers=1, max_retries=0),
        )
        .run(cancel_event=ev_c2)
        .status
        == "interrupted"
    )

    ev_rv = threading.Event()

    class _CancelInRecordVerifyAdapter(_FullScenarioAdapter):
        def execute_session(
            self,
            task: AgentTaskSpec,
            *,
            audit_dir: Path,
            cancel_event: threading.Event | None = None,
        ) -> AgentSessionResult:
            if task.action == "verify_record":
                if cancel_event is not None:
                    cancel_event.set()
                return _next_sess(task, "cancelled", err="cancelled in rv")
            return super().execute_session(task, audit_dir=audit_dir, cancel_event=cancel_event)

    assert (
        MultiAgentAuditOrchestrator(
            project_root=vuln_proj,
            audit_dir=tmp_path / "o_crv",
            audit_run_id="AUDIT-CRV",
            commit_sha=vuln_sha,
            runtime=_CancelInRecordVerifyAdapter(),
            config=OrchestrationConfig(max_workers=1, max_retries=0),
        )
        .run(cancel_event=ev_rv)
        .status
        == "interrupted"
    )

    # Post-orchestration validation failure branch + non-isolated PID fallback
    from arkhon.security_audit import orchestrator as orch_mod
    from arkhon.security_audit.validators import ArtifactValidationResult

    with patch.object(
        orch_mod,
        "validate_audit_directory",
        return_value=ArtifactValidationResult(False, ("bad-bundle",)),
    ):
        out_bad_val = MultiAgentAuditOrchestrator(
            project_root=clean_proj,
            audit_dir=tmp_path / "o_badval",
            audit_run_id="AUDIT-BVAL",
            commit_sha=clean_sha,
            runtime=IsolatedSubprocessWorkerRuntime(),
            config=OrchestrationConfig(max_workers=1, max_retries=0),
        ).run()
        assert out_bad_val.status == "blocked"

    # 4e. Anti-faking guarantee: in-process mock (pid == os.getpid()) NEVER claims multi_agent!
    class _InProcessFakeAdapter(AgentRuntimeAdapter):
        runtime_id = "inproc-fake"

        def probe(self) -> RuntimeDescriptor:
            return RuntimeDescriptor("inproc-fake", "mock", True, "/bin/true", False, "inproc")

        def execute_session(
            self,
            task: AgentTaskSpec,
            *,
            audit_dir: Path,
            cancel_event: threading.Event | None = None,
        ) -> AgentSessionResult:
            out = execute_worker_envelope(
                {
                    "session_id": f"fake-{seq['n'] + 1}",
                    "runtime_id": "inproc-fake",
                    "output_path": str(audit_dir / "f.json"),
                    "task": task.to_dict(),
                }
            )
            return _next_sess(task, "completed", out, pid=os.getpid())

    fake_out = MultiAgentAuditOrchestrator(
        project_root=clean_proj,
        audit_dir=tmp_path / "o_fake_inproc",
        audit_run_id="AUDIT-FAKE",
        commit_sha=clean_sha,
        runtime=_InProcessFakeAdapter(),
        config=OrchestrationConfig(max_workers=1, max_retries=0),
    ).run()
    assert fake_out.execution_mode == "single_process_deterministic"

    # 4f. Cancel after 1st verify & record-verify (589, 672) + partial resume (440, 756, 766)
    ev_v2 = threading.Event()
    v_seen = {"n": 0}

    class _CancelSecondVerifyAdapter(AgentRuntimeAdapter):
        runtime_id = "mock-rt"

        def probe(self) -> RuntimeDescriptor:
            return RuntimeDescriptor("mock-rt", "mock", True, "/bin/true", True, "ok")

        def execute_session(
            self,
            task: AgentTaskSpec,
            *,
            audit_dir: Path,
            cancel_event: threading.Event | None = None,
        ) -> AgentSessionResult:
            out = execute_worker_envelope(
                {
                    "session_id": f"sv2-{seq['n'] + 1}",
                    "runtime_id": "mock-rt",
                    "output_path": str(audit_dir / "x.json"),
                    "task": task.to_dict(),
                }
            )
            if task.action == "verify_candidate":
                v_seen["n"] += 1
                if v_seen["n"] == 1 and cancel_event is not None:
                    cancel_event.set()
            return _next_sess(task, "completed", out)

    MultiAgentAuditOrchestrator(
        project_root=vuln_proj,
        audit_dir=tmp_path / "o_cv2",
        audit_run_id="AUDIT-CV2",
        commit_sha=vuln_sha,
        runtime=_CancelSecondVerifyAdapter(),
        config=OrchestrationConfig(max_workers=1, max_retries=0),
    ).run(cancel_event=ev_v2)

    ev_rv2 = threading.Event()
    rv_seen = {"n": 0}

    class _CancelSecondRecordAdapter(AgentRuntimeAdapter):
        runtime_id = "mock-rt"

        def probe(self) -> RuntimeDescriptor:
            return RuntimeDescriptor("mock-rt", "mock", True, "/bin/true", True, "ok")

        def execute_session(
            self,
            task: AgentTaskSpec,
            *,
            audit_dir: Path,
            cancel_event: threading.Event | None = None,
        ) -> AgentSessionResult:
            out = execute_worker_envelope(
                {
                    "session_id": f"srv2-{seq['n'] + 1}",
                    "runtime_id": "mock-rt",
                    "output_path": str(audit_dir / "x.json"),
                    "task": task.to_dict(),
                }
            )
            if task.action == "verify_record":
                rv_seen["n"] += 1
                if rv_seen["n"] == 1 and cancel_event is not None:
                    cancel_event.set()
            return _next_sess(task, "completed", out)

    MultiAgentAuditOrchestrator(
        project_root=vuln_proj,
        audit_dir=tmp_path / "o_crv2",
        audit_run_id="AUDIT-CRV2",
        commit_sha=vuln_sha,
        runtime=_CancelSecondRecordAdapter(),
        config=OrchestrationConfig(max_workers=1, max_retries=0),
    ).run(cancel_event=ev_rv2)

    # Interrupted with non-empty findings in single_process_deterministic + stale in_progress unit
    # followed by resume hitting completed_hunt_units skip (440, 756-757, 766-767)
    part_dir = tmp_path / "o_part_resume"
    ev_part = threading.Event()

    class _InProcInterruptWithFindingAdapter(_InProcessFakeAdapter):
        def execute_session(
            self,
            task: AgentTaskSpec,
            *,
            audit_dir: Path,
            cancel_event: threading.Event | None = None,
        ) -> AgentSessionResult:
            res = super().execute_session(task, audit_dir=audit_dir, cancel_event=cancel_event)
            if (
                task.action == "hunt_unit"
                and res.output_data
                and res.output_data["candidates"]
                and cancel_event is not None
            ):
                # Leave another unit in_progress in ledger to exercise _mark_partial recovery
                led_p = audit_dir / "coverage-ledger.json"
                led_obj = CoverageLedger.load(led_p)
                for u in led_obj.units:
                    if u.status == "planned":
                        u.status = "in_progress"
                        u.investigator_id = "hunter-stale"
                        break
                led_obj.save(led_p)
                cancel_event.set()
            return res

    MultiAgentAuditOrchestrator(
        project_root=vuln_proj,
        audit_dir=part_dir,
        audit_run_id="AUDIT-PR1",
        commit_sha=vuln_sha,
        runtime=_InProcInterruptWithFindingAdapter(),
        config=OrchestrationConfig(max_workers=1, max_retries=0),
    ).run(cancel_event=ev_part)

    # Reset one completed_hunt_unit to planned on disk to exercise checkpoint skip line 440
    led_pr = CoverageLedger.load(part_dir / "coverage-ledger.json")
    ckpt_pr = json.loads((part_dir / "orchestration-state.json").read_text(encoding="utf-8"))
    done_cid = ckpt_pr["completed_hunt_units"][0]
    for u in led_pr.units:
        if u.coverage_id == done_cid:
            u.status = "planned"
            u.investigator_id = None
            u.reviewed_paths = []
            u.checks = []
            u.finding_ids = []
            u.candidate_fingerprints = []
    led_pr.save(part_dir / "coverage-ledger.json")
    MultiAgentAuditOrchestrator(
        project_root=vuln_proj,
        audit_dir=part_dir,
        audit_run_id="AUDIT-PR1",
        commit_sha=vuln_sha,
        runtime=_InProcFakeAdapter(),
        config=OrchestrationConfig(max_workers=1, max_retries=0),
    ).run(resume=True)

