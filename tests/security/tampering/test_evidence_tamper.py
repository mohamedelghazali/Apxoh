"""Security tests for evidence artifact integrity and commit binding."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from arkhon.core.errors import EvidenceTamperedError
from arkhon.evidence.integrity import sha256_of, verify_bundle


def _bundle(tmp_path: Path, content: bytes = b"payload") -> tuple[Path, Path, str]:
    artifact = tmp_path / "artifact.bin"
    artifact.write_bytes(content)
    bundle = tmp_path / "bundle.json"
    commit = "a" * 40
    bundle.write_text(
        json.dumps(
            {
                "evidence_id": "EVID-TEST-001",
                "source": "arkhon",
                "source_version": "0.1.0.dev1",
                "commit_sha": commit,
                "executed_at": "2026-11-01T00:00:00Z",
                "status": "PASS",
                "artifacts": [{"path": "artifact.bin", "sha256": sha256_of(artifact)}],
            }
        ),
        encoding="utf-8",
    )
    return bundle, artifact, commit


def test_untampered_bundle_and_artifact_pass_integrity_checks(tmp_path: Path) -> None:
    bundle, _, commit = _bundle(tmp_path)
    verify_bundle(bundle, evidence_root=tmp_path, expected_commit_sha=commit)


def test_modified_artifact_is_rejected(tmp_path: Path) -> None:
    bundle, artifact, commit = _bundle(tmp_path)
    artifact.write_bytes(b"TAMPERED")
    with pytest.raises(EvidenceTamperedError, match="hash mismatch"):
        verify_bundle(bundle, evidence_root=tmp_path, expected_commit_sha=commit)


def test_deleted_artifact_is_rejected(tmp_path: Path) -> None:
    bundle, artifact, commit = _bundle(tmp_path)
    artifact.unlink()
    with pytest.raises(EvidenceTamperedError, match="missing"):
        verify_bundle(bundle, evidence_root=tmp_path, expected_commit_sha=commit)


def test_bundle_commit_mismatch_is_rejected(tmp_path: Path) -> None:
    bundle, _, _ = _bundle(tmp_path)
    data = json.loads(bundle.read_text(encoding="utf-8"))
    data["commit_sha"] = "b" * 40
    bundle.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(EvidenceTamperedError, match="commit mismatch"):
        verify_bundle(bundle, evidence_root=tmp_path, expected_commit_sha="a" * 40)


def test_artifact_path_traversal_is_rejected(tmp_path: Path) -> None:
    outside = tmp_path.parent / "outside.bin"
    outside.write_bytes(b"outside")
    bundle = tmp_path / "bundle.json"
    bundle.write_text(
        json.dumps(
            {
                "evidence_id": "EVID-TEST-002",
                "source": "arkhon",
                "source_version": "0.1.0.dev1",
                "commit_sha": "a" * 40,
                "executed_at": "2026-11-01T00:00:00Z",
                "status": "PASS",
                "artifacts": [{"path": "../outside.bin", "sha256": sha256_of(outside)}],
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(EvidenceTamperedError, match="escapes evidence root"):
        verify_bundle(bundle, evidence_root=tmp_path, expected_commit_sha="a" * 40)


def test_empty_artifact_list_is_rejected(tmp_path: Path) -> None:
    bundle = tmp_path / "bundle.json"
    bundle.write_text(
        json.dumps(
            {
                "evidence_id": "EVID-TEST-003",
                "source": "arkhon",
                "source_version": "0.1.0.dev1",
                "commit_sha": "a" * 40,
                "executed_at": "2026-11-01T00:00:00Z",
                "status": "PASS",
                "artifacts": [],
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(EvidenceTamperedError, match="no artifacts"):
        verify_bundle(bundle, evidence_root=tmp_path, expected_commit_sha="a" * 40)
