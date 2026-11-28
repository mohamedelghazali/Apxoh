"""Comprehensive unit tests for GENCODE-GOV independent engineering assessment upgrades."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest

from gencode_gov.assessment.drift import compute_drift_snapshot, record_and_evaluate_drift
from gencode_gov.cli_extensions import (
    build_tools_matrix,
    cmd_attest,
    cmd_diff_check,
    cmd_drift,
    register_extended_subcommands,
    render_extended_report_format,
)
from gencode_gov.core.constants import (
    ALL_RULE_DOMAINS,
    STATUS_ACCEPTED_RISK,
    STATUS_BLOCKED,
    STATUS_FAIL,
    STATUS_PASS,
)
from gencode_gov.core.errors import EvidenceError, GovernanceError
from gencode_gov.evidence.attestation import (
    create_human_attestation,
    verify_human_attestation,
)
from gencode_gov.reporting.html_reporter import HtmlReporter, _atomic_safe_write
from gencode_gov.reporting.sarif_reporter import SarifReporter
from gencode_gov.rules.evaluator import RuleEvaluator
from gencode_gov.validation import run_cli_validate, validate_repository
from gencode_gov.verification.architecture_verifier import verify_architecture_contracts
from gencode_gov.verification.assess_dispatch import (
    create_assess_runner,
    evaluate_extended_method,
    inspect_junit_artifact,
)
from gencode_gov.verification.code_and_test_integrity import (
    analyze_production_code,
    compute_cyclomatic_complexity,
    verify_code_integrity_method,
    verify_test_adequacy_method,
)
from gencode_gov.verification.diff_governance import (
    evaluate_diff_governance,
    verify_frozen_apis,
)
from gencode_gov.verification.domain_verifiers import (
    GovernanceDomainRunner,
    HumanAttestationRunner,
    evaluate_domain_method,
)
from gencode_gov.verification.methods import METHOD_REGISTRY, resolve_method, resolve_methods
from gencode_gov.verification.runners.base import RunnerOutcome, RunnerResult
from gencode_gov.verification.runners.polyglot_quality_runner import PolyglotQualityRunner

_GIT = shutil.which("git") or "/usr/bin/git"


SHA_A = "a" * 40
SHA_B = "b" * 40


def _init_git_repo(root: Path) -> str:
    subprocess.run([_GIT, "init", "-q"], cwd=root, check=True, timeout=10)  # noqa: S603
    subprocess.run(  # noqa: S603
        [_GIT, "config", "user.email", "eng@example.invalid"], cwd=root, check=True, timeout=10
    )
    subprocess.run(  # noqa: S603
        [_GIT, "config", "user.name", "ci_committer_role"], cwd=root, check=True, timeout=10
    )
    (root / "README.md").write_text("# Test Repo\n", encoding="utf-8")
    subprocess.run([_GIT, "add", "-A"], cwd=root, check=True, timeout=10)  # noqa: S603
    subprocess.run(  # noqa: S603
        [_GIT, "commit", "-q", "-m", "init"], cwd=root, check=True, timeout=10
    )
    res = subprocess.run(  # noqa: S603
        [_GIT, "rev-parse", "HEAD"],
        cwd=root,
        capture_output=True,
        text=True,
        check=True,
        timeout=10,
    )
    return res.stdout.strip()


def test_human_attestation_lifecycle_and_anti_agent_guards(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("GENCODE_GOV_AGENT_SESSION_ID", raising=False)
    monkeypatch.delenv("GENCODE_GOV_SANDBOX", raising=False)

    doc = tmp_path / "docs" / "adr" / "0001-init.md"
    doc.parent.mkdir(parents=True)
    doc.write_text("# Status\nAccepted\n", encoding="utf-8")

    # Missing attestation blocks fail-closed
    st, rsn = verify_human_attestation(tmp_path, rule_id="SE-ARC-001", expected_commit_sha=SHA_A)
    assert st == STATUS_BLOCKED
    assert "missing" in rsn

    # Invalid commit SHA blocks
    st_no_sha, _ = verify_human_attestation(
        tmp_path, rule_id="SE-ARC-001", expected_commit_sha=None
    )
    assert st_no_sha == STATUS_BLOCKED

    # Reject bot / coding-agent identities and sandbox env vars
    for bot_name in ("bot-runner", "agent-worker", "ci-worker", "x"):
        with pytest.raises(EvidenceError):
            create_human_attestation(
                tmp_path,
                rule_ids=["SE-ARC-001"],
                reviewer=bot_name,
                approver_role="architecture-lead",
                commit_sha=SHA_A,
                rationale="Reviewed architecture decision records thoroughly.",
            )

    monkeypatch.setenv("GENCODE_GOV_AGENT_SESSION_ID", "sess-123")
    with pytest.raises(EvidenceError):
        create_human_attestation(
            tmp_path,
            rule_ids=["SE-ARC-001"],
            reviewer="reviewer_role_two",
            approver_role="architecture-lead",
            commit_sha=SHA_A,
            rationale="Reviewed architecture decision records thoroughly.",
        )
    monkeypatch.delenv("GENCODE_GOV_AGENT_SESSION_ID")

    # Reject invalid role, rationale, commit, expires_days, rule_ids, missing/escaping artifacts
    with pytest.raises(EvidenceError):
        create_human_attestation(
            tmp_path / "missing_dir",
            rule_ids=["SE-ARC-001"],
            reviewer="reviewer_role_two",
            approver_role="lead",
            commit_sha=SHA_A,
            rationale="Valid rationale string.",
        )
    with pytest.raises(EvidenceError):
        create_human_attestation(
            tmp_path,
            rule_ids=["SE-ARC-001"],
            reviewer="reviewer_role_two",
            approver_role="x",
            commit_sha=SHA_A,
            rationale="Valid rationale string.",
        )
    with pytest.raises(EvidenceError):
        create_human_attestation(
            tmp_path,
            rule_ids=["SE-ARC-001"],
            reviewer="reviewer_role_two",
            approver_role="lead",
            commit_sha=SHA_A,
            rationale="short",
        )
    with pytest.raises(EvidenceError):
        create_human_attestation(
            tmp_path,
            rule_ids=["SE-ARC-001"],
            reviewer="reviewer_role_two",
            approver_role="lead",
            commit_sha="bad-sha",
            rationale="Valid rationale string.",
        )
    with pytest.raises(EvidenceError):
        create_human_attestation(
            tmp_path,
            rule_ids=["SE-ARC-001"],
            reviewer="reviewer_role_two",
            approver_role="lead",
            commit_sha=SHA_A,
            rationale="Valid rationale string.",
            expires_days=0,
        )
    with pytest.raises(EvidenceError):
        create_human_attestation(
            tmp_path,
            rule_ids=["BAD-ID"],
            reviewer="reviewer_role_two",
            approver_role="lead",
            commit_sha=SHA_A,
            rationale="Valid rationale string.",
        )
    with pytest.raises(EvidenceError):
        create_human_attestation(
            tmp_path,
            rule_ids=["SE-ARC-001"],
            reviewer="reviewer_role_two",
            approver_role="lead",
            commit_sha=SHA_A,
            rationale="Valid rationale string.",
            artifact_paths=["../sibling_file.txt"],
        )
    with pytest.raises(EvidenceError):
        create_human_attestation(
            tmp_path,
            rule_ids=["SE-ARC-001"],
            reviewer="reviewer_role_two",
            approver_role="lead",
            commit_sha=SHA_A,
            rationale="Valid rationale string.",
            artifact_paths=["docs/adr/nonexistent.md"],
        )
    sym = tmp_path / "docs" / "sym.md"
    sym.symlink_to(doc)
    with pytest.raises(EvidenceError):
        create_human_attestation(
            tmp_path,
            rule_ids=["SE-ARC-001"],
            reviewer="reviewer_role_two",
            approver_role="lead",
            commit_sha=SHA_A,
            rationale="Valid rationale string.",
            artifact_paths=["docs/sym.md"],
        )

    # Valid attestation passes for matching commit & role
    att = create_human_attestation(
        tmp_path,
        rule_ids=["SE-ARC-001"],
        reviewer="reviewer_role_two",
        approver_role="architecture-lead",
        commit_sha=SHA_A,
        rationale="Verified ADR completeness and boundary trade-offs.",
        artifact_paths=["docs/adr/0001-init.md"],
        expires_days=14,
    )
    st_ok, _ = verify_human_attestation(
        tmp_path,
        rule_id="SE-ARC-001",
        expected_commit_sha=SHA_A,
        required_role="architecture-lead",
    )
    assert st_ok == STATUS_PASS

    # Wrong role or wrong commit blocks
    st_role, _ = verify_human_attestation(
        tmp_path,
        rule_id="SE-ARC-001",
        expected_commit_sha=SHA_A,
        required_role="security-lead",
    )
    assert st_role == STATUS_BLOCKED
    st_sha, _ = verify_human_attestation(
        tmp_path,
        rule_id="SE-ARC-001",
        expected_commit_sha=SHA_B,
        required_role="architecture-lead",
    )
    assert st_sha == STATUS_BLOCKED

    # Unlisted rule blocks cleanly
    st_other, _ = verify_human_attestation(tmp_path, rule_id="SE-DB-001", expected_commit_sha=SHA_A)
    assert st_other == STATUS_BLOCKED

    # Artifact tampering invalidates attestation!
    doc.write_text("# Modified after review\n", encoding="utf-8")
    st_mod, rsn_mod = verify_human_attestation(
        tmp_path, rule_id="SE-ARC-001", expected_commit_sha=SHA_A
    )
    assert st_mod == STATUS_BLOCKED
    assert "digest" in rsn_mod

    # Malformed & expired attestation files handled safely
    (att.path.parent / "invalid_doc.json").write_text("{bad", encoding="utf-8")
    expired_payload = json.loads(att.path.read_text(encoding="utf-8"))
    expired_payload["expires_at"] = "2020-01-01T00:00:00Z"
    att.path.write_text(json.dumps(expired_payload), encoding="utf-8")
    st_exp, rsn_exp = verify_human_attestation(
        tmp_path, rule_id="SE-ARC-001", expected_commit_sha=SHA_A
    )
    assert st_exp == STATUS_BLOCKED
    assert "expired" in rsn_exp


def test_architecture_verifier_layers_and_cycles(tmp_path: Path) -> None:
    # Missing src/ and contract blocks
    rep_empty = verify_architecture_contracts(tmp_path)
    assert rep_empty.status == STATUS_BLOCKED

    pkg = tmp_path / "src" / "demo_pkg"
    (pkg / "core").mkdir(parents=True)
    (pkg / "cli").mkdir(parents=True)
    (pkg / "__init__.py").write_text("", encoding="utf-8")
    (pkg / "core" / "__init__.py").write_text("import demo_pkg.core\n", encoding="utf-8")
    (pkg / "cli" / "__init__.py").write_text(
        "from demo_pkg.core import something\n", encoding="utf-8"
    )

    # Auto-discovered clean DAG passes
    rep_clean = verify_architecture_contracts(tmp_path)
    assert rep_clean.status == STATUS_PASS

    # Introduce forbidden import + cycle
    (pkg / "core" / "bad.py").write_text("from demo_pkg.cli import run\n", encoding="utf-8")
    gov = tmp_path / ".gencode-gov"
    gov.mkdir(exist_ok=True)
    (gov / "architecture-contracts.yaml").write_text(
        "version: '1.0.0'\n"
        "package_root: 'src/demo_pkg'\n"
        "package_name: 'demo_pkg'\n"
        "max_cycles: 0\n"
        "layers:\n"
        "  - name: 'core'\n"
        "    modules: ['core']\n"
        "    forbidden_imports: ['cli']\n",
        encoding="utf-8",
    )
    rep_fail = verify_architecture_contracts(tmp_path)
    assert rep_fail.status == STATUS_FAIL
    assert rep_fail.cycles
    assert rep_fail.layer_violations

    # Malformed contract cases
    (gov / "architecture-contracts.yaml").write_text("not: [valid", encoding="utf-8")
    assert verify_architecture_contracts(tmp_path).status == STATUS_BLOCKED
    (gov / "architecture-contracts.yaml").write_text("- list_root\n", encoding="utf-8")
    assert verify_architecture_contracts(tmp_path).status == STATUS_BLOCKED
    (gov / "architecture-contracts.yaml").write_text("version: '1.0.0'\n", encoding="utf-8")
    assert verify_architecture_contracts(tmp_path).status == STATUS_BLOCKED
    (gov / "architecture-contracts.yaml").write_text(
        "version: '1.0.0'\npackage_root: '../../parent_dir'\n", encoding="utf-8"
    )
    assert verify_architecture_contracts(tmp_path).status == STATUS_BLOCKED
    (gov / "architecture-contracts.yaml").write_text(
        "version: '1.0.0'\npackage_root: 'src/missing_pkg'\n", encoding="utf-8"
    )
    assert verify_architecture_contracts(tmp_path).status == STATUS_BLOCKED


def test_code_and_test_integrity_verifiers(tmp_path: Path) -> None:
    # Empty repo passes Python production scan
    assert verify_code_integrity_method("anti-fabrication-ast-check", tmp_path)[0] == STATUS_PASS

    src = tmp_path / "src" / "app"
    src.mkdir(parents=True)
    (src / "service.py").write_text(
        "class BaseRunner(Runner):\n"
        "    def run(self):\n"
        "        raise NotImplementedError\n\n"
        "def clean_fn(x: int) -> int:\n"
        "    return x + 1 if x > 0 and x < 10 else 0\n",
        encoding="utf-8",
    )
    assert verify_code_integrity_method("anti-fabrication-ast-check", tmp_path)[0] == STATUS_PASS
    assert (
        verify_code_integrity_method("exception-handling-safety-check", tmp_path)[0] == STATUS_PASS
    )
    assert verify_code_integrity_method("complexity-budget-check", tmp_path)[0] == STATUS_PASS
    assert verify_code_integrity_method("unknown-method", tmp_path)[0] == STATUS_BLOCKED

    # Inject stub, silent except, and low complexity ceiling
    (tmp_path / ".gencode-gov").mkdir(exist_ok=True)
    (tmp_path / ".gencode-gov" / "config.yaml").write_text(
        "code_quality:\n  max_function_complexity: 5\n", encoding="utf-8"
    )
    (src / "bad.py").write_text(
        "def fabricated_feature():\n"
        "    raise NotImplementedError('todo')\n\n"
        "def swallow():\n"
        "    try:\n"
        "        risky()\n"
        "    except Exception:\n"
        "        pass\n\n"
        "def too_branchy(a, b, c, d, e, f):\n"
        "    if a and b and c and d and e and f:\n"
        "        return 1\n"
        "    return 0\n",
        encoding="utf-8",
    )
    summary = analyze_production_code(tmp_path)
    assert summary.stub_violations
    assert summary.silent_except_violations
    assert summary.complexity_violations
    assert verify_code_integrity_method("anti-fabrication-ast-check", tmp_path)[0] == STATUS_FAIL
    assert (
        verify_code_integrity_method("exception-handling-safety-check", tmp_path)[0] == STATUS_FAIL
    )
    assert verify_code_integrity_method("complexity-budget-check", tmp_path)[0] == STATUS_FAIL

    # Test adequacy checks
    assert verify_test_adequacy_method("assertion-adequacy-check", tmp_path)[0] == STATUS_BLOCKED
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()
    tfile = tests_dir / "test_sample.py"
    tfile.write_text(
        "def test_tautology():\n    assert True\n\ndef test_hollow():\n    pass\n",
        encoding="utf-8",
    )
    assert verify_test_adequacy_method("assertion-adequacy-check", tmp_path)[0] == STATUS_FAIL

    tfile.write_text("def test_real():\n    val = 2 + 2\n    assert val == 4\n", encoding="utf-8")
    assert verify_test_adequacy_method("assertion-adequacy-check", tmp_path)[0] == STATUS_PASS
    assert verify_test_adequacy_method("regression-tamper-diff-check", tmp_path)[0] == STATUS_PASS
    assert verify_test_adequacy_method("unknown", tmp_path)[0] == STATUS_BLOCKED

    # Diff test deletion detection
    base_sha = _init_git_repo(tmp_path)
    tfile.unlink()
    subprocess.run([_GIT, "add", "-A"], cwd=tmp_path, check=True, timeout=10)  # noqa: S603
    subprocess.run(  # noqa: S603
        [_GIT, "commit", "-q", "-m", "drop test"], cwd=tmp_path, check=True, timeout=10
    )
    st_del, _ = verify_test_adequacy_method(
        "regression-tamper-diff-check", tmp_path, base_ref=base_sha
    )
    assert st_del == STATUS_FAIL


def test_diff_governance_and_frozen_apis(tmp_path: Path) -> None:
    # No compatibility manifest -> PASS
    assert verify_frozen_apis(tmp_path)[0] == STATUS_PASS

    pkg = tmp_path / "src" / "pkg"
    pkg.mkdir(parents=True)
    (pkg / "mod.py").write_text(
        "API_CONST = 1\ndef run_api() -> int:\n    return 1\n", encoding="utf-8"
    )
    (tmp_path / "manifest").mkdir()
    (tmp_path / "manifest" / "compatibility.yaml").write_text(
        "frozen_apis:\n  - src/pkg/mod.py::run_api\n  - src/pkg.mod::API_CONST\n",
        encoding="utf-8",
    )
    assert verify_frozen_apis(tmp_path)[0] == STATUS_PASS

    (tmp_path / "schemas").mkdir()
    (tmp_path / "schemas" / "item.schema.json").write_text(
        json.dumps(
            {
                "type": "object",
                "properties": {
                    "kind": {"type": "string", "enum": ["a", "b"]},
                    "name": {"type": "string"},
                },
            }
        ),
        encoding="utf-8",
    )
    (tmp_path / ".gencode-gov").mkdir(exist_ok=True)
    (tmp_path / ".gencode-gov" / "project.yaml").write_text(
        "governance_files:\n  read_only:\n    - manifest/compatibility.yaml\n",
        encoding="utf-8",
    )
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_core.py").write_text(
        "def test_ok():\n    assert 1 == 1\n", encoding="utf-8"
    )
    base_sha = _init_git_repo(tmp_path)

    # Snapshot diff check passes
    snap = evaluate_diff_governance(tmp_path)
    assert snap.status == STATUS_PASS

    # Break schema + touch protected + delete test
    (tmp_path / "schemas" / "item.schema.json").write_text(
        json.dumps({"type": "object", "properties": {"kind": {"type": "string", "enum": ["a"]}}}),
        encoding="utf-8",
    )
    (tmp_path / "manifest" / "compatibility.yaml").write_text(
        "frozen_apis:\n  - src/pkg/mod.py::missing_symbol\n", encoding="utf-8"
    )
    (tmp_path / "tests" / "test_core.py").unlink()
    subprocess.run([_GIT, "add", "-A"], cwd=tmp_path, check=True, timeout=10)  # noqa: S603
    subprocess.run(  # noqa: S603
        [_GIT, "commit", "-q", "-m", "breaking"], cwd=tmp_path, check=True, timeout=10
    )

    rep = evaluate_diff_governance(tmp_path, base_ref=base_sha, max_files=1)
    assert rep.status == STATUS_FAIL
    assert rep.protected_touched
    assert rep.deleted_tests
    assert rep.frozen_api_failures
    assert rep.schema_breaking_changes
    assert rep.to_dict()["status"] == STATUS_FAIL


def test_drift_ledger_and_html_sarif_reporters(tmp_path: Path) -> None:
    (tmp_path / "src" / "pkg").mkdir(parents=True)
    (tmp_path / "src" / "pkg" / "__init__.py").write_text("", encoding="utf-8")
    (tmp_path / "src" / "pkg" / "logic.py").write_text(
        "def calc(x: int) -> int:\n    return x * 2\n", encoding="utf-8"
    )
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "pkg"\nversion = "0.1.0"\ndependencies = ["pyyaml"]\n',
        encoding="utf-8",
    )
    snap1, prior1, warn1 = record_and_evaluate_drift(tmp_path, SHA_A, persist=True)
    assert prior1 is None
    assert not warn1
    assert snap1.declared_dependencies == 1

    # Increase complexity & deps to trigger drift warnings
    branch_expr = " and ".join(f"x > {i}" for i in range(14))
    (tmp_path / "src" / "pkg" / "logic.py").write_text(
        f"def calc(x: int) -> int:\n    return 1 if ({branch_expr}) else 0\n",
        encoding="utf-8",
    )
    deps_str = ", ".join(f'"dep{i}"' for i in range(8))
    (tmp_path / "pyproject.toml").write_text(
        f'[project]\nname = "pkg"\nversion = "0.1.0"\ndependencies = [{deps_str}]\n',
        encoding="utf-8",
    )
    snap2, prior2, warn2 = record_and_evaluate_drift(tmp_path, SHA_B, persist=True)
    assert prior2 is not None
    assert len(warn2) >= 2
    assert compute_cyclomatic_complexity is not None
    snap_check = compute_drift_snapshot(tmp_path, SHA_B)
    assert snap_check.max_cyclomatic_complexity == snap2.max_cyclomatic_complexity

    # HTML-escaped HTML reporter & SARIF reporter + symlink rejection
    sample_report = {
        "project": "R&D_Project",
        "decision": "REJECTED",
        "commit_sha": SHA_A,
        "score": {"total": 72.5},
        "rules": [
            {
                "rule_id": "SE-CQ-003",
                "domain": "code-quality",
                "status": "FAIL",
                "reason": "check & verify",
            },
            {"rule_id": "SE-ARC-002", "domain": "architecture", "status": "PASS", "reason": "ok"},
        ],
    }
    html_rep = HtmlReporter()
    html_out = tmp_path / ".gencode-gov" / "reports" / "report.html"
    html_rep.write(sample_report, html_out, project_root=tmp_path)
    rendered_html = html_out.read_text(encoding="utf-8")
    assert "R&D_Project" not in rendered_html
    assert "R&amp;D_Project" in rendered_html
    assert "Content-Security-Policy" in rendered_html

    sarif_rep = SarifReporter()
    sarif_out = tmp_path / ".gencode-gov" / "reports" / "report.sarif"
    sarif_rep.write(sample_report, sarif_out, project_root=tmp_path)
    sarif_json = json.loads(sarif_out.read_text(encoding="utf-8"))
    assert sarif_json["version"] == "2.1.0"
    assert len(sarif_json["runs"][0]["results"]) == 1
    # Symlink rejection on _atomic_safe_write
    sym_target = tmp_path / "sym.html"
    sym_target.symlink_to(html_out)
    with pytest.raises(GovernanceError):
        _atomic_safe_write(sym_target, "hello", root_anchor=tmp_path)
    with pytest.raises(GovernanceError):
        _atomic_safe_write(tmp_path.parent / "parent_out.html", "hello", root_anchor=tmp_path)


def test_domain_verifiers_and_polyglot_runner_comprehensive(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("GENCODE_GOV_AGENT_SESSION_ID", raising=False)
    monkeypatch.delenv("GENCODE_GOV_SANDBOX", raising=False)

    # Runners
    assert GovernanceDomainRunner().run(tmp_path).outcome == RunnerOutcome.PASS
    assert GovernanceDomainRunner().run(tmp_path / "missing").outcome == RunnerOutcome.BLOCKED
    assert HumanAttestationRunner().run(tmp_path).outcome == RunnerOutcome.PASS
    assert HumanAttestationRunner().run(tmp_path / "missing").outcome == RunnerOutcome.BLOCKED

    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "demo"\nversion = "1.2.3"\n[tool.coverage.report]\nfail_under = 95\n',
        encoding="utf-8",
    )
    (tmp_path / "src" / "demo").mkdir(parents=True)
    init_py = tmp_path / "src" / "demo" / "__init__.py"
    init_py.write_text('__version__ = "1.2.3"\n', encoding="utf-8")
    (tmp_path / "src" / "demo" / "http_client.py").write_text(
        "import requests\ndef fetch(u: str):\n    return requests.get(u, timeout=5)\n",
        encoding="utf-8",
    )
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_demo.py").write_text(
        "def test_demo():\n    assert 2 == 2\n", encoding="utf-8"
    )
    (tmp_path / "CHANGELOG.md").write_text(
        "# Changelog\n\n## [1.2.3] - 2026-11-27\n- Added deterministic governance checks.\n",
        encoding="utf-8",
    )
    (tmp_path / "requirements.lock").write_text(
        f"pyyaml==6.0.2 --hash=sha256:{'a' * 64}\n",
        encoding="utf-8",
    )
    (tmp_path / ".github" / "workflows").mkdir(parents=True)
    (tmp_path / ".github" / "workflows" / "ci.yml").write_text(
        "name: CI\non: [push]\njobs:\n  test:\n    runs-on: ubuntu-latest\n"
        f"    steps:\n      - uses: actions/checkout@{SHA_A}\n",
        encoding="utf-8",
    )
    (tmp_path / "docs" / "adr").mkdir(parents=True)
    (tmp_path / "docs" / "adr" / "0001-arch.md").write_text(
        "## Status\nAccepted\n## Context\nNeed safety.\n"
        "## Decision\nUse AST checks.\n## Consequences\nDeterministic gates.\n",
        encoding="utf-8",
    )
    (tmp_path / "schemas").mkdir()
    (tmp_path / "schemas" / "demo.schema.json").write_text(
        json.dumps({"$id": "https://example.invalid/demo/1.0.0", "type": "object"}),
        encoding="utf-8",
    )
    gov = tmp_path / ".gencode-gov"
    gov.mkdir(exist_ok=True)
    (gov / "project.yaml").write_text("name: demo\ntype: cli-tool\n", encoding="utf-8")
    (gov / "requirements.yaml").write_text(
        "requirements:\n"
        "  - id: REQ-001\n"
        "    statement: System must verify inputs.\n"
        "    acceptance_criteria: ['Reject invalid payloads']\n"
        "    tests: ['tests/test_demo.py']\n",
        encoding="utf-8",
    )
    (gov / "critical-workflows.yaml").write_text("workflows: ['auth']\n", encoding="utf-8")
    (gov / "database-governance.yaml").write_text(
        "controls:\n  migration-file-detection: true\n  prechange-backup-verification: true\n",
        encoding="utf-8",
    )
    (gov / "reliability-governance.yaml").write_text(
        "verified_methods:\n  slo-document-presence: true\n", encoding="utf-8"
    )
    (gov / "performance-governance.yaml").write_text(
        "verified_methods:\n  load-test-execution: true\n", encoding="utf-8"
    )
    (gov / "privacy-governance.yaml").write_text(
        "verified_methods:\n  data-inventory-presence: true\n", encoding="utf-8"
    )
    (gov / "infrastructure-governance.yaml").write_text(
        "verified_methods:\n  iac-file-detection: true\n", encoding="utf-8"
    )
    (gov / "observability-governance.yaml").write_text(
        "verified_methods:\n  endpoint-detection: true\n", encoding="utf-8"
    )
    (gov / "security-controls.yaml").write_text(
        "verified_methods:\n  authentication-flow-inventory: true\n",
        encoding="utf-8",
    )
    (gov / "evidence" / "supply-chain").mkdir(parents=True, exist_ok=True)
    (gov / "evidence" / "supply-chain" / "sbom.cdx.json").write_text(
        json.dumps(
            {
                "bomFormat": "CycloneDX",
                "specVersion": "1.5",
                "components": [{"name": "pyyaml", "licenses": [{"license": {"id": "MIT"}}]}],
                "vulnerabilities": [],
            }
        ),
        encoding="utf-8",
    )

    poly_res = PolyglotQualityRunner().run(tmp_path)
    assert poly_res.outcome == RunnerOutcome.PASS

    passing_methods = [
        "schema-validation",
        "acceptance-criteria-validation",
        "requirements-conflict-analysis",
        "requirements-traceability-analysis",
        "test-traceability-analysis",
        "adr-presence-check",
        "adr-structure-validation",
        "destructive-ddl-migration-scan",
        "concurrent-index-and-lock-check",
        "migration-file-detection",
        "prechange-backup-verification",
        "api-contract-analysis",
        "endpoint-version-inventory",
        "frozen-api-contract-check",
        "schema-compatibility-diff-check",
        "workflow-file-presence",
        "branch-protection-check",
        "github-actions-sha-pinning-scan",
        "dependency-lockfile-determinism-check",
        "changelog-format-validation",
        "version-consistency-check",
        "release-notes-presence",
        "release-notes-structure-validation",
        "outbound-timeout-enforcement-scan",
        "unbounded-retry-loop-scan",
        "secret-scanner",
        "env-file-audit",
        "lockfile-inventory",
        "sbom-component-inventory-check",
        "sbom-license-and-cve-policy-check",
        "authentication-flow-inventory",
        "slo-document-presence",
        "load-test-execution",
        "data-inventory-presence",
        "iac-file-detection",
        "endpoint-detection",
        "coverage-analysis",
        "ast-test-mapping",
        "commit-message-analysis",
        "critical-workflow-test-coverage-review",
    ]
    for mid in passing_methods:
        out = evaluate_domain_method(mid, tmp_path)
        assert out is not None and out[0] == STATUS_PASS, f"{mid} -> {out}"

    # Negative domain checks: destructive SQL, missing timeout, secret pattern, AGPL SBOM
    (tmp_path / "migrations").mkdir()
    (tmp_path / "migrations" / "001_schema_change.sql").write_text(
        "DROP TABLE items;\nCREATE INDEX idx_items_code ON items(code);\n",
        encoding="utf-8",
    )
    assert evaluate_domain_method("destructive-ddl-migration-scan", tmp_path) == (
        STATUS_FAIL,
        "unguarded destructive DDL: ['migrations/001_schema_change.sql']",
    )
    assert evaluate_domain_method("concurrent-index-and-lock-check", tmp_path)[0] == STATUS_FAIL

    (tmp_path / "src" / "demo" / "client_no_timeout.py").write_text(
        "import requests\ndef hang():\n    requests.get('https://example.invalid')\n"
        "    while True:\n        x = 1\n",
        encoding="utf-8",
    )
    assert evaluate_domain_method("outbound-timeout-enforcement-scan", tmp_path)[0] == STATUS_FAIL
    assert evaluate_domain_method("unbounded-retry-loop-scan", tmp_path)[0] == STATUS_FAIL

    # Construct fake secret dynamically to avoid static secret scanner triggers
    sample_val = "sk-" + ("A" * 24)
    (tmp_path / "src" / "demo" / "sample_cfg.py").write_text(
        f'api_key = "{sample_val}"\n', encoding="utf-8"
    )
    assert evaluate_domain_method("secret-scanner", tmp_path)[0] == STATUS_FAIL

    (gov / "evidence" / "supply-chain" / "sbom.cdx.json").write_text(
        json.dumps(
            {
                "components": [{"name": "bad", "licenses": [{"license": {"id": "AGPL-3.0"}}]}],
                "vulnerabilities": [{"id": "ADV-2026-0001", "ratings": [{"severity": "critical"}]}],
            }
        ),
        encoding="utf-8",
    )
    assert evaluate_domain_method("sbom-license-and-cve-policy-check", tmp_path)[0] == STATUS_FAIL


def test_assess_dispatch_method_registry_and_rule_evaluator(tmp_path: Path) -> None:
    # GAP-01 regression check: security-audit runner instantiates without ModuleNotFoundError!
    runner_names = (
        "test-suite",
        "ruff",
        "security-audit",
        "polyglot-quality",
        "governance-domain",
        "human-attestation",
    )
    for rname in runner_names:
        assert create_assess_runner(rname) is not None
    assert create_assess_runner("unknown-runner") is None

    # JUnit XML inspector
    junit = tmp_path / "junit.xml"
    junit.write_text(
        '<testsuite tests="4" failures="0" errors="0" skipped="0"></testsuite>',
        encoding="utf-8",
    )
    assert inspect_junit_artifact(junit) == (4, 0, 0, 0)
    assert inspect_junit_artifact(tmp_path / "missing.xml") is None

    # METHOD_REGISTRY validation
    assert len(METHOD_REGISTRY) >= 115
    assert resolve_method("anti-fabrication-ast-check") is not None
    with pytest.raises(ValueError):
        resolve_method("")
    with pytest.raises(ValueError):
        resolve_methods("not-a-list")
    with pytest.raises(ValueError):
        resolve_methods(["dup", "dup"])
    with pytest.raises(ValueError):
        resolve_methods([""])

    # RuleEvaluator with PASS, BLOCKED (dirty tree), and ACCEPTED_RISK exception
    (tmp_path / "src" / "pkg").mkdir(parents=True)
    (tmp_path / "src" / "pkg" / "ok.py").write_text(
        "def add(a: int, b: int) -> int:\n    return a + b\n", encoding="utf-8"
    )
    fake_rule = SimpleNamespace(
        id="SE-CQ-003",
        raw={
            "metadata": {"domain": "code-quality", "enforcement": "blocking"},
            "verification": {"methods": ["anti-fabrication-ast-check", "complexity-budget-check"]},
            "human_review": {"required": False},
        },
    )
    ev = RuleEvaluator(tmp_path, commit_sha=SHA_A, working_tree_clean=True)
    res_ok = ev.evaluate_all([fake_rule])[0]
    assert res_ok.status == STATUS_PASS

    ev_dirty = RuleEvaluator(tmp_path, commit_sha=SHA_A, working_tree_clean=False)
    assert ev_dirty.evaluate_rule(fake_rule).status == STATUS_BLOCKED

    # Accepted risk via active exception on non-critical rule
    (tmp_path / ".gencode-gov").mkdir(exist_ok=True)
    (tmp_path / ".gencode-gov" / "exceptions.yaml").write_text(
        "exceptions:\n"
        "  - exception_id: EXC-001\n"
        "    rule_id: SE-ADR-TEST\n"
        "    scope: {path: '*'}\n    rationale: Temporary migration window approved by lead.\n"
        "    owner: Lead\n    approver: Architecture Lead\n"
        "    approved_at: '2026-01-01T00:00:00Z'\n"
        "    expires_at: '2099-01-01T00:00:00Z'\n"
        "    compensating_control: Add ADRs in sprint 4.\n",
        encoding="utf-8",
    )
    blocked_rule = SimpleNamespace(
        id="SE-ADR-TEST",
        raw={
            "metadata": {"domain": "architecture", "enforcement": "blocking"},
            "verification": {"methods": ["adr-presence-check"]},
            "human_review": {"required": True, "approver_role": "arch-lead"},
        },
    )
    ev_exc = RuleEvaluator(tmp_path, commit_sha=SHA_A, working_tree_clean=True)
    res_exc = ev_exc.evaluate_rule(blocked_rule)
    assert res_exc.status in {STATUS_ACCEPTED_RISK, STATUS_BLOCKED}

    # Extended method ruff-check & polyglot-static-quality-check
    ruff_json = tmp_path / "ruff.json"
    ruff_json.write_text("[]", encoding="utf-8")
    r_pass = RunnerResult(runner="ruff", outcome=RunnerOutcome.PASS, artifacts=[ruff_json])
    assert evaluate_extended_method("ruff-check", r_pass, tmp_path) == (
        STATUS_PASS,
        "Ruff reported zero static analysis issues",
    )
    p_pass = RunnerResult(runner="polyglot-quality", outcome=RunnerOutcome.PASS, reason="ok")
    poly_eval = evaluate_extended_method("polyglot-static-quality-check", p_pass, tmp_path)
    assert poly_eval is not None and poly_eval[0] == STATUS_PASS


def test_cli_extensions_and_repository_validator(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("GENCODE_GOV_AGENT_SESSION_ID", raising=False)
    monkeypatch.delenv("GENCODE_GOV_SANDBOX", raising=False)

    repo_root = Path(__file__).resolve().parents[3]
    val_summary = validate_repository(repo_root)
    assert val_summary.ok, f"Repository validation errors: {val_summary.errors}"
    assert val_summary.rules_checked >= 47
    assert run_cli_validate(repo_root, as_json=True) == 0
    assert run_cli_validate(repo_root, as_json=False) == 0

    # Parser registration & CLI extension handlers
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command")
    register_extended_subcommands(sub, lambda _p: SHA_A)

    sha = _init_git_repo(tmp_path)
    att_args = parser.parse_args(
        [
            "attest",
            str(tmp_path),
            "--rule",
            "SE-ARC-001",
            "--reviewer",
            "reviewer_role_three",
            "--role",
            "architecture-lead",
            "--rationale",
            "Reviewed architecture boundaries and approved.",
            "--commit",
            sha,
            "--json",
        ]
    )
    assert cmd_attest(att_args, commit_resolver=lambda _p: sha) == 0

    diff_args = parser.parse_args(["diff-check", str(tmp_path), "--json"])
    assert cmd_diff_check(diff_args) == 0

    drift_args = parser.parse_args(["drift", str(tmp_path), "--json"])
    assert cmd_drift(drift_args, commit_resolver=lambda _p: sha) == 0

    matrix = build_tools_matrix(repo_root, repo_root)
    assert any(row["language"] == "python" for row in matrix)
    assert set(ALL_RULE_DOMAINS)

    html_dest = tmp_path / "out.html"
    sarif_dest = tmp_path / "out.sarif"
    payload = {"project": "demo", "decision": "APPROVED", "score": {"total": 100}, "rules": []}
    assert render_extended_report_format("html", payload, html_dest, tmp_path) == 0
    assert render_extended_report_format("sarif", payload, sarif_dest, tmp_path) == 0
    assert render_extended_report_format("json", payload, None, tmp_path) is None


def test_repository_frozen_apis_and_clean_integration(tmp_path: Path) -> None:
    from gencode_gov.assessment.gates import evaluate
    from gencode_gov.cli import main as cli_main
    from gencode_gov.config import load_manifest
    from gencode_gov.evidence.store import read_evidence

    repo_root = Path(__file__).resolve().parents[3]
    assert callable(cli_main)
    assert callable(load_manifest)
    assert callable(read_evidence)
    assert callable(evaluate)
    assert verify_frozen_apis(repo_root)[0] == STATUS_PASS
    assert not (repo_root / "staging").exists()
    assert not (repo_root / ".github" / "workflows" / "recon_full_audit.yml").exists()

    # Package __init__.py fallback when frozen_apis specifies module.py path
    pkg_dir = tmp_path / "src" / "demo_pkg" / "cfg"
    pkg_dir.mkdir(parents=True)
    (pkg_dir / "__init__.py").write_text(
        "def load_manifest() -> dict:\n    return {}\n", encoding="utf-8"
    )
    (tmp_path / "manifest").mkdir()
    (tmp_path / "manifest" / "compatibility.yaml").write_text(
        "frozen_apis:\n  - src/demo_pkg/cfg.py::load_manifest\n",
        encoding="utf-8",
    )
    assert verify_frozen_apis(tmp_path)[0] == STATUS_PASS
    assert read_evidence(tmp_path, "testing") is not None
