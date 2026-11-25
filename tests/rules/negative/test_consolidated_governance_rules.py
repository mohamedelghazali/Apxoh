"""Negative rule validation and malformed-YAML robustness tests (Finding 6)."""

from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

import yaml

from arkhon.rules.loader import Rule
from arkhon.rules.validator import validate_rule, validate_semantics

REPO_ROOT = Path(__file__).resolve().parents[3]
SCHEMA_PATH = REPO_ROOT / "schemas" / "rule.schema.json"
TST_004_PATH = (
    REPO_ROOT / "rules" / "testing" / "SE-TST-004-critical-and-negative-security-tests.yaml"
)


def _load_tst_004() -> dict[str, Any]:
    data = yaml.safe_load(TST_004_PATH.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    return data


def test_critical_rule_downgraded_to_advisory_is_rejected() -> None:
    raw = copy.deepcopy(_load_tst_004())
    raw["metadata"]["enforcement"] = "advisory"
    errors = validate_semantics(Rule(id=raw["id"], path=TST_004_PATH, raw=raw))
    assert any("cannot use 'advisory' enforcement" in str(e) for e in errors)


def test_human_review_true_without_approver_role_is_rejected() -> None:
    raw = copy.deepcopy(_load_tst_004())
    raw["human_review"] = {"required": True, "approver_role": "   "}
    errors = validate_semantics(Rule(id=raw["id"], path=TST_004_PATH, raw=raw))
    assert any("approver_role" in str(e) for e in errors)


def test_duplicate_valid_methods_rejected() -> None:
    raw = copy.deepcopy(_load_tst_004())
    raw["verification"]["methods"] = [
        "automated-test-suite-execution",
        "automated-test-suite-execution",
    ]
    errors = validate_rule(Rule(id=raw["id"], path=TST_004_PATH, raw=raw), SCHEMA_PATH)
    assert any("must not repeat" in str(e) for e in errors)


def test_validator_never_crashes_on_unhashable_or_malformed_method_entries() -> None:
    malformed_payloads: list[object] = [
        "automated-test-suite-execution",
        {"method": "dict-instead-of-list"},
        None,
        [],
        [{"unhashable": "mapping"}],
        [["nested-list"]],
        [None, "automated-test-suite-execution"],
        [123, True, "   "],
        [{"dup": 1}, {"dup": 1}],
    ]
    for bad_methods in malformed_payloads:
        raw = copy.deepcopy(_load_tst_004())
        raw["verification"]["methods"] = bad_methods
        errors = validate_semantics(Rule(id=raw["id"], path=TST_004_PATH, raw=raw))
        assert errors, f"expected validation error for {bad_methods!r}"


def test_validator_handles_malformed_scope_failure_and_metadata_without_type_error() -> None:
    raw = copy.deepcopy(_load_tst_004())
    raw["metadata"] = "not-a-mapping"
    raw["scope"] = {"project_types": [{"bad": 1}], "languages": [[1, 2]]}
    raw["failure"] = {"actions": [{"unhashable": True}, None]}
    raw["human_review"] = ["not-a-mapping"]
    errors = validate_semantics(Rule(id="SE-TST-004", path=TST_004_PATH, raw=raw))
    assert len(errors) >= 4
