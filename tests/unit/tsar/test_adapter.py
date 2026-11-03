"""Tests for the TSAR adapter."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

from arkhon.integrations.tsar.adapter import TsarAdapter, TsarConfig


def test_info() -> None:
    info = TsarAdapter().info
    assert info.id == "tsar"
    assert info.kind == "security"
    assert "audit" in info.capabilities


def test_health_check_missing_binary() -> None:
    with patch("shutil.which", return_value=None):
        assert TsarAdapter().health_check() is False


def test_health_check_binary_present() -> None:
    with (
        patch("shutil.which", return_value="/usr/local/bin/tsar"),
        patch("subprocess.run") as mock_run,
    ):
        mock_run.return_value.returncode = 0
        assert TsarAdapter().health_check() is True


def test_health_check_version_fails() -> None:
    with (
        patch("shutil.which", return_value="/usr/local/bin/tsar"),
        patch("subprocess.run") as mock_run,
    ):
        mock_run.return_value.returncode = 1
        assert TsarAdapter().health_check() is False


def test_audit_missing_binary(tmp_path: Path) -> None:
    with patch("shutil.which", return_value=None):
        result = TsarAdapter().audit(tmp_path, "a" * 40)
    assert not result.ok
    assert "not found" in result.reason.lower()


def test_audit_success(tmp_path: Path) -> None:
    payload = {
        "evidence_id": "EVID-TSAR-001",
        "tsar_version": "1.2.0",
        "commit_sha": "a" * 40,
        "executed_at": "2026-11-01T00:00:00Z",
        "status": "PASS",
        "rule_ids": ["TSAR-SEC-SECRET-001"],
        "summary": {"critical": 0, "high": 0, "medium": 1, "low": 2},
        "artifacts": [],
    }

    def _mock_run(cmd, **kwargs):
        # Write the output file when tsar runs
        output_idx = cmd.index("--output-file") + 1
        Path(cmd[output_idx]).write_text(json.dumps(payload), encoding="utf-8")
        result = type("R", (), {"returncode": 0, "stdout": "", "stderr": ""})()
        return result

    with (
        patch("shutil.which", return_value="/usr/local/bin/tsar"),
        patch("subprocess.run", side_effect=_mock_run),
    ):
        result = TsarAdapter().audit(tmp_path, "a" * 40)

    assert result.ok
    assert result.payload["evidence_id"] == "EVID-TSAR-001"
    assert len(result.artifacts) == 1
    assert result.artifacts[0].is_file()


def test_audit_nonzero_exit(tmp_path: Path) -> None:
    def _mock_run(cmd, **kwargs):
        result = type("R", (), {"returncode": 2, "stdout": "", "stderr": "error"})()
        return result

    with (
        patch("shutil.which", return_value="/usr/local/bin/tsar"),
        patch("subprocess.run", side_effect=_mock_run),
    ):
        result = TsarAdapter().audit(tmp_path, "a" * 40)

    assert not result.ok
    assert "exited with 2" in result.reason


def test_audit_invalid_json(tmp_path: Path) -> None:
    def _mock_run(cmd, **kwargs):
        output_idx = cmd.index("--output-file") + 1
        Path(cmd[output_idx]).write_text("not json", encoding="utf-8")
        result = type("R", (), {"returncode": 0, "stdout": "", "stderr": ""})()
        return result

    with (
        patch("shutil.which", return_value="/usr/local/bin/tsar"),
        patch("subprocess.run", side_effect=_mock_run),
    ):
        result = TsarAdapter().audit(tmp_path, "a" * 40)

    assert not result.ok
    assert "not valid JSON" in result.reason


def test_audit_timeout(tmp_path: Path) -> None:
    import subprocess

    with (
        patch("shutil.which", return_value="/usr/local/bin/tsar"),
        patch("subprocess.run", side_effect=subprocess.TimeoutExpired("tsar", 1)),
    ):
        result = TsarAdapter().audit(tmp_path, "a" * 40)

    assert not result.ok
    assert "timed out" in result.reason.lower()


def test_config_defaults() -> None:
    cfg = TsarConfig()
    assert cfg.binary == "tsar"
    assert cfg.minimum_version == "1.1.0"
    assert cfg.timeout_seconds == 1800
