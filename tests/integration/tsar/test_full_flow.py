"""End-to-end adapter/verifier flow using the actual TSAR SARIF CLI contract."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from unittest.mock import patch

from arkhon.integrations.tsar.adapter import TsarAdapter
from arkhon.integrations.tsar.verifier import TsarFindingsError, verify_tsar_evidence

COMMIT = "a" * 40


def _sarif(*, level: str | None = None) -> dict:
    results = []
    if level:
        results.append(
            {
                "ruleId": "tsar/secret",
                "level": level,
                "message": {"text": "scanner finding"},
            }
        )
    return {
        "version": "2.1.0",
        "runs": [
            {
                "tool": {
                    "driver": {
                        "name": "TSAR",
                        "version": "1.1.1",
                        "rules": [{"id": "tsar/secret"}] if level else [],
                    }
                },
                "results": results,
            }
        ],
    }


def _install_fake_cli(monkeypatch, payload: dict, code: int = 0) -> None:
    monkeypatch.setattr(
        "arkhon.integrations.tsar.adapter.shutil.which", lambda _name: "/usr/bin/tsar"
    )

    def fake_run(command, **kwargs):
        output = Path(command[command.index("--output") + 1])
        output.write_text(json.dumps(payload), encoding="utf-8")
        return subprocess.CompletedProcess(command, code, "", "")

    monkeypatch.setattr("arkhon.integrations.tsar.adapter.subprocess.run", fake_run)


def test_full_flow_real_cli_contract_passes_and_binds_commit(tmp_path: Path, monkeypatch) -> None:
    _install_fake_cli(monkeypatch, _sarif())
    response = TsarAdapter().audit(tmp_path, COMMIT)
    assert response.ok
    evidence = verify_tsar_evidence(
        response.payload, expected_commit_sha=COMMIT, evidence_root=tmp_path
    )
    assert evidence.status == "PASS"
    assert evidence.commit_sha == COMMIT
    assert evidence.rule_ids[0] == "TSAR-SCAN-EXECUTED"


def test_full_flow_high_finding_fails(tmp_path: Path, monkeypatch) -> None:
    _install_fake_cli(monkeypatch, _sarif(level="error"), code=1)
    response = TsarAdapter().audit(tmp_path, COMMIT)
    assert response.ok
    try:
        verify_tsar_evidence(response.payload, expected_commit_sha=COMMIT, evidence_root=tmp_path)
    except TsarFindingsError:
        pass
    else:
        raise AssertionError("high-severity TSAR finding was not rejected")


def test_full_flow_tsar_unavailable(tmp_path: Path) -> None:
    with patch("arkhon.integrations.tsar.adapter.shutil.which", return_value=None):
        response = TsarAdapter().audit(tmp_path, COMMIT)
    assert not response.ok
    assert "not found" in response.reason.lower()


def test_full_flow_commit_mismatch(tmp_path: Path, monkeypatch) -> None:
    _install_fake_cli(monkeypatch, _sarif())
    response = TsarAdapter().audit(tmp_path, COMMIT)
    try:
        verify_tsar_evidence(response.payload, expected_commit_sha="b" * 40, evidence_root=tmp_path)
    except Exception as exc:
        assert "commit" in str(exc).lower()
    else:
        raise AssertionError("commit mismatch was accepted")
