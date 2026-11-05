"""Deterministic evidence-presence checks and gate aggregation.

This module does not execute scanners or infer that evidence is trustworthy.
Presence is only a preliminary check; delegated verification must validate
content, provenance, integrity, freshness, and target binding separately.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from arkhon.core.constants import (
    ENFORCEMENT_BLOCKING,
    ENFORCEMENT_CRITICAL,
    ENFORCEMENT_REQUIRED,
    SEVERITY_CRITICAL,
    SEVERITY_HIGH,
    STATUS_BLOCKED,
    STATUS_FAIL,
    STATUS_NOT_APPLICABLE,
    STATUS_PASS,
)
from arkhon.core.errors import GovernanceError
from arkhon.core.logging import get_logger
from arkhon.rules.loader import Rule
from arkhon.rules.registry import RuleRegistry

logger = get_logger("governance.enforcement")


@dataclass(frozen=True)
class RuleOutcome:
    rule_id: str
    status: str
    reason: str = ""
    evidence_present: bool = False

    def __post_init__(self) -> None:
        if self.status not in {STATUS_PASS, STATUS_FAIL, STATUS_BLOCKED, STATUS_NOT_APPLICABLE}:
            raise GovernanceError(f"invalid outcome status: {self.status}")


@dataclass
class GateVerdict:
    gate: str
    status: str
    outcomes: list[RuleOutcome] = field(default_factory=list)
    blocking_failures: int = 0
    critical_failures: int = 0

    @property
    def closes(self) -> bool:
        return (
            self.status == STATUS_PASS and not self.blocking_failures and not self.critical_failures
        )


class EnforcementEngine:
    """Evaluate whether declared evidence artifacts are present."""

    def __init__(self, registry: RuleRegistry) -> None:
        self._registry = registry

    def evaluate_rule(self, rule: Rule, evidence_root: Path | None) -> RuleOutcome:
        """Check artifact presence without treating it as semantic verification."""
        evidence = rule.raw.get("evidence", {})
        if not isinstance(evidence, dict):
            return RuleOutcome(rule.id, STATUS_BLOCKED, "invalid evidence declaration")
        required = evidence.get("required", [])
        if not isinstance(required, list):
            return RuleOutcome(rule.id, STATUS_BLOCKED, "evidence.required must be a list")
        if not required:
            return RuleOutcome(
                rule.id,
                STATUS_BLOCKED,
                "no evidence artifacts declared; independent rule verification is unavailable",
            )
        if evidence_root is None or not evidence_root.is_dir():
            return RuleOutcome(rule.id, STATUS_BLOCKED, "evidence root missing")

        missing: list[str] = []
        root = evidence_root.resolve()
        for item in required:
            if isinstance(item, str) and item:
                candidate = (root / item).resolve()
                if root not in candidate.parents and candidate != root:
                    return RuleOutcome(
                        rule.id, STATUS_BLOCKED, "evidence path escapes evidence root"
                    )
                if not candidate.exists() or not candidate.is_file():
                    missing.append(item)
            elif isinstance(item, dict):
                kind = item.get("type")
                if not isinstance(kind, str) or not kind:
                    missing.append("<invalid evidence type>")
                elif not any(p.is_file() for p in root.glob(f"**/{kind}*")):
                    missing.append(kind)
            else:
                missing.append("<invalid evidence declaration>")
        if missing:
            return RuleOutcome(rule.id, STATUS_BLOCKED, f"missing evidence: {', '.join(missing)}")
        return RuleOutcome(
            rule.id,
            STATUS_BLOCKED,
            "evidence artifacts are present but have not been independently verified",
            True,
        )

    def evaluate_gate(
        self, gate_name: str, domain_filter: tuple[str, ...], evidence_root: Path | None
    ) -> GateVerdict:
        outcomes: list[RuleOutcome] = []
        blocking = critical = 0
        for domain in domain_filter:
            for rule in self._registry.by_domain(domain):
                if rule.status != "active":
                    continue
                outcome = self.evaluate_rule(rule, evidence_root)
                outcomes.append(outcome)
                if outcome.status not in {STATUS_FAIL, STATUS_BLOCKED}:
                    continue
                if rule.enforcement == ENFORCEMENT_CRITICAL:
                    critical += 1
                elif rule.enforcement in {ENFORCEMENT_BLOCKING, ENFORCEMENT_REQUIRED}:
                    blocking += 1
                if rule.severity in {SEVERITY_CRITICAL, SEVERITY_HIGH}:
                    critical += 1

        status = STATUS_FAIL if critical else STATUS_BLOCKED if blocking else STATUS_PASS
        return GateVerdict(gate_name, status, outcomes, blocking, critical)
