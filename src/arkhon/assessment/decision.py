"""Release decision combining score, gates, and accepted risks."""
from __future__ import annotations

from dataclasses import dataclass, field

from arkhon.assessment.gates import GateVerdict
from arkhon.assessment.scorer import Score
from arkhon.core.constants import STATUS_BLOCKED, STATUS_FAIL
from arkhon.core.errors import AssessmentError

RELEASE_MINIMUM_SCORE = 80.0
CRITICAL_GATES = ("security_gate", "release_gate")


@dataclass(frozen=True)
class Decision:
    decision: str
    reason: str
    score: float
    level: str
    gate_statuses: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, object]:
        return {
            "decision": self.decision, "decision_reason": self.reason,
            "score": self.score, "level": self.level,
            "gates": {key: {"gate": key, "status": value}
                      for key, value in self.gate_statuses.items()},
        }


def decide(
    score: Score, gate_verdicts: dict[str, GateVerdict], accepted_risk_count: int = 0,
) -> Decision:
    if not gate_verdicts:
        raise AssessmentError("no gate verdicts provided")
    if accepted_risk_count < 0:
        raise AssessmentError("accepted_risk_count must be non-negative")
    statuses = {key: value.status for key, value in gate_verdicts.items()}
    for gate in CRITICAL_GATES:
        verdict = gate_verdicts.get(gate)
        if verdict is None:
            return Decision(
                "REJECTED", f"missing critical gate: {gate}", score.total, score.level, statuses,
            )
        if verdict.status == STATUS_FAIL:
            return Decision(
                "REJECTED", f"{gate}: {verdict.reason or 'failed'}",
                score.total, score.level, statuses,
            )
        if verdict.status == STATUS_BLOCKED:
            return Decision(
                "PENDING_EVIDENCE", f"{gate}: {verdict.reason or 'blocked'}",
                score.total, score.level, statuses,
            )
    for gate, verdict in gate_verdicts.items():
        if verdict.status == STATUS_BLOCKED:
            return Decision(
                "PENDING_EVIDENCE", f"{gate}: {verdict.reason or 'blocked'}",
                score.total, score.level, statuses,
            )
        if verdict.status == STATUS_FAIL:
            return Decision(
                "REJECTED", f"{gate}: {verdict.reason or 'failed'}",
                score.total, score.level, statuses,
            )
    if score.total < RELEASE_MINIMUM_SCORE:
        return Decision(
            "REJECTED",
            f"score {score.total:.1f} below release minimum {RELEASE_MINIMUM_SCORE}",
            score.total, score.level, statuses,
        )
    if accepted_risk_count:
        return Decision(
            "APPROVED_WITH_CONDITIONS",
            f"{accepted_risk_count} accepted risk(s) carried forward",
            score.total, score.level, statuses,
        )
    return Decision("APPROVED", "all gates pass, score above threshold",
                    score.total, score.level, statuses)
