"""Exception hierarchy for Apxoh.

Every error carries a stable code so downstream consumers (CI, agents,
report generators) can branch on it without parsing messages.
"""
from __future__ import annotations


class ArkhonError(Exception):
    """Base exception for all Apxoh errors."""
    default_code: str = "ARKHON_ERROR"

    def __init__(self, message: str, *, code: str | None = None) -> None:
        super().__init__(message)
        self.code = code or self.default_code


class ConfigError(ArkhonError):
    """Configuration is missing or invalid."""
    default_code = "CONFIG_ERROR"


class ManifestError(ConfigError):
    """Manifest file is missing, invalid, or inconsistent."""
    default_code = "MANIFEST_ERROR"


class GovernanceError(ArkhonError):
    """A governance rule or policy was violated."""
    default_code = "GOVERNANCE_ERROR"


class AssessmentError(ArkhonError):
    """An engineering assessment could not be computed."""
    default_code = "ASSESSMENT_ERROR"


class RuleError(ArkhonError):
    """A rule is invalid or cannot be processed."""
    default_code = "RULE_ERROR"


class RuleNotFoundError(RuleError):
    default_code = "RULE_NOT_FOUND"


class RuleValidationError(RuleError):
    default_code = "RULE_VALIDATION_ERROR"


class RuleDuplicateError(RuleError):
    default_code = "RULE_DUPLICATE"


class EvidenceError(ArkhonError):
    """Evidence is missing, stale, or invalid."""
    default_code = "EVIDENCE_ERROR"


class EvidenceMissingError(EvidenceError):
    default_code = "EVIDENCE_MISSING"


class EvidenceStaleError(EvidenceError):
    default_code = "EVIDENCE_STALE"


class EvidenceTamperedError(EvidenceError):
    default_code = "EVIDENCE_TAMPERED"


class EvidenceSignatureError(EvidenceError):
    default_code = "EVIDENCE_SIGNATURE_INVALID"


class VerificationError(ArkhonError):
    """Verification failed."""
    default_code = "VERIFICATION_ERROR"


class VerificationBlockedError(VerificationError):
    default_code = "VERIFICATION_BLOCKED"


class SecurityError(ArkhonError):
    """A security-critical error occurred."""
    default_code = "SECURITY_ERROR"


class GateError(ArkhonError):
    """A release gate could not be evaluated or blocked."""
    default_code = "GATE_ERROR"


class ReleaseBlockedError(GateError):
    default_code = "RELEASE_BLOCKED"
