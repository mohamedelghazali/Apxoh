"""Tests for the explicit verification method inventory."""

from __future__ import annotations

import pytest

from arkhon.verification.methods import METHOD_REGISTRY, resolve_method, resolve_methods


def test_registry_contains_only_explicit_implementations() -> None:
    assert resolve_method("type-checker-execution") == METHOD_REGISTRY["type-checker-execution"]
    assert resolve_method("zero-type-errors-check").runner == "mypy"
    assert resolve_method("tsar-audit-invocation").runner == "tsar"
    assert resolve_method("evidence-integrity-check").component == "verify_tsar_evidence"
    assert resolve_method("evidence-commit-match").component == "verify_tsar_evidence"
    assert resolve_method("evidence-freshness-check").component == "verify_tsar_evidence"
    assert resolve_method("timestamp-verification").component == "verify_tsar_evidence"


def test_unknown_method_is_not_claimed_as_implemented() -> None:
    assert resolve_method("load-test-execution") is None


@pytest.mark.parametrize("value", ["", None])
def test_resolve_method_rejects_invalid_identifier(value: object) -> None:
    with pytest.raises(ValueError, match="non-empty string"):
        resolve_method(value)  # type: ignore[arg-type]


def test_resolve_methods_preserves_supported_and_unsupported_methods() -> None:
    result = resolve_methods(["type-checker-execution", "api-contract-analysis"])
    assert result[0][1] is not None
    assert result[1] == ("api-contract-analysis", None)


@pytest.mark.parametrize(
    ("value", "message"),
    [
        (None, "must be a list"),
        (["valid", ""], "non-empty strings"),
        (["valid", 3], "non-empty strings"),
        (["valid", "valid"], "must not contain duplicates"),
    ],
)
def test_resolve_methods_rejects_malformed_lists(value: object, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        resolve_methods(value)
