"""Parametrized validation for all repository rule files."""

from __future__ import annotations

from pathlib import Path

import pytest

from arkhon.rules.loader import load_rule_file
from arkhon.rules.validator import validate_rule

REPO_ROOT = Path(__file__).resolve().parents[3]
SCHEMA = REPO_ROOT / "schemas" / "rule.schema.json"


def _discover_rules() -> list[Path]:
    rules_root = REPO_ROOT / "rules"
    if not rules_root.is_dir():
        return []
    return sorted(
        path
        for path in rules_root.rglob("*.yaml")
        if not path.name.startswith("_")
        and "templates" not in path.parts
        and "partials" not in path.parts
    )


RULES = _discover_rules()


@pytest.mark.parametrize("rule_path", RULES, ids=lambda path: path.name)
def test_rule_loads(rule_path: Path) -> None:
    rule = load_rule_file(rule_path)
    assert rule.id, f"{rule_path}: empty id"


@pytest.mark.parametrize("rule_path", RULES, ids=lambda path: path.name)
def test_rule_validates(rule_path: Path) -> None:
    rule = load_rule_file(rule_path)
    errors = validate_rule(rule, SCHEMA if SCHEMA.is_file() else None)
    assert errors == [], f"{rule_path}: {errors}"


@pytest.mark.parametrize("rule_path", RULES, ids=lambda path: path.name)
def test_rule_id_matches_domain(rule_path: Path) -> None:
    from arkhon.core.constants import DOMAIN_RULE_PREFIX

    rule = load_rule_file(rule_path)
    domain = rule.domain
    if domain in DOMAIN_RULE_PREFIX:
        expected = DOMAIN_RULE_PREFIX[domain]
        assert rule.id.startswith(expected), (
            f"{rule_path}: id {rule.id} does not match domain {domain} ({expected})"
        )


def test_at_least_15_rules_present() -> None:
    assert len(RULES) >= 15, f"only {len(RULES)} rules found"
