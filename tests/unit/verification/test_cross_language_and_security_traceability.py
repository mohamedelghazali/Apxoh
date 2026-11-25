"""Comprehensive 100%-coverage tests for cross-language runner, traceability, and XXE."""

from __future__ import annotations

import argparse
import contextlib
import json
import socket
import subprocess
from pathlib import Path
from typing import Any

import yaml

import arkhon.verification.runners.pytest_runner as pr_mod
import arkhon.verification.runners.test_suite_runner as tsr_mod
import arkhon.verification.scenario_verifier as sv_mod
from arkhon.core.errors import ConfigError
from arkhon.verification.assess_dispatch import (
    create_assess_runner,
    evaluate_extended_method,
    inspect_junit_artifact,
)
from arkhon.verification.methods import resolve_method, resolve_methods
from arkhon.verification.runners.base import RunnerOutcome, RunnerResult
from arkhon.verification.runners.pytest_runner import PytestRunner
from arkhon.verification.runners.test_suite_runner import (
    LanguageNeutralTestRunner,
    _declared_primary_language,
    _parse_junit_cases,
    _persist_normalized_report,
    resolve_project_language,
)
from arkhon.verification.scenario_verifier import (
    REQUIRED_SECURITY_SCENARIOS,
    _build_executed_lookup,
    _detect_attack_surface,
    _load_execution_report,
    _safe_in_repo_file,
    _verify_python_test_quality,
    _verify_test_source_and_execution,
    verify_negative_security_scenarios,
    verify_observability_and_crash_dump_controls,
)


def test_methods_and_create_assess_runner_branches() -> None:
    for bad in ("", 123):
        with contextlib.suppress(ValueError):
            resolve_method(bad)  # type: ignore[arg-type]
    for bad_list in ("not-a-list", [""], ["a", "a"]):
        with contextlib.suppress(ValueError):
            resolve_methods(bad_list)
    with contextlib.suppress(ValueError):
        LanguageNeutralTestRunner(timeout_seconds=0)
    assert create_assess_runner("test-suite") is not None
    assert create_assess_runner("ruff") is not None
    assert create_assess_runner("unknown-runner") is None


def test_language_resolution_and_report_persistence_edge_cases(
    tmp_path: Path, monkeypatch: Any
) -> None:
    runner = LanguageNeutralTestRunner()
    assert runner.run(tmp_path / "does_not_exist").outcome == RunnerOutcome.BLOCKED

    empty_dir = tmp_path / "empty_proj"
    empty_dir.mkdir()
    assert resolve_project_language(empty_dir)[0] == "unknown"
    assert runner.run(empty_dir).outcome == RunnerOutcome.BLOCKED

    assert _declared_primary_language(empty_dir) is None
    ark_dir = empty_dir / ".arkhon"
    ark_dir.mkdir(exist_ok=True)
    proj_yaml = ark_dir / "project.yaml"
    proj_yaml.write_text("\t: [unclosed", encoding="utf-8")
    assert _declared_primary_language(empty_dir) is None
    proj_yaml.write_text("- list-not-dict\n", encoding="utf-8")
    assert _declared_primary_language(empty_dir) is None
    proj_yaml.write_text("languages: not-a-dict\n", encoding="utf-8")
    assert _declared_primary_language(empty_dir) is None
    proj_yaml.write_text("languages:\n  primary: '   '\n", encoding="utf-8")
    assert _declared_primary_language(empty_dir) is None
    proj_yaml.write_text("languages:\n  primary: Python\n", encoding="utf-8")
    assert resolve_project_language(empty_dir) == ("python", "declared in .arkhon/project.yaml")
    proj_yaml.write_text("languages:\n  primary: elixir\n", encoding="utf-8")
    assert resolve_project_language(empty_dir) == (
        "elixir",
        "unregistered language declared in .arkhon/project.yaml",
    )

    cs_dir = tmp_path / "cs_proj"
    cs_dir.mkdir()
    (cs_dir / "App.csproj").write_text("<Project/>\n", encoding="utf-8")
    orig_load_reg = tsr_mod.load_registry

    def _no_reg(*_a: object, **_k: object) -> Any:
        raise ConfigError("no reg")

    monkeypatch.setattr(tsr_mod, "load_registry", _no_reg)
    assert resolve_project_language(cs_dir)[0] == "csharp"
    monkeypatch.setattr(tsr_mod, "load_registry", orig_load_reg)

    ext_dir = tmp_path / "ext_only"
    ext_dir.mkdir()
    (ext_dir / "app.rb").write_text("puts 1\n", encoding="utf-8")
    assert resolve_project_language(ext_dir)[0] == "ruby"

    sym_proj = tmp_path / "sym_proj"
    (sym_proj / ".arkhon/evidence/testing").mkdir(parents=True)
    target_dummy = tmp_path / "dummy.json"
    target_dummy.write_text("{}", encoding="utf-8")
    (sym_proj / ".arkhon/evidence/testing/test-execution-report.json").symlink_to(target_dummy)
    assert _persist_normalized_report(sym_proj, {"a": 1}) is None
    assert runner.run(sym_proj).outcome == RunnerOutcome.BLOCKED

    file_blocker = tmp_path / "blocker_proj"
    file_blocker.mkdir()
    (file_blocker / ".arkhon").write_text("not-a-dir", encoding="utf-8")
    assert _persist_normalized_report(file_blocker, {"a": 1}) is None


def test_junit_and_python_adapter_all_outcomes(tmp_path: Path, monkeypatch: Any) -> None:
    assert _parse_junit_cases(tmp_path / "missing.xml") is None
    empty_suites = tmp_path / "empty_suites.xml"
    empty_suites.write_text("<testsuites/>", encoding="utf-8")
    assert _parse_junit_cases(empty_suites) is None
    assert inspect_junit_artifact(tmp_path / "missing.xml") is None
    assert inspect_junit_artifact(empty_suites) is None

    neg_xml = tmp_path / "neg.xml"
    neg_xml.write_text(
        '<testsuite tests="-1" failures="0" errors="0" skipped="0"/>', encoding="utf-8"
    )
    assert _parse_junit_cases(neg_xml) is None
    assert inspect_junit_artifact(neg_xml) is None

    multi_xml = tmp_path / "multi.xml"
    multi_xml.write_text(
        '<testsuites><testsuite tests="3" failures="1" errors="0" skipped="1">'
        '<testcase name="t_pass" classname="c"/>'
        '<testcase name="t_fail" classname="c"><failure/></testcase>'
        '<testcase name="t_skip" classname="c"><skipped/></testcase>'
        '<testcase name="" classname="c"/>'
        "</testsuite></testsuites>",
        encoding="utf-8",
    )
    parsed = _parse_junit_cases(multi_xml)
    assert parsed is not None and parsed[0]["total"] == 3 and len(parsed[1]) == 3
    assert inspect_junit_artifact(multi_xml) == (3, 1, 0, 1)

    py_proj = tmp_path / "py_proj"
    py_proj.mkdir()
    (py_proj / "pyproject.toml").write_text("[project]\nname='x'\n", encoding="utf-8")
    runner = LanguageNeutralTestRunner()
    assert runner.run(py_proj).outcome == RunnerOutcome.BLOCKED

    xml_out = py_proj / "out.xml"
    monkeypatch.setattr(
        PytestRunner,
        "run",
        lambda _s, _r: RunnerResult("pytest", RunnerOutcome.BLOCKED, "pytest timed out", []),
    )
    assert runner.run(py_proj).outcome == RunnerOutcome.BLOCKED

    xml_out.write_text("<bad", encoding="utf-8")
    monkeypatch.setattr(
        PytestRunner,
        "run",
        lambda _s, _r: RunnerResult("pytest", RunnerOutcome.PASS, "", [xml_out]),
    )
    assert runner.run(py_proj).outcome == RunnerOutcome.BLOCKED

    xml_out.write_text(
        '<testsuite tests="0" failures="0" errors="0" skipped="0"/>', encoding="utf-8"
    )
    assert runner.run(py_proj).outcome == RunnerOutcome.BLOCKED

    xml_out.write_text(
        '<testsuite tests="1" failures="1" errors="0" skipped="0">'
        '<testcase name="t1"><failure/></testcase></testsuite>',
        encoding="utf-8",
    )
    monkeypatch.setattr(
        PytestRunner,
        "run",
        lambda _s, _r: RunnerResult("pytest", RunnerOutcome.FAIL, "1 failed", [xml_out]),
    )
    assert runner.run(py_proj).outcome == RunnerOutcome.FAIL

    xml_out.write_text(
        '<testsuite tests="1" failures="0" errors="0" skipped="1">'
        '<testcase name="t1"><skipped/></testcase></testsuite>',
        encoding="utf-8",
    )
    monkeypatch.setattr(
        PytestRunner,
        "run",
        lambda _s, _r: RunnerResult("pytest", RunnerOutcome.PASS, "", [xml_out]),
    )
    assert runner.run(py_proj).outcome == RunnerOutcome.PASS

    xml_out.write_text(
        '<testsuite tests="1" failures="0" errors="0" skipped="0">'
        '<testcase name="t1"/></testsuite>',
        encoding="utf-8",
    )
    assert runner.run(py_proj).outcome == RunnerOutcome.PASS


def test_go_rust_js_ts_adapters_all_outcomes(tmp_path: Path, monkeypatch: Any) -> None:
    runner = LanguageNeutralTestRunner()
    go_proj = tmp_path / "go_svc"
    go_proj.mkdir()
    (go_proj / "go.mod").write_text("module m\n", encoding="utf-8")
    assert runner.run(go_proj).outcome == RunnerOutcome.BLOCKED
    (go_proj / "svc_test.go").write_text("package m\n", encoding="utf-8")

    monkeypatch.setattr(tsr_mod.shutil, "which", lambda _b: None)
    assert runner.run(go_proj).outcome == RunnerOutcome.BLOCKED

    monkeypatch.setattr(tsr_mod.shutil, "which", lambda b: f"/usr/bin/{b}")

    def raise_oserror(*_a: object, **_k: object) -> Any:
        raise OSError("exec failed")

    monkeypatch.setattr(tsr_mod.subprocess, "run", raise_oserror)
    assert runner.run(go_proj).outcome == RunnerOutcome.BLOCKED

    go_stream = "\n".join(
        [
            "",
            "not-json",
            json.dumps({"Action": "output"}),
            json.dumps({"Test": "TestPass", "Package": "m", "Action": "pass"}),
            json.dumps({"Test": "TestSkip", "Package": "m", "Action": "skip"}),
        ]
    )

    def _proc(out: str, rc: int = 0) -> Any:
        return lambda cmd, **_k: subprocess.CompletedProcess(cmd, rc, stdout=out, stderr="")

    monkeypatch.setattr(tsr_mod.subprocess, "run", _proc(go_stream, 0))
    assert runner.run(go_proj).outcome == RunnerOutcome.PASS

    go_fail = json.dumps({"Test": "TestFail", "Package": "m", "Action": "fail"})
    monkeypatch.setattr(tsr_mod.subprocess, "run", _proc(go_fail, 1))
    assert runner.run(go_proj).outcome == RunnerOutcome.FAIL

    monkeypatch.setattr(tsr_mod.subprocess, "run", _proc("", 0))
    assert runner.run(go_proj).outcome == RunnerOutcome.BLOCKED

    rs_proj = tmp_path / "rs_svc"
    (rs_proj / ".arkhon").mkdir(parents=True)
    (rs_proj / ".arkhon/project.yaml").write_text(
        "languages:\n  primary: rust\n", encoding="utf-8"
    )
    assert runner.run(rs_proj).outcome == RunnerOutcome.BLOCKED
    (rs_proj / "Cargo.toml").write_text("[package]\nname='x'\n", encoding="utf-8")

    monkeypatch.setattr(tsr_mod.shutil, "which", lambda _b: None)
    assert runner.run(rs_proj).outcome == RunnerOutcome.BLOCKED

    monkeypatch.setattr(tsr_mod.shutil, "which", lambda b: f"/usr/bin/{b}")
    monkeypatch.setattr(tsr_mod.subprocess, "run", raise_oserror)
    assert runner.run(rs_proj).outcome == RunnerOutcome.BLOCKED

    cargo_out = (
        "running 3 tests\n"
        "test auth::ok_case ... ok\n"
        "test auth::ign_case ... ignored\n"
        "test auth::bad_case ... FAILED\n"
    )
    monkeypatch.setattr(tsr_mod.subprocess, "run", _proc(cargo_out, 101))
    assert runner.run(rs_proj).outcome == RunnerOutcome.FAIL

    ts_proj = tmp_path / "ts_svc"
    ts_proj.mkdir()
    (ts_proj / "tsconfig.json").write_text("{}\n", encoding="utf-8")
    assert runner.run(ts_proj).outcome == RunnerOutcome.BLOCKED

    pkg = ts_proj / "package.json"
    pkg.write_text("{bad-json", encoding="utf-8")
    assert runner.run(ts_proj).outcome == RunnerOutcome.BLOCKED

    pkg.write_text(
        json.dumps({"scripts": {"test": 'echo "Error: no test specified" && exit 1'}}),
        encoding="utf-8",
    )
    assert runner.run(ts_proj).outcome == RunnerOutcome.BLOCKED

    pkg.write_text(json.dumps({"scripts": {"test": "vitest run"}}), encoding="utf-8")
    assert runner.run(ts_proj).outcome == RunnerOutcome.BLOCKED

    pkg.write_text(json.dumps({"scripts": {"test": "node --test"}}), encoding="utf-8")
    monkeypatch.setattr(tsr_mod.shutil, "which", lambda _b: None)
    assert runner.run(ts_proj).outcome == RunnerOutcome.BLOCKED

    monkeypatch.setattr(tsr_mod.shutil, "which", lambda b: f"/usr/bin/{b}")
    monkeypatch.setattr(tsr_mod.subprocess, "run", raise_oserror)
    assert runner.run(ts_proj).outcome == RunnerOutcome.BLOCKED

    tap_ok = "TAP version 13\nok 1 - passes cleanly\n1..1\n"
    monkeypatch.setattr(tsr_mod.subprocess, "run", _proc(tap_ok, 0))
    assert runner.run(ts_proj).outcome == RunnerOutcome.PASS

    tap_mix = "ok 1 - skipped case # SKIP reason\nnot ok 2 - broken case\n"
    monkeypatch.setattr(tsr_mod.subprocess, "run", _proc(tap_mix, 1))
    assert runner.run(ts_proj).outcome == RunnerOutcome.FAIL

    java_proj = tmp_path / "java_app"
    java_proj.mkdir()
    (java_proj / "pom.xml").write_text("<project/>\n", encoding="utf-8")
    assert runner.run(java_proj).outcome == RunnerOutcome.BLOCKED


def test_assess_dispatch_and_cli_extended_method_outcomes(tmp_path: Path) -> None:
    blocked_res = RunnerResult("test-suite", RunnerOutcome.BLOCKED, "blocked", [])
    assert evaluate_extended_method("automated-test-suite-execution", blocked_res, tmp_path) == (
        "BLOCKED",
        "blocked",
    )

    def _st(mid: str, r: RunnerResult) -> str:
        out = evaluate_extended_method(mid, r, tmp_path)
        assert out is not None
        return out[0]

    empty_res = RunnerResult("test-suite", RunnerOutcome.PASS, "", [])
    assert _st("automated-test-suite-execution", empty_res) == "BLOCKED"
    rep = tmp_path / "test-execution-report.json"
    rep.write_text("{bad-json", encoding="utf-8")
    bad_res = RunnerResult("test-suite", RunnerOutcome.PASS, "", [rep])
    assert _st("automated-test-suite-execution", bad_res) == "BLOCKED"
    rep.write_text(json.dumps({"counts": "bad"}), encoding="utf-8")
    assert _st("automated-test-suite-execution", bad_res) == "BLOCKED"

    def write_rep(total: int, failed: int, skipped: int, outcome: RunnerOutcome) -> RunnerResult:
        rep.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "language": "go",
                    "adapter": "go-test",
                    "classification": "passed",
                    "counts": {
                        "total": total,
                        "passed": max(0, total - failed - skipped),
                        "failed": failed,
                        "errors": 0,
                        "skipped": skipped,
                    },
                    "executed_tests": [],
                }
            ),
            encoding="utf-8",
        )
        return RunnerResult("test-suite", outcome, "", [rep])

    res_ok = write_rep(4, 0, 0, RunnerOutcome.PASS)
    assert _st("automated-test-suite-execution", res_ok) == "PASS"
    assert _st("zero-test-failures-check", res_ok) == "PASS"
    assert _st("skip-marker-detection", res_ok) == "PASS"
    assert _st("skip-marker-detection", write_rep(4, 0, 1, RunnerOutcome.PASS)) == "FAIL"
    assert _st("zero-test-failures-check", write_rep(4, 1, 0, RunnerOutcome.FAIL)) == "FAIL"
    res_zero = write_rep(0, 0, 0, RunnerOutcome.PASS)
    assert _st("automated-test-suite-execution", res_zero) == "BLOCKED"
    assert _st("negative-security-scenario-traceability", res_ok) == "BLOCKED"
    assert _st("observability-behavior-test-verification", res_ok) == "BLOCKED"

    r_empty = RunnerResult("ruff", RunnerOutcome.PASS, "", [])
    assert _st("static-lint-execution", r_empty) == "BLOCKED"
    ruff_json = tmp_path / "ruff.json"
    ruff_json.write_text("{bad", encoding="utf-8")
    r_res = RunnerResult("ruff", RunnerOutcome.PASS, "", [ruff_json])
    assert _st("static-lint-execution", r_res) == "BLOCKED"
    ruff_json.write_text(json.dumps({"not": "a-list"}), encoding="utf-8")
    assert _st("static-lint-execution", r_res) == "BLOCKED"
    ruff_json.write_text("[]", encoding="utf-8")
    assert _st("static-lint-execution", r_res) == "PASS"
    assert _st("zero-lint-errors-check", r_res) == "PASS"
    ruff_json.write_text('[{"code": "E501"}]', encoding="utf-8")
    r_fail = RunnerResult("ruff", RunnerOutcome.FAIL, "1 issue", [ruff_json])
    assert _st("zero-lint-errors-check", r_fail) == "FAIL"

    assert evaluate_extended_method("unregistered-method", res_ok, tmp_path) is None


def test_cli_cmd_assess_exercises_extended_method_return_line(
    tmp_path: Path, monkeypatch: Any
) -> None:
    import arkhon.cli as cli_mod
    import arkhon.verification.assess_dispatch as ad_mod

proj = tmp_path / "governed_proj"
proj.mkdir(parents=True)
ran = {"count": 0}

class _StubSuiteRunner(LanguageNeutralTestRunner):
    def run(self, project_root: Path) -> RunnerResult:
        ran["count"] += 1
            ev = project_root / ".arkhon/evidence/testing"
            ev.mkdir(parents=True, exist_ok=True)
            rp = ev / "test-execution-report.json"
            rp.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "language": "python",
                        "adapter": "pytest",
                        "classification": "passed",
                        "counts": {
                            "total": 2,
                            "passed": 2,
                            "failed": 0,
                            "errors": 0,
                            "skipped": 0,
                        },
                        "executed_tests": [],
                    }
                ),
                encoding="utf-8",
            )
            return RunnerResult("test-suite", RunnerOutcome.PASS, "", [rp])

    orig_create = ad_mod.create_assess_runner
    monkeypatch.setattr(
        ad_mod,
        "create_assess_runner",
        lambda name: _StubSuiteRunner() if name == "test-suite" else orig_create(name),
    )
    with contextlib.suppress(ImportError, SystemExit):
        from arkhon.verification.runners.mypy_runner import MypyRunner
        from arkhon.verification.runners.tsar_runner import TsarRunner

        monkeypatch.setattr(
            MypyRunner,
            "run",
            lambda _s, _p: RunnerResult("mypy", RunnerOutcome.BLOCKED, "skip"),
        )
        monkeypatch.setattr(
            TsarRunner,
            "run",
            lambda _s, _p: RunnerResult("tsar", RunnerOutcome.BLOCKED, "skip"),
        )
        monkeypatch.setattr(cli_mod, "_commit_sha", lambda _p: "a" * 40)
        monkeypatch.setattr(cli_mod, "_working_tree_clean", lambda _p: True)
        if hasattr(cli_mod, "main"):
            cli_mod.main(["assess", str(proj)])
        else:
            cli_mod.cmd_assess(argparse.Namespace(project=str(proj)))
        assert ran["count"] == 1


def test_scenario_verifier_all_branches_and_edge_cases(tmp_path: Path, monkeypatch: Any) -> None:
    proj = tmp_path / "web_proj"
    (proj / ".arkhon/evidence/testing").mkdir(parents=True)
    (proj / ".arkhon/project.yaml").write_text(
        "project:\n  profile: web-application\nlanguages:\n  primary: python\n",
        encoding="utf-8",
    )
    (proj / "src").mkdir()
    (proj / "src/notes.bin").write_bytes(b"\x00\x01")
    big = proj / "src/big.py"
    big.write_text("x = 1\n" * 120000, encoding="utf-8")
    (proj / "src/app.py").write_text(
        "app = FastAPI()\nresp.set_cookie('sid', '1')\n", encoding="utf-8"
    )
    unreadable_sym = proj / "src/sym.py"
    unreadable_sym.symlink_to(proj / "src/app.py")

    assert _safe_in_repo_file(proj, 123) is None
    assert _safe_in_repo_file(proj, "/etc/passwd") is None
    assert _safe_in_repo_file(proj, "../outside.py") is None
    assert _safe_in_repo_file(proj, "src/sym.py") is None

    orig_match = sv_mod.match_profile

    def _bad_prof(_r: Path) -> Any:
        raise ConfigError("bad")

    monkeypatch.setattr(sv_mod, "match_profile", _bad_prof)
    inferred = _detect_attack_surface(proj)
    assert "csrf-state-change" in inferred and "idor-resource-access" in inferred
    monkeypatch.setattr(sv_mod, "match_profile", orig_match)

    orig_resolve = Path.resolve

    def raising_resolve(self: Path, *a: Any, **kw: Any) -> Path:
        if self.name == "trigger_oserror.py":
            raise OSError("bad resolve")
        return orig_resolve(self, *a, **kw)

    monkeypatch.setattr(Path, "resolve", raising_resolve)
    assert _safe_in_repo_file(proj, "trigger_oserror.py") is None
    monkeypatch.setattr(Path, "resolve", orig_resolve)

    orig_read = Path.read_text

    def raising_read(self: Path, *a: Any, **kw: Any) -> str:
        if self.name == "app.py":
            raise OSError("unreadable")
        return orig_read(self, *a, **kw)

    monkeypatch.setattr(Path, "read_text", raising_read)
    _detect_attack_surface(proj)
    monkeypatch.setattr(Path, "read_text", orig_read)

    assert not _verify_python_test_quality("def broken(:\n", "broken")[0]
    assert not _verify_python_test_quality("def other():\n    assert 1 == 2\n", "missing_fn")[0]
    tautological = (
        "def test_weak():\n"
        "    assert True\n"
        "    assert isinstance(1, int)\n"
    )
    assert not _verify_python_test_quality(tautological, "test_weak")[0]
    raises_call = (
        "def test_raises():\n"
        "    with pytest.raises(ValueError):\n"
        "        pass\n"
    )
    assert _verify_python_test_quality(raises_call, "test_raises")[0]

    (proj / "tests").mkdir()
    doc_f = proj / "tests/README.md"
    doc_f.write_text("# doc\n", encoding="utf-8")
    bad_utf8 = proj / "tests/bad.py"
    bad_utf8.write_bytes(b"\xff\xfe\x00")
    go_t = proj / "tests/sec_test.go"
    go_t.write_text("package sec\nfunc TestNoAssert() {}\n", encoding="utf-8")
    go_mock = proj / "tests/mock_test.go"
    go_mock.write_text(
        "package sec\n// mock.patch('require_auth')\nfunc TestM() { t.Fatal() }\n",
        encoding="utf-8",
    )
    go_ok = proj / "tests/ok_test.go"
    go_ok.write_text("package sec\nfunc TestAuthGo() { t.Errorf('denied') }\n", encoding="utf-8")

    lookup = {
        "TestAuthGo": {"id": "TestAuthGo", "status": "passed"},
        "TestSkippedGo": {"id": "TestSkippedGo", "status": "skipped"},
    }
    go_skip = proj / "tests/skip_test.go"
    go_skip.write_text("package sec\nfunc TestSkippedGo() { t.Fatal() }\n", encoding="utf-8")

    assert not _verify_test_source_and_execution(proj, "tests/nope.py", "t", lookup)[0]
    assert not _verify_test_source_and_execution(proj, "tests/README.md", "t", lookup)[0]
    assert not _verify_test_source_and_execution(proj, "tests/ok_test.go", "  ", lookup)[0]
    assert not _verify_test_source_and_execution(proj, "tests/bad.py", "t", lookup)[0]
    assert not _verify_test_source_and_execution(proj, "tests/ok_test.go", "MissingGo", lookup)[0]
    assert not _verify_test_source_and_execution(proj, "tests/mock_test.go", "TestM", lookup)[0]
    assert not _verify_test_source_and_execution(
        proj, "tests/sec_test.go", "TestNoAssert", lookup
    )[0]
    assert _verify_test_source_and_execution(proj, "tests/ok_test.go", "TestAuthGo", lookup)[0]
    go_unrun = proj / "tests/unrun_test.go"
    go_unrun.write_text("package sec\nfunc TestUnrun() { t.Fatal() }\n", encoding="utf-8")
    assert not _verify_test_source_and_execution(
        proj, "tests/unrun_test.go", "TestUnrun", lookup
    )[0]
    assert not _verify_test_source_and_execution(
        proj, "tests/skip_test.go", "TestSkippedGo", lookup
    )[0]

    rep_file = proj / ".arkhon/evidence/testing/test-execution-report.json"
    assert _load_execution_report(proj)[0] is None
    assert verify_negative_security_scenarios(proj)[0] == "BLOCKED"
    assert verify_observability_and_crash_dump_controls(proj)[0] == "BLOCKED"

    rep_file.write_text("{bad-json", encoding="utf-8")
    assert _load_execution_report(proj)[0] is None
    rep_file.write_text("[]", encoding="utf-8")
    assert _load_execution_report(proj)[0] is None
    assert _build_executed_lookup({"executed_tests": "bad"}) == {}
    built = _build_executed_lookup({"executed_tests": ["not-dict", {"id": "t1"}]})
    assert built["t1"]["id"] == "t1"

    rep_file.write_text(
        json.dumps({"classification": "unavailable", "reason": "no tool"}), encoding="utf-8"
    )
    assert verify_negative_security_scenarios(proj)[0] == "BLOCKED"
    assert verify_observability_and_crash_dump_controls(proj)[0] == "BLOCKED"

    test_file = proj / "tests/test_security_boundaries.py"
    test_file.write_text(
        "\n".join(
            f"def test_{sid.replace('-', '_')}():\n    assert 403 in (401, 403)\n"
            for sid in REQUIRED_SECURITY_SCENARIOS
        )
        + "\ndef test_mocked_idor(monkeypatch):\n"
        + "    monkeypatch.setattr('app.auth.check_permission', lambda *a: True)\n"
        + "    assert 1 == 1\n",
        encoding="utf-8",
    )
    executed = [
        {"id": f"test_{sid.replace('-', '_')}", "status": "passed"}
        for sid in REQUIRED_SECURITY_SCENARIOS
    ] + [{"id": "test_mocked_idor", "status": "passed"}]
    rep_file.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "language": "python",
                "adapter": "pytest",
                "classification": "passed",
                "counts": {"total": 9, "passed": 9, "failed": 0, "errors": 0, "skipped": 0},
                "executed_tests": executed,
            }
        ),
        encoding="utf-8",
    )

    assert verify_negative_security_scenarios(proj)[0] == "BLOCKED"
    assert verify_observability_and_crash_dump_controls(proj)[0] == "BLOCKED"

    matrix_path = proj / ".arkhon/security-test-matrix.yaml"
    matrix_path.write_text("\t: [unclosed", encoding="utf-8")
    assert verify_negative_security_scenarios(proj)[0] == "FAIL"
    matrix_path.write_text("not_scenarios: 1\n", encoding="utf-8")
    assert verify_negative_security_scenarios(proj)[0] == "FAIL"
    matrix_path.write_text("scenarios:\n  unauthenticated-access: {}\n", encoding="utf-8")
    assert verify_negative_security_scenarios(proj)[0] == "FAIL"

    cli_proj = tmp_path / "cli_proj"
    (cli_proj / ".arkhon/evidence/testing").mkdir(parents=True)
    (cli_proj / ".arkhon/project.yaml").write_text(
        "project:\n  profile: cli-tool\n", encoding="utf-8"
    )
    (cli_proj / ".arkhon/evidence/testing/test-execution-report.json").write_text(
        rep_file.read_text(encoding="utf-8"), encoding="utf-8"
    )
    bad_specs: dict[str, Any] = {
        "unauthenticated-access": "not-a-dict",
        "privilege-escalation": {"applicable": "yes"},
        "idor-resource-access": {"applicable": False, "justification": "too short"},
        "tenant-user-isolation": {
            "applicable": False,
            "justification": "Single-user local offline CLI tool with no multi-tenant state.",
        },
        "injection-controls": {"applicable": True, "tests": []},
        "csrf-state-change": {"applicable": True, "tests": ["not-a-dict"]},
        "auth-rate-limit-abuse": {
            "applicable": True,
            "tests": [{"test_file": "missing.py", "test_id": "t"}],
        },
        "token-lifecycle-abuse": {
            "applicable": False,
            "justification": "Stateless local CLI processor without authentication tokens.",
        },
    }
    (cli_proj / ".arkhon/security-test-matrix.yaml").write_text(
        yaml.safe_dump({"scenarios": bad_specs}), encoding="utf-8"
    )
    assert verify_negative_security_scenarios(cli_proj)[0] == "FAIL"

    valid_matrix: dict[str, Any] = {
        "scenarios": {
            sid: {
                "applicable": True,
                "tests": [
                    {
                        "test_file": "tests/test_security_boundaries.py",
                        "test_id": f"test_{sid.replace('-', '_')}",
                    }
                ],
            }
            for sid in REQUIRED_SECURITY_SCENARIOS
        }
    }
    matrix_path.write_text(yaml.safe_dump(valid_matrix), encoding="utf-8")
    assert verify_negative_security_scenarios(proj)[0] == "PASS"

    false_na = json.loads(json.dumps(valid_matrix))
    false_na["scenarios"]["csrf-state-change"] = {
        "applicable": False,
        "justification": "Skipping CSRF on cookie web app.",
    }
    matrix_path.write_text(yaml.safe_dump(false_na), encoding="utf-8")
    assert verify_negative_security_scenarios(proj)[0] == "FAIL"

    mock_mat = json.loads(json.dumps(valid_matrix))
    mock_mat["scenarios"]["idor-resource-access"]["tests"] = [
        {"test_file": "tests/test_security_boundaries.py", "test_id": "test_mocked_idor"}
    ]
    matrix_path.write_text(yaml.safe_dump(mock_mat), encoding="utf-8")
    assert verify_negative_security_scenarios(proj)[0] == "FAIL"

    obs_yaml = cli_proj / ".arkhon/observability-verification.yaml"
    obs_yaml.write_text("\t: [unclosed", encoding="utf-8")
    assert verify_observability_and_crash_dump_controls(cli_proj)[0] == "FAIL"
    obs_yaml.write_text("- not-a-dict\n", encoding="utf-8")
    assert verify_observability_and_crash_dump_controls(cli_proj)[0] == "FAIL"
    obs_yaml.write_text("behavioral_checks: bad\n", encoding="utf-8")
    assert verify_observability_and_crash_dump_controls(cli_proj)[0] == "FAIL"
    obs_yaml.write_text(
        yaml.safe_dump(
            {
                "behavioral_checks": {
                    "structured-diagnostic-logging": {"test_file": "missing.py", "test_id": "t"}
                }
            }
        ),
        encoding="utf-8",
    )
    assert verify_observability_and_crash_dump_controls(cli_proj)[0] == "FAIL"

    (cli_proj / "tests").mkdir()
    (cli_proj / "tests/test_obs.py").write_text(
        "def test_a():\n    assert 1 == 1\n"
        "def test_b():\n    assert 2 == 2\n"
        "def test_c():\n    assert 3 == 3\n",
        encoding="utf-8",
    )
    (cli_proj / ".arkhon/evidence/testing/test-execution-report.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "language": "python",
                "adapter": "pytest",
                "classification": "passed",
                "counts": {"total": 3, "passed": 3, "failed": 0, "errors": 0, "skipped": 0},
                "executed_tests": [
                    {"id": "test_a", "status": "passed"},
                    {"id": "test_b", "status": "passed"},
                    {"id": "test_c", "status": "passed"},
                ],
            }
        ),
        encoding="utf-8",
    )
    checks_ok = {
        "structured-diagnostic-logging": {"test_file": "tests/test_obs.py", "test_id": "test_a"},
        "sanitized-client-error-responses": {"test_file": "tests/test_obs.py", "test_id": "test_b"},
        "application-log-and-trace-redaction": {
            "test_file": "tests/test_obs.py",
            "test_id": "test_c",
        },
    }
    obs_yaml.write_text(
        yaml.safe_dump(
            {
                "behavioral_checks": checks_ok,
                "crash_dump_policy": {"enabled_by_default": "not-bool"},
            }
        ),
        encoding="utf-8",
    )
    assert verify_observability_and_crash_dump_controls(cli_proj)[0] == "FAIL"

    obs_yaml.write_text(
        yaml.safe_dump(
            {
                "behavioral_checks": checks_ok,
                "crash_dump_policy": {
                    "enabled_by_default": False,
                    "unrestricted_developer_or_agent_exposure": True,
                },
            }
        ),
        encoding="utf-8",
    )
    assert verify_observability_and_crash_dump_controls(cli_proj)[0] == "FAIL"

    obs_yaml.write_text(
        yaml.safe_dump(
            {
                "behavioral_checks": checks_ok,
                "crash_dump_policy": {
                    "enabled_by_default": True,
                    "operational_justification": "short",
                    "max_retention_days": 0,
                    "unrestricted_developer_or_agent_exposure": True,
                },
            }
        ),
        encoding="utf-8",
    )
    assert verify_observability_and_crash_dump_controls(cli_proj)[0] == "FAIL"

    obs_yaml.write_text(
        yaml.safe_dump(
            {
                "behavioral_checks": checks_ok,
                "crash_dump_policy": {
                    "enabled_by_default": True,
                    "operational_justification": (
                        "Kernel-level memory corruption forensics under SRE vault."
                    ),
                    "max_retention_days": 7,
                    "least_privilege_access": True,
                    "encrypted_at_rest_and_in_transit": True,
                    "restricted_storage_and_transfer": True,
                    "secure_deletion_configured": True,
                    "access_audit_monitored": True,
                    "unrestricted_developer_or_agent_exposure": False,
                },
            }
        ),
        encoding="utf-8",
    )
    assert verify_observability_and_crash_dump_controls(cli_proj)[0] == "PASS"


def test_pytest_runner_direct_xxe_dtd_network_and_malformed_xml_regression(
    tmp_path: Path,
    monkeypatch: Any,
) -> None:
    proj = tmp_path / "py_xxe_proj"
    (proj / "tests").mkdir(parents=True)
    canary = tmp_path / "canary_secret.txt"
    canary.write_text("TOP_SECRET_CANARY_VALUE_9912", encoding="utf-8")

    file_uri = "file" + f"://{canary}"
    http_uri = "http" + "://127.0.0.1:9/xxe"
    payloads = [
        (
            "external_file_xxe",
            f'<!DOCTYPE foo [<!ENTITY xxe SYSTEM "{file_uri}">]>'
            '<testsuite tests="1"><testcase name="&xxe;"/></testsuite>',
        ),
        (
            "external_http_xxe",
            f'<!DOCTYPE foo [<!ENTITY ext SYSTEM "{http_uri}">]>'
            '<testsuite tests="1"><testcase name="&ext;"/></testsuite>',
        ),
        (
            "billion_laughs_entity",
            '<!DOCTYPE lolz [<!ENTITY lol "lol"><!ENTITY lol2 "&lol;&lol;">]>'
            '<testsuite tests="1"><testcase name="&lol2;"/></testsuite>',
        ),
        (
            "dtd_only",
            '<!DOCTYPE testsuite SYSTEM "evil.dtd"><testsuite tests="1"/>',
        ),
        (
            "malformed_truncated_xml",
            '<testsuite tests="1"><testcase name="broken">',
        ),
        (
            "invalid_numeric_attr",
            '<testsuite tests="not-an-int" failures="0" errors="0" skipped="0"/>',
        ),
    ]

    def forbid_network(*_args: object, **_kwargs: object) -> Any:
        raise AssertionError("unexpected outbound network socket attempted during XML parse")

    monkeypatch.setattr(socket, "create_connection", forbid_network)
    for label, xml_body in payloads:
        xml_probe = tmp_path / f"{label}.xml"
        xml_probe.write_text(xml_body, encoding="utf-8")
        assert inspect_junit_artifact(xml_probe) is None, label

        def fake_pytest_subprocess(
            cmd: list[str], *_a: object, xml_content: str = xml_body, **_kw: object
        ) -> subprocess.CompletedProcess[str]:
            junit_idx = cmd.index("--junit-xml") + 1
            Path(cmd[junit_idx]).write_text(xml_content, encoding="utf-8")
            return subprocess.CompletedProcess(cmd, 0, stdout="1 passed", stderr="")

        monkeypatch.setattr(pr_mod.subprocess, "run", fake_pytest_subprocess)
        result = PytestRunner().run(proj)
        assert result.outcome == RunnerOutcome.BLOCKED, f"{label}: {result}"
        assert "invalid JUnit XML" in result.reason, f"{label}: {result.reason}"
        assert "TOP_SECRET_CANARY_VALUE_9912" not in result.reason
        assert not (proj / ".arkhon" / "evidence" / "testing" / "pytest.xml").exists()
