from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest

from arkhon.core.errors import (
    EvidenceError,
    EvidenceStaleError,
    EvidenceTamperedError,
    SecurityError,
)
from arkhon.evidence.collector import Artifact, EvidenceCollector
from arkhon.evidence.integrity import sha256_of
from arkhon.integrations.tsar.verifier import (
    REQUIRED_RULE_IDS,
    _check_artifacts,
    _check_freshness,
    _maximum_version_tuple,
    _parse_tsar_payload,
    verify_tsar_evidence,
)


def test_collector_validation_and_optional_evidence_fields(tmp_path: Path) -> None:
    collector = EvidenceCollector(tmp_path)
    assert collector.root == tmp_path.resolve()
    with pytest.raises(EvidenceError, match="invalid evidence source"):
        collector.new_evidence(
            source="unknown", source_version="1", commit_sha="a" * 40, status="PASS"
        )  # type: ignore[arg-type]
    with pytest.raises(EvidenceError, match="invalid commit SHA"):
        collector.new_evidence(
            source="arkhon", source_version="1", commit_sha="A" * 40, status="PASS"
        )
    with pytest.raises(EvidenceError, match="source_version"):
        collector.new_evidence(
            source="arkhon", source_version=" ", commit_sha="a" * 40, status="PASS"
        )
    artifact = tmp_path / "artifact.bin"
    artifact.write_bytes(b"payload")
    item = Artifact(artifact, sha256_of(artifact))
    assert item.to_dict(root=tmp_path)["path"] == "artifact.bin"
    draft = collector.new_evidence(
        source="tsar", source_version="1.2.0", commit_sha="a" * 40, status="PASS"
    )
    draft.add_artifact(artifact)
    draft.summary = {"critical": 0}
    draft.rule_ids = ["TSAR-SEC-SECRET-001"]
    draft.tsar_metadata = {"version": "1.2.0"}
    draft.notes = "verified"
    payload = draft.to_evidence()
    assert payload["summary"] == {"critical": 0}
    assert payload["rule_ids"] == ["TSAR-SEC-SECRET-001"]
    assert payload["tsar_metadata"] == {"version": "1.2.0"}
    assert payload["notes"] == "verified"


def _payload(root: Path) -> dict:
    artifact = root / "scan.json"
    artifact.write_text("{}", encoding="utf-8")
    return {
        "evidence_id": "E1",
        "tsar_version": "1.2.0",
        "commit_sha": "a" * 40,
        "executed_at": "2026-11-03T00:00:00Z",
        "status": "PASS",
        "rule_ids": list(REQUIRED_RULE_IDS),
        "findings": [],
        "summary": {"critical": 0, "high": 0},
        "artifacts": [{"path": "scan.json", "sha256": sha256_of(artifact)}],
    }


def test_tsar_payload_rejects_identity_rules_and_artifact_shapes(tmp_path: Path) -> None:
    payload = _payload(tmp_path)
    payload["evidence_id"] = ""
    with pytest.raises(SecurityError, match="identity"):
        _parse_tsar_payload(payload)
    payload = _payload(tmp_path)
    payload["rule_ids"] = ["", 2]
    with pytest.raises(SecurityError, match="rule_ids"):
        _parse_tsar_payload(payload)
    payload = _payload(tmp_path)
    payload["summary"] = {1: 0}
    with pytest.raises(SecurityError, match="summary counts"):
        _parse_tsar_payload(payload)
    payload = _payload(tmp_path)
    payload["artifacts"] = ["not-an-object"]
    with pytest.raises(SecurityError, match="malformed"):
        _parse_tsar_payload(payload)
    payload = _payload(tmp_path)
    payload["artifacts"] = [{"path": "", "sha256": "A" * 64}]
    with pytest.raises(SecurityError, match="relative path"):
        _parse_tsar_payload(payload)


def test_tsar_version_freshness_and_artifact_failure_paths(tmp_path: Path) -> None:
    assert _maximum_version_tuple("1.2.3") == (1, 2, 3)
    with pytest.raises(SecurityError, match="invalid version bound"):
        _maximum_version_tuple("01.x.x")
    with pytest.raises(SecurityError, match="invalid version bound"):
        _maximum_version_tuple("1.x.2")
    with pytest.raises(EvidenceStaleError, match="future"):
        _check_freshness("2026-11-04T00:00:00Z", now=datetime(2026, 11, 3, tzinfo=UTC))
    with pytest.raises(EvidenceStaleError, match="invalid executed_at"):
        _check_freshness(None)  # type: ignore[arg-type]
    with pytest.raises(EvidenceTamperedError, match="missing"):
        _check_artifacts((("missing.json", "a" * 64),), tmp_path)
    artifact = tmp_path / "hash.json"
    artifact.write_text("actual", encoding="utf-8")
    with pytest.raises(EvidenceTamperedError, match="hash mismatch"):
        _check_artifacts((("hash.json", "b" * 64),), tmp_path)
    payload = _payload(tmp_path)
    payload["commit_sha"] = "bad"
    with pytest.raises(SecurityError, match="malformed"):
        verify_tsar_evidence(
            payload, expected_commit_sha="a" * 40, evidence_root=tmp_path
        )
