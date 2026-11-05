"""Security tests for the append-only evidence store."""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest

from arkhon.core.errors import EvidenceError, EvidenceTamperedError
from arkhon.evidence.store import EvidenceStore


def _record(evidence_id: str = "EVID-TEST-0001") -> dict[str, str]:
    return {
        "evidence_id": evidence_id,
        "source": "arkhon",
        "source_version": "0.1.0.dev1",
        "commit_sha": "a" * 40,
        "status": "PASS",
    }


def _symlink_or_skip(link: Path, target: Path, *, target_is_directory: bool = False) -> None:
    try:
        link.symlink_to(target, target_is_directory=target_is_directory)
    except (OSError, NotImplementedError) as exc:
        pytest.skip(f"symlinks unavailable in this environment: {exc}")


def test_write_rejects_domain_symlink_escape(tmp_path: Path) -> None:
    project = tmp_path / "project"
    outside = tmp_path / "outside"
    project.mkdir()
    outside.mkdir()
    evidence_root = project / ".arkhon" / "evidence"
    evidence_root.mkdir(parents=True)
    _symlink_or_skip(evidence_root / "security", outside, target_is_directory=True)

    store = EvidenceStore(project)
    with pytest.raises(EvidenceError, match="domain escapes evidence root"):
        store.write("security", _record())
    assert list(outside.iterdir()) == []


def test_write_rejects_evidence_root_symlink_escape(tmp_path: Path) -> None:
    project = tmp_path / "project"
    outside = tmp_path / "outside"
    project.mkdir()
    outside.mkdir()
    _symlink_or_skip(project / ".arkhon", outside, target_is_directory=True)

    store = EvidenceStore(project)
    with pytest.raises(EvidenceError, match="evidence root escapes project root"):
        store.write("security", _record())
    assert list(outside.iterdir()) == []


def test_read_rejects_symlinked_record(tmp_path: Path) -> None:
    project = tmp_path / "project"
    outside = tmp_path / "outside.json"
    project.mkdir()
    outside.write_text('{"evidence_id":"EVID-OUTSIDE"}', encoding="utf-8")
    evidence_dir = project / ".arkhon" / "evidence" / "security"
    evidence_dir.mkdir(parents=True)
    _symlink_or_skip(evidence_dir / "EVID-TEST-0001.json", outside)

    with pytest.raises(EvidenceTamperedError, match="record is a symlink"):
        EvidenceStore(project).read("security", "EVID-TEST-0001")


def test_write_rejects_symlinked_record(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    outside = tmp_path / "outside.json"
    outside.write_text('{"evidence_id":"EVID-OUTSIDE"}', encoding="utf-8")
    evidence_dir = project / ".arkhon" / "evidence" / "security"
    evidence_dir.mkdir(parents=True)
    _symlink_or_skip(evidence_dir / "EVID-TEST-0001.json", outside)

    with pytest.raises(EvidenceTamperedError, match="refusing symlinked"):
        EvidenceStore(project).write("security", _record())


def test_iter_records_rejects_symlinked_record(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    outside = tmp_path / "outside.json"
    outside.write_text('{"evidence_id":"EVID-OUTSIDE"}', encoding="utf-8")
    evidence_dir = project / ".arkhon" / "evidence" / "security"
    evidence_dir.mkdir(parents=True)
    _symlink_or_skip(evidence_dir / "EVID-TEST-0001.json", outside)

    with pytest.raises(EvidenceTamperedError, match="record is a symlink"):
        list(EvidenceStore(project).iter_records("security"))


def test_iter_records_rejects_resolved_path_escape(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project = tmp_path / "project"
    project.mkdir()
    evidence_dir = project / ".arkhon" / "evidence" / "security"
    evidence_dir.mkdir(parents=True)
    record = evidence_dir / "EVID-TEST.json"
    record.write_text('{"evidence_id":"EVID-TEST"}', encoding="utf-8")
    outside = tmp_path / "outside.json"
    original_resolve = Path.resolve

    def redirected_resolve(path: Path, *args: object, **kwargs: object) -> Path:
        if path == record:
            return outside
        return original_resolve(path, *args, **kwargs)

    monkeypatch.setattr(Path, "resolve", redirected_resolve)
    with pytest.raises(EvidenceTamperedError, match="escapes evidence root"):
        list(EvidenceStore(project).iter_records("security"))

def _valid_record(project: Path, evidence_id: str = "EVID-TEST-0002") -> dict[str, Any]:
    artifact = project / "artifact.txt"
    artifact.write_text("verified evidence", encoding="utf-8")
    return {
        "evidence_id": evidence_id,
        "source": "arkhon",
        "source_version": "0.1.0.dev1",
        "commit_sha": "a" * 40,
        "executed_at": datetime.now(UTC).isoformat(),
        "status": "PASS",
        "artifacts": [
            {
                "path": "artifact.txt",
                "sha256": hashlib.sha256(artifact.read_bytes()).hexdigest(),
            }
        ],
    }


def test_read_verifies_artifact_hash(tmp_path: Path) -> None:
    store = EvidenceStore(tmp_path)
    record = _valid_record(tmp_path)
    store.write("testing", record)

    (tmp_path / "artifact.txt").write_text("modified after evidence", encoding="utf-8")

    with pytest.raises(EvidenceTamperedError, match="hash mismatch"):
        store.read("testing", "EVID-TEST-0002")


def test_iter_records_verifies_artifact_hash(tmp_path: Path) -> None:
    store = EvidenceStore(tmp_path)
    record = _valid_record(tmp_path)
    store.write("testing", record)

    (tmp_path / "artifact.txt").write_text("modified after evidence", encoding="utf-8")

    with pytest.raises(EvidenceTamperedError, match="hash mismatch"):
        list(store.iter_records())


def test_read_rejects_malformed_evidence_metadata(tmp_path: Path) -> None:
    store = EvidenceStore(tmp_path)
    record = _valid_record(tmp_path)
    record["commit_sha"] = "not-a-commit"
    store.write("testing", record)

    with pytest.raises(EvidenceTamperedError, match="invalid commit SHA"):
        store.read("testing", "EVID-TEST-0002")


def test_read_rejects_artifact_path_traversal(tmp_path: Path) -> None:
    store = EvidenceStore(tmp_path)
    record = _valid_record(tmp_path)
    artifact = record["artifacts"][0]
    assert isinstance(artifact, dict)
    artifact["path"] = "../outside.txt"
    store.write("testing", record)

    with pytest.raises(EvidenceTamperedError, match="safe relative path"):
        store.read("testing", "EVID-TEST-0002")


def test_read_rejects_missing_artifact(tmp_path: Path) -> None:
    store = EvidenceStore(tmp_path)
    record = _valid_record(tmp_path)
    artifact = record["artifacts"][0]
    assert isinstance(artifact, dict)
    artifact["path"] = "missing.txt"
    store.write("testing", record)

    with pytest.raises(EvidenceTamperedError, match="artifact missing"):
        store.read("testing", "EVID-TEST-0002")

