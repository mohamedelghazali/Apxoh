"""Tests for arkhon.evidence.integrity."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from arkhon.core.errors import EvidenceError, EvidenceStaleError, EvidenceTamperedError
from arkhon.evidence.integrity import (
    sha256_of,
    verify_artifact,
    verify_bundle,
    verify_freshness,
)


def _write(tmp_path: Path, name: str, content: str) -> Path:
    path = tmp_path / name
    path.write_text(content, encoding="utf-8")
    return path


def _bundle(tmp_path: Path) -> tuple[Path, str]:
    artifact = _write(tmp_path, "art.txt", "content")
    data = {
        "evidence_id": "EVID-TEST-0001", "source": "arkhon",
        "source_version": "0.1.0.dev1", "commit_sha": "a" * 40,
        "executed_at": "2026-11-01T00:00:00Z", "status": "PASS",
        "artifacts": [{"path": "art.txt", "sha256": sha256_of(artifact)}],
    }
    bundle = tmp_path / "bundle.json"
    bundle.write_text(json.dumps(data), encoding="utf-8")
    return bundle, "a" * 40


def test_sha256_is_deterministic(tmp_path: Path) -> None:
    path = _write(tmp_path, "a.txt", "hello")
    assert sha256_of(path) == sha256_of(path)


def test_sha256_differs_for_different_content(tmp_path: Path) -> None:
    first = _write(tmp_path, "a.txt", "hello")
    second = _write(tmp_path, "b.txt", "world")
    assert sha256_of(first) != sha256_of(second)


def test_verify_artifact_ok(tmp_path: Path) -> None:
    path = _write(tmp_path, "a.txt", "hello")
    verify_artifact(path, sha256_of(path))


def test_verify_artifact_missing(tmp_path: Path) -> None:
    with pytest.raises(EvidenceTamperedError, match="missing"):
        verify_artifact(tmp_path / "nope", "a" * 64)


def test_verify_artifact_hash_mismatch(tmp_path: Path) -> None:
    path = _write(tmp_path, "a.txt", "hello")
    with pytest.raises(EvidenceTamperedError, match="hash mismatch"):
        verify_artifact(path, "b" * 64)


def test_verify_bundle_ok(tmp_path: Path) -> None:
    bundle, commit = _bundle(tmp_path)
    verify_bundle(bundle, evidence_root=tmp_path, expected_commit_sha=commit)


def test_verify_bundle_missing(tmp_path: Path) -> None:
    with pytest.raises(EvidenceTamperedError, match="missing"):
        verify_bundle(
            tmp_path / "nope.json", evidence_root=tmp_path, expected_commit_sha="a" * 40,
        )


def test_verify_bundle_commit_mismatch(tmp_path: Path) -> None:
    bundle, _ = _bundle(tmp_path)
    with pytest.raises(EvidenceTamperedError, match="commit mismatch"):
        verify_bundle(bundle, evidence_root=tmp_path, expected_commit_sha="b" * 40)


def test_verify_bundle_artifact_tampered(tmp_path: Path) -> None:
    bundle, commit = _bundle(tmp_path)
    (tmp_path / "art.txt").write_text("TAMPERED", encoding="utf-8")
    with pytest.raises(EvidenceTamperedError, match="hash mismatch"):
        verify_bundle(bundle, evidence_root=tmp_path, expected_commit_sha=commit)


def test_verify_bundle_rejects_path_traversal(tmp_path: Path) -> None:
    bundle, commit = _bundle(tmp_path)
    data = json.loads(bundle.read_text(encoding="utf-8"))
    data["artifacts"][0]["path"] = "../outside.txt"
    bundle.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(EvidenceTamperedError, match="escapes evidence root"):
        verify_bundle(bundle, evidence_root=tmp_path, expected_commit_sha=commit)


def test_freshness_ok() -> None:
    verify_freshness(
        "2026-11-01T00:00:00Z", max_age_hours=168,
        now_iso="2026-11-01T01:00:00Z",
    )


def test_freshness_stale() -> None:
    with pytest.raises(EvidenceStaleError, match="stale"):
        verify_freshness(
            "2026-10-01T00:00:00Z", max_age_hours=168,
            now_iso="2026-11-01T00:00:00Z",
        )


def test_freshness_invalid_timestamp() -> None:
    with pytest.raises(EvidenceError, match="invalid timestamp"):
        verify_freshness("not-a-timestamp", max_age_hours=168)


def test_freshness_future_timestamp_rejected() -> None:
    with pytest.raises(EvidenceError, match="future"):
        verify_freshness(
            "2026-11-02T00:00:00Z", max_age_hours=24,
            now_iso="2026-11-01T00:00:00Z",
        )
