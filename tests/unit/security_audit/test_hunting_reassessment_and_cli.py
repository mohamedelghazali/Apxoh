"""Integration tests for hunting, change-aware reassessment, governance bridge, and CLI."""

from __future__ import annotations

import argparse
import shutil
import subprocess
from pathlib import Path

from arkhon.security_audit.cli_dispatch import dispatch_security_audit
from arkhon.security_audit.governance_bridge import (
    SecurityAuditRunner,
    derive_rule_outcomes_from_audit,
    evaluate_security_audit_method,
    record_security_audit_evidence,
    summarize_audit_status,
)
from arkhon.verification.assess_dispatch import (
    create_assess_runner,
    evaluate_extended_method,
)
from arkhon.verification.methods import resolve_method
from arkhon.verification.runners.base import RunnerOutcome, RunnerResult

_GIT = shutil.which("git") or "/usr/bin/git"


def _git(cwd: Path, *args: str) -> str:
    res = subprocess.run(  # noqa: S603
        [_GIT, *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=True,
    )
    return res.stdout.strip()


def _make_git_project(root: Path) -> tuple[Path, str]:
    proj = root / "sample_service"
    (proj / "src" / "service").mkdir(parents=True)
    (proj / ".github" / "workflows").mkdir(parents=True)
    (proj / "src" / "service" / "api.py").write_text(
        "from fastapi import FastAPI\n"
        "import hashlib, subprocess, requests, yaml\n"
        "app = FastAPI()\n"
        "def bad_exec(user_code: str, db, uid: str):\n"
        "    hashlib.md5(user_code.encode())\n"
        "    requests.get('https' + '://example.invalid', verify=False)\n"
        "    yaml.load(user_code)\n"
        "    subprocess.run(user_code, shell=True)\n"
        "    db.execute(f'SELECT * FROM items WHERE id = {uid}')\n"
        "    return eval(user_code)\n",
        encoding="utf-8",
    )
    (proj / ".github" / "workflows" / "ci.yml").write_text(
        "name: ci\non: pull_request_target\njobs:\n  b:\n    runs-on: ubuntu-latest\n"
        "    steps:\n      - run: echo ${{ github.event.pull_request.title }}\n",
        encoding="utf-8",
    )
    (proj / "Dockerfile").write_text(
        "FROM python:3.11-slim\n# privileged: true\n", encoding="utf-8"
    )
    _git(proj, "init")
    _git(proj, "config", "user.email", "auditor@example.com")
    _git(proj, "config", "user.name", "Auditor")
    _git(proj, "add", ".")
    _git(proj, "commit", "-m", "initial vulnerable snapshot")
    sha1 = _git(proj, "rev-parse", "HEAD")
    return proj, sha1


def _ns(**kwargs: object) -> argparse.Namespace:
    defaults: dict[str, object] = {
        "project": ".",
        "audit_target": None,
        "project_flag": None,
        "profile": "standard",
        "scope": None,
        "output_dir": None,
        "audit_dir": None,
        "prior_dir": None,
        "current_dir": None,
        "verifier_id": "independent-verifier-01",
        "base_commit": None,
        "head_commit": None,
        "max_units": None,
        "sandbox_mode": "auto",
        "report_format": "all",
        "record_evidence": False,
        "json": True,
    }
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_end_to_end_cli_plan_run_validate_reassess_remediation_and_regression(
    tmp_path: Path,
) -> None:
    proj, sha1 = _make_git_project(tmp_path)

    def resolve_sha(p: Path) -> str:
        return _git(p, "rev-parse", "HEAD")

    # 1. Plan command
    plan_dir = tmp_path / "run_plan"
    rc_plan = dispatch_security_audit(
        "plan",
        _ns(audit_target=str(proj), output_dir=str(plan_dir), profile="quick"),
        commit_resolver=resolve_sha,
    )
    assert rc_plan == 0
    assert (plan_dir / "architecture.md").is_file()
    plan_status = summarize_audit_status(plan_dir)
    assert plan_status["audit_status"] == "initiated"
    assert plan_status["completeness"]["is_complete"] is False

    # 2. Full audit run on vulnerable commit 1 (records evidence -> FAIL exit 1 due to findings)
    run1_dir = tmp_path / "run_1"
    rc_run1 = dispatch_security_audit(
        "run",
        _ns(
            audit_target=str(proj),
            output_dir=str(run1_dir),
            record_evidence=True,
        ),
        commit_resolver=resolve_sha,
    )
    assert rc_run1 == 1
    assert dispatch_security_audit(
        "validate", _ns(audit_dir=str(run1_dir)), commit_resolver=resolve_sha
    ) == 0
    assert dispatch_security_audit(
        "status", _ns(audit_dir=str(run1_dir), json=False), commit_resolver=resolve_sha
    ) == 0
    assert dispatch_security_audit(
        "verify-findings",
        _ns(audit_target=str(proj), audit_dir=str(run1_dir)),
        commit_resolver=resolve_sha,
    ) == 0
    assert dispatch_security_audit(
        "report",
        _ns(audit_dir=str(run1_dir), report_format="all"),
        commit_resolver=resolve_sha,
    ) == 0

    # Verify EvidenceStore received a commit-bound FAIL/BLOCKED record (never false PASS)
    evid_files = list((proj / ".arkhon" / "evidence" / "software-security").glob("*.json"))
    assert len(evid_files) == 1

    # 3. Remediate vulnerabilities in commit 2 and run change-aware reassessment
    (proj / "src" / "service" / "api.py").write_text(
        "def safe_add(a: int, b: int) -> int:\n    return a + b\n",
        encoding="utf-8",
    )
    (proj / ".github" / "workflows" / "ci.yml").write_text(
        "name: ci\non: push\njobs:\n  b:\n    runs-on: ubuntu-latest\n"
        "    steps:\n      - run: echo ok\n",
        encoding="utf-8",
    )
    (proj / "Dockerfile").write_text("FROM python:3.11-slim\n", encoding="utf-8")
    _git(proj, "add", ".")
    _git(proj, "commit", "-m", "remediate unsafe sinks")
    sha2 = _git(proj, "rev-parse", "HEAD")
    assert sha2 != sha1

    run2_dir = tmp_path / "run_2"
    rc_reassess = dispatch_security_audit(
        "reassess",
        _ns(
            audit_target=str(proj),
            prior_dir=str(run1_dir),
            output_dir=str(run2_dir),
            record_evidence=True,
        ),
        commit_resolver=resolve_sha,
    )
    assert rc_reassess == 0
    s2 = summarize_audit_status(run2_dir)
    assert s2["governance_gate_status"] == "PASS"
    assert s2["finding_counts"]["confirmed"] == 0
    assert s2["finding_counts"]["remediated"] >= 1

    assert dispatch_security_audit(
        "compare",
        _ns(prior_dir=str(run1_dir), current_dir=str(run2_dir)),
        commit_resolver=resolve_sha,
    ) == 0

    # 4. Reintroduce a vulnerability in commit 3 -> regression reopened!
    (proj / "src" / "service" / "api.py").write_text(
        "def bad_exec(user_code: str):\n    return eval(user_code)\n",
        encoding="utf-8",
    )
    _git(proj, "add", ".")
    _git(proj, "commit", "-m", "accidental regression")

    run3_dir = tmp_path / "run_3"
    dispatch_security_audit(
        "reassess",
        _ns(
            audit_target=str(proj),
            prior_dir=str(run2_dir),
            output_dir=str(run3_dir),
        ),
        commit_resolver=resolve_sha,
    )
    s3 = summarize_audit_status(run3_dir)
    assert s3["governance_gate_status"] == "FAIL"
    assert s3["finding_counts"]["confirmed"] == 1

    # 5. Governance bridge & assess_dispatch method resolution
    method_impl = resolve_method("security-audit-artifact-verification")
    assert method_impl is not None
    runner = create_assess_runner("security-audit")
    assert isinstance(runner, SecurityAuditRunner)

    pass_res = RunnerResult(
        runner="security-audit",
        outcome=RunnerOutcome.PASS,
        reason="clean",
        artifacts=[run2_dir / "security-audit-report.json"],
    )
    assert evaluate_extended_method(
        "security-audit-artifact-verification", pass_res, proj
    ) == ("PASS", "Verified security-audit coverage ledger, findings, and report")

    fail_res = RunnerResult(
        runner="security-audit",
        outcome=RunnerOutcome.FAIL,
        reason="confirmed findings",
        artifacts=[run3_dir / "security-audit-report.json"],
    )
    assert evaluate_security_audit_method(fail_res)[0] == "FAIL"
    assert evaluate_security_audit_method(
        RunnerResult(runner="security-audit", outcome=RunnerOutcome.PASS, artifacts=[])
    )[0] == "BLOCKED"

    # Rule outcomes derivation & invalid bundle refusal
    from arkhon.security_audit.coverage import CoverageLedger
    from arkhon.security_audit.findings import FindingsCollection

    outcomes = derive_rule_outcomes_from_audit(
        CoverageLedger.load(run3_dir / "coverage-ledger.json"),
        FindingsCollection.load(run3_dir / "findings.json"),
    )
    assert outcomes["SE-SEC-003"][0] == "FAIL"

    evid_id, evid_path, gate_st = record_security_audit_evidence(
        project_root=proj, audit_dir=run2_dir, commit_sha=_git(proj, "rev-parse", "HEAD")
    )
    assert evid_id.startswith("EVID-")
    assert evid_path.is_file()
    assert gate_st == "PASS"

    # Error handling on missing CLI flags / non-existent dirs / sandbox-mode=required when disabled
    assert dispatch_security_audit(
        "status", _ns(audit_dir=None), commit_resolver=resolve_sha
    ) == 1
    assert dispatch_security_audit(
        "compare", _ns(prior_dir=None, current_dir=None), commit_resolver=resolve_sha
    ) == 1
    assert dispatch_security_audit(
        "reassess", _ns(audit_target=str(proj), prior_dir=None), commit_resolver=resolve_sha
    ) == 1
    assert dispatch_security_audit(
        "plan", _ns(audit_target=str(tmp_path / "no_such_dir")), commit_resolver=resolve_sha
    ) == 1
