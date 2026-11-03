"""Unit tests for the TSAR verifier — edge cases."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from arkhon.core.errors import (
    EvidenceStaleError,
    EvidenceTamperedError,
    SecurityError,
)
from arkhon.evidence.integrity import sha256_of
from arkhon.integrations.tsar.verifier import (
    FRESHNESS_HOURS,
    REQUIRED_RULE_IDS,
    _check_freshness,
    _check_required_rules,
    _check_version,
    _maximum_version_tuple,
    _parse_tsar_payload,
    verify_tsar_evidence,
)


def test_check_version_valid() -> None:
    _check_version("1.2.0", "1.1.0", "2.0.0")


def test_check_version_too_old() -> None:
    with pytest.raises(SecurityError, match="out of range"):
        _check_version("0.9.0", "1.1.0", "2.0.0")


def test_check_version_too_new() -> None:
    with pytest.raises(SecurityError, match="out of range"):
        _check_version("2.0.0", "1.1.0", "2.0.0")


def test_check_version_wildcard_max() -> None:
    _check_version("1.9.9", "1.1.0", "1.x.x")


def test_check_version_wildcard_rejects_2x() -> None:
    with pytest.raises(SecurityError):
        _check_version("2.0.0", "1.1.0", "1.x.x")


def test_check_version_invalid_string() -> None:
    with pytest.raises(SecurityError, match="invalid version"):
        _check_version("abc", "1.0.0", "2.0.0")


def test_check_freshness_ok() -> None:
        now = datetime(2026, 11, 2, 12, 0, 0, tzinfo=UTC)
    _check_freshness("2026-11-02T00:00:00Z", now=now)


def test_check_freshness_stale() -> None:
    from datetime import datetime

    now = datetime(2026, 11, 20, 0, 0, 0, tzinfo=UTC)
    with pytest.raises(EvidenceStaleError):
        _check_freshness("2026-11-01T00:00:00Z", now=now)


def test_check_freshness_boundary() -> None:
        executed = "2026-11-01T00:00:00Z"
    executed_dt = datetime(2026, 11, 1, tzinfo=UTC)

    just_at_limit = executed_dt + timedelta(hours=FRESHNESS_HOURS)
    _check_freshness(executed, now=just_at_limit)

    just_past = executed_dt + timedelta(hours=FRESHNESS_HOURS + 1)
    with pytest.raises(EvidenceStaleError):
        _check_freshness(executed, now=just_past)


def test_check_freshness_invalid() -> None:
    with pytest.raises(EvidenceStaleError, match="invalid executed_at"):
        _check_freshness("not-a-timestamp")


def test_check_required_rules_present() -> None:
    _check_required_rules(REQUIRED_RULE_IDS)


def test_check_required_rules_missing() -> None:
    with pytest.raises(SecurityError, match="missing required"):
        _check_required_rules(("TSAR-SEC-SECRET-001",))


def test_parse_payload_missing_field() -> None:
    with pytest.raises(SecurityError, match="missing fields"):
        _parse_tsar_payload({"evidence_id": "x"})


def test_parse_payload_malformed_artifact() -> None:
    payload = {
        "evidence_id": "EVID-1",
        "tsar_version": "1.2.0",
        "commit_sha": "a" * 40,
        "executed_at": "2026-11-01T00:00:00Z",
        "status": "PASS",
        "rule_ids": list(REQUIRED_RULE_IDS),
        "summary": {"critical": 0, "high": 0},
        "artifacts": [{"path": "x"}],
    }
    with pytest.raises(SecurityError) as exc_info:
        _parse_tsar_payload(payload)
    message = str(exc_info.value).lower()
    assert "artifact" in message, f"expected 'artifact' in error message, got: {exc_info.value!r}"


def _valid_payload(tmp_path: Path, commit_sha: str = "a" * 40) -> dict:
    artifact = tmp_path / "scan.json"
    artifact.write_text('{"ok": true}', encoding="utf-8")
    return {
        "evidence_id": "EVID-TSAR-001",
        "tsar_version": "1.2.0",
        "commit_sha": commit_sha,
        "executed_at": "2026-11-01T00:00:00Z",
        "status": "PASS",
        "rule_ids": list(REQUIRED_RULE_IDS),
        "summary": {"critical": 0, "high": 0, "medium": 2, "low": 3},
        "artifacts": [{"path": "scan.json", "sha256": sha256_of(artifact)}],
    }


def test_verify_valid(tmp_path: Path) -> None:
    evidence = verify_tsar_evidence(
        _valid_payload(tmp_path),
        expected_commit_sha="a" * 40,
        evidence_root=tmp_path,
    )
    assert evidence.status == "PASS"
    assert evidence.commit_sha == "a" * 40


def test_verify_commit_mismatch(tmp_path: Path) -> None:
    with pytest.raises(EvidenceTamperedError, match="commit"):
        verify_tsar_evidence(
            _valid_payload(tmp_path, "a" * 40),
            expected_commit_sha="b" * 40,
            evidence_root=tmp_path,
        )


def test_verify_tampered_artifact(tmp_path: Path) -> None:
    payload = _valid_payload(tmp_path)
    (tmp_path / "scan.json").write_text("TAMPERED", encoding="utf-8")
    with pytest.raises(EvidenceTamperedError, match="hash mismatch"):
        verify_tsar_evidence(
            payload,
            expected_commit_sha="a" * 40,
            evidence_root=tmp_path,
        )


def test_verify_critical_findings(tmp_path: Path) -> None:
    payload = _valid_payload(tmp_path)
    payload["summary"]["critical"] = 1
    with pytest.raises(SecurityError, match="critical/high"):
        verify_tsar_evidence(
            payload,
            expected_commit_sha="a" * 40,
            evidence_root=tmp_path,
        )


def test_verify_invalid_status(tmp_path: Path) -> None:
    payload = _valid_payload(tmp_path)
    payload["status"] = "MAYBE"
    with pytest.raises(SecurityError, match="invalid TSAR status"):
        verify_tsar_evidence(
            payload,
            expected_commit_sha="a" * 40,
            evidence_root=tmp_path,
        )


def test_parse_payload_rejects_invalid_shapes_and_summary() -> None:
    from arkhon.core.errors import SecurityError
    from arkhon.integrations.tsar.verifier import _parse_tsar_payload

    with pytest.raises(SecurityError, match="object"):
        _parse_tsar_payload([])  # type: ignore[arg-type]
    payload = {
        "evidence_id": "E1", "tsar_version": "1.2.0", "commit_sha": "a" * 40,
        "executed_at": "2026-11-01T00:00:00Z", "status": "PASS",
        "rule_ids": list(REQUIRED_RULE_IDS), "summary": {"critical": True},
        "artifacts": [{"path": "a", "sha256": "a" * 64}],
    }
    with pytest.raises(SecurityError, match="summary counts"):
        _parse_tsar_payload(payload)
    payload["summary"] = []
    with pytest.raises(SecurityError, match="summary"):
        _parse_tsar_payload(payload)
    payload["summary"] = {"critical": 0}
    payload["artifacts"] = []
    with pytest.raises(SecurityError, match="artifacts"):
        _parse_tsar_payload(payload)


def test_verify_rejects_invalid_commit_version_time_and_paths(tmp_path: Path) -> None:
        with pytest.raises(SecurityError, match="expected_commit_sha"):
        verify_tsar_evidence({}, expected_commit_sha="bad", evidence_root=tmp_path)
    with pytest.raises(SecurityError, match="invalid version bound"):
        _maximum_version_tuple("x.1.x")
    with pytest.raises(EvidenceStaleError, match="timezone"):
        _check_freshness("2026-11-01T00:00:00")
    with pytest.raises(ValueError, match="timezone-aware"):
        _check_freshness(
            "2026-11-01T00:00:00Z", now=datetime(2026, 11, 2)
        )
    payload = _valid_payload(tmp_path)
    payload["artifacts"][0]["path"] = "../outside.json"
    with pytest.raises(EvidenceTamperedError, match="escapes"):
        verify_tsar_evidence(
            payload, expected_commit_sha="a" * 40, evidence_root=tmp_path
        )
