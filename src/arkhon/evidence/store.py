"""Append-only JSON evidence storage scoped to a project."""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from arkhon.core.errors import EvidenceError, EvidenceTamperedError
from arkhon.core.logging import get_logger
from arkhon.evidence.integrity import sha256_of

logger = get_logger("evidence.store")
_SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
_EVIDENCE_ID = re.compile(r"^EVID-[A-Z0-9-]+$")


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

    def read(self, domain: str, evidence_id: str) -> EvidenceRecord:
        safe_id = self._validate_id(evidence_id)
        domain_root = self._domain_dir(domain)
        path = domain_root / f"{safe_id}.json"
        if path.is_symlink():
            raise EvidenceTamperedError(f"evidence record is a symlink: {path}")
        if not path.is_file():
            raise EvidenceError(f"evidence not found: {safe_id}")
        try:
            with path.open("r", encoding="utf-8") as stream:
                data = json.load(stream)
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            raise EvidenceTamperedError(f"evidence record is unreadable: {path}") from exc
        if not isinstance(data, dict):
            raise EvidenceTamperedError(f"evidence record is not an object: {path}")
        if data.get("evidence_id") != safe_id:
            raise EvidenceTamperedError(f"evidence ID does not match filename: {path}")
        return EvidenceRecord(path=path, data=data)

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
                try:
                    with resolved_path.open("r", encoding="utf-8") as stream:
                        data = json.load(stream)
                except (json.JSONDecodeError, UnicodeDecodeError) as exc:
                    raise EvidenceTamperedError(f"evidence record is unreadable: {path}") from exc
                if not isinstance(data, dict):
                    raise EvidenceTamperedError(f"evidence record is not an object: {path}")
                if data.get("evidence_id") != path.stem:
                    raise EvidenceTamperedError(f"evidence ID does not match filename: {path}")
                yield EvidenceRecord(path=resolved_path, data=data)

    def latest_for_commit(self, domain: str, commit_sha: str) -> EvidenceRecord | None:
        latest: EvidenceRecord | None = None
        for record in self.iter_records(domain):
            if record.commit_sha == commit_sha and (
                latest is None
                or record.data.get("executed_at", "") > latest.data.get("executed_at", "")
            ):
                latest = record
        return latest
