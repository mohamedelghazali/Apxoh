"""Integration contract checks for the external TSAR adapter boundary."""

from __future__ import annotations

from pathlib import Path

from arkhon.integrations.tsar.adapter import TsarAdapter


def test_tsar_adapter_metadata() -> None:
    info = TsarAdapter().info
    assert info.id == "tsar"
    assert info.kind == "security"
    assert "audit" in info.capabilities


def test_missing_tsar_binary_is_unavailable(monkeypatch) -> None:
    monkeypatch.setattr("arkhon.integrations.tsar.adapter.shutil.which", lambda _binary: None)
    assert TsarAdapter().health_check() is False


def test_invalid_commit_is_rejected_before_invocation(tmp_path: Path) -> None:
    result = TsarAdapter().audit(tmp_path, "not-a-commit")
    assert result.ok is False
    assert result.reason == "invalid commit SHA"
