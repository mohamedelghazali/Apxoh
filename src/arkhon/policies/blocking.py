"""Blocking policy evaluation.

Blocking policies are the hard stops. If any blocking policy is violated,
the release cannot proceed without a documented exception.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from arkhon.core.errors import GovernanceError
from arkhon.core.logging import get_logger
from arkhon.governance.policy_loader import Policy, PolicyRegistry

logger = get_logger("policies.blocking")


@dataclass(frozen=True)
class BlockingViolation:
    policy_id: str
    rule_id: str
    reason: str
    blocking: bool = True


@dataclass
class BlockingResult:
    violations: list[BlockingViolation] = field(default_factory=list)

    @property
    def blocks(self) -> bool:
        return any(v.blocking for v in self.violations)

    @property
    def count(self) -> int:
        return len(self.violations)


class BlockingPolicyEvaluator:
    """Evaluates blocking policies against a project state."""

    def __init__(self, registry: PolicyRegistry) -> None:
        self._registry = registry

    def policies(self) -> list[Policy]:
        return [p for p in self._registry.all() if p.category == "blocking" and p.enabled]

    def evaluate(
        self,
        *,
        failing_rules: set[str],
        project_root: Path,
    ) -> BlockingResult:
        """Evaluate all blocking policies against the failing rules."""
        result = BlockingResult()

        for policy in self.policies():
            trigger_rules = policy.raw.get("trigger_rules", [])
            if not isinstance(trigger_rules, list):
                continue

            for rule_id in trigger_rules:
                if rule_id in failing_rules:
                    result.violations.append(BlockingViolation(
                        policy_id=policy.id,
                        rule_id=rule_id,
                        reason=str(policy.raw.get("reason", f"policy {policy.id} triggered")),
                    ))

            # Optional: path-based triggers
            paths = policy.raw.get("trigger_paths", [])
            if isinstance(paths, list):
                for pattern in paths:
                    matches = list(project_root.glob(pattern))
                    if matches:
                        result.violations.append(BlockingViolation(
                            policy_id=policy.id,
                            rule_id=f"path:{pattern}",
                            reason=str(policy.raw.get("reason", f"path {pattern} matched")),
                        ))

        if result.violations:
            logger.warning("blocking evaluation found %d violation(s)", result.count)

        return result


def ensure_no_bypass(result: BlockingResult) -> None:
    """Raise if any blocking violation is present. Used by the release gate."""
    if result.blocks:
        ids = ", ".join(v.policy_id for v in result.violations)
        raise GovernanceError(f"blocking policies violated: {ids}")
