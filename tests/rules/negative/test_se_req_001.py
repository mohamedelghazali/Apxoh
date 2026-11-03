"""Negative tests for SE-REQ-001 — checks the rule rejects bad configurations."""

from __future__ import annotations

from pathlib import Path

from arkhon.rules.loader import Rule
from arkhon.rules.validator import validate_semantics

REPO_ROOT = Path(__file__).resolve().parents[3]
RULE_PATH = REPO_ROOT / "languages" / "python" / "rules" / "SE-REQ-001-verifiable-requirements.yaml"


def _load_raw() -> dict:
    import yaml
    with RULE_PATH.open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def _make_rule(raw: dict) -> Rule:
    return Rule(id=raw["id"], path=RULE_PATH, raw=raw)


def test_wrong_domain_prefix_rejected() -> None:
    raw = _load_raw()
    raw["id"] = "SE-TST-001"  # but domain is requirements
    errors = validate_semantics(_make_rule(raw))
    assert any("must start with 'SE-REQ'" in str(e) for e in errors)


def test_missing_verification_methods_rejected() -> None:
    raw = _load_raw()
    raw["verification"]["methods"] = []
    errors = validate_semantics(_make_rule(raw))
    assert any("non-empty list" in str(e) for e in errors)


def test_invalid_severity_rejected() -> None:
    raw = _load_raw()
    raw["metadata"]["severity"] = "super-critical"
    errors = validate_semantics(_make_rule(raw))
    assert any("invalid severity" in str(e) for e in errors)


def test_invalid_enforcement_rejected() -> None:
    raw = _load_raw()
    raw["metadata"]["enforcement"] = "sometimes"
    errors = validate_semantics(_make_rule(raw))
    assert any("invalid enforcement" in str(e) for e in errors)


def test_missing_acceptance_rejected() -> None:
    raw = _load_raw()
    raw["acceptance"] = {}
    errors = validate_semantics(_make_rule(raw))
    assert any("acceptance" in str(e) for e in errors)
