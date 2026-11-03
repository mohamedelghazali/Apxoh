"""Evidence collection for Apxoh.

The collector records outputs produced by independent tools, computes integrity
hashes, and writes evidence bundles in the shape defined by the evidence schema.
"""
from __future__ import annotations

import hashlib
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

from arkhon.core.constants import ALL_STATUSES
from arkhon.core.errors import EvidenceError
from arkhon.core.logging import get_logger

logger = get_logger("evidence.collector")
EvidenceSource = Literal["arkhon", "tsar", "external-tool"]


def _sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 16), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _utc_now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


@dataclass(frozen=True)
class Artifact:
    """A single file supporting an evidence claim."""
    path: Path
    sha256: str

    def to_dict(self, *, root: Path | None = None) -> dict[str, str]:
        path = self.path
        if root is not None:
            try:
                path = path.resolve().relative_to(root.resolve())
            except ValueError as exc:
                raise EvidenceError(f"artifact is outside evidence root: {path}") from exc
        return {"path": path.as_posix(), "sha256": self.sha256}


@dataclass
class EvidenceDraft:
    """Mutable draft before evidence is finalized."""
    evidence_id: str
    source: EvidenceSource
    source_version: str
    commit_sha: str
    status: str
    artifacts: list[Artifact] = field(default_factory=list)
    summary: dict[str, int] = field(default_factory=dict)
    rule_ids: list[str] = field(default_factory=list)
    tsar_metadata: dict[str, Any] | None = None
    notes: str | None = None

    def add_artifact(self, path: Path) -> None:
        path = Path(path).resolve()
        if not path.is_file():
            raise EvidenceError(f"artifact not found: {path}")
        self.artifacts.append(Artifact(path=path, sha256=_sha256_of(path)))

    def to_evidence(self) -> dict[str, Any]:
        if self.status not in ALL_STATUSES:
            raise EvidenceError(f"invalid status: {self.status}")
        if not self.artifacts:
            raise EvidenceError("evidence must have at least one artifact")
        if self.source == "tsar" and not self.tsar_metadata:
            raise EvidenceError("source='tsar' requires tsar_metadata")
        if not self.source_version.strip():
            raise EvidenceError("source_version must not be empty")
        payload: dict[str, Any] = {
            "evidence_id": self.evidence_id,
            "source": self.source,
            "source_version": self.source_version,
            "commit_sha": self.commit_sha,
            "executed_at": _utc_now(),
            "status": self.status,
            "artifacts": [artifact.to_dict() for artifact in self.artifacts],
        }
        if self.summary:
            payload["summary"] = self.summary
        if self.rule_ids:
            payload["rule_ids"] = self.rule_ids
        if self.tsar_metadata:
            payload["tsar_metadata"] = self.tsar_metadata
        if self.notes:
            payload["notes"] = self.notes
        return payload


class EvidenceCollector:
    """Collect evidence from independent tools into a single bundle."""
    def __init__(self, root: Path | None = None) -> None:
        self._root = Path(root or Path.cwd()).resolve()

    @property
    def root(self) -> Path:
        return self._root

    def new_evidence(
        self, *, source: EvidenceSource, source_version: str,
        commit_sha: str, status: str,
    ) -> EvidenceDraft:
        if source not in {"arkhon", "tsar", "external-tool"}:
            raise EvidenceError(f"invalid evidence source: {source!r}")
        if len(commit_sha) != 40 or any(c not in "0123456789abcdef" for c in commit_sha):
            raise EvidenceError(f"invalid commit SHA: {commit_sha!r}")
        if not source_version.strip():
            raise EvidenceError("source_version must not be empty")
        evidence_id = f"EVID-{source.upper()}-{uuid.uuid4().hex[:12].upper()}"
        return EvidenceDraft(
            evidence_id=evidence_id, source=source, source_version=source_version,
            commit_sha=commit_sha, status=status,
        )
