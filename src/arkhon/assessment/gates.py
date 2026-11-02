"""Aggregate rule outcomes into non-downgradable gate verdicts."""
from __future__ import annotations

from dataclasses import dataclass, field

from arkhon.core.constants import (
    ENFORCEMENT_BLOCKING, ENFORCEMENT_CRITICAL, ENFORCEMENT_REQUIRED,
    STATUS_BLOCKED, STATUS_FAIL, STATUS_NOT_APPLICABLE, STATUS_PASS,
)
from arkhon.core.errors import GateError

GATE_DOMAINS: dict[str, tuple[str, ...]] = {
    "requirements_gate": ("requirements",),
    "architecture_gate": ("architecture",),
    "implementation_gate": ("code-quality", "devops", "infrastructure"),
    "testing_gate": ("testing",),
    "security_gate": ("software-security",),
    "performance_gate": ("performance",),
    "reliability_gate": ("reliability",),
    "release_gate": (
        "release", "maintenance", "api-integration", "database",
        "observability", "privacy-compliance", "scalability",
    ),
}


@dataclass(frozen=True)
class RuleOutcome:
    rule_id: str
    enforcement: str
    status: str
    reason: str = ""


@dataclass
class GateVerdict:
    gate: str
    status: str
    outcomes: list[RuleOutcome] = field(default_factory=list)
    blocking_failures: int = 0
    critical_failures: int = 0
    reason: str = ""

    def __post_init__(self) -> None:
        if self.status not in {STATUS_PASS, STATUS_FAIL, STATUS_BLOCKED}:
            raise GateError(f"invalid gate status: {self.status}")

    @property
    def closes(self) -> bool:
        return self.status == STATUS_PASS

    def to_dict(self) -> dict[str, object]:
        return {
            "gate": self.gate, "status": self.status,
            "blocking_failures": self.blocking_failures,
            "critical_failures": self.critical_failures, "reason": self.reason,
        }


def evaluate_gate(gate: str, outcomes: list[RuleOutcome]) -> GateVerdict:
    if gate not in GATE_DOMAINS:
        raise GateError(f"unknown gate: {gate}")
    critical = 0
    blocking = 0
    reasons: list[str] = []
    for outcome in outcomes:
        if outcome.status in {STATUS_PASS, STATUS_NOT_APPLICABLE}:
            continue
        if outcome.status not in {STATUS_FAIL, STATUS_BLOCKED}:
            raise GateError(f"{outcome.rule_id}: unsupported outcome status {outcome.status!r}")
        if outcome.enforcement == ENFORCEMENT_CRITICAL:
            critical += 1
            reasons.append(f"{outcome.rule_id}: critical {outcome.status.lower()}")
        elif outcome.enforcement in {ENFORCEMENT_BLOCKING, ENFORCEMENT_REQUIRED}:
            blocking += 1
            reasons.append(f"{outcome.rule_id}: {outcome.status.lower()}")
    status = STATUS_FAIL if critical else STATUS_BLOCKED if blocking else STATUS_PASS
    return GateVerdict(
        gate=gate, status=status, outcomes=list(outcomes),
        blocking_failures=blocking, critical_failures=critical,
        reason="; ".join(reasons) if reasons else "",
    )


def evaluate_all_gates(
    outcomes_per_domain: dict[str, list[RuleOutcome]],
) -> dict[str, GateVerdict]:
    unknown = set(outcomes_per_domain) - {
        domain for domains in GATE_DOMAINS.values() for domain in domains
    }
    if unknown:
        raise GateError(f"unknown outcome domains: {sorted(unknown)}")
    return {
        gate: evaluate_gate(
            gate, [item for domain in domains for item in outcomes_per_domain.get(domain, [])]
        )
        for gate, domains in GATE_DOMAINS.items()
    }
