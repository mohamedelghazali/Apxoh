"""Tests for the generic-agents fallback adapter."""

from __future__ import annotations

from pathlib import Path

from arkhon.integrations.generic_agents.adapter import GenericAgentAdapter


def test_info() -> None:
    info = GenericAgentAdapter().info

    assert info.id == "generic-agents"

    assert info.kind == "generic"


def test_health_check() -> None:
    assert GenericAgentAdapter().health_check() is True


def test_system_prompt_present() -> None:
    assert GenericAgentAdapter().system_prompt()


def test_install_returns_instructions(tmp_path: Path) -> None:
    adapter = GenericAgentAdapter()

    result = adapter.install(tmp_path)

    assert result.ok

    assert "instructions" in result.payload

    assert len(result.payload["instructions"]) > 100


def test_install_does_not_write_files(tmp_path: Path) -> None:
    """Generic agent adapter cannot install — user must apply manually."""

    before = set(tmp_path.iterdir())

    GenericAgentAdapter().install(tmp_path)

    after = set(tmp_path.iterdir())

    assert before == after


def test_install_note_present(tmp_path: Path) -> None:
    result = GenericAgentAdapter().install(tmp_path)

    assert "manual" in result.payload["note"].lower()
