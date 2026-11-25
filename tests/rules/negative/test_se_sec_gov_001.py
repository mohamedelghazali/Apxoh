"""Negative tests for SE-SEC-GOV-001 — verifies the rule enforces its own contract."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from arkhon.rules.loader import Rule
from arkhon.rules.validator import validate_semantics

REPO_ROOT = Path(__file__).resolve().parents[3]
RULE_PATH = REPO_ROOT / "rules" / "software-security" / "SE-SEC-GOV-001-tsar-audit-required.yaml"


def _load_raw() -> dict[str, Any]:
    with RULE_PATH.open("r", encoding="utf-8") as fh:
        data: dict[str, Any] = yaml.safe_load(fh)
        return data


def _make(raw: dict[str, Any]) -> Rule:
    return Rule(id=raw["id"], path=RULE_PATH, raw=raw)


def test_delegated_without_target_rejected() -> None:
    raw = _load_raw()
    raw["verification"]["mode"] = "delegated"
    del raw["verification"]["delegate_to"]
    errors = validate_semantics(_make(raw))
    assert any("delegate_to" in str(e) for e in errors)


def test_downgraded_enforcement_rejected() -> None:
    """A critical rule cannot be silently downgraded to advisory enforcement."""
    raw = _load_raw()
    raw["metadata"]["enforcement"] = "advisory"
    errors = validate_semantics(_make(raw))
    assert any("cannot use 'advisory' enforcement" in str(e) for e in errors)


def test_invalid_domain_rejected() -> None:
    raw = _load_raw()
    raw["metadata"]["domain"] = "made-up-domain"
    errors = validate_semantics(_make(raw))
    assert any("unknown domain" in str(e) for e in errors)


def test_wrong_prefix_rejected() -> None:
    raw = _load_raw()
    raw["id"] = "SE-REQ-001"
    errors = validate_semantics(_make(raw))
    assert any("must start with 'SE-SEC'" in str(e) for e in errors)


def test_empty_acceptance_rejected() -> None:
    raw = _load_raw()
    raw["acceptance"] = {}
    errors = validate_semantics(_make(raw))
    assert any("acceptance" in str(e) for e in errors)
