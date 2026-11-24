"""Tests for arkhon.rules.validator."""

from __future__ import annotations

from pathlib import Path

from arkhon.core.constants import (
    ALL_ENFORCEMENT,
    ALL_RULE_DOMAINS,
    ALL_RULE_STATUSES,
    ALL_SEVERITIES,
    DOMAIN_RULE_PREFIX,
)
from arkhon.rules.loader import Rule
from arkhon.rules.validator import validate_against_schema, validate_rule, validate_semantics


def _make_rule(raw: dict) -> Rule:
    return Rule(id=raw.get("id", "SE-REQ-001"), path=Path("x.yaml"), raw=raw)


def _valid_raw() -> dict:
    return {
        "id": "SE-REQ-001",
        "metadata": {
            "title": "Test rule",
            "domain": "requirements",
            "version": "1.0.0",
            "status": "active",
            "severity": "high",
            "enforcement": "blocking",
        },
        "scope": {"project_types": ["all"]},
        "requirement": {"statement": "The system must do X."},
        "verification": {"mode": "deterministic", "methods": ["schema-validation"]},
        "acceptance": {"unverified": 0},
    }


def test_valid_rule_has_no_errors() -> None:
    assert validate_semantics(_make_rule(_valid_raw())) == []


def test_unknown_domain() -> None:
    raw = _valid_raw()
    raw["metadata"]["domain"] = "not-a-domain"
    assert any("unknown domain" in str(e) for e in validate_semantics(_make_rule(raw)))


def test_invalid_enforcement() -> None:
    raw = _valid_raw()
    raw["metadata"]["enforcement"] = "wrong"
    assert any("invalid enforcement" in str(e) for e in validate_semantics(_make_rule(raw)))


def test_invalid_severity() -> None:
    raw = _valid_raw()
    raw["metadata"]["severity"] = "wrong"
    assert any("invalid severity" in str(e) for e in validate_semantics(_make_rule(raw)))


def test_invalid_status() -> None:
    raw = _valid_raw()
    raw["metadata"]["status"] = "wrong"
    assert any("invalid status" in str(e) for e in validate_semantics(_make_rule(raw)))


def test_rule_id_prefix_mismatch() -> None:
    raw = _valid_raw()
    raw["id"] = "SE-TST-001"
    assert any("must start with 'SE-REQ'" in str(e) for e in validate_semantics(_make_rule(raw)))


def test_missing_verification_methods() -> None:
    raw = _valid_raw()
    raw["verification"]["methods"] = []
    assert any("non-empty list" in str(e) for e in validate_semantics(_make_rule(raw)))


def test_delegated_mode_requires_delegate_to() -> None:
    raw = _valid_raw()
    raw["verification"]["mode"] = "delegated"
    assert any("delegate_to" in str(e) for e in validate_semantics(_make_rule(raw)))


def test_delegated_mode_with_delegate_to() -> None:
    raw = _valid_raw()
    raw["verification"].update(mode="delegated", delegate_to="tsar")
    assert validate_semantics(_make_rule(raw)) == []


def test_missing_acceptance() -> None:
    raw = _valid_raw()
    raw["acceptance"] = {}
    assert any("acceptance" in str(e) for e in validate_semantics(_make_rule(raw)))


def test_schema_validation_missing_file(tmp_path: Path) -> None:
    errors = validate_against_schema(_make_rule(_valid_raw()), tmp_path / "nope.json")
    assert any("schema not found" in str(e) for e in errors)


def test_validate_rule_combines() -> None:
    raw = _valid_raw()
    raw["metadata"]["domain"] = "wrong"
    assert validate_rule(_make_rule(raw))


def test_all_domains_have_prefixes() -> None:
    assert set(DOMAIN_RULE_PREFIX) == set(ALL_RULE_DOMAINS)


def test_all_constants_non_empty() -> None:
    assert ALL_ENFORCEMENT and ALL_SEVERITIES and ALL_RULE_STATUSES


def test_schema_validation_import_invalid_json_and_schema_errors(
    tmp_path: Path, monkeypatch
) -> None:
    import sys

    from arkhon.core.errors import RuleValidationError
    from arkhon.rules.validator import validate_against_schema

    rule = _make_rule(_valid_raw())
    missing_dependency = tmp_path / "missing-dependency.json"
    monkeypatch.setitem(sys.modules, "jsonschema", None)
    errors = validate_against_schema(rule, missing_dependency)
    assert any("jsonschema is required" in str(error) for error in errors)
    monkeypatch.delitem(sys.modules, "jsonschema")
    malformed = tmp_path / "malformed.json"
    malformed.write_text("{", encoding="utf-8")
    errors = validate_against_schema(rule, malformed)
    assert any("cannot load valid rule schema" in str(error) for error in errors)
    schema = tmp_path / "schema.json"
    schema.write_text('{"type": "object", "required": ["missing"]}', encoding="utf-8")
    errors = validate_against_schema(rule, schema)
    assert errors and isinstance(errors[0], RuleValidationError)
    invalid_schema = tmp_path / "invalid-schema.json"
    invalid_schema.write_text('{"type": "not-a-json-schema-type"}', encoding="utf-8")
    assert validate_against_schema(rule, invalid_schema)
