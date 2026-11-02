"""Deterministic engineering score calculator."""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Mapping

from arkhon.core.errors import AssessmentError

WEIGHTS: dict[str, int] = {
    "requirements": 15,
    "architecture_and_code_quality": 10,
    "testing": 15,
    "security": 20,
    "performance": 10,
    "reliability": 10,
    "scalability": 10,
    "documentation_deployment_maintenance": 10,
}
TOTAL_WEIGHT = sum(WEIGHTS.values())
if TOTAL_WEIGHT != 100:
    raise RuntimeError("assessment weights must sum to 100")

LEVEL_THRESHOLDS: tuple[tuple[float, str], ...] = (
    (95.0, "hyperscale-validated"),
    (90.0, "enterprise-grade"),
    (80.0, "production-ready"),
    (70.0, "controlled-release"),
    (0.0, "development"),
)


@dataclass(frozen=True)
class ScoreBreakdown:
    domain: str
    awarded: float
    maximum: float

    def __post_init__(self) -> None:
        if not math.isfinite(self.awarded) or not math.isfinite(self.maximum):
            raise AssessmentError(f"{self.domain}: score values must be finite")
        if self.maximum < 0 or self.awarded < 0 or self.awarded > self.maximum:
            raise AssessmentError(
                f"{self.domain}: awarded={self.awarded} not in [0, {self.maximum}]"
            )


@dataclass(frozen=True)
class Score:
    total: float
    maximum: float
    breakdown: dict[str, ScoreBreakdown] = field(default_factory=dict)

    @property
    def level(self) -> str:
        for threshold, label in LEVEL_THRESHOLDS:
            if self.total >= threshold:
                return label
        return "development"

    def to_dict(self) -> dict[str, object]:
        return {
            "total": round(self.total, 2),
            "max": self.maximum,
            "breakdown": {key: round(value.awarded, 2) for key, value in self.breakdown.items()},
        }


def _validate_inputs(ratios: Mapping[str, float]) -> None:
    missing = set(WEIGHTS) - set(ratios)
    if missing:
        raise AssessmentError(f"missing domains: {sorted(missing)}")
    extra = set(ratios) - set(WEIGHTS)
    if extra:
        raise AssessmentError(f"unknown domains: {sorted(extra)}")
    for domain, ratio in ratios.items():
        try:
            numeric = float(ratio)
        except (TypeError, ValueError) as exc:
            raise AssessmentError(f"{domain}: ratio must be numeric") from exc
        if not math.isfinite(numeric) or not 0.0 <= numeric <= 1.0:
            raise AssessmentError(f"{domain}: ratio {ratio} must be finite and in [0.0, 1.0]")


def score_from_ratios(ratios: Mapping[str, float]) -> Score:
    """Map per-domain earned fractions to a weighted score."""
    _validate_inputs(ratios)
    breakdown: dict[str, ScoreBreakdown] = {}
    total = 0.0
    for domain, weight in WEIGHTS.items():
        awarded = float(ratios[domain]) * weight
        total += awarded
        breakdown[domain] = ScoreBreakdown(domain, awarded, float(weight))
    return Score(total=total, maximum=float(TOTAL_WEIGHT), breakdown=breakdown)


def score_from_outcomes(outcomes_per_domain: Mapping[str, list[str]]) -> Score:
    """Score rule outcomes: PASS=1, ACCEPTED_RISK=.5, N/A=1, FAIL/BLOCKED=0."""
    values = {
        "PASS": 1.0, "ACCEPTED_RISK": 0.5, "NOT_APPLICABLE": 1.0,
        "FAIL": 0.0, "BLOCKED": 0.0,
    }
    unknown_domains = set(outcomes_per_domain) - set(WEIGHTS)
    if unknown_domains:
        raise AssessmentError(f"unknown domains: {sorted(unknown_domains)}")
    ratios: dict[str, float] = {}
    for domain in WEIGHTS:
        items = outcomes_per_domain.get(domain, [])
        if not items:
            ratios[domain] = 0.0
            continue
        for outcome in items:
            if outcome not in values:
                raise AssessmentError(f"unknown outcome: {outcome}")
        ratios[domain] = sum(values[item] for item in items) / len(items)
    return score_from_ratios(ratios)
