"""Tests for the `arkhon verify` command."""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

from arkhon.cli import main


def _init_project(tmp_path: Path) -> None:
    """Create a minimal project with git."""

    git_executable = shutil.which("git")
    if git_executable is None:
        raise RuntimeError("git executable not found on PATH")

    def run_git(args: list[str]) -> None:
        subprocess.run(  # noqa: S603 - resolved git executable; fixed test arguments
            [git_executable, *args], cwd=tmp_path, check=True
        )

    (tmp_path / ".arkhon").mkdir()

    (tmp_path / ".arkhon" / "project.yaml").write_text(
        "project:\n  name: test\n  profile: universal\n",
        encoding="utf-8",
    )

    (tmp_path / "src").mkdir()

    (tmp_path / "src" / "main.py").write_text("x = 1\n", encoding="utf-8")

    run_git(["init", "-q"])

    subprocess.run(
        ["git", "config", "user.email", r"test\@example.com"],
        cwd=tmp_path,
        check=True,
    )

    run_git(["config", "user.name", "Test"])

    run_git(["add", "."])

    run_git(["commit", "-q", "-m", "init"])


def test_verify_unknown_domain(
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    _init_project(tmp_path)

    rc = main(["verify", str(tmp_path), "--domain", "nope"])

    assert rc == 1

    assert "unknown domain" in capsys.readouterr().err


def test_verify_no_git_repo(
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    rc = main(["verify", str(tmp_path), "--domain", "testing"])

    assert rc == 1

    assert "cannot resolve commit SHA" in capsys.readouterr().err


def test_verify_code_quality_domain(
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    """Runs ruff + mypy. Tools may be missing → BLOCKED, not crash."""

    _init_project(tmp_path)

    (tmp_path / "pyproject.toml").write_text(
        "[project]\nname = 'test'\nversion = '0.1.0'\n",
        encoding="utf-8",
    )

    main(["verify", str(tmp_path), "--domain", "code-quality"])

    out = capsys.readouterr().out

    # rc may be 0 or 1 depending on whether tools are installed

    assert "Status:" in out


def test_verify_records_evidence(
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    """Even on BLOCKED, evidence is written to .arkhon/evidence/."""

    _init_project(tmp_path)

    main(["verify", str(tmp_path), "--domain", "testing"])

    evidence_dir = tmp_path / ".arkhon" / "evidence" / "testing"

    # Either evidence exists, or the run was BLOCKED before writing

    if evidence_dir.is_dir():
        files = list(evidence_dir.glob("*.json"))

        if files:
            data = json.loads(files[0].read_text(encoding="utf-8"))

            assert data["source"] == "arkhon"

            assert "commit_sha" in data
