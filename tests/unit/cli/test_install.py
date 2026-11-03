"""Tests for safe staging of the packaged agent governance resources."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from arkhon.cli import main


def test_project_install_stages_pack_and_manifest(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert main(["install", "--scope", "project", "--project", str(tmp_path)]) == 0
    target = tmp_path / ".arkhon" / "agent-pack"
    assert (target / "AGENTS.md").is_file()
    assert (target / "SECURITY_AGENTS.md").is_file()
    assert (target / "agents" / "developer" / "AGENT.md").is_file()
    assert (target / "skills" / "arkhon-governance" / "SKILL.md").is_file()
    manifest = json.loads((target / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["scope"] == "project"
    assert manifest["activation"] == "manual"
    assert len(manifest["files"]) == 20
    assert "settings were not changed" in capsys.readouterr().out


def test_install_refuses_overwrite_and_force_replaces_managed_pack(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert main(["install", "--project", str(tmp_path)]) == 0
    target = tmp_path / ".arkhon" / "agent-pack"
    (target / "AGENTS.md").write_text("tampered", encoding="utf-8")
    assert main(["install", "--project", str(tmp_path)]) == 1
    assert "already exists" in capsys.readouterr().err
    assert main(["install", "--project", str(tmp_path), "--force"]) == 0
    assert (target / "AGENTS.md").read_text(encoding="utf-8") != "tampered"


def test_global_install_uses_home_scoped_directory(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    assert main(["install", "--scope", "global"]) == 0
    assert (tmp_path / ".arkhon" / "agent-pack" / "manifest.json").is_file()


def test_install_rejects_missing_project(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert main(["install", "--scope", "project", "--project", str(tmp_path / "missing")]) == 1
    assert "not a directory" in capsys.readouterr().err


def test_install_rejects_symlinked_parent_without_writing_outside(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    project = tmp_path / "project"
    project.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    try:
        (project / ".arkhon").symlink_to(outside, target_is_directory=True)
    except OSError:
        pytest.skip("symlink creation is unavailable on this runner")
    assert main(["install", "--project", str(project)]) == 1
    assert "symlinked install directory" in capsys.readouterr().err
    assert not (outside / "agent-pack").exists()


def test_install_rejects_symlinked_target(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    project = tmp_path / "project"
    project.mkdir()
    parent = project / ".arkhon"
    parent.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    try:
        (parent / "agent-pack").symlink_to(outside, target_is_directory=True)
    except OSError:
        pytest.skip("symlink creation is unavailable on this runner")
    assert main(["install", "--project", str(project), "--force"]) == 1
    assert "symlinked agent pack" in capsys.readouterr().err


def test_install_fails_when_packaged_resources_are_missing(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr("arkhon.cli._agent_pack_source", lambda: tmp_path / "missing")
    assert main(["install", "--project", str(tmp_path)]) == 1
    assert "resources not found" in capsys.readouterr().err


def test_install_fails_when_packaged_resources_are_empty(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    empty = tmp_path / "empty"
    empty.mkdir()
    monkeypatch.setattr("arkhon.cli._agent_pack_source", lambda: empty)
    assert main(["install", "--project", str(tmp_path)]) == 1
    assert "pack is empty" in capsys.readouterr().err


def test_install_cleans_staging_directory_after_copy_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    def fail_copy(*args: object, **kwargs: object) -> None:
        raise OSError("copy failure")

    monkeypatch.setattr("arkhon.cli.shutil.copytree", fail_copy)
    assert main(["install", "--project", str(tmp_path)]) == 1
    assert "installation failed" in capsys.readouterr().err
    assert not list((tmp_path / ".arkhon").glob(".agent-pack-staging-*"))


def test_install_restores_previous_pack_if_atomic_swap_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert main(["install", "--project", str(tmp_path)]) == 0
    target = tmp_path / ".arkhon" / "agent-pack"
    original = target / "AGENTS.md"
    original.write_text("preserve old pack", encoding="utf-8")
    real_rename = Path.rename
    failed_staging = False

    def fail_staging_once(path: Path, destination: Path) -> Path:
        nonlocal failed_staging
        if path.name.startswith(".agent-pack-staging-") and not failed_staging:
            failed_staging = True
            raise OSError("simulated atomic swap failure")
        return real_rename(path, destination)

    monkeypatch.setattr(Path, "rename", fail_staging_once)
    assert main(["install", "--project", str(tmp_path), "--force"]) == 1
    assert "installation failed" in capsys.readouterr().err
    assert original.read_text(encoding="utf-8") == "preserve old pack"
