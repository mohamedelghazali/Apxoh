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


def test_version_success_and_failures(monkeypatch) -> None:
    monkeypatch.setattr("arkhon.integrations.tsar.adapter.shutil.which", lambda _name: None)
    from arkhon.core.errors import SecurityError
    import pytest
    with pytest.raises(SecurityError, match="not found"):
        TsarAdapter().version()
    monkeypatch.setattr(
        "arkhon.integrations.tsar.adapter.shutil.which", lambda _name: "/usr/bin/tsar"
    )
    monkeypatch.setattr(
        "arkhon.integrations.tsar.adapter.subprocess.run",
        lambda *args, **kwargs: type("Result", (), {
            "returncode": 1, "stdout": "", "stderr": "failed"
        })(),
    )
    with pytest.raises(SecurityError, match="failed"):
        TsarAdapter().version()
    monkeypatch.setattr(
        "arkhon.integrations.tsar.adapter.subprocess.run",
        lambda *args, **kwargs: type("Result", (), {
            "returncode": 0, "stdout": "TSAR 1.2.0", "stderr": ""
        })(),
    )
    assert TsarAdapter().version() == "TSAR 1.2.0"


def test_audit_rejects_invalid_commit_and_missing_project(tmp_path: Path, monkeypatch) -> None:
    adapter = TsarAdapter()
    assert "invalid commit SHA" in adapter.audit(tmp_path, "bad").reason
    monkeypatch.setattr(
        "arkhon.integrations.tsar.adapter.shutil.which", lambda _name: "/usr/bin/tsar"
    )
    assert "project directory not found" in adapter.audit(
        tmp_path / "missing", "a" * 40
    ).reason


def test_audit_rejects_non_object_json(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(
        "arkhon.integrations.tsar.adapter.shutil.which", lambda _name: "/usr/bin/tsar"
    )
    monkeypatch.setattr(
        "arkhon.integrations.tsar.adapter.subprocess.run",
        lambda *args, **kwargs: type("Result", (), {
            "returncode": 0, "stdout": "[]", "stderr": ""
        })(),
    )
    result = TsarAdapter().audit(tmp_path, "a" * 40)
    assert not result.ok
    assert "must be an object" in result.reason


def test_audit_rejects_different_existing_evidence(tmp_path: Path, monkeypatch) -> None:
    import json

    commit = "a" * 40
    target_dir = tmp_path / ".arkhon" / "evidence" / "security"
    target_dir.mkdir(parents=True)
    target = target_dir / f"tsar-{commit[:12]}.json"
    target.write_text(json.dumps({"old": True}), encoding="utf-8")
    monkeypatch.setattr(
        "arkhon.integrations.tsar.adapter.shutil.which", lambda _name: "/usr/bin/tsar"
    )
    monkeypatch.setattr(
        "arkhon.integrations.tsar.adapter.subprocess.run",
        lambda *args, **kwargs: type("Result", (), {
            "returncode": 0, "stdout": json.dumps({"new": True}), "stderr": ""
        })(),
    )
    result = TsarAdapter().audit(tmp_path, commit)
    assert not result.ok
    assert "refusing to overwrite different" in result.reason


def test_audit_handles_start_and_directory_errors(tmp_path: Path, monkeypatch) -> None:
    import subprocess
    from pathlib import Path as PathType

    monkeypatch.setattr(
        "arkhon.integrations.tsar.adapter.shutil.which", lambda _name: "/usr/bin/tsar"
    )
    def start_error(*args, **kwargs):
        raise OSError("cannot start")
    monkeypatch.setattr(
        "arkhon.integrations.tsar.adapter.subprocess.run", start_error
    )
    result = TsarAdapter().audit(tmp_path, "a" * 40)
    assert not result.ok and "failed to start" in result.reason

    original_mkdir = PathType.mkdir
    def mkdir(path, *args, **kwargs):
        if path.name == "security" and path.parent.name == "evidence":
            raise OSError("read only")
        return original_mkdir(path, *args, **kwargs)
    monkeypatch.setattr(PathType, "mkdir", mkdir)
    project = tmp_path / "other"
    project.mkdir()
    result = TsarAdapter().audit(project, "b" * 40)
    assert not result.ok and "cannot prepare" in result.reason
