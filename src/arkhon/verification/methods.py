"""Explicit inventory of rule verification methods backed by real implementations.

A method being registered means an implementation exists; it does not mean a
rule has passed. Rule-level outcomes still require validated, commit-bound
evidence and any required human approval.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType


@dataclass(frozen=True)
class MethodImplementation:
    """Implementation component that can execute or validate one method."""

    method_id: str
    component: str
    runner: str
    allowed_domains: frozenset[str] = frozenset()


METHOD_REGISTRY: Mapping[str, MethodImplementation] = MappingProxyType(
    {
        "type-checker-execution": MethodImplementation(
            "type-checker-execution", "MypyRunner", "mypy", frozenset({"code-quality"})
        ),
        "zero-type-errors-check": MethodImplementation(
            "zero-type-errors-check", "MypyRunner", "mypy", frozenset({"code-quality"})
        ),
        "static-lint-execution": MethodImplementation(
            "static-lint-execution", "RuffRunner", "ruff", frozenset({"code-quality"})
        ),
        "zero-lint-errors-check": MethodImplementation(
            "zero-lint-errors-check", "RuffRunner", "ruff", frozenset({"code-quality"})
        ),
        "automated-test-suite-execution": MethodImplementation(
            "automated-test-suite-execution",
            "LanguageNeutralTestRunner",
            "test-suite",
            frozenset({"testing"}),
        ),
        "zero-test-failures-check": MethodImplementation(
            "zero-test-failures-check",
            "LanguageNeutralTestRunner",
            "test-suite",
            frozenset({"testing"}),
        ),
        "test-collector-analysis": MethodImplementation(
            "test-collector-analysis",
            "LanguageNeutralTestRunner",
            "test-suite",
            frozenset({"testing"}),
        ),
        "skip-marker-detection": MethodImplementation(
            "skip-marker-detection",
            "LanguageNeutralTestRunner",
            "test-suite",
            frozenset({"testing"}),
        ),
        "negative-security-scenario-traceability": MethodImplementation(
            "negative-security-scenario-traceability",
            "verify_negative_security_scenarios",
            "test-suite",
            frozenset({"testing"}),
        ),
        "observability-behavior-test-verification": MethodImplementation(
            "observability-behavior-test-verification",
            "verify_observability_and_crash_dump_controls",
            "test-suite",
            frozenset({"observability"}),
        ),
        "tsar-audit-invocation": MethodImplementation(
            "tsar-audit-invocation", "TsarRunner", "tsar", frozenset({"software-security"})
        ),
        "evidence-integrity-check": MethodImplementation(
            "evidence-integrity-check",
            "verify_tsar_evidence",
            "tsar",
            frozenset({"software-security"}),
        ),
        "evidence-commit-match": MethodImplementation(
            "evidence-commit-match",
            "verify_tsar_evidence",
            "tsar",
            frozenset({"software-security"}),
        ),
        "evidence-freshness-check": MethodImplementation(
            "evidence-freshness-check",
            "verify_tsar_evidence",
            "tsar",
            frozenset({"software-security"}),
        ),
        "timestamp-verification": MethodImplementation(
            "timestamp-verification",
            "verify_tsar_evidence",
            "tsar",
            frozenset({"software-security"}),
        ),
    }
)


def resolve_method(method_id: str) -> MethodImplementation | None:
    """Return the registered implementation, or None when unsupported."""
    if not isinstance(method_id, str) or not method_id:
        raise ValueError("method_id must be a non-empty string")
    return METHOD_REGISTRY.get(method_id)


def resolve_methods(method_ids: object) -> tuple[tuple[str, MethodImplementation | None], ...]:
    """Resolve a rule's declared method list without silently dropping entries."""
    if not isinstance(method_ids, list):
        raise ValueError("verification.methods must be a list")
    if any(not isinstance(method_id, str) or not method_id for method_id in method_ids):
        raise ValueError("verification.methods must contain non-empty strings")
    if len(set(method_ids)) != len(method_ids):
        raise ValueError("verification.methods must not contain duplicates")
    return tuple((method_id, resolve_method(method_id)) for method_id in method_ids)
