"""Append-only JSON evidence storage scoped to a project."""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any

from arkhon.core.constants import ALL_STATUSES
from arkhon.core.errors import EvidenceError, EvidenceTamperedError
from arkhon.core.logging import get_logger
from arkhon.evidence.integrity import sha256_of, verify_bundle

logger = get_logger("evidence.store")
_SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
_EVIDENCE_ID = re.compile(r"^EVID-[A-Z0-9-]+$")
_COMMIT_SHA = re.compile(r"^[0-9a-f]{40}$")
_ALLOWED_SOURCES = frozenset({"arkhon", "tsar", "external-tool"})


@dataclass(frozen=True)
class EvidenceRecord:
    path: Path
    data: dict[str, Any]

    @property
    def evidence_id(self) -> str:
        return str(self.data.get("evidence_id", ""))

    @property
    def commit_sha(self) -> str:
        return str(self.data.get("commit_sha", ""))

    @property
    def status(self) -> str:
        return str(self.data.get("status", ""))


class EvidenceStore:
    """Append-only evidence store scoped to a project."""

    def __init__(self, root: Path) -> None:
        self._project_root = Path(root).resolve()
        self._root = self._project_root / ".arkhon" / "evidence"

    def _resolved_root(self) -> Path:
        root = self._root.resolve()
        try:
            root.relative_to(self._project_root)
        except ValueError as exc:
            raise EvidenceError("evidence root escapes project root") from exc
        return root

    @property
    def root(self) -> Path:
        return self._root

    def _domain_dir(self, domain: str) -> Path:
        if not isinstance(domain, str) or not domain or not _SAFE_ID.fullmatch(domain):
            raise EvidenceError(f"invalid domain: {domain!r}")
        root = self._resolved_root()
        candidate = (self._root / domain).resolve()
        try:
            candidate.relative_to(root)
        except ValueError as exc:
            raise EvidenceError(f"evidence domain escapes evidence root: {domain!r}") from exc
        return candidate

    @staticmethod
    def _validate_id(evidence_id: object) -> str:
        if not isinstance(evidence_id, str) or not _EVIDENCE_ID.fullmatch(evidence_id):
            raise EvidenceError("invalid or missing evidence_id")
        return evidence_id

    def _validate_record(self, path: Path, data: dict[str, Any], evidence_id: str) -> None:
        """Validate evidence metadata and every artifact before trusting a record."""
        if data.get("evidence_id") != evidence_id:
            raise EvidenceTamperedError(f"evidence ID does not match filename: {path}")

        required = {
            "source",
            "source_version",
            "commit_sha",
            "executed_at",
            "status",
            "artifacts",
        }
        missing = sorted(required - data.keys())
        if missing:
            raise EvidenceTamperedError(
                f"evidence record is missing required fields: {', '.join(missing)}"
            )

        source = data["source"]
        if not isinstance(source, str) or source not in _ALLOWED_SOURCES:
            raise EvidenceTamperedError(f"evidence record has an invalid source: {source!r}")
        source_version = data["source_version"]
        if not isinstance(source_version, str) or not source_version.strip():
            raise EvidenceTamperedError("evidence source_version must be a non-empty string")

        commit_sha = data["commit_sha"]
        if not isinstance(commit_sha, str) or not _COMMIT_SHA.fullmatch(commit_sha):
            raise EvidenceTamperedError("evidence record has an invalid commit SHA")

        status = data["status"]
        if status not in ALL_STATUSES:
            raise EvidenceTamperedError(f"evidence record has an invalid status: {status!r}")

        executed_at = data["executed_at"]
        if not isinstance(executed_at, str):
            raise EvidenceTamperedError("evidence executed_at must be a date-time string")
        try:
            timestamp = datetime.fromisoformat(executed_at.replace("Z", "+00:00"))
        except ValueError as exc:
            raise EvidenceTamperedError("evidence executed_at is not a valid date-time") from exc
        if timestamp.tzinfo is None:
            raise EvidenceTamperedError("evidence executed_at must include a timezone")

        artifacts = data["artifacts"]
        if not isinstance(artifacts, list) or not artifacts:
            raise EvidenceTamperedError("evidence record must contain at least one artifact")
        for artifact in artifacts:
            if not isinstance(artifact, dict):
                raise EvidenceTamperedError("evidence artifact entry must be an object")
            relative_path = artifact.get("path")
            if (
                not isinstance(relative_path, str)
                or not relative_path
                or "\x00" in relative_path
                or "\\" in relative_path
                or PurePosixPath(relative_path).is_absolute()
                or PureWindowsPath(relative_path).is_absolute()
                or ".." in PurePosixPath(relative_path).parts
            ):
                raise EvidenceTamperedError("evidence artifact path must be a safe relative path")

        verify_bundle(
            path,
            evidence_root=self._project_root,
            expected_commit_sha=commit_sha,
        )

    def write(self, domain: str, evidence: dict[str, Any]) -> Path:
        if not isinstance(evidence, dict):
            raise EvidenceError("evidence record must be a mapping")
        evidence_id = self._validate_id(evidence.get("evidence_id"))
        target_dir = self._domain_dir(domain)
        target_dir.mkdir(parents=True, exist_ok=True)
        target_dir = self._domain_dir(domain)
        target = target_dir / f"{evidence_id}.json"
        if target.is_symlink():
            raise EvidenceTamperedError(f"refusing symlinked evidence record: {target}")
        payload = json.dumps(evidence, indent=2, sort_keys=True, ensure_ascii=False).encode("utf-8")
        new_hash = hashlib.sha256(payload).hexdigest()
        if target.exists():
            if sha256_of(target) != new_hash:
                raise EvidenceTamperedError(
                    f"refusing to overwrite evidence with different content: {target}"
                )
            logger.debug("evidence already present: %s", target)
            return target
        try:
            with target.open("xb") as stream:
                stream.write(payload)
        except FileExistsError:
            if sha256_of(target) != new_hash:
                raise EvidenceTamperedError(f"concurrent evidence collision: {target}") from None
        logger.debug("wrote evidence %s to %s", evidence_id, target)
        return target

    def _read_record(self, path: Path, evidence_id: str) -> EvidenceRecord:
        if path.is_symlink():
            raise EvidenceTamperedError(f"evidence record is a symlink: {path}")
        if not path.is_file():
            raise EvidenceError(f"evidence not found: {evidence_id}")
        try:
            with path.open("r", encoding="utf-8") as stream:
                data = json.load(stream)
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            raise EvidenceTamperedError(f"evidence record is unreadable: {path}") from exc
        if not isinstance(data, dict):
            raise EvidenceTamperedError(f"evidence record is not an object: {path}")
        self._validate_record(path, data, evidence_id)
        return EvidenceRecord(path=path, data=data)

    def read(self, domain: str, evidence_id: str) -> EvidenceRecord:
        safe_id = self._validate_id(evidence_id)
        domain_root = self._domain_dir(domain)
        return self._read_record(domain_root / f"{safe_id}.json", safe_id)

    def iter_records(self, domain: str | None = None) -> Iterator[EvidenceRecord]:
        roots = [self._resolved_root()] if domain is None else [self._domain_dir(domain)]
        for base in roots:
            if not base.is_dir():
                continue
            for path in sorted(base.rglob("*.json")):
                if not path.stem.startswith("EVID-"):
                    continue
                if not _EVIDENCE_ID.fullmatch(path.stem):
                    raise EvidenceTamperedError(f"invalid evidence record filename: {path}")
                if path.is_symlink():
                    raise EvidenceTamperedError(f"evidence record is a symlink: {path}")
                resolved_path = path.resolve()
                try:
                    resolved_path.relative_to(base.resolve())
                except ValueError as exc:
                    raise EvidenceTamperedError(
                        f"evidence record escapes evidence root: {path}"
                    ) from exc
                yield self._read_record(resolved_path, path.stem)

    def latest_for_commit(self, domain: str, commit_sha: str) -> EvidenceRecord | None:
        latest: EvidenceRecord | None = None
        for record in self.iter_records(domain):
            if record.commit_sha == commit_sha and (
                latest is None
                or record.data.get("executed_at", "") > latest.data.get("executed_at", "")
            ):
                latest = record
        return latest
