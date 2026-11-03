"""Tests for the supported TSAR scan/SARIF CLI adapter."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from arkhon.core.errors import SecurityError
from arkhon.integrations.tsar.adapter import TsarAdapter, TsarConfig

SHA = "a" * 40


def _sarif(*, version: str = "1.1.1", results: list | None = None) -> dict:
    return {
        "version": "2.1.0",
        "runs": [
            {
                "tool": {
                    "driver": {
                        "name": "TSAR",
                        "version": version,
                        "rules": [{"id": "tsar/secret"}],
                    }
                },
                "results": results or [],
            }
        ],
    }


def _run_with_sarif(monkeypatch: pytest.MonkeyPatch, payload: dict, code: int = 0) -> None:
    def fake_run(command, **kwargs):
        assert command[1] == "scan"
        assert command[command.index("--format") + 1] == "sarif"
        output = Path(command[command.index("--output") + 1])
        output.write_text(json.dumps(payload), encoding="utf-8")
        return subprocess.CompletedProcess(command, code, "", "")

    monkeypatch.setattr(
        "arkhon.integrations.tsar.adapter.shutil.which", lambda _name: "/usr/bin/tsar"
    )
    monkeypatch.setattr("arkhon.integrations.tsar.adapter.subprocess.run", fake_run)


def test_info_and_config() -> None:
    info = TsarAdapter().info
    assert info.id == "tsar"
    assert info.kind == "security"
    assert "sarif-2.1.0" in info.capabilities
    with pytest.raises(ValueError, match="positive"):
        TsarAdapter(TsarConfig(timeout_seconds=0))


def test_health_check_missing_and_success(monkeypatch: pytest.MonkeyPatch) -> None:
    adapter = TsarAdapter()
    monkeypatch.setattr("arkhon.integrations.tsar.adapter.shutil.which", lambda _name: None)
    assert adapter.health_check() is False
    monkeypatch.setattr(
        "arkhon.integrations.tsar.adapter.shutil.which", lambda _name: "/usr/bin/tsar"
    )
    monkeypatch.setattr(
        "arkhon.integrations.tsar.adapter.subprocess.run",
        lambda *a, **k: subprocess.CompletedProcess(a[0], 0, "usage: tsar scan", ""),
    )
    monkeypatch.setattr("arkhon.integrations.tsar.adapter.package_version", lambda _name: "1.1.1")
    assert adapter.health_check() is True


@pytest.mark.parametrize(
    ("code", "stdout", "expected"),
    [(1, "", False), (0, "usage: tsar audit", False)],
)
def test_health_check_rejects_invalid_cli(
    monkeypatch: pytest.MonkeyPatch, code: int, stdout: str, expected: bool
) -> None:
    monkeypatch.setattr(
        "arkhon.integrations.tsar.adapter.shutil.which", lambda _name: "/usr/bin/tsar"
    )
    monkeypatch.setattr(
        "arkhon.integrations.tsar.adapter.subprocess.run",
        lambda *a, **k: subprocess.CompletedProcess(a[0], code, stdout, ""),
    )
    assert TsarAdapter().health_check() is expected


def test_health_check_handles_process_and_version_failures(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "arkhon.integrations.tsar.adapter.shutil.which", lambda _name: "/usr/bin/tsar"
    )
    monkeypatch.setattr(
        "arkhon.integrations.tsar.adapter.subprocess.run",
        lambda *a, **k: (_ for _ in ()).throw(OSError("no process")),
    )
    assert TsarAdapter().health_check() is False
    monkeypatch.setattr(
        "arkhon.integrations.tsar.adapter.subprocess.run",
        lambda *a, **k: subprocess.CompletedProcess(a[0], 0, "tsar scan", ""),
    )
    monkeypatch.setattr(
        "arkhon.integrations.tsar.adapter.package_version",
        lambda _name: (_ for _ in ()).throw(SecurityError("no version")),
    )
    assert TsarAdapter().health_check() is False


def test_version_checks_installed_distribution(monkeypatch: pytest.MonkeyPatch) -> None:
    adapter = TsarAdapter()
    monkeypatch.setattr("arkhon.integrations.tsar.adapter.shutil.which", lambda _name: None)
    with pytest.raises(SecurityError, match="not found"):
        adapter.version()
    monkeypatch.setattr(
        "arkhon.integrations.tsar.adapter.shutil.which", lambda _name: "/usr/bin/tsar"
    )
    monkeypatch.setattr(
        "arkhon.integrations.tsar.adapter.package_version",
        lambda _name: (_ for _ in ()).throw(
            __import__(
                "importlib.metadata", fromlist=["PackageNotFoundError"]
            ).PackageNotFoundError()
        ),
    )
    with pytest.raises(SecurityError, match="metadata"):
        adapter.version()
    monkeypatch.setattr("arkhon.integrations.tsar.adapter.package_version", lambda _name: "bad")
    with pytest.raises(SecurityError, match="invalid TSAR package"):
        adapter.version()
    monkeypatch.setattr("arkhon.integrations.tsar.adapter.package_version", lambda _name: "1.1.1")
    assert adapter.version() == "1.1.1"


def test_audit_rejects_invalid_inputs(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    adapter = TsarAdapter()
    assert adapter.audit(tmp_path, "bad").reason == "invalid commit SHA"
    monkeypatch.setattr("arkhon.integrations.tsar.adapter.shutil.which", lambda _name: None)
    assert "not found" in adapter.audit(tmp_path, SHA).reason
    monkeypatch.setattr(
        "arkhon.integrations.tsar.adapter.shutil.which", lambda _name: "/usr/bin/tsar"
    )
    assert "not found" in adapter.audit(tmp_path / "missing", SHA).reason


def test_audit_clean_sarif_passes_and_binds_artifact(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _run_with_sarif(monkeypatch, _sarif())
    result = TsarAdapter().audit(tmp_path, SHA)
    assert result.ok
    assert result.payload["status"] == "PASS"
    assert result.payload["rule_ids"] == ["TSAR-SCAN-EXECUTED", "tsar/secret"]
    artifact = result.artifacts[0]
    assert artifact.is_file()
    assert result.payload["artifacts"][0]["path"] == artifact.relative_to(tmp_path).as_posix()


def test_audit_findings_are_fail_closed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _run_with_sarif(
        monkeypatch,
        _sarif(
            results=[{"ruleId": "tsar/secret", "level": "error", "message": {"text": "finding"}}]
        ),
        code=1,
    )
    result = TsarAdapter().audit(tmp_path, SHA)
    assert result.ok
    assert result.payload["status"] == "FAIL"
    assert result.payload["summary"]["high"] == 1
    assert result.payload["findings"][0]["ruleId"] == "tsar/secret"


def test_audit_rejects_tool_exit_without_sarif(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        "arkhon.integrations.tsar.adapter.shutil.which", lambda _name: "/usr/bin/tsar"
    )
    monkeypatch.setattr(
        "arkhon.integrations.tsar.adapter.subprocess.run",
        lambda *a, **k: subprocess.CompletedProcess(a[0], 2, "", "tool error"),
    )
    assert "exited with 2" in TsarAdapter().audit(tmp_path, SHA).reason
    monkeypatch.setattr(
        "arkhon.integrations.tsar.adapter.subprocess.run",
        lambda *a, **k: subprocess.CompletedProcess(a[0], 0, "", ""),
    )
    assert "without producing SARIF" in TsarAdapter().audit(tmp_path, SHA).reason


@pytest.mark.parametrize(
    ("raw", "message"),
    [
        ("not json", "valid SARIF"),
        ('{"version":"1.0.0","runs":[]}', "SARIF 2.1.0"),
        ('{"version":"2.1.0","runs":[]}', "no runs"),
        ('{"version":"2.1.0","runs":[null]}', "run must be an object"),
        ('{"version":"2.1.0","runs":[{}]}', "driver identity"),
        ('{"version":"2.1.0","runs":[{"tool":{"driver":{"name":"TSAR"}}}]}', "semantic version"),
        (
            '{"version":"2.1.0","runs":[{"tool":{"driver":{"name":"TSAR","version":"1.1.1"}},"results":{}}]}',
            "arrays",
        ),
        (
            '{"version":"2.1.0","runs":[{"tool":{"driver":{"name":"TSAR","version":"1.1.1"}},"results":[{}]}]}',
            "malformed finding",
        ),
        (
            '{"version":"2.1.0","runs":[{"tool":{"driver":{"name":"TSAR","version":"1.1.1"}},"results":[{"ruleId":"x","level":"fatal"}]}]}',
            "severity",
        ),
    ],
)
def test_audit_rejects_malformed_sarif(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, raw: str, message: str
) -> None:
    monkeypatch.setattr(
        "arkhon.integrations.tsar.adapter.shutil.which", lambda _name: "/usr/bin/tsar"
    )

    def fake_run(command, **kwargs):
        Path(command[command.index("--output") + 1]).write_text(raw, encoding="utf-8")
        return subprocess.CompletedProcess(command, 0, "", "")

    monkeypatch.setattr("arkhon.integrations.tsar.adapter.subprocess.run", fake_run)
    result = TsarAdapter().audit(tmp_path, SHA)
    assert result.ok is False
    assert message.lower() in result.reason.lower()


def test_audit_rejects_unsupported_version(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _run_with_sarif(monkeypatch, _sarif(version="2.0.0"))
    result = TsarAdapter().audit(tmp_path, SHA)
    assert not result.ok
    assert "out of range" in result.reason


@pytest.mark.parametrize("error", [OSError("cannot start"), subprocess.TimeoutExpired("tsar", 1)])
def test_audit_handles_process_errors(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, error: Exception
) -> None:
    monkeypatch.setattr(
        "arkhon.integrations.tsar.adapter.shutil.which", lambda _name: "/usr/bin/tsar"
    )

    def fail(*args, **kwargs):
        raise error

    monkeypatch.setattr("arkhon.integrations.tsar.adapter.subprocess.run", fail)
    result = TsarAdapter().audit(tmp_path, SHA)
    assert not result.ok
    assert (
        "timed out" in result.reason
        if isinstance(error, subprocess.TimeoutExpired)
        else "failed to start" in result.reason
    )
