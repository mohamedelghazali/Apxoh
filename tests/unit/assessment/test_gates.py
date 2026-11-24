"""Tests for arkhon.assessment.gates."""

from __future__ import annotations

import pytest

from arkhon.assessment.gates import (
    GATE_DOMAINS,
    RuleOutcome,
    evaluate_all_gates,
    evaluate_gate,
)
from arkhon.core.errors import GateError


def _outcome(rule_id: str, enforcement: str, status: str) -> RuleOutcome:
    return RuleOutcome(rule_id=rule_id, enforcement=enforcement, status=status)


def test_gate_domains_cover_all() -> None:
    assert "release_gate" in GATE_DOMAINS
    assert "security_gate" in GATE_DOMAINS


def test_unknown_gate_raises() -> None:
    with pytest.raises(GateError, match="unknown gate"):
        evaluate_gate("nope_gate", [])


def test_all_pass_closes() -> None:
    verdict = evaluate_gate(
        "requirements_gate",
        [
            _outcome("SE-REQ-001", "blocking", "PASS"),
            _outcome("SE-REQ-002", "critical", "PASS"),
        ],
    )
    assert verdict.status == "PASS"
    assert verdict.closes


def test_critical_fail_is_fail() -> None:
    verdict = evaluate_gate("security_gate", [_outcome("SE-SEC-001", "critical", "FAIL")])
    assert verdict.status == "FAIL"
    assert not verdict.closes


def test_blocking_fail_is_blocked() -> None:
    verdict = evaluate_gate("testing_gate", [_outcome("SE-TST-001", "blocking", "FAIL")])
    assert verdict.status == "BLOCKED"


def test_required_fail_is_blocked() -> None:
    verdict = evaluate_gate("requirements_gate", [_outcome("SE-REQ-001", "required", "FAIL")])
    assert verdict.status == "BLOCKED"


def test_advisory_fail_does_not_block() -> None:
    verdict = evaluate_gate("requirements_gate", [_outcome("SE-REQ-001", "advisory", "FAIL")])
    assert verdict.status == "PASS"


def test_not_applicable_is_neutral() -> None:
    verdict = evaluate_gate(
        "requirements_gate", [_outcome("SE-REQ-001", "blocking", "NOT_APPLICABLE")]
    )
    assert verdict.status == "PASS"


def test_critical_overrides_blocking() -> None:
    verdict = evaluate_gate(
        "security_gate",
        [
            _outcome("SE-A", "blocking", "FAIL"),
            _outcome("SE-B", "critical", "FAIL"),
        ],
    )
    assert verdict.status == "FAIL"
    assert verdict.critical_failures == 1
    assert verdict.blocking_failures == 1


def test_evaluate_all_gates() -> None:
    outcomes = {
        "requirements": [_outcome("SE-REQ-001", "blocking", "PASS")],
        "testing": [_outcome("SE-TST-001", "blocking", "PASS")],
        "software-security": [_outcome("SE-SEC-001", "critical", "PASS")],
        "release": [_outcome("SE-REL-001", "blocking", "PASS")],
    }
    verdicts = evaluate_all_gates(outcomes)
    assert "security_gate" in verdicts and "release_gate" in verdicts
    assert verdicts["security_gate"].status == "PASS"
    assert verdicts["release_gate"].status == "PASS"


def test_unknown_domain_rejected() -> None:
    with pytest.raises(GateError, match="unknown outcome domains"):
        evaluate_all_gates({"made-up": []})


def test_to_dict() -> None:
    verdict = evaluate_gate("requirements_gate", [_outcome("SE-REQ-001", "blocking", "PASS")])
    data = verdict.to_dict()
    assert data["gate"] == "requirements_gate"
    assert data["status"] == "PASS"


def test_empty_outcomes_are_blocked() -> None:
    verdict = evaluate_gate("security_gate", [])
    assert verdict.status == "BLOCKED"
    assert not verdict.closes


def test_unknown_enforcement_cannot_downgrade_failure() -> None:
    with pytest.raises(GateError, match="unsupported enforcement"):
        evaluate_gate("security_gate", [_outcome("SE-SEC-999", "unrecognized", "FAIL")])


def test_unknown_enforcement_is_rejected_even_for_pass() -> None:
    with pytest.raises(GateError, match="unsupported enforcement"):
        evaluate_gate("testing_gate", [_outcome("SE-TST-999", "unknown", "PASS")])
