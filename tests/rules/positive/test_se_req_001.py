"""Positive tests for SE-REQ-001 (Verifiable Requirements)."""

from __future__ import annotations

from pathlib import Path

import yaml

from arkhon.rules.loader import load_rule_file
from arkhon.rules.validator import validate_rule

REPO_ROOT = Path(__file__).resolve().parents[3]
RULE_PATH = REPO_ROOT / "languages" / "python" / "rules" / "SE-REQ-001-verifiable-requirements.yaml"


def test_rule_file_exists() -> None:
    assert RULE_PATH.is_file()


def test_rule_loads_successfully() -> None:
    rule = load_rule_file(RULE_PATH)
    assert rule.id == "SE-REQ-001"
    assert rule.domain == "requirements"
    assert rule.enforcement == "blocking"


def test_rule_passes_validation() -> None:
    rule = load_rule_file(RULE_PATH)
    schema_path = REPO_ROOT / "schemas" / "rule.schema.json"
    errors = validate_rule(rule, schema_path if schema_path.is_file() else None)
    assert errors == [], f"validation errors: {errors}"


def test_rule_has_all_required_metadata() -> None:
    rule = load_rule_file(RULE_PATH)
    meta = rule.raw["metadata"]
    for field in ("title", "domain", "version", "status", "severity", "enforcement"):
        assert field in meta


def test_rule_has_verification_methods() -> None:
    rule = load_rule_file(RULE_PATH)
    methods = rule.raw["verification"]["methods"]
    assert len(methods) >= 1


def test_rule_has_acceptance_criteria() -> None:
    rule = load_rule_file(RULE_PATH)
    acceptance = rule.raw["acceptance"]
    assert isinstance(acceptance, dict)
    assert len(acceptance) > 0


def test_rule_id_matches_domain_prefix() -> None:
    rule = load_rule_file(RULE_PATH)
    assert rule.id.startswith("SE-REQ")
