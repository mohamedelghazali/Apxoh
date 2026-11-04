from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from arkhon.core.errors import ConfigError
from arkhon.integrations.platforms.github_copilot.adapter import GitHubCopilotAdapter
from arkhon.language_support.detector import _should_skip, detect_languages
from arkhon.language_support.registry import _parse_language
from arkhon.language_support.tool_resolver import ToolStatus, _check_tool, resolve_tools


def test_github_copilot_install_verify_and_preserve_user_changes(tmp_path: Path) -> None:
    adapter = GitHubCopilotAdapter()
    assert adapter.health_check()
    assert not adapter.verify(tmp_path).ok
    installed = adapter.install(tmp_path)
    assert installed.ok
    assert adapter.verify(tmp_path).ok
    target = tmp_path / ".github" / "copilot-instructions.md"
    target.write_text("user-owned instructions", encoding="utf-8")
    assert "does not match" in adapter.verify(tmp_path).reason
    result = adapter.install(tmp_path)
    assert not result.ok
    assert "refusing to overwrite user content" in result.reason
    assert target.read_text(encoding="utf-8") == "user-owned instructions"


def test_language_detector_skip_and_sample_validation(tmp_path: Path, monkeypatch) -> None:
    root = tmp_path / "project"
    root.mkdir()
    outside = tmp_path / "outside.py"
    outside.write_text("x", encoding="utf-8")
    assert _should_skip(outside, root)
    link = root / "linked.py"
    try:
        link.symlink_to(outside)
    except OSError:
        pytest.skip("symlinks are unavailable")
    assert _should_skip(link, root)
    link.unlink()
    huge = root / "huge.py"
    huge.write_text("12345", encoding="utf-8")
    monkeypatch.setattr("arkhon.language_support.detector.MAX_FILE_SIZE", 1)
    assert _should_skip(huge, root)
    with pytest.raises(ValueError, match="max_samples"):
        detect_languages(root, max_samples=-1)
    with pytest.raises(ValueError, match="max_samples"):
        detect_languages(root, max_samples=True)


def test_language_registry_rejects_bad_planned_tools_and_milestone() -> None:
    base = {
        "id": "python",
        "detection": {"extensions": [".py"]},
        "planned_tools": {"lint": ["ruff"]},
        "milestone": 1,
    }
    assert _parse_language(base).id == "python"
    bad = {**base, "planned_tools": {"lint": "ruff"}}
    with pytest.raises(ConfigError, match="planned_tools"):
        _parse_language(bad)
    bad = {**base, "milestone": True}
    with pytest.raises(ConfigError, match="milestone"):
        _parse_language(bad)
    bad = {**base, "primary_use": ["valid", 1]}
    with pytest.raises(ConfigError, match="primary_use"):
        _parse_language(bad)


def test_tool_resolver_missing_unknown_and_available(monkeypatch) -> None:
    monkeypatch.setattr("arkhon.language_support.tool_resolver.shutil.which", lambda _n: None)
    assert _check_tool("missing").status == ToolStatus.MISSING
    monkeypatch.setattr(
        "arkhon.language_support.tool_resolver.shutil.which", lambda _n: "/usr/bin/tool"
    )
    monkeypatch.setattr(
        "arkhon.language_support.tool_resolver.subprocess.run",
        lambda *a, **k: (_ for _ in ()).throw(subprocess.TimeoutExpired("tool", 1)),
    )
    assert _check_tool("tool").status == ToolStatus.VERSION_UNKNOWN
    monkeypatch.setattr(
        "arkhon.language_support.tool_resolver.subprocess.run",
        lambda *a, **k: (_ for _ in ()).throw(OSError("cannot execute")),
    )
    assert _check_tool("tool").status == ToolStatus.VERSION_UNKNOWN
    monkeypatch.setattr(
        "arkhon.language_support.tool_resolver.subprocess.run",
        lambda command, **kwargs: subprocess.CompletedProcess(command, 1, "", "error"),
    )
    assert _check_tool("tool").status == ToolStatus.VERSION_UNKNOWN
    monkeypatch.setattr(
        "arkhon.language_support.tool_resolver.subprocess.run",
        lambda command, **kwargs: subprocess.CompletedProcess(command, 0, "Tool 1.2", ""),
    )
    result = resolve_tools("python", ["tool"])
    assert result.all_available
    assert result.get("tool").version == "Tool 1.2"
    assert result.missing == []
    assert not resolve_tools("python", []).all_available
