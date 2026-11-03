"""Tests for the JSON reporter."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from arkhon.core.errors import EvidenceError
from arkhon.reporting.json_reporter import SECTION_MAP, JsonReporter


def _write_evidence(
    project: Path,
    domain: str,
    evidence_id: str,
    status: str = "PASS",
) -> Path:
    target_dir = project / ".arkhon" / "evidence" / domain
    target_dir.mkdir(parents=True, exist_ok=True)
    artifact = project / "x"
    artifact.write_text("report evidence", encoding="utf-8")
    target = target_dir / f"{evidence_id}.json"
    target.write_text(
        json.dumps(
            {
                "evidence_id": evidence_id,
                "source": "arkhon",
                "source_version": "0.1.0.dev1",
                "commit_sha": "a" * 40,
                "executed_at": "2026-11-01T00:00:00Z",
                "status": status,
                "artifacts": [{"path": "x", "sha256": hashlib.sha256(artifact.read_bytes()).hexdigest()}],
            }
        ),
        encoding="utf-8",
    )
    return target


def test_build_fails_with_no_evidence(tmp_path: Path) -> None:
    with pytest.raises(EvidenceError, match="no evidence"):
        JsonReporter().build(tmp_path)


def test_build_aggregates_sections(tmp_path: Path) -> None:
    _write_evidence(tmp_path, "testing", "EVID-ARKHON-1", "PASS")
    _write_evidence(tmp_path, "software-security", "EVID-TSAR-2", "PASS")
    report = JsonReporter().build(tmp_path)
    assert report["sections"]["testing"]["status"] == "PASS"
    assert report["sections"]["security"]["status"] == "PASS"
    assert "EVID-ARKHON-1" in report["sections"]["testing"]["evidence_ids"]


def test_evidence_ids_are_isolated_by_section(tmp_path: Path) -> None:
    _write_evidence(tmp_path, "testing", "EVID-TEST")
    _write_evidence(tmp_path, "software-security", "EVID-SEC")
    report = JsonReporter().build(tmp_path)
    assert report["sections"]["testing"]["evidence_ids"] == ["EVID-TEST"]
    assert report["sections"]["security"]["evidence_ids"] == ["EVID-SEC"]


def test_fail_status_takes_precedence_over_blocked(tmp_path: Path) -> None:
    _write_evidence(tmp_path, "testing", "EVID-A-FAIL", "FAIL")
    _write_evidence(tmp_path, "testing", "EVID-B-BLOCKED", "BLOCKED")
    report = JsonReporter().build(tmp_path)
    assert report["sections"]["testing"]["status"] == "FAIL"
    assert report["final_decision"] == "REJECTED"


def test_build_final_decision_approved(tmp_path: Path) -> None:
    _write_evidence(tmp_path, "testing", "EVID-A", "PASS")
    assert JsonReporter().build(tmp_path)["final_decision"] == "PENDING_EVIDENCE"


def test_build_final_decision_rejected_on_fail(tmp_path: Path) -> None:
    _write_evidence(tmp_path, "testing", "EVID-A", "FAIL")
    assert JsonReporter().build(tmp_path)["final_decision"] == "REJECTED"


def test_build_final_decision_pending_on_blocked(tmp_path: Path) -> None:
    _write_evidence(tmp_path, "testing", "EVID-A", "BLOCKED")
    assert JsonReporter().build(tmp_path)["final_decision"] == "PENDING_EVIDENCE"


def test_write_creates_file(tmp_path: Path) -> None:
    _write_evidence(tmp_path, "testing", "EVID-A", "PASS")
    output = tmp_path / "out"
    path = JsonReporter().write(tmp_path, output)
    assert path.is_file()
    assert json.loads(path.read_text(encoding="utf-8"))["project"] == tmp_path.name


def test_build_rejects_invalid_commit_and_ignores_unknown_domain(tmp_path: Path) -> None:
    _write_evidence(tmp_path, "unmapped-domain", "EVID-UNKNOWN")
    report = JsonReporter().build(tmp_path)
    assert report["final_decision"] == "PENDING_EVIDENCE"
    (tmp_path / ".arkhon" / "evidence" / "testing").mkdir(parents=True)
    (tmp_path / ".arkhon" / "evidence" / "testing" / "bad.json").write_text(
        json.dumps({"evidence_id": "bad", "commit_sha": "short", "status": "PASS"}),
        encoding="utf-8",
    )
    with pytest.raises(EvidenceError, match="valid commit_sha"):
        JsonReporter().build(tmp_path)


def test_build_approves_only_when_every_section_has_verified_evidence(tmp_path: Path) -> None:
    for index, domain in enumerate(SECTION_MAP):
        _write_evidence(tmp_path, domain, f"EVID-ALL-{index}")
    report = JsonReporter().build(tmp_path)
    assert report["final_decision"] == "APPROVED"
    assert all(section["status"] == "PASS" for section in report["sections"].values())


def test_build_rejects_mixed_commit_evidence(tmp_path: Path) -> None:
    _write_evidence(tmp_path, "testing", "EVID-A")
    target = _write_evidence(tmp_path, "software-security", "EVID-B")
    data = json.loads(target.read_text(encoding="utf-8"))
    data["commit_sha"] = "c" * 40
    target.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(EvidenceError, match="commit mismatch"):
        JsonReporter().build(tmp_path)


def test_build_rejects_tampered_artifact(tmp_path: Path) -> None:
    _write_evidence(tmp_path, "testing", "EVID-A")
    (tmp_path / "x").write_text("modified", encoding="utf-8")
    with pytest.raises(EvidenceError, match="verification failed"):
        JsonReporter().build(tmp_path)


def test_build_rejects_stale_evidence(tmp_path: Path) -> None:
    target = _write_evidence(tmp_path, "testing", "EVID-STALE")
    data = json.loads(target.read_text(encoding="utf-8"))
    data["executed_at"] = "2026-01-01T00:00:00Z"
    target.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(EvidenceError, match="stale"):
        JsonReporter().build(tmp_path)
