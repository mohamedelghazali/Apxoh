"""Tests for arkhon.policies.blocking."""

from __future__ import annotations

from pathlib import Path

import pytest

from arkhon.core.errors import GovernanceError
from arkhon.governance.policy_loader import Policy, PolicyRegistry
from arkhon.policies.blocking import (
    BlockingPolicyEvaluator,
    BlockingResult,
    BlockingViolation,
    ensure_no_bypass,
)


def _policy(
    policy_id: str,
    category: str = "blocking",
    trigger_rules: list[str] | None = None,
    trigger_paths: list[str] | None = None,
    enabled: bool = True,
) -> Policy:
    return Policy(
        id=policy_id,
        category=category,
        path=Path(f"{policy_id}.yaml"),
        raw={
            "id": policy_id,
            "title": policy_id,
            "enabled": enabled,
            "trigger_rules": trigger_rules or [],
            "trigger_paths": trigger_paths or [],
            "reason": f"policy {policy_id}",
        },
    )


def test_no_violations() -> None:
    registry = PolicyRegistry([_policy("p1", trigger_rules=["SE-X-001"])])
    evaluator = BlockingPolicyEvaluator(registry)
    result = evaluator.evaluate(
        failing_rules=set(),
        project_root=Path.cwd(),
    )
    assert not result.blocks
    assert result.count == 0


def test_rule_trigger() -> None:
    registry = PolicyRegistry(
        [
            _policy("p1", trigger_rules=["SE-SEC-001"]),
        ]
    )
    evaluator = BlockingPolicyEvaluator(registry)
    result = evaluator.evaluate(
        failing_rules={"SE-SEC-001"},
        project_root=Path.cwd(),
    )
    assert result.blocks
    assert result.count == 1
    assert result.violations[0].policy_id == "p1"
    assert result.violations[0].rule_id == "SE-SEC-001"


def test_disabled_policy_ignored() -> None:
    registry = PolicyRegistry(
        [
            _policy("p1", trigger_rules=["SE-SEC-001"], enabled=False),
        ]
    )
    evaluator = BlockingPolicyEvaluator(registry)
    result = evaluator.evaluate(
        failing_rules={"SE-SEC-001"},
        project_root=Path.cwd(),
    )
    assert not result.blocks


def test_non_blocking_category_ignored() -> None:
    registry = PolicyRegistry(
        [
            _policy("p1", category="advisory", trigger_rules=["SE-SEC-001"]),
        ]
    )
    evaluator = BlockingPolicyEvaluator(registry)
    result = evaluator.evaluate(
        failing_rules={"SE-SEC-001"},
        project_root=Path.cwd(),
    )
    assert not result.blocks


def test_path_trigger(tmp_path: Path) -> None:
    (tmp_path / "migrations").mkdir()
    (tmp_path / "migrations" / "001.sql").write_text("x", encoding="utf-8")
    registry = PolicyRegistry(
        [
            _policy("p1", trigger_paths=["migrations/**"]),
        ]
    )
    evaluator = BlockingPolicyEvaluator(registry)
    result = evaluator.evaluate(
        failing_rules=set(),
        project_root=tmp_path,
    )
    assert result.blocks
    assert "path:" in result.violations[0].rule_id


def test_ensure_no_bypass_raises() -> None:
    result = BlockingResult(
        violations=[
            BlockingViolation(policy_id="p1", rule_id="SE-X-001", reason="x"),
        ]
    )
    with pytest.raises(GovernanceError, match="blocking policies violated"):
        ensure_no_bypass(result)


def test_ensure_no_bypass_passes() -> None:
    ensure_no_bypass(BlockingResult())


def test_invalid_trigger_rules_are_ignored_and_nonblocking_violation_does_not_block(
    tmp_path: Path,
) -> None:
    invalid = Policy(
        id="invalid",
        category="blocking",
        path=Path("invalid.yaml"),
        raw={"trigger_rules": "not-a-list", "trigger_paths": []},
    )
    registry = PolicyRegistry([invalid])
    result = BlockingPolicyEvaluator(registry).evaluate(
        failing_rules={"SE-X-001"}, project_root=tmp_path
    )
    assert result.count == 0
    nonblocking = BlockingResult(
        violations=[
            BlockingViolation(
                policy_id="advisory",
                rule_id="SE-X-001",
                reason="informational",
                blocking=False,
            )
        ]
    )
    assert not nonblocking.blocks
