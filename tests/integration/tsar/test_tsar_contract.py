"""TSAR contract tests; no installed TSAR binary is required."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
import yaml

from arkhon.core.errors import EvidenceStaleError, EvidenceTamperedError, SecurityError
from arkhon.evidence.integrity import sha256_of
from arkhon.integrations.tsar.verifier import verify_tsar_evidence

REPO_ROOT = Path(__file__).resolve().parents[3]
CONTRACT = REPO_ROOT / "integrations" / "tsar" / "contract.yaml"


def _load_contract() -> dict:
    with CONTRACT.open("r", encoding="utf-8") as stream:
        data = yaml.safe_load(stream)
    assert isinstance(data, dict)
    return data


def test_contract_exists() -> None:
    assert CONTRACT.is_file()


def test_contract_required_fields() -> None:
    data = _load_contract()
    for key in ("version", "provider", "consumer", "handshake", "evidence_contract", "failure_handling"):
        assert key in data


def test_contract_fail_closed() -> None:
    assert _load_contract()["no_trust_without_verification"] is True


def test_contract_failure_modes_never_pass() -> None:
    for mode, spec in _load_contract()["failure_handling"].items():
        assert spec["gate_status"] in {"BLOCKED", "FAIL"}, mode


def test_contract_requires_security_gate() -> None:
    assert "security_gate" in _load_contract()["provider"]["required_for"]


def _valid_payload(tmp_path: Path, commit_sha: str) -> dict:
    artifact = tmp_path / "scan.json"
    artifact.write_text('{"scan": "complete"}', encoding="utf-8")
    executed = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    return {
        "evidence_id": "EVID-TSAR-ABC123", "tsar_version": "1.2.3",
        "commit_sha": commit_sha, "executed_at": executed, "status": "PASS",
        "rule_ids": [
            "TSAR-SEC-SECRET-001", "TSAR-SEC-CRYPTO-001",
            "TSAR-SEC-DEP-001", "TSAR-SEC-ASVS-V2",
        ],
        "summary": {"critical": 0, "high": 0, "medium": 2, "low": 5},
        "artifacts": [{"path": "scan.json", "sha256": sha256_of(artifact)}],
    }


def test_verifier_accepts_valid_payload(tmp_path: Path) -> None:
    sha = "a" * 40
    result = verify_tsar_evidence(_valid_payload(tmp_path, sha), expected_commit_sha=sha, evidence_root=tmp_path)
    assert result.commit_sha == sha
    assert result.status == "PASS"


def test_verifier_rejects_commit_mismatch(tmp_path: Path) -> None:
    with pytest.raises(EvidenceTamperedError, match="commit"):
        verify_tsar_evidence(_valid_payload(tmp_path, "a" * 40), expected_commit_sha="b" * 40, evidence_root=tmp_path)


def test_verifier_rejects_version_out_of_range(tmp_path: Path) -> None:
    payload = _valid_payload(tmp_path, "a" * 40)
    payload["tsar_version"] = "0.9.0"
    with pytest.raises(SecurityError, match="out of range"):
        verify_tsar_evidence(payload, expected_commit_sha="a" * 40, evidence_root=tmp_path)


def test_verifier_rejects_missing_required_rule(tmp_path: Path) -> None:
    payload = _valid_payload(tmp_path, "a" * 40)
    payload["rule_ids"] = ["TSAR-SEC-SECRET-001"]
    with pytest.raises(SecurityError, match="missing required"):
        verify_tsar_evidence(payload, expected_commit_sha="a" * 40, evidence_root=tmp_path)


def test_verifier_rejects_stale_evidence(tmp_path: Path) -> None:
    payload = _valid_payload(tmp_path, "a" * 40)
    payload["executed_at"] = "2020-01-01T00:00:00Z"
    with pytest.raises(EvidenceStaleError):
        verify_tsar_evidence(payload, expected_commit_sha="a" * 40, evidence_root=tmp_path)


def test_verifier_rejects_future_timestamp(tmp_path: Path) -> None:
    payload = _valid_payload(tmp_path, "a" * 40)
    payload["executed_at"] = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
    with pytest.raises(EvidenceStaleError, match="future"):
        verify_tsar_evidence(payload, expected_commit_sha="a" * 40, evidence_root=tmp_path)


def test_verifier_rejects_path_traversal(tmp_path: Path) -> None:
    payload = _valid_payload(tmp_path, "a" * 40)
    payload["artifacts"][0]["path"] = "../outside.json"
    with pytest.raises(EvidenceTamperedError, match="escapes"):
        verify_tsar_evidence(payload, expected_commit_sha="a" * 40, evidence_root=tmp_path)


def test_verifier_rejects_tampered_artifact(tmp_path: Path) -> None:
    payload = _valid_payload(tmp_path, "a" * 40)
    (tmp_path / "scan.json").write_text("tampered", encoding="utf-8")
    with pytest.raises(EvidenceTamperedError, match="hash mismatch"):
        verify_tsar_evidence(payload, expected_commit_sha="a" * 40, evidence_root=tmp_path)


def test_verifier_rejects_critical_findings(tmp_path: Path) -> None:
    payload = _valid_payload(tmp_path, "a" * 40)
    payload["summary"]["critical"] = 1
    with pytest.raises(SecurityError, match="critical/high"):
        verify_tsar_evidence(payload, expected_commit_sha="a" * 40, evidence_root=tmp_path)


def test_verifier_rejects_missing_fields(tmp_path: Path) -> None:
    payload = _valid_payload(tmp_path, "a" * 40)
    del payload["rule_ids"]
    with pytest.raises(SecurityError, match="missing fields"):
        verify_tsar_evidence(payload, expected_commit_sha="a" * 40, evidence_root=tmp_path)
