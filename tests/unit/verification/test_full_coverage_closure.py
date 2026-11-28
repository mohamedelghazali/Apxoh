"""Targeted branch-closure tests achieving 100% statement coverage."""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
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


def test_drift_text_warnings_and_dispatch_branches(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    p = tmp_path / "drift_repo"
    (p / "src").mkdir(parents=True)
    (p / "src" / "a.py").write_text("def f() -> int:\n    return 1\n", encoding="utf-8")
    _git_init(p)
    assert cli_mod.main(["drift", str(p)]) == 0
    capsys.readouterr()

    complex_fn = "def g(x: int) -> int:\n" + "".join(
        f"    if x == {i}:\n        return {i}\n" for i in range(12)
    ) + "    return 0\n"
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
    assert ad_mod.evaluate_extended_method(
        "observability-behavior-test-verification", res_pass, tmp_path
    ) is not None
    assert ad_mod.evaluate_extended_method(
        "polyglot-static-quality-check", res_pass, tmp_path
    )[0] == "PASS"
    assert ad_mod.evaluate_extended_method(
        "polyglot-static-quality-check", res_fail, tmp_path
    )[0] == "FAIL"

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


def test_validation_integrity_and_diff_edge_branches(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo_root = Path(__file__).resolve().parents[3]
    vroot = tmp_path / "val_missing_rules"
    (vroot / "schemas").mkdir(parents=True)
    monkeypatch.setattr(val_mod, "__file__", str(tmp_path / "pkg" / "validation.py"))
    s1 = val_mod.validate_repository(vroot)
    assert not s1.ok

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
    s2 = val_mod.validate_repository(vroot2)
    assert not s2.ok

    # code_and_test_integrity edge branches
    croot = tmp_path / "cti_repo"
    (croot / "src").mkdir(parents=True)
    (croot / "tests").mkdir(parents=True)
    (croot / ".gencode-gov").mkdir(parents=True)
    (croot / ".gencode-gov" / "config.yaml").write_text("bad: [\n", encoding="utf-8")
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
    (croot / "tests" / "test_broken.py").write_text("def bad(:\n", encoding="utf-8")
    assert cti_mod.analyze_production_code(croot).stub_functions
    assert cti_mod.verify_test_adequacy_method("assertion-adequacy-check", croot)[0] == "PASS"
    (croot / "tests" / "test_broken.py").unlink()
    (croot / "tests" / "test_del.py").unlink()
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

    # diff_governance blast radius & blocked frozen_apis
    (croot / "manifest").mkdir(parents=True)
    (croot / "manifest" / "compatibility.yaml").write_text("bad: [\n", encoding="utf-8")
    rep_blk = dg_mod.evaluate_diff_governance(croot, base_ref=base_sha, max_files=0)
    assert rep_blk.status == "BLOCKED"


def test_domain_verifiers_remaining_branches(tmp_path: Path) -> None:
    d = tmp_path / "dom"
    (d / "schemas").mkdir(parents=True)
    (d / "src").mkdir(parents=True)
    real_s = d / "schemas" / "bad.schema.json"
    real_s.write_text("{broken", encoding="utf-8")
    (d / "schemas" / "sym.schema.json").symlink_to(real_s)
    assert dv_mod.evaluate_domain_method("frozen-api-contract-check", d) == (
        "BLOCKED",
        "not a Git repository or HEAD commit unavailable",
    )
    assert dv_mod.evaluate_domain_method("api-contract-analysis", d)[0] == "FAIL"

    real_s.write_text('{"type": "object"}', encoding="utf-8")
    assert dv_mod.evaluate_domain_method("endpoint-version-inventory", d)[0] == "FAIL"

    (d / ".github" / "workflows").mkdir(parents=True)
    wf = d / ".github" / "workflows" / "ci.yml"
    wf.write_text("on: [push]\njobs:\n  b:\n    steps:\n      - uses: a/b@v1\n", encoding="utf-8")
    assert dv_mod.evaluate_domain_method("github-actions-sha-pinning-scan", d)[0] == "FAIL"

    (d / "pyproject.toml").write_text("[broken", encoding="utf-8")
    assert dv_mod.evaluate_domain_method("version-consistency-check", d)[0] == "FAIL"
    (d / "pyproject.toml").write_text('[project]\nname = "x"\n', encoding="utf-8")
    assert dv_mod.evaluate_domain_method("version-consistency-check", d)[0] == "FAIL"

    (d / "RELEASE_NOTES.md").write_text("short", encoding="utf-8")
    assert dv_mod.evaluate_domain_method("release-notes-presence", d)[0] == "PASS"
    assert dv_mod.evaluate_domain_method("release-notes-structure-validation", d)[0] == "FAIL"

    (d / "src" / "loop.py").write_text(
        "def run() -> None:\n    while True:\n        break\n", encoding="utf-8"
    )
    assert dv_mod.evaluate_domain_method("unbounded-retry-loop-scan", d)[0] == "PASS"

    (d / "sbom.cdx.json").write_text("{bad", encoding="utf-8")
    assert dv_mod.evaluate_domain_method("sbom-component-inventory-check", d)[0] == "FAIL"
    (d / "sbom.cdx.json").write_text('{"components": []}', encoding="utf-8")
    assert dv_mod.evaluate_domain_method("sbom-component-inventory-check", d)[0] == "FAIL"
    (d / "sbom.cdx.json").unlink()
    (d / "requirements.lock").write_text("pyyaml==6.0.2\n", encoding="utf-8")
    assert dv_mod.evaluate_domain_method("sbom-component-inventory-check", d)[0] == "PASS"
    assert dv_mod.evaluate_domain_method("sbom-license-and-cve-policy-check", d)[0] == "PASS"

    hr_rule = SimpleNamespace(
        id="SE-ARC-001", raw={"human_review": {"approver_role": "lead"}}
    )
    assert (
        dv_mod.evaluate_domain_method(
            "human-review", d, rule=hr_rule, commit_sha=SHA_1
        )[0]
        == "BLOCKED"
    )

    _git_init(d)
    assert dv_mod.evaluate_domain_method("test-diff-analysis", d)[0] in {"PASS", "BLOCKED"}
