"""Tests for arkhon.language_support.tool_resolver."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from arkhon.language_support.tool_resolver import (
    ToolStatus,
    _check_tool,
    resolve_tools,
)


def test_check_tool_missing() -> None:
    with patch("shutil.which", return_value=None):
        result = _check_tool("nonexistent-tool-xyz")
    assert result.status == ToolStatus.MISSING
    assert "not found" in result.reason


def test_check_tool_available() -> None:
    with patch("shutil.which", return_value="/usr/bin/python3"), \
         patch("subprocess.run") as mock_run:
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "Python 3.11.0\n"
        mock_run.return_value.stderr = ""
        result = _check_tool("python")
    assert result.status == ToolStatus.AVAILABLE
    assert "3.11" in result.version


def test_check_tool_version_unknown() -> None:
    with patch("shutil.which", return_value="/usr/bin/weird"), \
         patch("subprocess.run") as mock_run:
        mock_run.return_value.returncode = 1
        mock_run.return_value.stdout = ""
        mock_run.return_value.stderr = "error"
        result = _check_tool("weird")
    assert result.status == ToolStatus.VERSION_UNKNOWN


def test_resolve_tools_aggregates() -> None:
    with patch("arkhon.language_support.tool_resolver._check_tool") as mock_check:
        from arkhon.language_support.tool_resolver import ToolCheck
        mock_check.side_effect = [
            ToolCheck(name="a", status=ToolStatus.AVAILABLE, version="1.0"),
            ToolCheck(name="b", status=ToolStatus.MISSING, reason="not found"),
        ]
        result = resolve_tools("python", ["a", "b"])
    assert result.language_id == "python"
    assert len(result.tools) == 2
    assert not result.all_available
    assert len(result.missing) == 1


def test_resolve_tools_all_available() -> None:
    with patch("arkhon.language_support.tool_resolver._check_tool") as mock_check:
        from arkhon.language_support.tool_resolver import ToolCheck
        mock_check.side_effect = [
            ToolCheck(name="a", status=ToolStatus.AVAILABLE, version="1.0"),
            ToolCheck(name="b", status=ToolStatus.AVAILABLE, version="2.0"),
        ]
        result = resolve_tools("python", ["a", "b"])
    assert result.all_available
    assert result.missing == []


def test_get_by_name() -> None:
    with patch("arkhon.language_support.tool_resolver._check_tool") as mock_check:
        from arkhon.language_support.tool_resolver import ToolCheck
        mock_check.return_value = ToolCheck(name="ruff", status=ToolStatus.AVAILABLE, version="0.7")
        result = resolve_tools("python", ["ruff"])
    found = result.get("ruff")
    assert found is not None
    assert found.version == "0.7"
    assert result.get("mypy") is None
