"""Tests for the Apxoh error hierarchy."""
from __future__ import annotations

import pytest

from arkhon.core.errors import (
    ArkhonError,
    ConfigError,
    EvidenceError,
    EvidenceMissingError,
    EvidenceSignatureError,
    EvidenceStaleError,
    EvidenceTamperedError,
    GateError,
    GovernanceError,
    ManifestError,
    ReleaseBlockedError,
    RuleDuplicateError,
    RuleError,
    RuleNotFoundError,
    RuleValidationError,
    SecurityError,
    VerificationBlockedError,
    VerificationError,
)


def test_base_error_is_exception() -> None:
    assert issubclass(ArkhonError, Exception)


def test_base_error_default_code() -> None:
    error = ArkhonError("boom")
    assert error.code == "ARKHON_ERROR"
    assert str(error) == "boom"


def test_base_error_custom_code() -> None:
    assert ArkhonError("boom", code="CUSTOM").code == "CUSTOM"


@pytest.mark.parametrize(
    ("error_type", "parent", "code"),
    [
        (ConfigError, ArkhonError, "CONFIG_ERROR"),
        (ManifestError, ConfigError, "MANIFEST_ERROR"),
        (GovernanceError, ArkhonError, "GOVERNANCE_ERROR"),
        (RuleError, ArkhonError, "RULE_ERROR"),
        (RuleNotFoundError, RuleError, "RULE_NOT_FOUND"),
        (RuleValidationError, RuleError, "RULE_VALIDATION_ERROR"),
        (RuleDuplicateError, RuleError, "RULE_DUPLICATE"),
        (EvidenceError, ArkhonError, "EVIDENCE_ERROR"),
        (EvidenceMissingError, EvidenceError, "EVIDENCE_MISSING"),
        (EvidenceStaleError, EvidenceError, "EVIDENCE_STALE"),
        (EvidenceTamperedError, EvidenceError, "EVIDENCE_TAMPERED"),
        (EvidenceSignatureError, EvidenceError, "EVIDENCE_SIGNATURE_INVALID"),
        (VerificationError, ArkhonError, "VERIFICATION_ERROR"),
        (VerificationBlockedError, VerificationError, "VERIFICATION_BLOCKED"),
        (SecurityError, ArkhonError, "SECURITY_ERROR"),
        (GateError, ArkhonError, "GATE_ERROR"),
        (ReleaseBlockedError, GateError, "RELEASE_BLOCKED"),
    ],
)
def test_error_hierarchy_and_codes(
    error_type: type[ArkhonError], parent: type[ArkhonError], code: str
) -> None:
    assert issubclass(error_type, parent)
    assert error_type.default_code == code
    assert error_type("boom").code == code


def test_error_can_be_caught_by_base_class() -> None:
    with pytest.raises(ArkhonError):
        raise ManifestError("invalid manifest")
