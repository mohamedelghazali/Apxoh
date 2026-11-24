"""Tests for arkhon.rules.registry."""

from __future__ import annotations

from pathlib import Path

import pytest

from arkhon.core.errors import RuleError, RuleNotFoundError
from arkhon.rules.loader import Rule
from arkhon.rules.registry import RuleRegistry, build_registry


def _rule(
    rule_id: str,
    domain: str = "requirements",
    status: str = "active",
    enforcement: str = "blocking",
    severity: str = "high",
) -> Rule:
    return Rule(
        id=rule_id,
        path=Path(f"{rule_id}.yaml"),
        raw={
            "id": rule_id,
            "metadata": {
                "title": rule_id,
                "domain": domain,
                "version": "1.0.0",
                "status": status,
                "severity": severity,
                "enforcement": enforcement,
            },
            "scope": {"project_types": ["all"]},
            "requirement": {"statement": "x"},
            "verification": {"mode": "deterministic", "methods": ["schema-validation"]},
            "acceptance": {"x": 1},
        },
    )


@pytest.fixture
def registry() -> RuleRegistry:
    return RuleRegistry(
        [
            _rule("SE-REQ-001", enforcement="blocking"),
            _rule("SE-REQ-002", enforcement="advisory"),
            _rule("SE-TST-001", domain="testing", enforcement="critical"),
            _rule(
                "SE-SEC-001",
                domain="software-security",
                status="deprecated",
                enforcement="required",
            ),
        ]
    )


def test_len(registry: RuleRegistry) -> None:
    assert len(registry) == 4


def test_contains(registry: RuleRegistry) -> None:
    assert "SE-REQ-001" in registry
    assert "SE-NOPE-999" not in registry


def test_get(registry: RuleRegistry) -> None:
    assert registry.get("SE-REQ-001").id == "SE-REQ-001"


def test_get_missing(registry: RuleRegistry) -> None:
    with pytest.raises(RuleNotFoundError):
        registry.get("SE-NOPE-999")


def test_all(registry: RuleRegistry) -> None:
    assert len(registry.all()) == 4


def test_by_domain(registry: RuleRegistry) -> None:
    assert len(registry.by_domain("requirements")) == 2
    assert registry.by_domain("nope") == []


def test_by_enforcement(registry: RuleRegistry) -> None:
    assert len(registry.by_enforcement("blocking")) == 1
    assert len(registry.by_enforcement("critical")) == 1


def test_by_severity(registry: RuleRegistry) -> None:
    assert len(registry.by_severity("high")) == 4


def test_by_status(registry: RuleRegistry) -> None:
    assert len(registry.by_status("active")) == 3
    assert len(registry.by_status("deprecated")) == 1


def test_active(registry: RuleRegistry) -> None:
    assert len(registry.active()) == 3


def test_domains(registry: RuleRegistry) -> None:
    assert registry.domains() == ["requirements", "software-security", "testing"]


def test_duplicate_raises() -> None:
    with pytest.raises(RuleError, match="duplicate rule id"):
        RuleRegistry([_rule("SE-REQ-001"), _rule("SE-REQ-001")])


def test_build_registry_from_dir(tmp_path: Path) -> None:
    import yaml

    raw = {
        "id": "SE-REQ-001",
        "metadata": {
            "title": "x",
            "domain": "requirements",
            "version": "1.0.0",
            "status": "active",
            "severity": "high",
            "enforcement": "blocking",
        },
        "scope": {"project_types": ["all"]},
        "requirement": {"statement": "x"},
        "verification": {"mode": "deterministic", "methods": ["x"]},
        "acceptance": {"x": 1},
    }
    (tmp_path / "r.yaml").write_text(yaml.safe_dump(raw), encoding="utf-8")
    assert len(build_registry(tmp_path)) == 1
