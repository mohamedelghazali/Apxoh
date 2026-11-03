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
        "metadata": {"title": "Test rule", "domain": "requirements", "version": "1.0.0",
                     "status": "active", "severity": "high", "enforcement": "blocking"},
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
