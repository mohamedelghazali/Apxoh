from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest
import yaml

from arkhon.cli import _commit_sha, main
from arkhon.core.errors import EvidenceError
from arkhon.evidence.store import EvidenceStore


def _git_project(root: Path, *, with_tests: bool = False) -> None:
    git = shutil.which("git")
    if git is None:
        raise RuntimeError("git not available")
    root.mkdir(parents=True, exist_ok=True)
    (root / "src").mkdir(exist_ok=True)
    (root / "src" / "app.py").write_text("value = 1\n", encoding="utf-8")
    if with_tests:
        (root / "tests").mkdir()
        (root / "tests" / "test_app.py").write_text(
            "def test_value():\n    assert 1 == 1\n", encoding="utf-8"
        )
    def run(args: list[str]) -> None:
        subprocess.run(  # noqa: S603 - resolved git binary and fixed test arguments
            [git, *args], cwd=root, check=True, capture_output=True
        )
    run(["init", "-q"])
    run(["config", "user.email", "ci@example.com"])
    run(["config", "user.name", "CI"])
    run(["add", "."])
    run(["commit", "-q", "-m", "fixture"])


def test_version_text_json_and_help(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["version"]) == 0
    assert "Apxoh" in capsys.readouterr().out
    assert main(["version", "--json"]) == 0
    data = json.loads(capsys.readouterr().out)
    assert data["identifier"] == "arkhon"
    assert main([]) == 1
    assert "usage:" in capsys.readouterr().out.lower()


def test_commit_sha_missing_git_and_git_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr("arkhon.cli.shutil.which", lambda _name: None)
    assert _commit_sha(tmp_path) is None
    assert "not found" in capsys.readouterr().err
    monkeypatch.setattr("arkhon.cli.shutil.which", lambda _name: "/usr/bin/git")
    def fail(*args: object, **kwargs: object) -> None:
        raise OSError("git unavailable")
    monkeypatch.setattr("arkhon.cli.subprocess.run", fail)
    assert _commit_sha(tmp_path) is None
    assert "cannot resolve commit SHA" in capsys.readouterr().err


def test_assess_reports_score_and_gates(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert main(["assess", str(tmp_path)]) == 0
    output = capsys.readouterr().out
    assert "Score:" in output and "Gates:" in output
    assert main(["assess", str(tmp_path / "missing")]) == 1
    assert "not a directory" in capsys.readouterr().err


def test_report_writes_json_and_markdown(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    store = EvidenceStore(tmp_path)
    store.write(
        "testing",
        {
            "evidence_id": "EVID-REPORT",
            "commit_sha": "a" * 40,
            "status": "PASS",
        },
    )
    assert main(["report", str(tmp_path)]) == 0
    assert "report.json" in capsys.readouterr().out
    assert (tmp_path / ".arkhon" / "reports" / "report.json").is_file()
    output = tmp_path / "custom-reports"
    assert main([
        "report", str(tmp_path), "--format", "markdown", "--output", str(output)
    ]) == 0
    assert "report.md" in capsys.readouterr().out
    assert (output / "report.md").is_file()


def test_report_rejects_missing_project_and_missing_evidence(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert main(["report", str(tmp_path / "missing")]) == 1
    assert "not a directory" in capsys.readouterr().err
    with pytest.raises(EvidenceError, match="no evidence"):
        main(["report", str(tmp_path)])


def test_audit_passes_with_committed_tests(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _git_project(tmp_path, with_tests=True)
    assert main(["audit", str(tmp_path), "--domain", "testing"]) == 0
    output = capsys.readouterr().out
    assert "Status:   PASS" in output
    assert "Evidence:" in output


def test_audit_rejects_invalid_project_and_git_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert main(["audit", str(tmp_path / "missing")]) == 1
    assert "not a directory" in capsys.readouterr().err
    _git_project(tmp_path)

    def fail_git(*args: object, **kwargs: object) -> None:
        raise OSError("git unavailable")

    monkeypatch.setattr("arkhon.cli.subprocess.run", fail_git)
    assert main(["audit", str(tmp_path)]) == 1
    assert "cannot resolve commit SHA" in capsys.readouterr().err


def test_doctor_reports_success_and_missing_files(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr("arkhon.cli._repo_root", lambda: tmp_path)
    (tmp_path / "VERSION").write_text("1.0.0", encoding="utf-8")
    (tmp_path / "README.md").write_text("# Apxoh", encoding="utf-8")
    (tmp_path / "AGENTS.md").write_text("# Agents", encoding="utf-8")
    manifest = tmp_path / "manifest"
    manifest.mkdir()
    names = ("system", "products", "integrations", "languages", "standards", "compatibility")
    refs = {name: f"{name}.yaml" for name in names}
    (manifest / "index.yaml").write_text(yaml.safe_dump({"files": refs}), encoding="utf-8")
    for name in names:
        value = {"system": {"name": "Apxoh", "identifier": "arkhon", "version": "1.0.0"}}
        (manifest / f"{name}.yaml").write_text(yaml.safe_dump(value), encoding="utf-8")
    monkeypatch.setattr(
        "arkhon.integrations.tsar.adapter.TsarAdapter.health_check", lambda _self: False
    )
    assert main(["doctor"]) == 0
    output = capsys.readouterr().out
    assert "doctor — OK" in output and "TSAR is not available" in output
    (tmp_path / "AGENTS.md").unlink()
    assert main(["doctor"]) == 1
    assert "missing required file" in capsys.readouterr().out
