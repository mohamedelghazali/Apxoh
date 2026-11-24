"""Additional TSAR adapter filesystem failure paths."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from arkhon.integrations.tsar.adapter import TsarAdapter

SHA = "a" * 40


def _sarif() -> dict:
    return {
        "version": "2.1.0",
        "runs": [
            {
                "tool": {"driver": {"name": "TSAR", "version": "1.1.1", "rules": []}},
                "results": [],
            }
        ],
    }


def _configure(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "arkhon.integrations.tsar.adapter.shutil.which", lambda _name: "/usr/bin/tsar"
    )

    def fake_run(command, **kwargs):
        Path(command[command.index("--output") + 1]).write_text(
            json.dumps(_sarif()), encoding="utf-8"
        )
        return subprocess.CompletedProcess(command, 0, "", "")

    monkeypatch.setattr("arkhon.integrations.tsar.adapter.subprocess.run", fake_run)


def test_audit_reports_evidence_directory_creation_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _configure(monkeypatch)
    original = Path.mkdir

    def fail(path: Path, *args, **kwargs):
        if path.name == "security":
            raise OSError("read-only")
        return original(path, *args, **kwargs)

    monkeypatch.setattr(Path, "mkdir", fail)
    result = TsarAdapter().audit(tmp_path, SHA)
    assert not result.ok
    assert "cannot persist TSAR evidence" in result.reason


def test_audit_reports_evidence_write_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _configure(monkeypatch)
    original = Path.write_text

    def fail(path: Path, data: str, *args, **kwargs):
        if path.name.startswith("EVID-TSAR-") and path.suffix == ".sarif":
            raise OSError("read-only evidence store")
        return original(path, data, *args, **kwargs)

    monkeypatch.setattr(Path, "write_text", fail)
    result = TsarAdapter().audit(tmp_path, SHA)
    assert not result.ok
    assert "cannot persist TSAR evidence" in result.reason
