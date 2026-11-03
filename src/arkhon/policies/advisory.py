"""Advisory policy evaluation.

Advisory policies are recommendations. They do not block a release, but
they are recorded and visible in the report.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from arkhon.core.logging import get_logger
from arkhon.governance.policy_loader import Policy, PolicyRegistry

logger = get_logger("policies.advisory")


@dataclass(frozen=True)
class AdvisoryNote:
    policy_id: str
    rule_id: str
    message: str


@dataclass
class AdvisoryResult:
    notes: list[AdvisoryNote] = field(default_factory=list)

    @property
    def count(self) -> int:
        return len(self.notes)


class AdvisoryPolicyEvaluator:
    """Evaluates advisory policies."""

    def __init__(self, registry: PolicyRegistry) -> None:
        self._registry = registry

    def policies(self) -> list[Policy]:
        return [p for p in self._registry.all() if p.category == "advisory" and p.enabled]

    def evaluate(
        self,
        *,
        failing_rules: set[str],
        project_root: Path,
    ) -> AdvisoryResult:
        result = AdvisoryResult()
        for policy in self.policies():
            trigger_rules = policy.raw.get("trigger_rules", [])
            if not isinstance(trigger_rules, list):
                continue
            for rule_id in trigger_rules:
                if rule_id in failing_rules:
                    result.notes.append(
                        AdvisoryNote(
                            policy_id=policy.id,
                            rule_id=rule_id,
                            message=str(policy.raw.get("message", f"see {policy.id}")),
                        )
                    )
        return result
