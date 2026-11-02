"""Shared fixtures for platform integration tests."""

from __future__ import annotations

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]

PLATFORMS_DIR = REPO_ROOT / "integrations" / "platforms"

@pytest.fixture

def copilot_project(tmp_path: Path) -> Path:

    """A minimal project for testing the Copilot adapter."""

    (tmp_path / ".git").mkdir()

    return tmp_path
