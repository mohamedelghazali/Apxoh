"""Edge-branch and negative-path unit tests for 100% governance statement coverage."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest

from gencode_gov.assessment.drift import record_and_evaluate_drift
from gencode_gov.cli_extensions import (
    build_tools_matrix,
    cmd_attest,
    cmd_diff_check,
    cmd_drift,
    register_extended_subcommands,
    render_extended_report_format,
)
from gencode_gov.core.constants import STATUS_BLOCKED, STATUS_FAIL, STATUS_PASS
from gencode_gov.core.errors import EvidenceError, GovernanceError
from gencode_gov.evidence.attestation import (
    _parse_utc,
    create_human_attestation,
    verify_human_attestation,
)
from gencode_gov.reporting.html_reporter import HtmlReporter, _atomic_safe_write
from gencode_gov.reporting.sarif_reporter import SarifReporter
from gencode_gov.rules.evaluator import RuleEvaluator
from gencode_gov.validation import run_cli_validate, validate_repository
from gencode_gov.verification.architecture_verifier import _extract_submodules
from gencode_gov.verification.code_and_test_integrity import (
    analyze_production_code,
    verify_test_adequacy_method,
)
from gencode_gov.verification.diff_governance import (
    evaluate_diff_governance,
    verify_frozen_apis,
)
from gencode_gov.verification.domain_verifiers import evaluate_domain_method
from gencode_gov.verification.runners.base import Runner, RunnerOutcome, RunnerResult
from gencode_gov.verification.runners.polyglot_quality_runner import PolyglotQualityRunner

_GIT = shutil.which("git") or "/usr/bin/git"


SHA_1 = "1" * 40
SHA_2 = "2" * 40


def test_attestation_and_drift_symlink_and_timestamp_edges(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("GENCODE_GOV_AGENT_SESSION_ID", raising=False)
    monkeypatch.delenv("GENCODE_GOV_SANDBOX", raising=False)

    with pytest.raises(EvidenceError):
        _parse_utc("not-a-date", "attested_at")
    with pytest.raises(EvidenceError):
        _parse_utc("2026-01-01T00:00:00", "attested_at")

    # Symlinked .gencode-gov rejected in create_human_attestation
    real_dir = tmp_path / "real"
    real_dir.mkdir()
    p1 = tmp_path / "p1"
    p1.mkdir()
    (p1 / ".gencode-gov").symlink_to(real_dir)
    with pytest.raises(EvidenceError):
        create_human_attestation(
            p1,
            rule_ids=["SE-ARC-001"],
            reviewer="lead_reviewer_role",
            approver_role="lead",
            commit_sha=SHA_1,
            rationale="Valid rationale text here.",
        )

    p2 = tmp_path / "p2"
    (p2 / ".gencode-gov").mkdir(parents=True)
    (p2 / ".gencode-gov" / "evidence").symlink_to(real_dir)
    with pytest.raises(EvidenceError):
        create_human_attestation(
            p2,
            rule_ids=["SE-ARC-001"],
            reviewer="lead_reviewer_role",
            approver_role="lead",
            commit_sha=SHA_1,
            rationale="Valid rationale text here.",
        )

    p3 = tmp_path / "p3"
    (p3 / ".gencode-gov" / "evidence").mkdir(parents=True)
    (p3 / ".gencode-gov" / "evidence" / "attestations").symlink_to(real_dir)
    with pytest.raises(EvidenceError):
        create_human_attestation(
            p3,
            rule_ids=["SE-ARC-001"],
            reviewer="lead_reviewer_role",
            approver_role="lead",
            commit_sha=SHA_1,
            rationale="Valid rationale text here.",
        )

    # Bot reviewer & bad timestamp inside stored attestation JSON
    p4 = tmp_path / "p4"
    att_dir = p4 / ".gencode-gov" / "evidence" / "attestations"
    att_dir.mkdir(parents=True)
    (att_dir / "ATTEST-AUTO0001.json").write_text(
        json.dumps(
            {
                "attestation_id": "ATTEST-AUTO0001",
                "rule_ids": ["SE-ARC-001"],
                "reviewer": "bot-service",
                "approver_role": "lead",
                "commit_sha": SHA_1,
                "attested_at": "2026-01-01T00:00:00Z",
                "expires_at": "2026-02-01T00:00:00Z",
                "rationale": "Automated service check.",
                "reviewed_artifacts": [],
            }
        ),
        encoding="utf-8",
    )
    (att_dir / "ATTEST-BADTIME1.json").write_text(
        json.dumps(
            {
                "attestation_id": "ATTEST-BADTIME1",
                "rule_ids": ["SE-ARC-001"],
                "reviewer": "lead_reviewer_role",
                "approver_role": "lead",
                "commit_sha": SHA_1,
                "attested_at": "bad-date",
                "expires_at": "2026-02-01T00:00:00Z",
                "rationale": "Malformed timestamp test.",
                "reviewed_artifacts": [],
            }
        ),
        encoding="utf-8",
    )
    st, rsn = verify_human_attestation(p4, rule_id="SE-ARC-001", expected_commit_sha=SHA_1)
    assert st == STATUS_BLOCKED
    assert "bot/agent" in rsn and "invalid attested_at" in rsn

    # Drift symlink guards & active_exceptions increase warning
    p_drift = tmp_path / "p_drift"
    (p_drift / ".gencode-gov").mkdir(parents=True)
    (p_drift / ".gencode-gov" / "state").symlink_to(real_dir)
    with pytest.raises(GovernanceError):
        record_and_evaluate_drift(p_drift, SHA_1)

    p_drift2 = tmp_path / "p_drift2"
    (p_drift2 / ".gencode-gov" / "state").mkdir(parents=True)
    dummy_file = tmp_path / "dummy.jsonl"
    dummy_file.write_text("", encoding="utf-8")
    (p_drift2 / ".gencode-gov" / "state" / "drift-ledger.jsonl").symlink_to(dummy_file)
    with pytest.raises(GovernanceError):
        record_and_evaluate_drift(p_drift2, SHA_1)

    p_drift3 = tmp_path / "p_drift3"
    p_drift3.mkdir()
    record_and_evaluate_drift(p_drift3, SHA_1, persist=True)
    exc_dir = p_drift3 / "system" / "policies" / "exceptions"
    exc_dir.mkdir(parents=True)
    (exc_dir / "registry.yaml").write_text(
        "exceptions:\n"
        "  - exception_id: EXC-99\n"
        "    rule_id: SE-ARC-001\n"
        "    scope: {path: '*'}\n    rationale: Approved temporary exception.\n"
        "    owner: Lead\n    approver: Lead\n"
        "    approved_at: '2026-01-01T00:00:00Z'\n"
        "    expires_at: '2099-01-01T00:00:00Z'\n"
        "    compensating_control: Complete ADR.\n",
        encoding="utf-8",
    )
    _, _, warnings = record_and_evaluate_drift(p_drift3, SHA_2, persist=False)
    assert any("exceptions" in w for w in warnings)


def test_cli_extensions_text_modes_and_errors(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("GENCODE_GOV_AGENT_SESSION_ID", raising=False)
    monkeypatch.delenv("GENCODE_GOV_SANDBOX", raising=False)

    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command")
    register_extended_subcommands(sub, lambda _p: None)

    # cmd_attest missing commit & error path & text output
    args_no_sha = parser.parse_args(
        [
            "attest",
            str(tmp_path),
            "--rule",
            "SE-ARC-001",
            "--reviewer",
            "lead_reviewer_role",
            "--role",
            "lead",
            "--rationale",
            "Valid rationale text.",
        ]
    )
    assert cmd_attest(args_no_sha, commit_resolver=lambda _p: None) == 1

    args_bad = parser.parse_args(
        [
            "attest",
            str(tmp_path),
            "--rule",
            "SE-ARC-001",
            "--reviewer",
            "ci-worker",
            "--role",
            "lead",
            "--rationale",
            "Valid rationale text.",
            "--commit",
            SHA_1,
        ]
    )
    assert cmd_attest(args_bad, commit_resolver=lambda _p: SHA_1) == 1

    args_txt = parser.parse_args(
        [
            "attest",
            str(tmp_path),
            "--rule",
            "SE-ARC-001",
            "--reviewer",
            "lead_reviewer_role",
            "--role",
            "lead",
            "--rationale",
            "Valid rationale text.",
            "--commit",
            SHA_1,
        ]
    )
    assert cmd_attest(args_txt, commit_resolver=lambda _p: SHA_1) == 0

    # cmd_diff_check text mode with failure
    (tmp_path / "manifest").mkdir()
    (tmp_path / "manifest" / "compatibility.yaml").write_text(
        "frozen_apis:\n  - bad_entry_without_colons\n", encoding="utf-8"
    )
    diff_txt = parser.parse_args(["diff-check", str(tmp_path)])
    assert cmd_diff_check(diff_txt) == 1

    # cmd_drift text mode + symlink error
    drift_txt = parser.parse_args(["drift", str(tmp_path)])
    assert cmd_drift(drift_txt, commit_resolver=lambda _p: SHA_1) == 0

    bad_drift = tmp_path / "bad_drift"
    (bad_drift / ".gencode-gov").mkdir(parents=True)
    (bad_drift / ".gencode-gov" / "state").symlink_to(tmp_path / "manifest")
    d_args = parser.parse_args(["drift", str(bad_drift)])
    assert cmd_drift(d_args, commit_resolver=lambda _p: SHA_1) == 1

    # render_extended_report_format to stdout + non-dict rule entries + parent symlink error
    payload = {"project": "p", "rules": ["skip-me"]}
    assert render_extended_report_format("html", payload, None, tmp_path) == 0
    assert render_extended_report_format("sarif", payload, None, tmp_path) == 0
    capsys.readouterr()

    sym_parent = tmp_path / "sym_parent"
    sym_parent.symlink_to(tmp_path / "manifest")
    with pytest.raises(GovernanceError):
        _atomic_safe_write(sym_parent / "r.html", "x")
    assert HtmlReporter().render(payload)
    assert SarifReporter().to_sarif(payload)

    # build_tools_matrix with custom languages dir
    fake_langs = tmp_path / "langs_root"
    (fake_langs / "languages").mkdir(parents=True)
    assert build_tools_matrix(tmp_path, fake_langs)


def test_evaluator_validator_and_diff_edge_branches(tmp_path: Path) -> None:
    # RuleEvaluator: unregistered method, disallowed domain, custom runner PASS/FAIL/BLOCKED
    class CustomRunner(Runner):
        name = "mypy"

        def __init__(self, outcome: RunnerOutcome) -> None:
            self._outcome = outcome

        def run(self, project_root: Path, artifact_dir: Path | None = None) -> RunnerResult:
            _ = project_root, artifact_dir
            return RunnerResult(runner="mypy", outcome=self._outcome, reason="done")

    r_unreg = SimpleNamespace(
        id="SE-CQ-999",
        raw={
            "metadata": {"domain": "code-quality", "enforcement": "blocking"},
            "verification": {"methods": ["nonexistent-method", "slo-document-presence"]},
        },
    )
    ev = RuleEvaluator(tmp_path, commit_sha=SHA_1)
    assert ev.evaluate_rule(r_unreg).status == STATUS_BLOCKED

    r_mypy = SimpleNamespace(
        id="SE-CQ-002",
        raw={
            "metadata": {"domain": "code-quality", "enforcement": "critical"},
            "verification": {"methods": ["type-checker-execution"]},
        },
    )
    assert (
        RuleEvaluator(
            tmp_path,
            commit_sha=SHA_1,
            runner_overrides={"mypy": CustomRunner(RunnerOutcome.PASS)},
        )
        .evaluate_rule(r_mypy)
        .status
        == STATUS_PASS
    )
    assert (
        RuleEvaluator(
            tmp_path,
            commit_sha=SHA_1,
            runner_overrides={"mypy": CustomRunner(RunnerOutcome.FAIL)},
        )
        .evaluate_rule(r_mypy)
        .status
        == STATUS_FAIL
    )
    assert (
        RuleEvaluator(
            tmp_path,
            commit_sha=SHA_1,
            runner_overrides={"mypy": CustomRunner(RunnerOutcome.BLOCKED)},
        )
        .evaluate_rule(r_mypy)
        .status
        == STATUS_BLOCKED
    )
    # Missing runner override
    r_tsar = SimpleNamespace(
        id="SE-SEC-GOV-001",
        raw={
            "metadata": {"domain": "software-security", "enforcement": "critical"},
            "verification": {"methods": ["tsar-audit-invocation"]},
        },
    )
    assert RuleEvaluator(tmp_path, commit_sha=SHA_1).evaluate_rule(r_tsar).status == STATUS_BLOCKED

    # validation.py negative branches (schemas, duplicate rules, links, wheel)
    wheel_sim = tmp_path / "wheel_only"
    wheel_sim.mkdir()
    assert validate_repository(wheel_sim).rules_checked == 0

    bad_repo = tmp_path / "bad_repo"
    (bad_repo / "rules" / "testing").mkdir(parents=True)
    (bad_repo / "languages" / "python" / "rules").mkdir(parents=True)
    (bad_repo / "schemas").mkdir(parents=True)
    (bad_repo / "schemas" / "bad.json").write_text("{invalid", encoding="utf-8")
    dup_yaml = (
        "id: SE-TST-901\n"
        "metadata:\n  domain: architecture\n"
        "verification:\n  methods: [missing-m, ruff-check]\n"
    )
    (bad_repo / "rules" / "testing" / "SE-TST-901.yaml").write_text(dup_yaml, encoding="utf-8")
    (bad_repo / "languages" / "python" / "rules" / "SE-TST-901.yaml").write_text(
        dup_yaml, encoding="utf-8"
    )
    (bad_repo / "skills" / "demo").mkdir(parents=True)
    (bad_repo / "skills" / "demo" / "SKILL.md").write_text(
        "No frontmatter [bad](missing.md) [rel](../missing_ref.md) [anchor](#ok)\n",
        encoding="utf-8",
    )
    (bad_repo / "agents").mkdir()
    (bad_repo / "agents" / "_roles.yaml").write_text(
        "roles:\n  - id: dev\n    rule_domains: [testing]\n    skills: [unknown-skill]\n",
        encoding="utf-8",
    )
    (bad_repo / "README.md").write_text("# Doc\nSee [missing](docs/nope.md).\n", encoding="utf-8")
    bad_summary = validate_repository(bad_repo)
    assert not bad_summary.ok
    assert run_cli_validate(bad_repo, as_json=False) == 1

    # Invalid YAML in _roles.yaml & missing schemas dir
    no_schema_repo = tmp_path / "no_schema"
    (no_schema_repo / "rules").mkdir(parents=True)
    (no_schema_repo / "agents").mkdir()
    (no_schema_repo / "agents" / "_roles.yaml").write_text("bad: [yaml", encoding="utf-8")
    assert not validate_repository(no_schema_repo).ok

    # architecture_verifier Import statement & 3-node cycle
    assert "sub" in _extract_submodules("import pkg.sub.mod\n", "pkg", "core")

    # code_and_test_integrity decorators, docstrings, helper calls, non-Python tests, git diff
    c_repo = tmp_path / "c_repo"
    (c_repo / "src").mkdir(parents=True)
    (c_repo / "src" / "abs.py").write_text(
        "import abc\n"
        "class Base:\n"
        '    """Doc."""\n'
        "    @abc.abstractmethod\n"
        "    def f(self):\n"
        '        """Method doc."""\n'
        "        raise NotImplementedError\n"
        "    @overload\n"
        "    def g(self):\n"
        "        raise NotImplementedError\n"
        "def raw_raise():\n"
        "    raise NotImplementedError\n",
        encoding="utf-8",
    )
    c_sum = analyze_production_code(c_repo)
    assert len(c_sum.stub_violations) == 1

    # Non-Python test file path
    np_repo = tmp_path / "np_repo"
    np_repo.mkdir()
    (np_repo / "app.spec.ts").write_text("expect(1).toBe(1);", encoding="utf-8")
    assert verify_test_adequacy_method("assertion-adequacy-check", np_repo)[0] == STATUS_PASS

    # Python test file with 0 test_* functions, and one with pytest.raises helper
    py_empty = tmp_path / "py_empty"
    py_empty.mkdir()
    (py_empty / "test_none.py").write_text("def helper():\n    return 1\n", encoding="utf-8")
    assert verify_test_adequacy_method("assertion-adequacy-check", py_empty)[0] == STATUS_BLOCKED

    (py_empty / "test_raises.py").write_text(
        "import pytest\ndef test_err():\n    with pytest.raises(ValueError):\n        int('x')\n",
        encoding="utf-8",
    )
    assert verify_test_adequacy_method("assertion-adequacy-check", py_empty)[0] == STATUS_PASS
    assert (
        verify_test_adequacy_method("regression-tamper-diff-check", py_empty, base_ref="badref")[0]
        == STATUS_BLOCKED
    )

    # diff_governance malformed compatibility.yaml, ImportFrom symbol, clean diff, deleted schema
    d_repo = tmp_path / "d_repo"
    (d_repo / "manifest").mkdir(parents=True)
    (d_repo / "manifest" / "compatibility.yaml").write_text("bad: [yaml", encoding="utf-8")
    assert verify_frozen_apis(d_repo)[0] == STATUS_BLOCKED
    assert evaluate_diff_governance(d_repo, base_ref="HEAD").status == STATUS_BLOCKED

    (d_repo / "manifest" / "compatibility.yaml").write_text("- list\n", encoding="utf-8")
    assert verify_frozen_apis(d_repo)[0] == STATUS_BLOCKED
    compat_p = d_repo / "manifest" / "compatibility.yaml"
    compat_p.write_text("frozen_apis: 'str'\n", encoding="utf-8")
    assert verify_frozen_apis(d_repo)[0] == STATUS_BLOCKED
    (d_repo / "manifest" / "compatibility.yaml").write_text("frozen_apis: []\n", encoding="utf-8")
    assert verify_frozen_apis(d_repo)[0] == STATUS_PASS

    (d_repo / "src").mkdir()
    (d_repo / "src" / "reexport.py").write_text(
        "from math import sqrt as exported_sqrt\n", encoding="utf-8"
    )
    (d_repo / "manifest" / "compatibility.yaml").write_text(
        "frozen_apis:\n  - src/reexport.py::exported_sqrt\n", encoding="utf-8"
    )
    assert verify_frozen_apis(d_repo)[0] == STATUS_PASS

    (d_repo / "schemas").mkdir()
    (d_repo / "schemas" / "s.json").write_text('{"type": "object"}', encoding="utf-8")
    subprocess.run([_GIT, "init", "-q"], cwd=d_repo, check=True, timeout=10)  # noqa: S603
    subprocess.run(  # noqa: S603
        [_GIT, "config", "user.email", "a@b.c"], cwd=d_repo, check=True, timeout=10
    )
    subprocess.run(  # noqa: S603
        [_GIT, "config", "user.name", "A"], cwd=d_repo, check=True, timeout=10
    )
    subprocess.run([_GIT, "add", "-A"], cwd=d_repo, check=True, timeout=10)  # noqa: S603
    subprocess.run(  # noqa: S603
        [_GIT, "commit", "-q", "-m", "c1"], cwd=d_repo, check=True, timeout=10
    )
    b_sha = subprocess.run(  # noqa: S603
        [_GIT, "rev-parse", "HEAD"],
        cwd=d_repo,
        capture_output=True,
        text=True,
        check=True,
        timeout=10,
    ).stdout.strip()
    assert evaluate_diff_governance(d_repo, base_ref=b_sha).status == STATUS_PASS
    assert evaluate_diff_governance(d_repo, base_ref="nonexistent_ref").status == STATUS_BLOCKED

    # Delete schema & corrupt modified schema
    (d_repo / "schemas" / "s.json").unlink()
    subprocess.run([_GIT, "add", "-A"], cwd=d_repo, check=True, timeout=10)  # noqa: S603
    subprocess.run(  # noqa: S603
        [_GIT, "commit", "-q", "-m", "del"], cwd=d_repo, check=True, timeout=10
    )
    assert evaluate_diff_governance(d_repo, base_ref=b_sha).status == STATUS_FAIL

    # PolyglotQualityRunner missing root
    assert PolyglotQualityRunner().run(tmp_path / "nope").outcome == RunnerOutcome.BLOCKED

    # Additional domain_verifiers negative/fallback branches
    empty_p = tmp_path / "empty_p"
    empty_p.mkdir()
    for blocked_m in (
        "schema-validation",
        "adr-presence-check",
        "api-contract-analysis",
        "branch-protection-check",
        "github-actions-sha-pinning-scan",
        "version-consistency-check",
        "release-notes-presence",
        "sbom-component-inventory-check",
        "authentication-flow-inventory",
        "slo-document-presence",
        "coverage-analysis",
        "commit-message-analysis",
        "critical-workflow-test-coverage-review",
        "human-review",
    ):
        assert evaluate_domain_method(blocked_m, empty_p) is not None
    assert evaluate_domain_method("workflow-file-presence", empty_p)[0] == STATUS_FAIL
    lock_res = evaluate_domain_method("dependency-lockfile-determinism-check", empty_p)
    assert lock_res is not None and lock_res[0] == STATUS_FAIL
    assert evaluate_domain_method("changelog-format-validation", empty_p)[0] == STATUS_FAIL
    assert evaluate_domain_method("ast-analysis", empty_p)[0] == STATUS_PASS


def test_domain_verifiers_all_remaining_error_and_fallback_branches(tmp_path: Path) -> None:
    req_p = tmp_path / "req_p"
    (req_p / ".gencode-gov").mkdir(parents=True)
    req_f = req_p / ".gencode-gov" / "requirements.yaml"
    req_f.write_text("requirements: []\n", encoding="utf-8")
    assert evaluate_domain_method("schema-validation", req_p)[0] == STATUS_FAIL
    req_f.write_text("requirements:\n  - 'not-a-dict'\n", encoding="utf-8")
    assert evaluate_domain_method("schema-validation", req_p)[0] == STATUS_FAIL
    req_f.write_text("requirements:\n  - id: ''\n    statement: ''\n", encoding="utf-8")
    assert evaluate_domain_method("schema-validation", req_p)[0] == STATUS_FAIL
    req_f.write_text(
        "requirements:\n"
        "  - id: R1\n    statement: s1\n    conflicts_with: R2\n"
        "  - id: R1\n    statement: s2\n    tests: ['missing.py']\n",
        encoding="utf-8",
    )
    assert evaluate_domain_method("acceptance-criteria-validation", req_p)[0] == STATUS_FAIL
    assert evaluate_domain_method("requirements-conflict-analysis", req_p)[0] == STATUS_FAIL
    assert evaluate_domain_method("requirements-traceability-analysis", req_p)[0] == STATUS_FAIL
    assert evaluate_domain_method("test-traceability-analysis", req_p)[0] == STATUS_FAIL

    adr_p = tmp_path / "adr_p"
    (adr_p / "docs" / "adr").mkdir(parents=True)
    (adr_p / "docs" / "adr" / "0001-bad.md").write_text("# Incomplete ADR\n", encoding="utf-8")
    assert evaluate_domain_method("adr-structure-validation", adr_p)[0] == STATUS_FAIL

    db_p = tmp_path / "db_p"
    (db_p / "migrations").mkdir(parents=True)
    (db_p / "migrations" / "001_ok.sql").write_text(
        "-- gencode-gov:allow-destructive-migration\nDROP TABLE old_tmp;\n",
        encoding="utf-8",
    )
    assert evaluate_domain_method("destructive-ddl-migration-scan", db_p)[0] == STATUS_PASS
    assert evaluate_domain_method("migration-file-detection", db_p)[0] == STATUS_BLOCKED
    (db_p / ".gencode-gov").mkdir()
    (db_p / ".gencode-gov" / "database-governance.yaml").write_text("- list\n", encoding="utf-8")
    assert evaluate_domain_method("migration-file-detection", db_p)[0] == STATUS_FAIL
    (db_p / ".gencode-gov" / "database-governance.yaml").write_text(
        "controls:\n  migration-file-detection: false\n", encoding="utf-8"
    )
    assert evaluate_domain_method("migration-file-detection", db_p)[0] == STATUS_FAIL

    api_p = tmp_path / "api_p"
    (api_p / "schemas").mkdir(parents=True)
    (api_p / "schemas" / "bad.schema.json").write_text("{bad", encoding="utf-8")
    assert evaluate_domain_method("api-contract-analysis", api_p)[0] == STATUS_FAIL
    (api_p / "schemas" / "bad.schema.json").write_text('{"$id": "unversioned"}', encoding="utf-8")
    assert evaluate_domain_method("endpoint-version-inventory", api_p)[0] == STATUS_FAIL
    (api_p / "manifest").mkdir()
    (api_p / "manifest" / "compatibility.yaml").write_text(
        "frozen_apis:\n  - src/missing.py::fn\n", encoding="utf-8"
    )
    assert evaluate_domain_method("frozen-api-contract-check", api_p)[0] == STATUS_FAIL

    dev_p = tmp_path / "dev_p"
    (dev_p / ".github" / "workflows").mkdir(parents=True)
    (dev_p / ".github" / "workflows" / "ci.yml").write_text(
        "steps:\n"
        "  - uses: slsa-framework/slsa-github-generator/"
        ".github/workflows/generator_generic_slsa3.yml@v2.1.0\n"
        "  - uses: ./local-action\n"
        "  - uses: actions/checkout@v4\n"
        "  - uses: broken-no-at\n",
        encoding="utf-8",
    )
    assert evaluate_domain_method("github-actions-sha-pinning-scan", dev_p)[0] == STATUS_FAIL

    mnt_p = tmp_path / "mnt_p"
    mnt_p.mkdir()
    (mnt_p / "CHANGELOG.md").write_text("just plain text\n", encoding="utf-8")
    assert evaluate_domain_method("changelog-format-validation", mnt_p)[0] == STATUS_FAIL
    assert evaluate_domain_method("release-notes-structure-validation", mnt_p)[0] == STATUS_FAIL
    (mnt_p / "pyproject.toml").write_text("bad = [toml", encoding="utf-8")
    assert evaluate_domain_method("version-consistency-check", mnt_p)[0] == STATUS_FAIL
    (mnt_p / "pyproject.toml").write_text("[project]\nname = 'x'\n", encoding="utf-8")
    assert evaluate_domain_method("version-consistency-check", mnt_p)[0] == STATUS_FAIL
    (mnt_p / "pyproject.toml").write_text(
        "[project]\nname = 'x'\nversion = '1.0.0'\n", encoding="utf-8"
    )
    (mnt_p / "src" / "x").mkdir(parents=True)
    (mnt_p / "src" / "x" / "__init__.py").write_text('__version__ = "2.0.0"\n', encoding="utf-8")
    assert evaluate_domain_method("version-consistency-check", mnt_p)[0] == STATUS_FAIL

    sec_p = tmp_path / "sec_p"
    sec_p.mkdir()
    (sec_p / ".env").write_text("FOO=bar\n", encoding="utf-8")
    assert evaluate_domain_method("env-file-audit", sec_p)[0] == STATUS_FAIL
    (sec_p / "requirements.lock").write_text(
        f"pyyaml==6.0.2 --hash=sha256:{'a' * 64}\n",
        encoding="utf-8",
    )
    (sec_p / "pyproject.toml").write_text("license = 'AGPL-3.0'\n", encoding="utf-8")
    assert evaluate_domain_method("sbom-component-inventory-check", sec_p)[0] == STATUS_PASS
    assert evaluate_domain_method("sbom-license-and-cve-policy-check", sec_p)[0] == STATUS_FAIL
    (sec_p / "pyproject.toml").write_text("license = 'MIT'\n", encoding="utf-8")
    assert evaluate_domain_method("sbom-license-and-cve-policy-check", sec_p)[0] == STATUS_PASS
    (sec_p / "sbom.cdx.json").write_text("{invalid", encoding="utf-8")
    assert evaluate_domain_method("sbom-component-inventory-check", sec_p)[0] == STATUS_FAIL
    (sec_p / "sbom.cdx.json").write_text('{"components": []}', encoding="utf-8")
    assert evaluate_domain_method("sbom-component-inventory-check", sec_p)[0] == STATUS_FAIL

    (sec_p / ".gencode-gov").mkdir()
    (sec_p / ".gencode-gov" / "security-controls.yaml").write_text("- bad\n", encoding="utf-8")
    assert evaluate_domain_method("authentication-flow-inventory", sec_p)[0] == STATUS_FAIL
    (sec_p / ".gencode-gov" / "security-controls.yaml").write_text(
        "verified_methods:\n  authentication-flow-inventory: false\n", encoding="utf-8"
    )
    assert evaluate_domain_method("authentication-flow-inventory", sec_p)[0] == STATUS_FAIL
    (sec_p / ".gencode-gov" / "security-controls.yaml").write_text(
        "verified_methods: {}\n", encoding="utf-8"
    )
    assert evaluate_domain_method("authentication-flow-inventory", sec_p)[0] == STATUS_BLOCKED

    (sec_p / ".gencode-gov" / "reliability-governance.yaml").write_text("- bad\n", encoding="utf-8")
    assert evaluate_domain_method("slo-document-presence", sec_p)[0] == STATUS_FAIL
    (sec_p / ".gencode-gov" / "reliability-governance.yaml").write_text(
        "verified_methods:\n  slo-document-presence: false\n", encoding="utf-8"
    )
    assert evaluate_domain_method("slo-document-presence", sec_p)[0] == STATUS_FAIL
    (sec_p / ".gencode-gov" / "reliability-governance.yaml").write_text(
        "verified_methods: {}\n", encoding="utf-8"
    )
    assert evaluate_domain_method("prechange-backup-verification", sec_p)[0] == STATUS_BLOCKED
    (sec_p / ".gencode-gov" / "observability-verification.yaml").write_text(
        "verified_methods:\n  endpoint-detection: true\n", encoding="utf-8"
    )
    assert evaluate_domain_method("endpoint-detection", sec_p)[0] == STATUS_PASS

    tst_p = tmp_path / "tst_p"
    (tst_p / "src").mkdir(parents=True)
    (tst_p / "src" / "m.py").write_text("x = 1\n", encoding="utf-8")
    assert evaluate_domain_method("ast-test-mapping", tst_p)[0] == STATUS_FAIL
    no_src = tmp_path / "no_src"
    no_src.mkdir()
    assert evaluate_domain_method("ast-test-mapping", no_src)[0] == STATUS_PASS

    cov_dir = tst_p / ".gencode-gov" / "evidence" / "testing"
    cov_dir.mkdir(parents=True)
    (cov_dir / "coverage.json").write_text("{bad", encoding="utf-8")
    assert evaluate_domain_method("coverage-analysis", tst_p)[0] == STATUS_FAIL
    cov_f = cov_dir / "coverage.json"
    cov_f.write_text('{"totals": {"percent_covered": 50.0}}', encoding="utf-8")
    assert evaluate_domain_method("coverage-analysis", tst_p)[0] == STATUS_FAIL
    cov_f.write_text('{"totals": {"percent_covered": 92.0}}', encoding="utf-8")
    assert evaluate_domain_method("coverage-analysis", tst_p)[0] == STATUS_PASS
    (tst_p / "pyproject.toml").write_text("bad = [toml", encoding="utf-8")
    assert evaluate_domain_method("coverage-analysis", tst_p)[0] == STATUS_FAIL
    (tst_p / ".gencode-gov" / "critical-workflows.yaml").write_text("- bad\n", encoding="utf-8")
    assert evaluate_domain_method("critical-workflow-test-coverage-review", tst_p)[0] == STATUS_FAIL

    att_d = tst_p / ".gencode-gov" / "evidence" / "attestations"
    att_d.mkdir(parents=True)
    (att_d / "a.json").write_text('{"rule_ids": ["SE-ARC-001"]}', encoding="utf-8")
    assert evaluate_domain_method("human-review", tst_p)[0] == STATUS_BLOCKED
    rule_obj = SimpleNamespace(
        id="SE-ARC-001",
        raw={"human_review": {"required": True, "approver_role": "arch-lead"}},
    )
    hr_res = evaluate_domain_method("human-review", tst_p, rule=rule_obj, commit_sha=SHA_1)
    assert hr_res is not None and hr_res[0] == STATUS_BLOCKED
