"""Deterministic & hybrid rule evaluation engine with attestation and exception integration."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from gencode_gov.core.constants import (
    STATUS_ACCEPTED_RISK,
    STATUS_BLOCKED,
    STATUS_FAIL,
    STATUS_PASS,
)
from gencode_gov.evidence.attestation import verify_human_attestation
from gencode_gov.policies.exceptions import load_exceptions
from gencode_gov.verification.assess_dispatch import (
    create_assess_runner,
    evaluate_extended_method,
)
from gencode_gov.verification.methods import resolve_methods
from gencode_gov.verification.runners.base import Runner, RunnerOutcome, RunnerResult


@dataclass(frozen=True)
class EvaluatedMethod:
    """Verification outcome of a single method declared by a rule."""

    method_id: str
    status: str
    reason: str


@dataclass(frozen=True)
class EvaluatedRule:
    """Complete governance outcome for a single rule."""

    rule_id: str
    domain: str
    enforcement: str
    status: str
    reason: str
    methods: tuple[EvaluatedMethod, ...]
    exception_id: str | None = None


class RuleEvaluator:
    """Evaluate loaded Rule objects deterministically with fail-closed semantics."""

    def __init__(
        self,
        project_root: Path,
        *,
        commit_sha: str | None = None,
        working_tree_clean: bool = True,
        runner_overrides: dict[str, Runner] | None = None,
    ) -> None:
        self.project_root = project_root.resolve()
        self.commit_sha = commit_sha
        self.working_tree_clean = working_tree_clean
        self._runner_overrides = dict(runner_overrides or {})
        self._runner_cache: dict[str, RunnerResult] = {}
        self._active_exceptions = self._load_active_exceptions()

    def _load_active_exceptions(self) -> dict[str, str]:
        candidates = [
            self.project_root / ".gencode-gov" / "exceptions.yaml",
            self.project_root / "system" / "policies" / "exceptions" / "registry.yaml",
        ]
        mapping: dict[str, str] = {}
        for path in candidates:
            if path.is_file() and not path.is_symlink():
                try:
                    reg = load_exceptions(path)
                    for exc in reg.exceptions:
                        if exc.is_active():
                            mapping[exc.rule_id] = exc.exception_id
                except (OSError, ValueError, KeyError) as err:  # pragma: no cover
                    _ = err
        return mapping

    def _get_runner_result(self, runner_name: str) -> RunnerResult:
        if runner_name in self._runner_cache:
            return self._runner_cache[runner_name]
        if not self.working_tree_clean:
            res = RunnerResult(
                runner=runner_name,
                outcome=RunnerOutcome.BLOCKED,
                reason="working tree is dirty; evidence cannot be bound to HEAD",
            )
            self._runner_cache[runner_name] = res
            return res

        runner = self._runner_overrides.get(runner_name) or create_assess_runner(runner_name)
        if runner is None:
            res = RunnerResult(
                runner=runner_name,
                outcome=RunnerOutcome.BLOCKED,
                reason=f"no deterministic runner available for {runner_name!r}",
            )
        else:
            res = runner.run(self.project_root)
        self._runner_cache[runner_name] = res
        return res

    def evaluate_rule(self, rule: Any) -> EvaluatedRule:
        """Evaluate all verification methods, human review requirements, and exceptions."""
        raw = getattr(rule, "raw", {})
        meta = raw.get("metadata", {}) if isinstance(raw, dict) else {}
        domain = str(meta.get("domain", getattr(rule, "domain", "unknown")))
        enforcement = str(meta.get("enforcement", getattr(rule, "enforcement", "blocking")))
        verif = raw.get("verification", {}) if isinstance(raw, dict) else {}
        raw_methods = verif.get("methods", []) if isinstance(verif, dict) else []

        resolved = resolve_methods(list(raw_methods))
        method_outcomes: list[EvaluatedMethod] = []

        for method_id, impl in resolved:
            if impl is None:
                method_outcomes.append(
                    EvaluatedMethod(
                        method_id,
                        STATUS_BLOCKED,
                        f"unregistered verification method: {method_id}",
                    )
                )
                continue
            if impl.allowed_domains and domain not in impl.allowed_domains:
                method_outcomes.append(
                    EvaluatedMethod(
                        method_id,
                        STATUS_BLOCKED,
                        f"method {method_id} not permitted for domain {domain}",
                    )
                )
                continue

            r_res = self._get_runner_result(impl.runner)
            ext = evaluate_extended_method(
                method_id,
                r_res,
                self.project_root,
                rule=rule,
                commit_sha=self.commit_sha,
            )
            if ext is not None:
                m_status, m_reason = ext
            elif r_res.outcome == RunnerOutcome.PASS:
                m_status, m_reason = STATUS_PASS, r_res.reason or f"{impl.runner} passed"
            elif r_res.outcome == RunnerOutcome.FAIL:
                m_status, m_reason = STATUS_FAIL, r_res.reason or f"{impl.runner} failed"
            else:
                m_status, m_reason = STATUS_BLOCKED, r_res.reason or f"{impl.runner} blocked"
            method_outcomes.append(EvaluatedMethod(method_id, m_status, m_reason))

        human_cfg = raw.get("human_review", {}) if isinstance(raw, dict) else {}
        if isinstance(human_cfg, dict) and human_cfg.get("required") is True:
            already_checked = any(
                m.method_id in {"human-review", "human-security-review", "human-approval"}
                for m in method_outcomes
            )
            if not already_checked:
                role = human_cfg.get("approver_role")
                h_status, h_reason = verify_human_attestation(
                    self.project_root,
                    rule_id=rule.id,
                    expected_commit_sha=self.commit_sha,
                    required_role=str(role) if isinstance(role, str) and role.strip() else None,
                )
                method_outcomes.append(EvaluatedMethod("human-review-gate", h_status, h_reason))

        statuses = [m.status for m in method_outcomes]
        if not statuses or STATUS_FAIL in statuses:
            failed_msgs = [
                f"{m.method_id}: {m.reason}" for m in method_outcomes if m.status == STATUS_FAIL
            ]
            final_status = STATUS_FAIL
            final_reason = "; ".join(failed_msgs) if failed_msgs else "rule declared no methods"
        elif STATUS_BLOCKED in statuses:
            blocked_msgs = [
                f"{m.method_id}: {m.reason}" for m in method_outcomes if m.status == STATUS_BLOCKED
            ]
            final_status = STATUS_BLOCKED
            final_reason = "; ".join(blocked_msgs)
        else:
            final_status = STATUS_PASS
            final_reason = f"all {len(method_outcomes)} verification method(s) passed"

        exc_id = self._active_exceptions.get(rule.id)
        if (
            final_status in {STATUS_FAIL, STATUS_BLOCKED}
            and exc_id is not None
            and enforcement != "critical"
        ):
            return EvaluatedRule(
                rule_id=rule.id,
                domain=domain,
                enforcement=enforcement,
                status=STATUS_ACCEPTED_RISK,
                reason=f"accepted risk under active exception {exc_id} ({final_reason})",
                methods=tuple(method_outcomes),
                exception_id=exc_id,
            )

        return EvaluatedRule(
            rule_id=rule.id,
            domain=domain,
            enforcement=enforcement,
            status=final_status,
            reason=final_reason,
            methods=tuple(method_outcomes),
        )

    def evaluate_all(self, rules: list[Any] | tuple[Any, ...]) -> tuple[EvaluatedRule, ...]:
        return tuple(self.evaluate_rule(r) for r in rules)


__all__ = ["RuleEvaluator"]
