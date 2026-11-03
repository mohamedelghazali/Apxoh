from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from arkhon.core.errors import SecurityError
from arkhon.integrations.tsar.adapter import TsarAdapter


SHA = "a" * 40


def _configure_binary(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "arkhon.integrations.tsar.adapter.shutil.which",
        lambda _name: "/usr/bin/tsar",
    )


def test_health_check_and_version_handle_process_errors(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _configure_binary(monkeypatch)

    def fail(*args, **kwargs):
        raise OSError("cannot execute")

    monkeypatch.setattr("arkhon.integrations.tsar.adapter.subprocess.run", fail)
    assert TsarAdapter().health_check() is False
    with pytest.raises(SecurityError, match="version check failed"):
        TsarAdapter().version()


def test_audit_rejects_unreadable_existing_evidence(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _configure_binary(monkeypatch)
    evidence_dir = tmp_path / ".arkhon" / "evidence" / "security"
    evidence_dir.mkdir(parents=True)
    target = evidence_dir / f"tsar-{SHA[:12]}.json"
    target.write_text("{invalid", encoding="utf-8")
    monkeypatch.setattr(
        "arkhon.integrations.tsar.adapter.subprocess.run",
        lambda *args, **kwargs: subprocess.CompletedProcess(
            args[0], 0, json.dumps({"fresh": True}), ""
        ),
    )
    result = TsarAdapter().audit(tmp_path, SHA)
    assert result.ok is False
    assert "existing TSAR evidence is invalid" in result.reason


def test_audit_reports_evidence_persistence_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _configure_binary(monkeypatch)
    monkeypatch.setattr(
        "arkhon.integrations.tsar.adapter.subprocess.run",
        lambda *args, **kwargs: subprocess.CompletedProcess(
            args[0], 0, json.dumps({"fresh": True}), ""
        ),
    )
    original_write_text = Path.write_text

    def fail_target(path: Path, data: str, *args, **kwargs):
        if path.name == f"tsar-{SHA[:12]}.json":
            raise OSError("read-only evidence store")
        return original_write_text(path, data, *args, **kwargs)

    monkeypatch.setattr(Path, "write_text", fail_target)
    result = TsarAdapter().audit(tmp_path, SHA)
    assert result.ok is False
    assert "cannot persist TSAR evidence" in result.reason
