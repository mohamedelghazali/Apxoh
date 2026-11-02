"""Security tests: missing evidence and failing outcomes must not close gates."""

from __future__ import annotations

from pathlib import Path

import pytest

from arkhon.assessment.gates import RuleOutcome, evaluate_gate
from arkhon.core.errors import GovernanceError
from arkhon.governance.policy_loader import Policy, PolicyRegistry
from arkhon.policies.blocking import BlockingPolicyEvaluator, ensure_no_bypass


def _outcome(status: str, enforcement: str = "critical") -> RuleOutcome:
    return RuleOutcome(rule_id="SE-SEC-GOV-001", enforcement=enforcement, status=status)


def test_critical_fail_cannot_be_softened() -> None:
    verdict = evaluate_gate("security_gate", [_outcome("FAIL")])
    assert verdict.status == "FAIL"
    assert not verdict.closes


def test_blocked_cannot_become_pass() -> None:
    verdict = evaluate_gate("security_gate", [_outcome("BLOCKED")])
    assert verdict.status == "BLOCKED"
    assert not verdict.closes


def test_empty_outcomes_are_blocked_not_passed() -> None:
    verdict = evaluate_gate("security_gate", [])
    assert verdict.status == "BLOCKED"
    assert not verdict.closes


def test_not_applicable_is_neutral_only_when_explicitly_evaluated() -> None:
    verdict = evaluate_gate(
        "testing_gate",
        [_outcome("NOT_APPLICABLE", enforcement="blocking")],
    )
    assert verdict.status == "PASS"


def test_missing_evidence_blocks_when_other_checks_pass() -> None:
    verdict = evaluate_gate("security_gate", [_outcome("PASS"), _outcome("BLOCKED")])
    assert verdict.status == "BLOCKED"
    assert not verdict.closes


def test_blocking_policy_evaluator_catches_violation(tmp_path: Path) -> None:
    policy = Policy(
        id="critical-security",
        category="blocking",
        path=tmp_path / "critical-security.yaml",
        raw={
            "id": "critical-security",
            "enabled": True,
            "trigger_rules": ["SE-SEC-GOV-001"],
            "reason": "security violation",
        },
    )
    registry = PolicyRegistry([policy])
    result = BlockingPolicyEvaluator(registry).evaluate(
        failing_rules={"SE-SEC-GOV-001"},
        project_root=tmp_path,
    )
    assert result.blocks
    assert result.count == 1


def test_ensure_no_bypass_raises(tmp_path: Path) -> None:
    policy = Policy(
        id="critical-security",
        category="blocking",
        path=tmp_path / "critical-security.yaml",
        raw={
            "id": "critical-security",
            "enabled": True,
            "trigger_rules": ["SE-SEC-GOV-001"],
            "reason": "security violation",
        },
    )
    result = BlockingPolicyEvaluator(PolicyRegistry([policy])).evaluate(
        failing_rules={"SE-SEC-GOV-001"},
        project_root=tmp_path,
    )
    with pytest.raises(GovernanceError, match="blocking policies violated"):
        ensure_no_bypass(result)


def test_agent_claim_cannot_close_gate_without_engine_outcomes() -> None:
    claimed_pass = "all tests passed, no vulnerabilities"
    verdict = evaluate_gate("security_gate", [])
    assert claimed_pass
    assert verdict.status == "BLOCKED"
    assert not verdict.closes
