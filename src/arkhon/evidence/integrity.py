"""Evidence integrity and freshness verification."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from arkhon.core.errors import EvidenceError, EvidenceStaleError, EvidenceTamperedError
from arkhon.core.logging import get_logger

logger = get_logger("evidence.integrity")


def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 16), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_artifact(artifact_path: Path, expected_sha256: str) -> None:
    if not artifact_path.is_file():
        raise EvidenceTamperedError(f"artifact missing: {artifact_path}")
    if len(expected_sha256) != 64 or any(c not in "0123456789abcdef" for c in expected_sha256):
        raise EvidenceTamperedError("artifact contains an invalid SHA-256 value")
    actual = sha256_of(artifact_path)
    if actual != expected_sha256:
        raise EvidenceTamperedError(
            f"artifact hash mismatch: {artifact_path} "
            f"(expected {expected_sha256[:8]}..., got {actual[:8]}...)"
        )


def verify_bundle(
    bundle_path: Path,
    *,
    evidence_root: Path,
    expected_commit_sha: str,
) -> None:
    """Verify a bundle's commit binding and every referenced artifact."""
    if not bundle_path.is_file():
        raise EvidenceTamperedError(f"evidence bundle missing: {bundle_path}")
    try:
        with bundle_path.open("r", encoding="utf-8") as stream:
            data: dict[str, Any] = json.load(stream)
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise EvidenceTamperedError(f"evidence bundle is not valid JSON: {bundle_path}") from exc
    if not isinstance(data, dict):
        raise EvidenceTamperedError(f"evidence bundle must be a JSON object: {bundle_path}")
    commit = data.get("commit_sha")
    if commit != expected_commit_sha:
        raise EvidenceTamperedError(
            f"commit mismatch: bundle says {commit!r}, expected {expected_commit_sha!r}"
        )
    artifacts = data.get("artifacts")
    if not isinstance(artifacts, list) or not artifacts:
        raise EvidenceTamperedError(f"evidence has no artifacts: {bundle_path}")
    root = evidence_root.resolve()
    for artifact in artifacts:
        if not isinstance(artifact, dict):
            raise EvidenceTamperedError(f"malformed artifact entry in {bundle_path}")
        relative = artifact.get("path")
        expected_hash = artifact.get("sha256")
        if not isinstance(relative, str) or not relative:
            raise EvidenceTamperedError(f"malformed artifact path in {bundle_path}")
        candidate = (root / relative).resolve()
        try:
            candidate.relative_to(root)
        except ValueError as exc:
            raise EvidenceTamperedError(f"artifact path escapes evidence root: {relative}") from exc
        if not isinstance(expected_hash, str):
            raise EvidenceTamperedError(f"malformed artifact hash in {bundle_path}")
        verify_artifact(candidate, expected_hash)
    logger.debug("verified bundle %s with %d artifacts", bundle_path, len(artifacts))


def verify_freshness(
    executed_at: str,
    *,
    max_age_hours: int,
    now_iso: str | None = None,
) -> None:
    """Raise when evidence is older than the configured maximum age."""
    if max_age_hours < 0:
        raise EvidenceError("max_age_hours must be non-negative")

    def parse(value: str) -> datetime:
        if value.endswith("Z"):
            value = value[:-1] + "+00:00"
        return datetime.fromisoformat(value)

    try:
        executed = parse(executed_at)
        now = parse(now_iso) if now_iso else datetime.now(UTC)
    except (TypeError, ValueError) as exc:
        raise EvidenceError(f"invalid timestamp: {exc}") from exc
    if executed.tzinfo is None:
        executed = executed.replace(tzinfo=UTC)
    if now.tzinfo is None:
        now = now.replace(tzinfo=UTC)
    age = (now - executed).total_seconds() / 3600.0
    if age < 0:
        raise EvidenceError("evidence timestamp is in the future")
    if age > max_age_hours:
        raise EvidenceStaleError(f"evidence is stale: {age:.1f}h old, maximum {max_age_hours}h")
