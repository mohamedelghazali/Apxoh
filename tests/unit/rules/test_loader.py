"""Tests for arkhon.rules.loader."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from arkhon.core.errors import RuleDuplicateError, RuleError, RuleValidationError
from arkhon.rules.loader import Rule, load_rule_file, load_rules_dir

VALID_RULE = {
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


def _write_rule(path: Path, data: dict) -> Path:
    path.write_text(yaml.safe_dump(data), encoding="utf-8")
    return path


@pytest.fixture
def valid_rule_file(tmp_path: Path) -> Path:
    return _write_rule(tmp_path / "SE-REQ-001.yaml", VALID_RULE)


def test_load_valid_rule(valid_rule_file: Path) -> None:
    rule = load_rule_file(valid_rule_file)
    assert isinstance(rule, Rule)
    assert (rule.id, rule.title, rule.domain) == ("SE-REQ-001", "Test rule", "requirements")
    assert (rule.severity, rule.enforcement, rule.status) == ("high", "blocking", "active")


def test_load_missing_file(tmp_path: Path) -> None:
    with pytest.raises(RuleError, match="not found"):
        load_rule_file(tmp_path / "missing.yaml")


def test_load_wrong_extension(tmp_path: Path) -> None:
    path = tmp_path / "rule.txt"
    path.write_text("not yaml", encoding="utf-8")
    with pytest.raises(RuleError, match="must be YAML"):
        load_rule_file(path)


@pytest.mark.parametrize("data", [{}, {"id": ""}, {"id": 42}])
def test_load_rule_without_valid_id(tmp_path: Path, data: dict) -> None:
    path = _write_rule(tmp_path / "invalid.yaml", data)
    with pytest.raises(RuleValidationError, match="valid 'id'"):
        load_rule_file(path)


def test_load_empty_file(tmp_path: Path) -> None:
    path = tmp_path / "empty.yaml"
    path.write_text("", encoding="utf-8")
    with pytest.raises(RuleValidationError, match="empty YAML"):
        load_rule_file(path)


def test_load_non_mapping(tmp_path: Path) -> None:
    path = tmp_path / "list.yaml"
    path.write_text("- one\n- two\n", encoding="utf-8")
    with pytest.raises(RuleValidationError, match="mapping"):
        load_rule_file(path)


def test_load_rules_dir_empty(tmp_path: Path) -> None:
    result = load_rules_dir(tmp_path)
    assert result.ok and not result.rules


def test_load_rules_dir_missing(tmp_path: Path) -> None:
    result = load_rules_dir(tmp_path / "missing")
    assert result.ok and len(result.warnings) == 1


def test_load_rules_dir_multiple_and_yml(tmp_path: Path) -> None:
    for index, suffix in enumerate((".yaml", ".yml", ".yaml"), start=1):
        item = dict(VALID_RULE)
        item["id"] = f"SE-REQ-{index:03d}"
        _write_rule(tmp_path / f"rule-{index}{suffix}", item)
    result = load_rules_dir(tmp_path)
    assert result.ok and len(result.rules) == 3


def test_load_rules_dir_duplicate_ids(tmp_path: Path) -> None:
    _write_rule(tmp_path / "a.yaml", VALID_RULE)
    _write_rule(tmp_path / "b.yaml", VALID_RULE)
    result = load_rules_dir(tmp_path)
    assert not result.ok
    assert any(isinstance(error, RuleDuplicateError) for error in result.errors)


def test_load_rules_dir_skips_templates_and_recurses(tmp_path: Path) -> None:
    _write_rule(tmp_path / "_template.yaml", VALID_RULE)
    nested = tmp_path / "nested"
    nested.mkdir()
    _write_rule(nested / "rule.yaml", VALID_RULE)
    result = load_rules_dir(tmp_path)
    assert result.ok and len(result.rules) == 1


def test_load_invalid_yaml(tmp_path: Path) -> None:
    path = tmp_path / "malformed.yaml"
    path.write_text("[", encoding="utf-8")
    with pytest.raises(RuleValidationError, match="valid YAML"):
        load_rule_file(path)
