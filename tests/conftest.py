"""Shared pytest fixtures for Apxoh tests."""

from __future__ import annotations

import os
import shutil
import subprocess
from collections.abc import Iterator
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
GIT_EXECUTABLE = shutil.which("git")


def _run_git(args: list[str], cwd: Path) -> None:
    if GIT_EXECUTABLE is None:
        raise RuntimeError("git executable not found on PATH")
    subprocess.run(  # noqa: S603 - resolved git executable; arguments are test fixtures
        [GIT_EXECUTABLE, *args], cwd=cwd, check=True
    )


@pytest.fixture(scope="session")
def repo_root() -> Path:
    """Absolute path to the Apxoh repository root."""
    return REPO_ROOT


@pytest.fixture(scope="session")
def manifest_index(repo_root: Path) -> dict:
    """Parsed manifest/index.yaml."""
    path = repo_root / "manifest" / "index.yaml"
    with path.open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


@pytest.fixture(scope="session")
def manifest_system(repo_root: Path) -> dict:
    path = repo_root / "manifest" / "system.yaml"
    with path.open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


@pytest.fixture(scope="session")
def manifest_integrations(repo_root: Path) -> dict:
    path = repo_root / "manifest" / "integrations.yaml"
    with path.open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


@pytest.fixture(scope="session")
def manifest_languages(repo_root: Path) -> dict:
    path = repo_root / "manifest" / "languages.yaml"
    with path.open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


@pytest.fixture(scope="session")
def manifest_products(repo_root: Path) -> dict:
    path = repo_root / "manifest" / "products.yaml"
    with path.open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


@pytest.fixture(scope="session")
def manifest_standards(repo_root: Path) -> dict:
    path = repo_root / "manifest" / "standards.yaml"
    with path.open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


@pytest.fixture(scope="session")
def manifest_compatibility(repo_root: Path) -> dict:
    path = repo_root / "manifest" / "compatibility.yaml"
    with path.open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


@pytest.fixture
def tmp_project(tmp_path: Path) -> Iterator[Path]:
    """Create a minimal governed project skeleton in a temp directory."""
    (tmp_path / ".arkhon" / "evidence").mkdir(parents=True)
    (tmp_path / ".arkhon" / "state").mkdir(parents=True)
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text(
        "def hello() -> str:\n    return 'world'\n",
        encoding="utf-8",
    )
    (tmp_path / ".arkhon" / "project.yaml").write_text(
        "project:\n  name: tmp\n  type: library\n  profile: universal\n",
        encoding="utf-8",
    )
    yield tmp_path


@pytest.fixture
def clean_git_env() -> Iterator[None]:
    """Unset git environment variables that can leak between test runs."""
    to_unset = [
        "GIT_AUTHOR_NAME",
        "GIT_AUTHOR_EMAIL",
        "GIT_COMMITTER_NAME",
        "GIT_COMMITTER_EMAIL",
    ]
    saved = {k: os.environ.get(k) for k in to_unset}
    for k in to_unset:
        os.environ.pop(k, None)
    yield
    for k, v in saved.items():
        if v is not None:
            os.environ[k] = v


@pytest.fixture
def git_repo(tmp_path: Path, clean_git_env: None) -> Path:
    """Initialize a minimal git repository in tmp_path."""
    _run_git(["init", "-q"], cwd=tmp_path)
    _run_git(["config", "user.email", "test@example.com"], cwd=tmp_path)
    _run_git(["config", "user.name", "Test"], cwd=tmp_path)
    (tmp_path / "README.md").write_text("# tmp\n", encoding="utf-8")
    _run_git(["add", "."], cwd=tmp_path)
    _run_git(["commit", "-q", "-m", "init"], cwd=tmp_path)
    return tmp_path
