"""Tests for arkhon.evidence.collector."""

from __future__ import annotations

from pathlib import Path

import pytest

from arkhon.core.errors import EvidenceError
from arkhon.evidence.collector import EvidenceCollector


def _write(tmp_path: Path, name: str, content: str = "data") -> Path:
    path = tmp_path / name
    path.write_text(content, encoding="utf-8")
    return path


def test_new_evidence_produces_id(tmp_path: Path) -> None:
    draft = EvidenceCollector(root=tmp_path).new_evidence(
        source="arkhon",
        source_version="0.1.0.dev1",
        commit_sha="a" * 40,
        status="PASS",
    )
    assert draft.evidence_id.startswith("EVID-ARKHON-")


def test_invalid_commit_sha_rejected(tmp_path: Path) -> None:
    with pytest.raises(EvidenceError, match="invalid commit SHA"):
        EvidenceCollector(root=tmp_path).new_evidence(
            source="arkhon",
            source_version="0.1.0.dev1",
            commit_sha="not-a-sha",
            status="PASS",
        )


def test_add_artifact_computes_hash(tmp_path: Path) -> None:
    draft = EvidenceCollector(root=tmp_path).new_evidence(
        source="arkhon",
        source_version="0.1.0.dev1",
        commit_sha="b" * 40,
        status="PASS",
    )
    draft.add_artifact(_write(tmp_path, "test.xml", "<tests/>"))
    assert len(draft.artifacts) == 1
    assert len(draft.artifacts[0].sha256) == 64


def test_add_missing_artifact_raises(tmp_path: Path) -> None:
    draft = EvidenceCollector(root=tmp_path).new_evidence(
        source="arkhon",
        source_version="0.1.0.dev1",
        commit_sha="c" * 40,
        status="PASS",
    )
    with pytest.raises(EvidenceError, match="not found"):
        draft.add_artifact(tmp_path / "missing.txt")


def test_to_evidence_requires_artifact(tmp_path: Path) -> None:
    draft = EvidenceCollector(root=tmp_path).new_evidence(
        source="arkhon",
        source_version="0.1.0.dev1",
        commit_sha="d" * 40,
        status="PASS",
    )
    with pytest.raises(EvidenceError, match="at least one artifact"):
        draft.to_evidence()


def test_to_evidence_tsar_requires_metadata(tmp_path: Path) -> None:
    draft = EvidenceCollector(root=tmp_path).new_evidence(
        source="tsar",
        source_version="1.1.0",
        commit_sha="e" * 40,
        status="PASS",
    )
    draft.add_artifact(_write(tmp_path, "scan.json", "{}"))
    with pytest.raises(EvidenceError, match="tsar_metadata"):
        draft.to_evidence()


def test_to_evidence_success(tmp_path: Path) -> None:
    draft = EvidenceCollector(root=tmp_path).new_evidence(
        source="arkhon",
        source_version="0.1.0.dev1",
        commit_sha="f" * 40,
        status="PASS",
    )
    draft.add_artifact(_write(tmp_path, "test.xml", "<tests/>"))
    draft.summary = {"pass": 10, "fail": 0, "blocked": 0}
    evidence = draft.to_evidence()
    assert evidence["status"] == "PASS"
    assert len(evidence["artifacts"]) == 1
    assert evidence["summary"]["pass"] == 10


def test_to_evidence_invalid_status(tmp_path: Path) -> None:
    draft = EvidenceCollector(root=tmp_path).new_evidence(
        source="arkhon",
        source_version="0.1.0.dev1",
        commit_sha="a" * 40,
        status="PASS",
    )
    draft.add_artifact(_write(tmp_path, "t.xml", "x"))
    draft.status = "WHATEVER"
    with pytest.raises(EvidenceError, match="invalid status"):
        draft.to_evidence()


def test_artifact_outside_explicit_root_is_rejected(tmp_path: Path) -> None:
    draft = EvidenceCollector(root=tmp_path / "root").new_evidence(
        source="arkhon",
        source_version="0.1.0.dev1",
        commit_sha="a" * 40,
        status="PASS",
    )
    artifact = _write(tmp_path, "outside.txt")
    draft.add_artifact(artifact)
    with pytest.raises(EvidenceError, match="outside evidence root"):
        draft.artifacts[0].to_dict(root=tmp_path / "root")


def test_to_evidence_rejects_artifact_outside_collector_root(tmp_path: Path) -> None:
    root = tmp_path / "project"
    root.mkdir()
    outside = _write(tmp_path, "outside.txt")
    draft = EvidenceCollector(root=root).new_evidence(
        source="arkhon",
        source_version="0.1.0.dev1",
        commit_sha="a" * 40,
        status="PASS",
    )
    draft.add_artifact(outside)
    with pytest.raises(EvidenceError, match="outside evidence root"):
        draft.to_evidence()


def test_to_evidence_stores_relative_artifact_paths(tmp_path: Path) -> None:
    artifact = _write(tmp_path, "inside.txt")
    draft = EvidenceCollector(root=tmp_path).new_evidence(
        source="arkhon",
        source_version="0.1.0.dev1",
        commit_sha="b" * 40,
        status="PASS",
    )
    draft.add_artifact(artifact)
    evidence = draft.to_evidence()
    assert evidence["artifacts"][0]["path"] == "inside.txt"
