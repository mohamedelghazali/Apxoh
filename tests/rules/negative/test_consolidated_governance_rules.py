"""Negative rule validation and malformed-YAML robustness tests (Finding 6)."""

from __future__ import annotations

import builtins
import copy
from pathlib import Path
from typing import Any

import yaml

from gencode_gov.rules.loader import Rule
from gencode_gov.rules.validator import validate_against_schema, validate_rule, validate_semantics

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


def test_validator_handles_malformed_scope_failure_and_metadata_without_type_error(
    tmp_path: Path,
    monkeypatch: Any,
) -> None:
    bad_raw: Any = "not-a-dict"
    non_dict_rule = Rule(id="SE-TST-004", path=TST_004_PATH, raw=bad_raw)
    assert any("mapping" in str(e) for e in validate_semantics(non_dict_rule))

    raw = copy.deepcopy(_load_tst_004())
    raw["metadata"] = "not-a-mapping"
    raw["scope"] = {"project_types": [{"bad": 1}], "languages": [[1, 2]]}
    raw["failure"] = {"actions": [{"unhashable": True}, None, "dup", "dup"]}
    raw["human_review"] = ["not-a-mapping"]
    raw["verification"] = "not-a-mapping"
    errors = validate_semantics(Rule(id="SE-TST-999", path=TST_004_PATH, raw=raw))
    assert len(errors) >= 5

    raw2 = copy.deepcopy(_load_tst_004())
    raw2["scope"] = "not-a-mapping"
    raw2["failure"] = "not-a-mapping"
    errs2 = validate_semantics(Rule(id="SE-TST-004", path=TST_004_PATH, raw=raw2))
    assert any("'scope' must be a mapping" in str(e) for e in errs2)
    assert any("'failure' must be a mapping" in str(e) for e in errs2)

    missing_schema = tmp_path / "missing.json"
    rule2 = Rule(id="SE-TST-004", path=TST_004_PATH, raw=raw2)
    assert validate_against_schema(rule2, missing_schema)
    bad_schema = tmp_path / "bad.json"
    bad_schema.write_text("{not-json", encoding="utf-8")
    assert validate_against_schema(Rule(id="SE-TST-004", path=TST_004_PATH, raw=raw2), bad_schema)

    orig_import = builtins.__import__

    def deny_jsonschema(name: str, *args: Any, **kwargs: Any) -> Any:
        if name == "jsonschema":
            raise ImportError("missing jsonschema")
        return orig_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", deny_jsonschema)
    errs_imp = validate_against_schema(
        Rule(id="SE-TST-004", path=TST_004_PATH, raw=raw2), SCHEMA_PATH
    )
    assert any("jsonschema is required" in str(e) for e in errs_imp)
