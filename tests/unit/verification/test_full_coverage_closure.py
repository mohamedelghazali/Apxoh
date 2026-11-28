"""Targeted branch-closure and regression-audit tests achieving 100% coverage."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest

from gencode_gov import cli as cli_mod
from gencode_gov import validation as val_mod
from gencode_gov.evidence import attestation as att_mod
from gencode_gov.rules import evaluator as eval_mod
from gencode_gov.verification import assess_dispatch as ad_mod
from gencode_gov.verification import code_and_test_integrity as cti_mod
from gencode_gov.verification import diff_governance as dg_mod
from gencode_gov.verification import domain_verifiers as dv_mod
from gencode_gov.verification.runners import base as rb_mod

_GIT = shutil.which("git") or "/usr/bin/git"
SHA_1 = "1" * 40


def _git_init(root: Path) -> str:
    subprocess.run([_GIT, "init", "-q"], cwd=root, check=True, timeout=10)  # noqa: S603
    subprocess.run(  # noqa: S603
        [_GIT, "config", "user.email", "ci@test.local"], cwd=root, check=True
    )
    subprocess.run(  # noqa: S603
        [_GIT, "config", "user.name", "CI"], cwd=root, check=True
    )
    subprocess.run([_GIT, "add", "-A"], cwd=root, check=True, timeout=10)  # noqa: S603
    subprocess.run(  # noqa: S603
        [_GIT, "commit", "-q", "-m", "init"], cwd=root, check=True, timeout=10
    )
    out = subprocess.run(  # noqa: S603
        [_GIT, "rev-parse", "HEAD"],
        cwd=root,
        capture_output=True,
        text=True,
        check=True,
    )
    return out.stdout.strip()


def test_cli_and_drift_text_warning_branches(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    assert cli_mod.main(["validate", "--json"]) == 0
    capsys.readouterr()
    assert cli_mod.main(["validate", "--root", str(tmp_path), "--json"]) == 0
    capsys.readouterr()
    monkeypatch.setattr(cli_mod, "_repo_root", lambda: tmp_path)
    monkeypatch.chdir(tmp_path)
    assert cli_mod.main(["validate", "--json"]) == 0
    capsys.readouterr()

    assert cli_mod.main(["assess", str(tmp_path / "missing"), "--json"]) == 1
    capsys.readouterr()

    fake_proc = SimpleNamespace(stdout="\nR  a.txt -> .gencode-gov/reports/r.json\n")
    monkeypatch.setattr(subprocess, "run", lambda *_a, **_kw: fake_proc)
    assert cli_mod._working_tree_clean(tmp_path) is True


def test_drift_text_warnings_and_evaluator_blocked_fallback(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    p = tmp_path / "drift_repo"
    (p / "src").mkdir(parents=True)
    (p / "src" / "a.py").write_text("def f() -> int:\n    return 1\n", encoding="utf-8")
    _git_init(p)
    assert cli_mod.main(["drift", str(p)]) == 0
    capsys.readouterr()

    branches = "".join(f"    if x == {i}:\n        return {i}\n" for i in range(12))
    complex_fn = "def g(x: int) -> int:\n" + branches + "    return 0\n"
    (p / "src" / "a.py").write_text(complex_fn, encoding="utf-8")
    (p / "pyproject.toml").write_text(
        '[project]\nname = "d"\ndependencies = ["pyyaml", "jsonschema"]\n',
        encoding="utf-8",
    )
    subprocess.run([_GIT, "add", "-A"], cwd=p, check=True, timeout=10)  # noqa: S603
    subprocess.run(  # noqa: S603
        [_GIT, "commit", "-q", "-m", "grow"], cwd=p, check=True, timeout=10
    )
    assert cli_mod.main(["drift", str(p)]) == 0
    assert "[WARN]" in capsys.readouterr().out

    res_pass = rb_mod.RunnerResult(
        runner="polyglot-quality", outcome=rb_mod.RunnerOutcome.PASS, reason="ok"
    )
    res_fail = rb_mod.RunnerResult(
        runner="polyglot-quality", outcome=rb_mod.RunnerOutcome.FAIL, reason="bad"
    )
    obs = ad_mod.evaluate_extended_method(
        "observability-behavior-test-verification", res_pass, tmp_path
    )
    assert obs is not None
    p_ok = ad_mod.evaluate_extended_method(
        "polyglot-static-quality-check", res_pass, tmp_path
    )
    p_bad = ad_mod.evaluate_extended_method(
        "polyglot-static-quality-check", res_fail, tmp_path
    )
    assert p_ok is not None and p_ok[0] == "PASS"
    assert p_bad is not None and p_bad[0] == "FAIL"

    r_hr = SimpleNamespace(
        id="SE-ARC-001",
        raw={
            "metadata": {"domain": "architecture", "enforcement": "blocking"},
            "verification": {"methods": ["adr-presence-check"]},
            "human_review": {"required": True, "approver_role": "lead"},
        },
    )
    ev = eval_mod.RuleEvaluator(tmp_path, commit_sha=SHA_1)
    assert ev.evaluate_rule(r_hr).status == "BLOCKED"

    class BlockedRunner(rb_mod.Runner):
        name = "mypy"

        def run(
            self, project_root: Path, artifact_dir: Path | None = None
        ) -> rb_mod.RunnerResult:
            _ = project_root, artifact_dir
            return rb_mod.RunnerResult(
                runner="mypy", outcome=rb_mod.RunnerOutcome.BLOCKED, reason="blocked"
            )

    r_mypy = SimpleNamespace(
        id="SE-CQ-002",
        raw={
            "metadata": {"domain": "code-quality", "enforcement": "critical"},
            "verification": {"methods": ["type-checker-execution"]},
        },
    )
    monkeypatch.setattr(eval_mod, "evaluate_extended_method", lambda *_a, **_kw: None)
    ev_blk = eval_mod.RuleEvaluator(
        tmp_path, commit_sha=SHA_1, runner_overrides={"mypy": BlockedRunner()}
    )
    assert ev_blk.evaluate_rule(r_mypy).status == "BLOCKED"


def test_validation_integrity_and_diff_edge_branches(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo_root = Path(__file__).resolve().parents[3]
    vroot = tmp_path / "val_missing_rules"
    (vroot / "schemas").mkdir(parents=True)
    monkeypatch.setattr(val_mod, "__file__", str(tmp_path / "pkg" / "validation.py"))
    assert not val_mod.validate_repository(vroot).ok

    vroot2 = tmp_path / "val_bad_rules"
    (vroot2 / "rules").mkdir(parents=True)
    (vroot2 / "schemas").mkdir(parents=True)
    shutil.copy2(
        repo_root / "schemas" / "rule.schema.json",
        vroot2 / "schemas" / "rule.schema.json",
    )
    (vroot2 / "rules" / "bad.yaml").write_text("id: [unclosed\n", encoding="utf-8")
    (vroot2 / "rules" / "SE-TST-999.yaml").write_text(
        "id: SE-TST-999\n"
        "metadata:\n"
        "  title: Extra Field Rule\n"
        "  domain: testing\n"
        "  version: 1.0.0\n"
        "  status: active\n"
        "  severity: high\n"
        "  enforcement: blocking\n"
        "  description: Valid load with extra schema error.\n"
        "unexpected_top_key: true\n",
        encoding="utf-8",
    )
    (vroot2 / "skills" / "demo").mkdir(parents=True)
    (vroot2 / "skills" / "demo" / "SKILL.md").write_text(
        "---\nname: demo\ndescription: Demo skill.\n---\n"
        "See [sec](#top) and [out](../../../../outside.md).\n",
        encoding="utf-8",
    )
    assert not val_mod.validate_repository(vroot2).ok

    croot = tmp_path / "cti_repo"
    (croot / "src").mkdir(parents=True)
    (croot / "tests").mkdir(parents=True)
    (croot / "schemas").mkdir(parents=True)
    (croot / ".gencode-gov").mkdir(parents=True)
    (croot / ".gencode-gov" / "config.yaml").write_text("bad: [\n", encoding="utf-8")
    (croot / "schemas" / "s.schema.json").write_text(
        '{"type": "object"}\n', encoding="utf-8"
    )
    (croot / "src" / "stub.py").write_text(
        'def f() -> None:\n    """Docstring."""\n    raise NotImplementedError\n',
        encoding="utf-8",
    )
    (croot / "src" / "unit_test.py").write_text("x = 1\n", encoding="utf-8")
    (croot / "tests" / "test_keep.py").write_text(
        "def test_ok() -> None:\n    assert 1 == 1\n", encoding="utf-8"
    )
    (croot / "tests" / "test_del.py").write_text(
        "def test_gone() -> None:\n    assert 2 == 2\n", encoding="utf-8"
    )
    base_sha = _git_init(croot)
    assert (
        cti_mod.verify_test_adequacy_method(
            "regression-tamper-diff-check", croot, base_ref=base_sha
        )[0]
        == "PASS"
    )
    (croot / "tests" / "test_broken.py").write_text("def bad(:\n", encoding="utf-8")
    assert cti_mod.analyze_production_code(croot).stub_violations
    assert (
        cti_mod.verify_test_adequacy_method("assertion-adequacy-check", croot)[0]
        == "PASS"
    )
    (croot / "tests" / "test_broken.py").unlink()
    (croot / "tests" / "test_del.py").unlink()
    (croot / "schemas" / "s.schema.json").write_text("{broken\n", encoding="utf-8")
    subprocess.run([_GIT, "add", "-A"], cwd=croot, check=True, timeout=10)  # noqa: S603
    subprocess.run(  # noqa: S603
        [_GIT, "commit", "-q", "-m", "del test"], cwd=croot, check=True, timeout=10
    )
    assert (
        cti_mod.verify_test_adequacy_method(
            "regression-tamper-diff-check", croot, base_ref=base_sha
        )[0]
        == "FAIL"
    )

    rep_bad_schema = dg_mod.evaluate_diff_governance(croot, base_ref=base_sha)
    assert rep_bad_schema.schema_breaking_changes

    (croot / "manifest").mkdir(parents=True)
    (croot / "manifest" / "compatibility.yaml").write_text("bad: [\n", encoding="utf-8")
    rep_blk = dg_mod.evaluate_diff_governance(croot, base_ref=base_sha, max_files=0)
    assert rep_blk.status == "BLOCKED"


def test_domain_verifiers_all_remaining_branches(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("GENCODE_GOV_AGENT_SESSION_ID", raising=False)
    monkeypatch.delenv("GENCODE_GOV_SANDBOX", raising=False)

    empty_d = tmp_path / "empty_dom"
    empty_d.mkdir()
    for blk_method in (
        "github-actions-sha-pinning-scan",
        "release-notes-presence",
        "sbom-component-inventory-check",
        "api-contract-analysis",
        "version-consistency-check",
        "test-diff-analysis",
        "human-review",
    ):
        res_blk = dv_mod.evaluate_domain_method(blk_method, empty_d)
        assert res_blk is not None and res_blk[0] == "BLOCKED"

    d = tmp_path / "dom"
    (d / "migrations").mkdir(parents=True)
    (d / "migrations" / "001_safe.sql").write_text(
        "CREATE INDEX CONCURRENTLY idx_ok ON items(id);\n", encoding="utf-8"
    )
    assert dv_mod.evaluate_domain_method("concurrent-index-and-lock-check", d) == (
        "PASS",
        "scanned 1 migration(s); index locks safe",
    )

    (d / "manifest").mkdir(parents=True)
    (d / "manifest" / "compatibility.yaml").write_text("bad: [\n", encoding="utf-8")
    assert dv_mod.evaluate_domain_method("frozen-api-contract-check", d)[0] == "BLOCKED"

    fake_diff = SimpleNamespace(
        status="FAIL",
        reasons=("schema break",),
        frozen_api_failures=(),
        schema_breaking_changes=("schemas/a.json: removed id",),
    )
    monkeypatch.setattr(dv_mod, "evaluate_diff_governance", lambda _r: fake_diff)
    assert (
        dv_mod.evaluate_domain_method("schema-compatibility-diff-check", d)[0] == "FAIL"
    )

    (d / "schemas").mkdir(parents=True)
    real_s = d / "schemas" / "ok.schema.json"
    real_s.write_text('{"$id": "urn:gencode-gov:ok:1.0.0"}\n', encoding="utf-8")
    (d / "schemas" / "sym.schema.json").symlink_to(real_s)
    assert dv_mod.evaluate_domain_method("api-contract-analysis", d)[0] == "PASS"

    assert dv_mod._verify_devops_methods("unknown-devops", d)[0] == "BLOCKED"
    assert dv_mod._verify_maintenance_methods("unknown-maint", d)[0] == "BLOCKED"
    assert dv_mod._verify_testing_auxiliary_methods("unknown-test", d)[0] == "BLOCKED"

    # Dedicated RELEASE_NOTES.md presence, unstructured FAIL, and structured PASS
    (d / "RELEASE_NOTES.md").write_text("short", encoding="utf-8")
    assert dv_mod.evaluate_domain_method("release-notes-presence", d)[0] == "PASS"
    assert (
        dv_mod.evaluate_domain_method("release-notes-structure-validation", d)[0]
        == "FAIL"
    )
    (d / "RELEASE_NOTES.md").write_text(
        "# Release Notes\n\n## 1.0.0 - 2026-11-28\n- Verified governance controls.\n",
        encoding="utf-8",
    )
    assert (
        dv_mod.evaluate_domain_method("release-notes-structure-validation", d)[0]
        == "PASS"
    )

    (d / "pyproject.toml").write_text(
        '[project]\nname = "x"\nversion = "1.0.0"\n', encoding="utf-8"
    )
    (d / "src" / "real_pkg").mkdir(parents=True)
    real_init = d / "src" / "real_pkg" / "__init__.py"
    real_init.write_text('__version__ = "1.0.0"\n', encoding="utf-8")
    (d / "src" / "sym_pkg").mkdir(parents=True)
    (d / "src" / "sym_pkg" / "__init__.py").symlink_to(real_init)
    assert dv_mod.evaluate_domain_method("version-consistency-check", d)[0] == "PASS"

    (d / "src" / "examples").mkdir(parents=True)
    (d / "src" / "examples" / "skip.py").write_text("x = 1\n", encoding="utf-8")
    (d / "src" / "real_pkg" / "bad_syn.py").write_text("def bad(:\n", encoding="utf-8")
    assert (
        dv_mod.evaluate_domain_method("outbound-timeout-enforcement-scan", d)[0]
        == "PASS"
    )

    (d / "big.py").write_text("x = 1\n" + ("#" * (260 * 1024)), encoding="utf-8")
    assert dv_mod.evaluate_domain_method("secret-scanner", d)[0] == "PASS"

    (d / "sbom.cdx.json").write_text(
        '{"components": ["skip-str", {"name": "a"}], "vulnerabilities": []}\n',
        encoding="utf-8",
    )
    assert (
        dv_mod.evaluate_domain_method("sbom-license-and-cve-policy-check", d)[0]
        == "PASS"
    )

    # Strict BLOCKED and PASS behavioral checks for test-diff-analysis
    assert dv_mod.evaluate_domain_method("test-diff-analysis", d)[0] == "BLOCKED"
    (d / "tests").mkdir(parents=True)
    (d / "tests" / "test_sample.py").write_text(
        "def test_sample() -> None:\n    assert 1 == 1\n", encoding="utf-8"
    )
    assert dv_mod.evaluate_domain_method("test-diff-analysis", d)[0] == "PASS"

    # Human-review malformed/empty BLOCKED and verified commit-bound PASS across aliases
    att_dir = d / ".gencode-gov" / "evidence" / "attestations"
    att_dir.mkdir(parents=True)
    (att_dir / "01_bad.json").write_text("{broken\n", encoding="utf-8")
    (att_dir / "02_empty.json").write_text('{"rule_ids": []}\n', encoding="utf-8")
    assert (
        dv_mod.evaluate_domain_method("human-review", d, commit_sha=SHA_1)[0]
        == "BLOCKED"
    )
    hr_rule = SimpleNamespace(
        id="SE-ARC-001", raw={"human_review": {"approver_role": "arch-lead"}}
    )
    assert (
        dv_mod.evaluate_domain_method(
            "human-review", d, rule=hr_rule, commit_sha=SHA_1
        )[0]
        == "BLOCKED"
    )
    att_mod.create_human_attestation(
        d,
        rule_ids=["SE-ARC-001"],
        reviewer="lead_reviewer_human",
        approver_role="arch-lead",
        commit_sha=SHA_1,
        rationale="Reviewed architecture boundaries and approved commit.",
    )
    for hr_method in ("human-review", "human-security-review", "human-approval"):
        assert (
            dv_mod.evaluate_domain_method(
                hr_method, d, rule=hr_rule, commit_sha=SHA_1
            )[0]
            == "PASS"
        )
    assert (
        dv_mod.evaluate_domain_method("human-review", d, commit_sha=SHA_1)[0] == "PASS"
    )

from types import SimpleNamespace

import pytest

from gencode_gov import cli as cli_mod
from gencode_gov import validation as val_mod
from gencode_gov.rules import evaluator as eval_mod
from gencode_gov.verification import assess_dispatch as ad_mod
from gencode_gov.verification import code_and_test_integrity as cti_mod
from gencode_gov.verification import diff_governance as dg_mod
from gencode_gov.verification import domain_verifiers as dv_mod
from gencode_gov.verification.runners import base as rb_mod

_GIT = shutil.which("git") or "/usr/bin/git"
SHA_1 = "1" * 40


def _git_init(root: Path) -> str:
    subprocess.run([_GIT, "init", "-q"], cwd=root, check=True, timeout=10)  # noqa: S603
    subprocess.run(  # noqa: S603
        [_GIT, "config", "user.email", "ci@test.local"], cwd=root, check=True
    )
    subprocess.run(  # noqa: S603
        [_GIT, "config", "user.name", "CI"], cwd=root, check=True
    )
    subprocess.run([_GIT, "add", "-A"], cwd=root, check=True, timeout=10)  # noqa: S603
    subprocess.run(  # noqa: S603
        [_GIT, "commit", "-q", "-m", "init"], cwd=root, check=True, timeout=10
    )
    out = subprocess.run(  # noqa: S603
        [_GIT, "rev-parse", "HEAD"],
        cwd=root,
        capture_output=True,
        text=True,
        check=True,
    )
    return out.stdout.strip()


def test_cli_and_drift_text_warning_branches(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    assert cli_mod.main(["validate", "--json"]) == 0
    capsys.readouterr()
    assert cli_mod.main(["validate", "--root", str(tmp_path), "--json"]) == 0
    capsys.readouterr()
    monkeypatch.setattr(cli_mod, "_repo_root", lambda: tmp_path)
    monkeypatch.chdir(tmp_path)
    assert cli_mod.main(["validate", "--json"]) == 0
    capsys.readouterr()

    assert cli_mod.main(["assess", str(tmp_path / "missing"), "--json"]) == 1
    capsys.readouterr()

    fake_proc = SimpleNamespace(stdout="\nR  a.txt -> .gencode-gov/reports/r.json\n")
    monkeypatch.setattr(subprocess, "run", lambda *_a, **_kw: fake_proc)
    assert cli_mod._working_tree_clean(tmp_path) is True


def test_drift_text_warnings_and_evaluator_blocked_fallback(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    p = tmp_path / "drift_repo"
    (p / "src").mkdir(parents=True)
    (p / "src" / "a.py").write_text("def f() -> int:\n    return 1\n", encoding="utf-8")
    _git_init(p)
    assert cli_mod.main(["drift", str(p)]) == 0
    capsys.readouterr()

    branches = "".join(f"    if x == {i}:\n        return {i}\n" for i in range(12))
    complex_fn = "def g(x: int) -> int:\n" + branches + "    return 0\n"
    (p / "src" / "a.py").write_text(complex_fn, encoding="utf-8")
    (p / "pyproject.toml").write_text(
        '[project]\nname = "d"\ndependencies = ["pyyaml", "jsonschema"]\n',
        encoding="utf-8",
    )
    subprocess.run([_GIT, "add", "-A"], cwd=p, check=True, timeout=10)  # noqa: S603
    subprocess.run(  # noqa: S603
        [_GIT, "commit", "-q", "-m", "grow"], cwd=p, check=True, timeout=10
    )
    assert cli_mod.main(["drift", str(p)]) == 0
    assert "[WARN]" in capsys.readouterr().out

    res_pass = rb_mod.RunnerResult(
        runner="polyglot-quality", outcome=rb_mod.RunnerOutcome.PASS, reason="ok"
    )
    res_fail = rb_mod.RunnerResult(
        runner="polyglot-quality", outcome=rb_mod.RunnerOutcome.FAIL, reason="bad"
    )
    obs = ad_mod.evaluate_extended_method(
        "observability-behavior-test-verification", res_pass, tmp_path
    )
    assert obs is not None
    p_ok = ad_mod.evaluate_extended_method(
        "polyglot-static-quality-check", res_pass, tmp_path
    )
    p_bad = ad_mod.evaluate_extended_method(
        "polyglot-static-quality-check", res_fail, tmp_path
    )
    assert p_ok is not None and p_ok[0] == "PASS"
    assert p_bad is not None and p_bad[0] == "FAIL"

    r_hr = SimpleNamespace(
        id="SE-ARC-001",
        raw={
            "metadata": {"domain": "architecture", "enforcement": "blocking"},
            "verification": {"methods": ["adr-presence-check"]},
            "human_review": {"required": True, "approver_role": "lead"},
        },
    )
    ev = eval_mod.RuleEvaluator(tmp_path, commit_sha=SHA_1)
    assert ev.evaluate_rule(r_hr).status == "BLOCKED"

    class BlockedRunner(rb_mod.Runner):
        name = "mypy"

        def run(
            self, project_root: Path, artifact_dir: Path | None = None
        ) -> rb_mod.RunnerResult:
            _ = project_root, artifact_dir
            return rb_mod.RunnerResult(
                runner="mypy", outcome=rb_mod.RunnerOutcome.BLOCKED, reason="blocked"
            )

    r_mypy = SimpleNamespace(
        id="SE-CQ-002",
        raw={
            "metadata": {"domain": "code-quality", "enforcement": "critical"},
            "verification": {"methods": ["type-checker-execution"]},
        },
    )
    monkeypatch.setattr(eval_mod, "evaluate_extended_method", lambda *_a, **_kw: None)
    ev_blk = eval_mod.RuleEvaluator(
        tmp_path, commit_sha=SHA_1, runner_overrides={"mypy": BlockedRunner()}
    )
    assert ev_blk.evaluate_rule(r_mypy).status == "BLOCKED"


def test_validation_integrity_and_diff_edge_branches(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo_root = Path(__file__).resolve().parents[3]
    vroot = tmp_path / "val_missing_rules"
    (vroot / "schemas").mkdir(parents=True)
    monkeypatch.setattr(val_mod, "__file__", str(tmp_path / "pkg" / "validation.py"))
    assert not val_mod.validate_repository(vroot).ok

    vroot2 = tmp_path / "val_bad_rules"
    (vroot2 / "rules").mkdir(parents=True)
    (vroot2 / "schemas").mkdir(parents=True)
    shutil.copy2(
        repo_root / "schemas" / "rule.schema.json",
        vroot2 / "schemas" / "rule.schema.json",
    )
    (vroot2 / "rules" / "bad.yaml").write_text("id: [unclosed\n", encoding="utf-8")
    (vroot2 / "rules" / "SE-TST-999.yaml").write_text(
        "id: SE-TST-999\n"
        "metadata:\n"
        "  title: Extra Field Rule\n"
        "  domain: testing\n"
        "  version: 1.0.0\n"
        "  status: active\n"
        "  severity: high\n"
        "  enforcement: blocking\n"
        "  description: Valid load with extra schema error.\n"
        "unexpected_top_key: true\n",
        encoding="utf-8",
    )
    (vroot2 / "skills" / "demo").mkdir(parents=True)
    (vroot2 / "skills" / "demo" / "SKILL.md").write_text(
        "---\nname: demo\ndescription: Demo skill.\n---\n"
        "See [sec](#top) and [out](../../../../outside.md).\n",
        encoding="utf-8",
    )
    assert not val_mod.validate_repository(vroot2).ok

    croot = tmp_path / "cti_repo"
    (croot / "src").mkdir(parents=True)
    (croot / "tests").mkdir(parents=True)
    (croot / "schemas").mkdir(parents=True)
    (croot / ".gencode-gov").mkdir(parents=True)
    (croot / ".gencode-gov" / "config.yaml").write_text("bad: [\n", encoding="utf-8")
    (croot / "schemas" / "s.schema.json").write_text(
        '{"type": "object"}\n', encoding="utf-8"
    )
    (croot / "src" / "stub.py").write_text(
        'def f() -> None:\n    """Docstring."""\n    raise NotImplementedError\n',
        encoding="utf-8",
    )
    (croot / "src" / "unit_test.py").write_text("x = 1\n", encoding="utf-8")
    (croot / "tests" / "test_keep.py").write_text(
        "def test_ok() -> None:\n    assert 1 == 1\n", encoding="utf-8"
    )
    (croot / "tests" / "test_del.py").write_text(
        "def test_gone() -> None:\n    assert 2 == 2\n", encoding="utf-8"
    )
    base_sha = _git_init(croot)
    assert (
        cti_mod.verify_test_adequacy_method(
            "regression-tamper-diff-check", croot, base_ref=base_sha
        )[0]
        == "PASS"
    )
    (croot / "tests" / "test_broken.py").write_text("def bad(:\n", encoding="utf-8")
    assert cti_mod.analyze_production_code(croot).stub_violations
    assert (
        cti_mod.verify_test_adequacy_method("assertion-adequacy-check", croot)[0]
        == "PASS"
    )
    (croot / "tests" / "test_broken.py").unlink()
    (croot / "tests" / "test_del.py").unlink()
    (croot / "schemas" / "s.schema.json").write_text("{broken\n", encoding="utf-8")
    subprocess.run([_GIT, "add", "-A"], cwd=croot, check=True, timeout=10)  # noqa: S603
    subprocess.run(  # noqa: S603
        [_GIT, "commit", "-q", "-m", "del test"], cwd=croot, check=True, timeout=10
    )
    assert (
        cti_mod.verify_test_adequacy_method(
            "regression-tamper-diff-check", croot, base_ref=base_sha
        )[0]
        == "FAIL"
    )

    rep_bad_schema = dg_mod.evaluate_diff_governance(croot, base_ref=base_sha)
    assert rep_bad_schema.schema_breaking_changes

    (croot / "manifest").mkdir(parents=True)
    (croot / "manifest" / "compatibility.yaml").write_text("bad: [\n", encoding="utf-8")
    rep_blk = dg_mod.evaluate_diff_governance(croot, base_ref=base_sha, max_files=0)
    assert rep_blk.status == "BLOCKED"


def test_domain_verifiers_all_remaining_branches(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    d = tmp_path / "dom"
    (d / "migrations").mkdir(parents=True)
    (d / "migrations" / "001_safe.sql").write_text(
        "CREATE INDEX CONCURRENTLY idx_ok ON items(id);\n", encoding="utf-8"
    )
    assert dv_mod.evaluate_domain_method("concurrent-index-and-lock-check", d) == (
        "PASS",
        "scanned 1 migration(s); index locks safe",
    )

    (d / "manifest").mkdir(parents=True)
    (d / "manifest" / "compatibility.yaml").write_text("bad: [\n", encoding="utf-8")
    assert dv_mod.evaluate_domain_method("frozen-api-contract-check", d)[0] == "BLOCKED"

    fake_diff = SimpleNamespace(
        status="FAIL",
        reasons=("schema break",),
        frozen_api_failures=(),
        schema_breaking_changes=("schemas/a.json: removed id",),
    )
    monkeypatch.setattr(dv_mod, "evaluate_diff_governance", lambda _r: fake_diff)
    assert (
        dv_mod.evaluate_domain_method("schema-compatibility-diff-check", d)[0] == "FAIL"
    )

    (d / "schemas").mkdir(parents=True)
    real_s = d / "schemas" / "ok.schema.json"
    real_s.write_text('{"$id": "urn:gencode-gov:ok:1.0.0"}\n', encoding="utf-8")
    (d / "schemas" / "sym.schema.json").symlink_to(real_s)
    assert dv_mod.evaluate_domain_method("api-contract-analysis", d)[0] == "PASS"

    assert dv_mod._verify_devops_methods("unknown-devops", d)[0] == "BLOCKED"
    assert dv_mod._verify_maintenance_methods("unknown-maint", d)[0] == "BLOCKED"
    assert dv_mod._verify_testing_auxiliary_methods("unknown-test", d)[0] == "BLOCKED"

    (d / "pyproject.toml").write_text(
        '[project]\nname = "x"\nversion = "1.0.0"\n', encoding="utf-8"
    )
    (d / "src" / "real_pkg").mkdir(parents=True)
    real_init = d / "src" / "real_pkg" / "__init__.py"
    real_init.write_text('__version__ = "1.0.0"\n', encoding="utf-8")
    (d / "src" / "sym_pkg").mkdir(parents=True)
    (d / "src" / "sym_pkg" / "__init__.py").symlink_to(real_init)
    assert dv_mod.evaluate_domain_method("version-consistency-check", d)[0] == "PASS"

    (d / "src" / "examples").mkdir(parents=True)
    (d / "src" / "examples" / "skip.py").write_text("x = 1\n", encoding="utf-8")
    (d / "src" / "real_pkg" / "bad_syn.py").write_text("def bad(:\n", encoding="utf-8")
    assert (
        dv_mod.evaluate_domain_method("outbound-timeout-enforcement-scan", d)[0]
        == "PASS"
    )

    (d / "big.py").write_text("x = 1\n" + ("#" * (260 * 1024)), encoding="utf-8")
    assert dv_mod.evaluate_domain_method("secret-scanner", d)[0] == "PASS"

    (d / "sbom.cdx.json").write_text(
        '{"components": ["skip-str", {"name": "a"}], "vulnerabilities": []}\n',
        encoding="utf-8",
    )
    assert (
        dv_mod.evaluate_domain_method("sbom-license-and-cve-policy-check", d)[0]
        == "PASS"
    )

    att_dir = d / ".gencode-gov" / "evidence" / "attestations"
    att_dir.mkdir(parents=True)
    (att_dir / "01_bad.json").write_text("{broken\n", encoding="utf-8")
    (att_dir / "02_empty.json").write_text('{"rule_ids": []}\n', encoding="utf-8")
    assert (
        dv_mod.evaluate_domain_method("human-review", d, commit_sha=SHA_1)[0]
        == "BLOCKED"
    )
