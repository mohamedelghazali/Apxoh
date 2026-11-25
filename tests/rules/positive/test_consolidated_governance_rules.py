"""Positive schema, semantic, cross-language, and crash-dump policy tests for consolidated rules."""

from __future__ import annotations

from pathlib import Path

from arkhon.rules.loader import load_rule_file
from arkhon.rules.validator import validate_rule
from arkhon.verification.methods import resolve_method, resolve_methods

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
