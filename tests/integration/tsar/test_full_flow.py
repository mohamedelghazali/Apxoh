"""End-to-end TSAR flow tests using the documented stdout JSON contract.

No TSAR executable is required; subprocess is replaced with a deterministic
fake that emits the same JSON transport documented in integrations/tsar/contract.yaml.
"""
from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from arkhon.evidence.integrity import sha256_of
from arkhon.integrations.tsar.adapter import TsarAdapter
from arkhon.integrations.tsar.verifier import REQUIRED_RULE_IDS, verify_tsar_evidence


def _make_tsar_output(
    commit_sha: str,
    artifact_path: Path,
    status: str = "PASS",
    summary: dict | None = None,
) -> dict:
    if summary is None:
        summary = {"critical": 0, "high": 0, "medium": 1, "low": 2}
    return {
        "evidence_id": "EVID-TSAR-FULLFLOW",
        "tsar_version": "1.2.5",
        "commit_sha": commit_sha,
        "executed_at": "2026-11-01T00:00:00Z",
        "status": status,
        "rule_ids": list(REQUIRED_RULE_IDS),
        "summary": summary,
        "artifacts": [{"path": artifact_path.name, "sha256": sha256_of(artifact_path)}],
    }


def _setup_tsar_mock(payload: dict):
    def _fake_run(cmd, **kwargs):
        assert cmd[cmd.index("--output") + 1] == "json"
        assert "--commit" in cmd
        return SimpleNamespace(returncode=0, stdout=json.dumps(payload), stderr="")
    return _fake_run


def _artifact_in_evidence_dir(project: Path) -> Path:
    evidence_dir = project / ".arkhon" / "evidence" / "security"
    evidence_dir.mkdir(parents=True, exist_ok=True)
    artifact = evidence_dir / "scan.json"
    artifact.write_text('{"findings": []}', encoding="utf-8")
    return artifact


def test_full_flow_pass(tmp_path: Path) -> None:
    commit = "a" * 40
    artifact = _artifact_in_evidence_dir(tmp_path)
    payload = _make_tsar_output(commit, artifact)
    with patch("shutil.which", return_value="/usr/local/bin/tsar"), \
         patch("subprocess.run", side_effect=_setup_tsar_mock(payload)):
        result = TsarAdapter().audit(tmp_path, commit)

    assert result.ok
    evidence_dir = tmp_path / ".arkhon" / "evidence" / "security"
    evidence = verify_tsar_evidence(
        result.payload, expected_commit_sha=commit, evidence_root=evidence_dir,
    )
    assert evidence.status == "PASS"
    assert evidence.evidence_id == "EVID-TSAR-FULLFLOW"


def test_full_flow_critical_blocks(tmp_path: Path) -> None:
    commit = "b" * 40
    artifact = _artifact_in_evidence_dir(tmp_path)
    payload = _make_tsar_output(
        commit, artifact, status="FAIL",
        summary={"critical": 3, "high": 0, "medium": 0, "low": 0},
    )
    with patch("shutil.which", return_value="/usr/local/bin/tsar"), \
         patch("subprocess.run", side_effect=_setup_tsar_mock(payload)):
        result = TsarAdapter().audit(tmp_path, commit)

    assert result.ok
    evidence_dir = tmp_path / ".arkhon" / "evidence" / "security"
    with pytest.raises(Exception, match="critical/high"):
        verify_tsar_evidence(
            result.payload, expected_commit_sha=commit, evidence_root=evidence_dir,
        )


def test_full_flow_tsar_unavailable(tmp_path: Path) -> None:
    with patch("shutil.which", return_value=None):
        result = TsarAdapter().audit(tmp_path, "c" * 40)
    assert not result.ok
    assert "not found" in result.reason.lower()


def test_full_flow_wrong_commit(tmp_path: Path) -> None:
    commit = "d" * 40
    wrong_commit = "e" * 40
    artifact = _artifact_in_evidence_dir(tmp_path)
    payload = _make_tsar_output(wrong_commit, artifact)
    with patch("shutil.which", return_value="/usr/local/bin/tsar"), \
         patch("subprocess.run", side_effect=_setup_tsar_mock(payload)):
        result = TsarAdapter().audit(tmp_path, commit)

    assert result.ok
    evidence_dir = tmp_path / ".arkhon" / "evidence" / "security"
    with pytest.raises(Exception, match="commit"):
        verify_tsar_evidence(
            result.payload, expected_commit_sha=commit, evidence_root=evidence_dir,
        )
