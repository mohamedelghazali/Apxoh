"""Commit-bound human engineering review attestations with anti-self-approval guards."""

from __future__ import annotations

import json
import os
import re
import tempfile
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import jsonschema

from gencode_gov.core.constants import STATUS_BLOCKED, STATUS_PASS
from gencode_gov.core.errors import EvidenceError
from gencode_gov.evidence.integrity import sha256_of

MAX_ATTESTATION_DAYS = 90
_RULE_ID_RE = re.compile(r"^SE-[A-Z]+(-[A-Z]+)?-\d{3,}$")
_COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")
_FORBIDDEN_REVIEWER_TOKENS = (
    "[bot]",
    "dependabot",
    "github-actions",
    "renovate",
    "ai-agent",
    "claude",
    "codex",
    "cursor",
    "copilot",
    "gemini",
    "gencode-gov-bot",
    "bot-",
    "agent-",
    "ci-worker",
)


@dataclass(frozen=True)
class ReviewAttestation:
    """Verified human review attestation bound to a commit and artifact hashes."""

    attestation_id: str
    rule_ids: tuple[str, ...]
    reviewer: str
    approver_role: str
    commit_sha: str
    attested_at: str
    expires_at: str
    rationale: str
    reviewed_artifacts: tuple[dict[str, str], ...]
    path: Path


def _schema_dict() -> dict[str, Any]:
    return {
        "type": "object",
        "additionalProperties": False,
        "required": [
            "attestation_id",
            "rule_ids",
            "reviewer",
            "approver_role",
            "commit_sha",
            "attested_at",
            "expires_at",
            "rationale",
            "reviewed_artifacts",
        ],
        "properties": {
            "attestation_id": {"type": "string", "pattern": "^ATTEST-[A-Z0-9-]{8,48}$"},
            "rule_ids": {
                "type": "array",
                "minItems": 1,
                "uniqueItems": True,
                "items": {"type": "string", "pattern": "^SE-[A-Z]+(-[A-Z]+)?-\\d{3,}$"},
            },
            "reviewer": {"type": "string", "minLength": 2, "maxLength": 128},
            "approver_role": {"type": "string", "minLength": 2, "maxLength": 128},
            "commit_sha": {"type": "string", "pattern": "^[0-9a-f]{40}$"},
            "attested_at": {"type": "string"},
            "expires_at": {"type": "string"},
            "rationale": {"type": "string", "minLength": 10, "maxLength": 4000},
            "reviewed_artifacts": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["path", "sha256"],
                    "properties": {
                        "path": {"type": "string", "minLength": 1},
                        "sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
                    },
                },
            },
        },
    }


def _parse_utc(value: str, label: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise EvidenceError(f"invalid {label} timestamp: {value!r}") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise EvidenceError(f"{label} timestamp must include timezone: {value!r}")
    return parsed.astimezone(UTC)


def _ensure_human_reviewer(reviewer: str) -> str:
    if os.environ.get("GENCODE_GOV_AGENT_SESSION_ID") or os.environ.get("GENCODE_GOV_SANDBOX"):
        raise EvidenceError(
            "automated agent or sandbox sessions are forbidden from creating human attestations"
        )
    cleaned = reviewer.strip()
    lowered = cleaned.lower()
    if len(cleaned) < 2 or any(tok in lowered for tok in _FORBIDDEN_REVIEWER_TOKENS):
        raise EvidenceError(
            f"reviewer {reviewer!r} looks like an automated bot or coding agent; "
            "human reviewer identity required"
        )
    return cleaned


def create_human_attestation(
    project_root: Path,
    *,
    rule_ids: list[str],
    reviewer: str,
    approver_role: str,
    commit_sha: str,
    rationale: str,
    artifact_paths: list[str] | None = None,
    expires_days: int = 30,
) -> ReviewAttestation:
    """Create and atomically persist a commit-bound human review attestation."""
    root = project_root.resolve()
    if not root.is_dir():
        raise EvidenceError(f"project root is not a directory: {root}")
    human = _ensure_human_reviewer(reviewer)
    role = approver_role.strip()
    if len(role) < 2:
        raise EvidenceError("approver_role must be at least 2 characters")
    clean_rationale = rationale.strip()
    if len(clean_rationale) < 10:
        raise EvidenceError("rationale must be at least 10 characters")
    if not _COMMIT_RE.fullmatch(commit_sha):
        raise EvidenceError(f"invalid 40-char commit SHA: {commit_sha!r}")
    if isinstance(expires_days, bool) or not (1 <= expires_days <= MAX_ATTESTATION_DAYS):
        raise EvidenceError(f"expires_days must be between 1 and {MAX_ATTESTATION_DAYS}")
    if not rule_ids or any(not _RULE_ID_RE.fullmatch(rid) for rid in rule_ids):
        raise EvidenceError("at least one valid SE-* rule_id is required")

    artifacts: list[dict[str, str]] = []
    for rel_str in artifact_paths or []:
        candidate = root / rel_str
        if candidate.is_symlink():
            raise EvidenceError(f"refusing symlinked reviewed artifact: {rel_str}")
        resolved = candidate.resolve()
        try:
            rel_norm = resolved.relative_to(root).as_posix()
        except ValueError as exc:
            raise EvidenceError(f"reviewed artifact escapes project root: {rel_str}") from exc
        if not resolved.is_file():
            raise EvidenceError(f"reviewed artifact does not exist: {rel_str}")
        artifacts.append({"path": rel_norm, "sha256": sha256_of(resolved)})

    now = datetime.now(UTC)
    expires = now + timedelta(days=expires_days)
    attest_id = f"ATTEST-GENCODE-GOV-{uuid.uuid4().hex[:12].upper()}"
    payload: dict[str, Any] = {
        "attestation_id": attest_id,
        "rule_ids": sorted(set(rule_ids)),
        "reviewer": human,
        "approver_role": role,
        "commit_sha": commit_sha,
        "attested_at": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "expires_at": expires.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "rationale": clean_rationale,
        "reviewed_artifacts": artifacts,
    }
    jsonschema.validate(instance=payload, schema=_schema_dict())

    gov_dir = root / ".gencode-gov"
    if gov_dir.is_symlink():
        raise EvidenceError("refusing symlinked .gencode-gov directory")
    evid_dir = gov_dir / "evidence"
    if evid_dir.is_symlink():
        raise EvidenceError("refusing symlinked .gencode-gov/evidence directory")
    attest_dir = evid_dir / "attestations"
    if attest_dir.exists() and attest_dir.is_symlink():
        raise EvidenceError("refusing symlinked attestations directory")
    attest_dir.mkdir(parents=True, exist_ok=True)
    attest_dir.resolve().relative_to(root)

    target = attest_dir / f"{attest_id}.json"
    if target.exists():  # pragma: no cover
        raise EvidenceError(f"attestation already exists: {target}")

    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        dir=attest_dir,
        prefix=".attest-",
        suffix=".tmp",
        delete=False,
    ) as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
        tmp_path = Path(handle.name)
    tmp_path.replace(target)

    return ReviewAttestation(
        attestation_id=attest_id,
        rule_ids=tuple(payload["rule_ids"]),
        reviewer=human,
        approver_role=role,
        commit_sha=commit_sha,
        attested_at=payload["attested_at"],
        expires_at=payload["expires_at"],
        rationale=clean_rationale,
        reviewed_artifacts=tuple(artifacts),
        path=target,
    )


def verify_human_attestation(
    project_root: Path,
    *,
    rule_id: str,
    expected_commit_sha: str | None,
    required_role: str | None = None,
) -> tuple[str, str]:
    """Verify commit-bound, non-expired, hash-intact human attestation for rule_id."""
    if expected_commit_sha is None or not _COMMIT_RE.fullmatch(expected_commit_sha):
        return STATUS_BLOCKED, "cannot verify human attestation without a clean Git commit SHA"

    root = project_root.resolve()
    attest_dir = root / ".gencode-gov" / "evidence" / "attestations"
    if not attest_dir.is_dir() or attest_dir.is_symlink():
        return (
            STATUS_BLOCKED,
            f"authorized human review attestation missing for {rule_id} "
            f"(record via 'gencode-gov attest --rule {rule_id}')",
        )

    now = datetime.now(UTC)
    schema = _schema_dict()
    stale_reasons: list[str] = []

    for candidate in sorted(attest_dir.glob("*.json")):
        if candidate.is_symlink() or not candidate.is_file():  # pragma: no cover
            continue
        try:
            data = json.loads(candidate.read_text(encoding="utf-8"))
            jsonschema.validate(instance=data, schema=schema)
        except (OSError, UnicodeDecodeError, json.JSONDecodeError, jsonschema.ValidationError):
            stale_reasons.append(f"malformed attestation {candidate.name}")
            continue

        if rule_id not in data["rule_ids"]:
            continue

        reviewer = str(data["reviewer"]).strip()
        if any(tok in reviewer.lower() for tok in _FORBIDDEN_REVIEWER_TOKENS):
            stale_reasons.append(f"attestation {data['attestation_id']} uses bot/agent reviewer")
            continue

        if data["commit_sha"] != expected_commit_sha:
            stale_reasons.append(
                f"attestation {data['attestation_id']} bound to {data['commit_sha'][:12]}, "
                f"not {expected_commit_sha[:12]}"
            )
            continue

        try:
            attested_dt = _parse_utc(data["attested_at"], "attested_at")
            expires_dt = _parse_utc(data["expires_at"], "expires_at")
        except EvidenceError as exc:
            stale_reasons.append(str(exc))
            continue

        if expires_dt <= now or (expires_dt - attested_dt).days > MAX_ATTESTATION_DAYS:
            stale_reasons.append(f"attestation {data['attestation_id']} is expired")
            continue

        if required_role and data["approver_role"].strip() != required_role.strip():
            stale_reasons.append(
                f"attestation {data['attestation_id']} role {data['approver_role']!r} "
                f"!= required {required_role!r}"
            )
            continue

        tampered = False
        for item in data["reviewed_artifacts"]:
            art_path = root / item["path"]
            if art_path.is_symlink():  # pragma: no cover
                tampered = True
                break
            resolved = art_path.resolve()
            try:
                resolved.relative_to(root)
            except ValueError:  # pragma: no cover
                tampered = True
                break
            if not resolved.is_file() or sha256_of(resolved) != item["sha256"]:
                tampered = True
                break
        if tampered:
            stale_reasons.append(
                f"attestation {data['attestation_id']} invalidated by modified artifact digest"
            )
            continue

        return (
            STATUS_PASS,
            f"verified commit-bound human attestation {data['attestation_id']} "
            f"by {reviewer} ({data['approver_role']})",
        )

    if stale_reasons:
        return STATUS_BLOCKED, "; ".join(stale_reasons)
    return (
        STATUS_BLOCKED,
        f"authorized human review attestation missing for {rule_id} at commit "
        f"{expected_commit_sha[:12]}",
    )
