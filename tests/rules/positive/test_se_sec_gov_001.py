"""Positive tests for SE-SEC-GOV-001 (TSAR audit required)."""

from __future__ import annotations

from pathlib import Path

from arkhon.rules.loader import load_rule_file
from arkhon.rules.validator import validate_rule

REPO_ROOT = Path(__file__).resolve().parents[3]
RULE_PATH = REPO_ROOT / "rules" / "software-security" / "SE-SEC-GOV-001-tsar-audit-required.yaml"


def test_rule_exists() -> None:
    assert RULE_PATH.is_file()


def test_rule_loads() -> None:
    rule = load_rule_file(RULE_PATH)
    assert rule.id == "SE-SEC-GOV-001"
    assert rule.domain == "software-security"
    assert rule.enforcement == "critical"
    assert rule.severity == "critical"


def test_rule_validates() -> None:
    rule = load_rule_file(RULE_PATH)
    schema_path = REPO_ROOT / "schemas" / "rule.schema.json"
    errors = validate_rule(rule, schema_path if schema_path.is_file() else None)
    assert errors == []


def test_rule_delegates_to_tsar() -> None:
    rule = load_rule_file(RULE_PATH)
    verification = rule.raw["verification"]
    assert verification["mode"] == "delegated"
    assert verification["delegate_to"] == "tsar"


def test_rule_requires_human_review() -> None:
    rule = load_rule_file(RULE_PATH)
    assert rule.raw["human_review"]["required"] is True
    assert rule.raw["human_review"]["approver_role"] == "Security Lead"


def test_rule_blocks_release_gate() -> None:
    rule = load_rule_file(RULE_PATH)
    assert "block-release-gate" in rule.raw["failure"]["actions"]


def test_rule_requires_tsar_evidence() -> None:
    rule = load_rule_file(RULE_PATH)
    required = rule.raw["evidence"]["required"]
    sources = [r.get("source") if isinstance(r, dict) else r for r in required]
    assert "tsar" in sources
