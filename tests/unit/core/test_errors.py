"""Tests for the GENCODE-GOV error hierarchy."""

from __future__ import annotations

import pytest

from gencode_gov.core.errors import (
    ConfigError,
    EvidenceError,
    EvidenceMissingError,
    EvidenceSignatureError,
    EvidenceStaleError,
    EvidenceTamperedError,
    GateError,
    GencodeGovError,
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
    assert issubclass(GencodeGovError, Exception)


def test_base_error_default_code() -> None:
    error = GencodeGovError("boom")
    assert error.code == "GENCODE_GOV_ERROR"
    assert str(error) == "boom"


def test_base_error_custom_code() -> None:
    assert GencodeGovError("boom", code="CUSTOM").code == "CUSTOM"


@pytest.mark.parametrize(
    ("error_type", "parent", "code"),
    [
        (ConfigError, GencodeGovError, "CONFIG_ERROR"),
        (ManifestError, ConfigError, "MANIFEST_ERROR"),
        (GovernanceError, GencodeGovError, "GOVERNANCE_ERROR"),
        (RuleError, GencodeGovError, "RULE_ERROR"),
        (RuleNotFoundError, RuleError, "RULE_NOT_FOUND"),
        (RuleValidationError, RuleError, "RULE_VALIDATION_ERROR"),
        (RuleDuplicateError, RuleError, "RULE_DUPLICATE"),
        (EvidenceError, GencodeGovError, "EVIDENCE_ERROR"),
        (EvidenceMissingError, EvidenceError, "EVIDENCE_MISSING"),
        (EvidenceStaleError, EvidenceError, "EVIDENCE_STALE"),
        (EvidenceTamperedError, EvidenceError, "EVIDENCE_TAMPERED"),
        (EvidenceSignatureError, EvidenceError, "EVIDENCE_SIGNATURE_INVALID"),
        (VerificationError, GencodeGovError, "VERIFICATION_ERROR"),
        (VerificationBlockedError, VerificationError, "VERIFICATION_BLOCKED"),
        (SecurityError, GencodeGovError, "SECURITY_ERROR"),
        (GateError, GencodeGovError, "GATE_ERROR"),
        (ReleaseBlockedError, GateError, "RELEASE_BLOCKED"),
    ],
)
def test_error_hierarchy_and_codes(
    error_type: type[GencodeGovError], parent: type[GencodeGovError], code: str
) -> None:
    assert issubclass(error_type, parent)
    assert error_type.default_code == code
    assert error_type("boom").code == code


def test_error_can_be_caught_by_base_class() -> None:
    with pytest.raises(GencodeGovError):
        raise ManifestError("invalid manifest")
