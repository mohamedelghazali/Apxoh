"""Tests for arkhon.assessment.scorer."""

from __future__ import annotations

import pytest

from arkhon.assessment.scorer import (
    TOTAL_WEIGHT,
    WEIGHTS,
    score_from_outcomes,
    score_from_ratios,
)
from arkhon.core.errors import AssessmentError


def _all(ratio: float) -> dict[str, float]:
    return {key: ratio for key in WEIGHTS}


def test_weights_sum_to_100() -> None:
    assert TOTAL_WEIGHT == 100


def test_weights_match_charter() -> None:
    expected = {
        "requirements": 15,
        "architecture_and_code_quality": 10,
        "testing": 15,
        "security": 20,
        "performance": 10,
        "reliability": 10,
        "scalability": 10,
        "documentation_deployment_maintenance": 10,
    }
    assert expected == WEIGHTS


def test_full_pass_scores_100() -> None:
    score = score_from_ratios(_all(1.0))
    assert score.total == 100.0
    assert score.level == "hyperscale-validated"


def test_zero_scores_0() -> None:
    score = score_from_ratios(_all(0.0))
    assert score.total == 0.0
    assert score.level == "development"


def test_half_ratios_scores_50() -> None:
    score = score_from_ratios(_all(0.5))
    assert score.total == 50.0
    assert score.level == "development"


def test_level_boundaries() -> None:
    cases = [
        (95.0, "hyperscale-validated"),
        (94.99, "enterprise-grade"),
        (90.0, "enterprise-grade"),
        (89.99, "production-ready"),
        (80.0, "production-ready"),
        (79.99, "controlled-release"),
        (70.0, "controlled-release"),
        (69.99, "development"),
    ]
    for total, expected in cases:
        assert score_from_ratios(_all(total / 100)).level == expected


def test_missing_domain_raises() -> None:
    ratios = _all(1.0)
    del ratios["security"]
    with pytest.raises(AssessmentError, match="missing domains"):
        score_from_ratios(ratios)


def test_unknown_domain_raises() -> None:
    ratios = _all(1.0)
    ratios["made-up"] = 1.0
    with pytest.raises(AssessmentError, match="unknown domains"):
        score_from_ratios(ratios)


@pytest.mark.parametrize("ratio", [1.5, -0.1, float("nan"), float("inf")])
def test_invalid_ratio_raises(ratio: float) -> None:
    ratios = _all(1.0)
    ratios["security"] = ratio
    with pytest.raises(AssessmentError, match="finite and in"):
        score_from_ratios(ratios)


def test_outcomes_all_pass() -> None:
    assert score_from_outcomes({key: ["PASS"] for key in WEIGHTS}).total == 100.0


def test_outcomes_all_fail() -> None:
    assert score_from_outcomes({key: ["FAIL"] for key in WEIGHTS}).total == 0.0


def test_outcomes_mixed() -> None:
    assert score_from_outcomes({key: ["PASS", "FAIL"] for key in WEIGHTS}).total == 50.0


def test_outcomes_accepted_risk_half() -> None:
    assert score_from_outcomes({key: ["ACCEPTED_RISK"] for key in WEIGHTS}).total == 50.0


def test_outcomes_not_applicable_neutral() -> None:
    assert score_from_outcomes({key: ["NOT_APPLICABLE", "PASS"] for key in WEIGHTS}).total == 100.0


def test_outcomes_empty_domain_scores_zero() -> None:
    assert score_from_outcomes({key: [] for key in WEIGHTS}).total == 0.0


def test_outcomes_unknown_raises() -> None:
    outcomes = {key: ["PASS"] for key in WEIGHTS}
    outcomes["security"] = ["MAYBE"]
    with pytest.raises(AssessmentError, match="unknown outcome"):
        score_from_outcomes(outcomes)


def test_outcomes_unknown_domain_raises() -> None:
    with pytest.raises(AssessmentError, match="unknown domains"):
        score_from_outcomes({**{key: ["PASS"] for key in WEIGHTS}, "unknown": ["PASS"]})


def test_to_dict_rounds() -> None:
    result = score_from_ratios(_all(0.777)).to_dict()
    assert isinstance(result["total"], float)
    assert isinstance(result["breakdown"], dict)
