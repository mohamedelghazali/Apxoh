"""Explicit inventory of rule verification methods backed by real implementations.

A method being registered means an implementation exists; it does not mean a
rule has passed. Rule-level outcomes still require validated, commit-bound
evidence and any required human approval.
"""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping


@dataclass(frozen=True)
class MethodImplementation:
    """Implementation component that can execute or validate one method."""

    method_id: str
    component: str
    runner: str


METHOD_REGISTRY: Mapping[str, MethodImplementation] = MappingProxyType(
    {
        "type-checker-execution": MethodImplementation(
            "type-checker-execution", "MypyRunner", "mypy"
        ),
        "zero-type-errors-check": MethodImplementation(
            "zero-type-errors-check", "MypyRunner", "mypy"
        ),
        "tsar-audit-invocation": MethodImplementation(
            "tsar-audit-invocation", "TsarRunner", "tsar"
        ),
        "evidence-integrity-check": MethodImplementation(
            "evidence-integrity-check", "verify_tsar_evidence", "tsar"
        ),
        "evidence-commit-match": MethodImplementation(
            "evidence-commit-match", "verify_tsar_evidence", "tsar"
        ),
        "evidence-freshness-check": MethodImplementation(
            "evidence-freshness-check", "verify_tsar_evidence", "tsar"
        ),
        "timestamp-verification": MethodImplementation(
            "timestamp-verification", "verify_tsar_evidence", "tsar"
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
