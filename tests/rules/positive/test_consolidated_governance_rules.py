"""Positive schema, semantic, cross-language, and CLI dispatch tests for consolidated rules."""

from __future__ import annotations

import contextlib
import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import arkhon.cli as cli_mod
import arkhon.verification.assess_dispatch as ad_mod
from arkhon.rules.loader import load_rule_file
from arkhon.rules.validator import validate_rule
from arkhon.verification.methods import resolve_method, resolve_methods
from arkhon.verification.runners.base import RunnerOutcome, RunnerResult
from arkhon.verification.runners.mypy_runner import MypyRunner
from arkhon.verification.runners.tsar_runner import TsarRunner

REPO_ROOT = Path(__file__).resolve().parents[3]
SCHEMA_PATH = REPO_ROOT / "schemas" / "rule.schema.json"

CONSOLIDATED_RULES = {
    "SE-OBS-003": (
        REPO_ROOT / "rules" / "observability" / "SE-OBS-003-structured-logging-error-handling.yaml",
        "observability",
        "high",
        "blocking",
    ),
    "SE-PRF-002": (
        REPO_ROOT / "rules" / "performance" / "SE-PRF-002-latency-degradation-alerting.yaml",
        "performance",
        "high",
        "blocking",
    ),
    "SE-TST-004": (
        REPO_ROOT / "rules" / "testing" / "SE-TST-004-critical-and-negative-security-tests.yaml",
        "testing",
        "critical",
        "critical",
    ),
}


def test_consolidated_rules_exist_and_validate() -> None:
    for rule_id, (path, domain, severity, enforcement) in CONSOLIDATED_RULES.items():
        assert path.is_file(), f"missing {path}"
        rule = load_rule_file(path)
        assert rule.id == rule_id
        assert rule.domain == domain
        assert rule.severity == severity
        assert rule.enforcement == enforcement
        errors = validate_rule(rule, SCHEMA_PATH)
        assert errors == [], f"{rule_id} validation failed: {errors}"


def test_se_tst_004_uses_language_neutral_runner_and_scenario_traceability() -> None:
    path = CONSOLIDATED_RULES["SE-TST-004"][0]
    rule = load_rule_file(path)
    methods = rule.raw["verification"]["methods"]
    assert "pytest-suite-execution" not in methods
    resolutions = dict(resolve_methods(methods))
    for method_id in (
        "automated-test-suite-execution",
        "zero-test-failures-check",
        "negative-security-scenario-traceability",
    ):
        impl = resolutions[method_id]
        assert impl is not None, method_id
        assert impl.runner == "test-suite"
        assert "testing" in impl.allowed_domains


def test_se_obs_003_excludes_ruff_and_separates_crash_dump_controls() -> None:
    path = CONSOLIDATED_RULES["SE-OBS-003"][0]
    rule = load_rule_file(path)
    methods = rule.raw["verification"]["methods"]
    assert "static-lint-execution" not in methods
    ruff_impl = resolve_method("static-lint-execution")
    assert ruff_impl is not None
    assert "observability" not in ruff_impl.allowed_domains

    resolutions = dict(resolve_methods(methods))
    obs_impl = resolutions["observability-behavior-test-verification"]
    assert obs_impl is not None
    assert obs_impl.runner == "test-suite"
    assert obs_impl.allowed_domains == frozenset({"observability"})
    assert rule.raw["human_review"]["required"] is True

    statement = rule.raw["requirement"]["statement"].lower()
    assert "crash dumps and memory snapshots" in statement
    assert "disable core dumps, crash dumps, and heap snapshots by default" in statement
    assert rule.raw["acceptance"]["unjustified_production_crash_dumps_enabled"] == 0
    assert rule.raw["acceptance"]["unrestricted_crash_dump_exposure_paths"] == 0


def test_cli_assess_dispatches_language_neutral_runner_outcome(
    tmp_path: Path,
    monkeypatch: Any,
) -> None:
    proj = tmp_path / "universal_proj"
    proj.mkdir()
    invoked: list[bool] = []

    def _stub_run(project_root: Path) -> RunnerResult:
        invoked.append(True)
        ev_dir = project_root / ".arkhon" / "evidence" / "testing"
        ev_dir.mkdir(parents=True, exist_ok=True)
        rep = ev_dir / "test-execution-report.json"
        payload = {
            "schema_version": 1,
            "language": "python",
            "adapter": "pytest",
            "classification": "passed",
            "counts": {"total": 2, "passed": 2, "failed": 0, "errors": 0, "skipped": 0},
            "executed_tests": [],
        }
        rep.write_text(json.dumps(payload), encoding="utf-8")
        return RunnerResult("test-suite", RunnerOutcome.PASS, "", [rep])

    orig_create = ad_mod.create_assess_runner
    stub_runner = SimpleNamespace(name="test-suite", run=_stub_run)
    monkeypatch.setattr(
        ad_mod,
        "create_assess_runner",
        lambda r_name: stub_runner if r_name == "test-suite" else orig_create(r_name),
    )
    monkeypatch.setattr(
        MypyRunner, "run", lambda _s, _p: RunnerResult("mypy", RunnerOutcome.BLOCKED, "skip")
    )
    monkeypatch.setattr(
        TsarRunner, "run", lambda _s, _p: RunnerResult("tsar", RunnerOutcome.BLOCKED, "skip")
    )
    monkeypatch.setattr(cli_mod, "_commit_sha", lambda _p: "a" * 40)
    monkeypatch.setattr(cli_mod, "_working_tree_clean", lambda _p: True)
    with contextlib.suppress(SystemExit):
        cli_mod.main(["assess", str(proj)])
    assert invoked == [True]
