"""Validate TSAR evidence against Apxoh's trust contract.

No TSAR status is trusted until commit, version, timestamp, required rules,
artifact paths, and SHA-256 digests have been checked.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from arkhon.core.errors import EvidenceStaleError, EvidenceTamperedError, SecurityError
from arkhon.core.logging import get_logger
from arkhon.evidence.integrity import sha256_of

logger = get_logger("integrations.tsar.verifier")

REQUIRED_RULE_IDS = (
    "TSAR-SEC-SECRET-001",
    "TSAR-SEC-CRYPTO-001",
    "TSAR-SEC-DEP-001",
    "TSAR-SEC-ASVS-V2",
)
FRESHNESS_HOURS = 168
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")
_SEMVER_RE = re.compile(r"(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:[-+][0-9A-Za-z.-]+)?")


@dataclass(frozen=True)
class TsarEvidence:
    evidence_id: str
    tsar_version: str
    commit_sha: str
    executed_at: str
    status: str
    rule_ids: tuple[str, ...]
    summary: dict[str, int]
    artifacts: tuple[tuple[str, str], ...]


def _parse_tsar_payload(payload: dict[str, Any]) -> TsarEvidence:
    if not isinstance(payload, dict):
        raise SecurityError("TSAR payload must be an object")
    required = (
        "evidence_id",
        "tsar_version",
        "commit_sha",
        "executed_at",
        "status",
        "rule_ids",
        "summary",
        "artifacts",
    )
    missing = [key for key in required if key not in payload]
    if missing:
        raise SecurityError(f"TSAR payload missing fields: {missing}")
    identity_fields = (
        "evidence_id",
        "tsar_version",
        "commit_sha",
        "executed_at",
        "status",
    )
    if not all(isinstance(payload[key], str) and payload[key] for key in identity_fields):
        raise SecurityError("TSAR evidence identity and status fields must be non-empty strings")
    if not isinstance(payload["rule_ids"], list) or not all(
        isinstance(item, str) and item for item in payload["rule_ids"]
    ):
        raise SecurityError("TSAR rule_ids must be a list of non-empty strings")
    summary_raw = payload["summary"]
    if not isinstance(summary_raw, dict):
        raise SecurityError("TSAR summary must be an object")
    summary: dict[str, int] = {}
    for key, value in summary_raw.items():
        if (
            not isinstance(key, str)
            or isinstance(value, bool)
            or not isinstance(value, int)
            or value < 0
        ):
            raise SecurityError("TSAR summary counts must be non-negative integers")
        summary[key] = value
    artifacts_raw = payload["artifacts"]
    if not isinstance(artifacts_raw, list) or not artifacts_raw:
        raise SecurityError("TSAR evidence must contain artifacts")
    artifacts: list[tuple[str, str]] = []
    for item in artifacts_raw:
        if not isinstance(item, dict):
            raise SecurityError("malformed TSAR artifact entry")
        path, digest = item.get("path"), item.get("sha256")
        if (
            not isinstance(path, str)
            or not path
            or not isinstance(digest, str)
            or not _SHA256_RE.fullmatch(digest)
        ):
            raise SecurityError("TSAR artifact requires a relative path and lowercase SHA-256")
        artifacts.append((path, digest))
    return TsarEvidence(
        evidence_id=payload["evidence_id"],
        tsar_version=payload["tsar_version"],
        commit_sha=payload["commit_sha"],
        executed_at=payload["executed_at"],
        status=payload["status"],
        rule_ids=tuple(payload["rule_ids"]),
        summary=summary,
        artifacts=tuple(artifacts),
    )


def _version_tuple(value: str) -> tuple[int, int, int]:
    match = _SEMVER_RE.fullmatch(value)
    if not match:
        raise SecurityError(f"invalid version: {value!r}")
    return tuple(int(part) for part in match.groups())  # type: ignore[return-value]


def _maximum_version_tuple(value: str) -> tuple[int, int, int]:
    """Resolve an exclusive upper bound, accepting trailing x wildcards."""
    parts = value.split(".")
    if len(parts) != 3:
        raise SecurityError(f"invalid version bound: {value!r}")
    wildcard_indexes = [index for index, part in enumerate(parts) if part.lower() == "x"]
    if not wildcard_indexes:
        return _version_tuple(value)
    first_wildcard = wildcard_indexes[0]
    if first_wildcard == 0 or any(part.lower() != "x" for part in parts[first_wildcard:]):
        raise SecurityError(f"invalid version bound: {value!r}")
    numeric = [int(part) for part in parts[:first_wildcard]]
    if any(str(number) != part for number, part in zip(numeric, parts, strict=False)):
        raise SecurityError(f"invalid version bound: {value!r}")
    numeric[-1] += 1
    numeric.extend([0] * (3 - len(numeric)))
    return tuple(numeric)  # type: ignore[return-value]


def _check_version(version: str, minimum: str, maximum: str) -> None:
    current = _version_tuple(version)
    lower = _version_tuple(minimum)
    upper = _maximum_version_tuple(maximum)
    if current < lower or current >= upper:
        raise SecurityError(f"TSAR version {version} out of range [{minimum}, {maximum})")


def _check_freshness(executed_at: str, *, now: datetime | None = None) -> None:
    try:
        value = executed_at[:-1] + "+00:00" if executed_at.endswith("Z") else executed_at
        executed = datetime.fromisoformat(value)
    except (TypeError, ValueError) as exc:
        raise EvidenceStaleError(f"invalid executed_at: {executed_at!r}") from exc
    if executed.tzinfo is None:
        raise EvidenceStaleError("executed_at must include a timezone")
    now_dt = now or datetime.now(UTC)
    if now_dt.tzinfo is None:
        raise ValueError("now must be timezone-aware")
    age = (now_dt - executed.astimezone(UTC)).total_seconds() / 3600
    if age < 0:
        raise EvidenceStaleError("TSAR evidence timestamp is in the future")
    if age > FRESHNESS_HOURS:
        raise EvidenceStaleError(f"TSAR evidence is stale: {age:.1f}h, maximum {FRESHNESS_HOURS}h")


def _check_required_rules(rule_ids: tuple[str, ...]) -> None:
    """Ensure every required TSAR rule ID is present in the evidence."""
    present = set(rule_ids)
    missing = [rule_id for rule_id in REQUIRED_RULE_IDS if rule_id not in present]
    if missing:
        raise SecurityError(f"TSAR evidence missing required rule_ids: {missing}")


def _check_artifacts(
    artifacts: tuple[tuple[str, str], ...],
    evidence_root: Path,
) -> None:
    root = evidence_root.resolve()
    for relative, expected in artifacts:
        candidate = (root / relative).resolve()
        try:
            candidate.relative_to(root)
        except ValueError as exc:
            raise EvidenceTamperedError(
                f"TSAR artifact path escapes evidence root: {relative}"
            ) from exc
        if not candidate.is_file():
            raise EvidenceTamperedError(f"TSAR artifact missing: {candidate}")
        actual = sha256_of(candidate)
        if actual != expected:
            raise EvidenceTamperedError(
                f"TSAR artifact hash mismatch: {candidate} "
                f"(expected {expected[:8]}..., got {actual[:8]}...)"
            )


def verify_tsar_evidence(
    payload: dict[str, Any],
    *,
    expected_commit_sha: str,
    evidence_root: Path,
    minimum_version: str = "1.1.0",
    maximum_version: str = "2.0.0",
    required_rule_ids: tuple[str, ...] = REQUIRED_RULE_IDS,
    now: datetime | None = None,
) -> TsarEvidence:
    """Return validated evidence or raise a security/evidence exception."""
    if not _COMMIT_RE.fullmatch(expected_commit_sha):
        raise SecurityError("expected_commit_sha must be a 40-character lowercase SHA-1")
    evidence = _parse_tsar_payload(payload)
    if not _COMMIT_RE.fullmatch(evidence.commit_sha):
        raise SecurityError("TSAR commit_sha is malformed")
    if evidence.commit_sha != expected_commit_sha:
        raise EvidenceTamperedError(
            f"TSAR evidence commit {evidence.commit_sha!r} != expected {expected_commit_sha!r}"
        )
    _check_version(evidence.tsar_version, minimum_version, maximum_version)
    _check_freshness(evidence.executed_at, now=now)
    _check_required_rules(evidence.rule_ids)
    _check_artifacts(evidence.artifacts, evidence_root)

    if evidence.status not in {"PASS", "FAIL", "BLOCKED"}:
        raise SecurityError(f"invalid TSAR status: {evidence.status!r}")
    critical = evidence.summary.get("critical", 0)
    high = evidence.summary.get("high", 0)
    if critical or high:
        raise SecurityError(
            f"TSAR reports unresolved critical/high findings: critical={critical}, high={high}"
        )
    logger.info("TSAR evidence %s verified", evidence.evidence_id)
    return evidence
