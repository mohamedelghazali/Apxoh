"""Tests for the arkhon verify command."""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

from arkhon.cli import main


def _init_project(tmp_path: Path, *, with_tests: bool = False) -> None:
    git = shutil.which("git")
    if git is None:
        raise RuntimeError("git executable not found")
    (tmp_path / ".arkhon").mkdir()
    (tmp_path / ".arkhon" / "project.yaml").write_text(
        "project:\n  name: test\n  profile: universal\n", encoding="utf-8"
    )
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("x = 1\n", encoding="utf-8")
    if with_tests:
        (tmp_path / "tests").mkdir()
        (tmp_path / "tests" / "test_sample.py").write_text(
            "def test_sample():\n    assert 1 + 1 == 2\n", encoding="utf-8"
        )

    def git_run(args: list[str]) -> None:
        subprocess.run(  # noqa: S603 - resolved git executable; fixed test arguments
            [git, *args], cwd=tmp_path, check=True
        )

    git_run(["init", "-q"])
    git_run(["config", "user.email", "test@example.com"])
    git_run(["config", "user.name", "Test"])
    git_run(["add", "."])
    git_run(["commit", "-q", "-m", "init"])


def test_verify_unknown_domain(capsys: pytest.CaptureFixture[str], tmp_path: Path) -> None:
    _init_project(tmp_path)
    assert main(["verify", str(tmp_path), "--domain", "nope"]) == 1
    assert "unknown domain" in capsys.readouterr().err


def test_verify_no_git_repo(capsys: pytest.CaptureFixture[str], tmp_path: Path) -> None:
    assert main(["verify", str(tmp_path), "--domain", "testing"]) == 1
    assert "cannot resolve commit SHA" in capsys.readouterr().err


def test_verify_code_quality_reports_status_and_evidence(
    capsys: pytest.CaptureFixture[str], tmp_path: Path
) -> None:
    _init_project(tmp_path)
    (tmp_path / "pyproject.toml").write_text(
        "[project]\nname = 'test'\nversion = '0.1.0'\n", encoding="utf-8"
    )
    rc = main(["verify", str(tmp_path), "--domain", "code-quality"])
    output = capsys.readouterr().out
    assert rc in {0, 1}
    assert "Status:" in output and "Evidence:" in output


def test_verify_blocked_run_persists_diagnostic_evidence(
    capsys: pytest.CaptureFixture[str], tmp_path: Path
) -> None:
    _init_project(tmp_path)
    assert main(["verify", str(tmp_path), "--domain", "testing"]) == 1
    output = capsys.readouterr().out
    assert "Status:   BLOCKED" in output
    records = list((tmp_path / ".arkhon" / "evidence" / "testing").glob("*.json"))
    assert len(records) == 1
    data = json.loads(records[0].read_text(encoding="utf-8"))
    assert data["source"] == "arkhon" and data["commit_sha"]
    assert data["status"] == "BLOCKED" and data["summary"]["blocked"] == 1
    diagnostic = tmp_path / ".arkhon" / "reports" / "verification"
    assert len(list(diagnostic.glob("*.json"))) == 1


def test_verify_passes_and_persists_junit_evidence(
    capsys: pytest.CaptureFixture[str], tmp_path: Path
) -> None:
    _init_project(tmp_path, with_tests=True)
    assert main(["verify", str(tmp_path), "--domain", "testing"]) == 0
    assert "Status:   PASS" in capsys.readouterr().out
    records = list((tmp_path / ".arkhon" / "evidence" / "testing").glob("*.json"))
    assert len(records) == 1
    data = json.loads(records[0].read_text(encoding="utf-8"))
    assert data["status"] == "PASS" and data["summary"]["pass"] == 1
