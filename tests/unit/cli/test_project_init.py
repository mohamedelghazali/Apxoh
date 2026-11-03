"""Tests for the project initialization CLI command."""

from __future__ import annotations

import json
from pathlib import Path

import jsonschema
import pytest
import yaml

from arkhon.cli import main


def test_project_init_creates_schema_valid_declaration(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "app.py").write_text("value = 1\n", encoding="utf-8")
    assert main(["project", "init", str(tmp_path), "--name", "Example App"]) == 0
    target = tmp_path / ".arkhon" / "project.yaml"
    data = yaml.safe_load(target.read_text(encoding="utf-8"))
    schema = json.loads(
        (Path(__file__).resolve().parents[3] / "schemas" / "project.schema.json").read_text(
            encoding="utf-8"
        )
    )
    jsonschema.validate(instance=data, schema=schema)
    assert data["project"]["identifier"] == "example-app"
    assert data["languages"]["primary"] == "python"
    assert "project declaration created" in capsys.readouterr().out


def test_project_init_without_detected_language_uses_unknown(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert main(["project", "init", str(tmp_path)]) == 0
    data = yaml.safe_load(
        (tmp_path / ".arkhon" / "project.yaml").read_text(encoding="utf-8")
    )
    assert data["languages"]["primary"] == "unknown"
    assert "Languages: unknown" in capsys.readouterr().out


def test_project_init_refuses_existing_declaration_unless_forced(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    target = tmp_path / ".arkhon" / "project.yaml"
    target.parent.mkdir()
    target.write_text("existing: true\n", encoding="utf-8")
    assert main(["project", "init", str(tmp_path)]) == 1
    assert "already exists" in capsys.readouterr().err
    assert main(["project", "init", str(tmp_path), "--force"]) == 0
    data = yaml.safe_load(target.read_text(encoding="utf-8"))
    assert data["project"]["profile"] == "universal"


def test_project_init_rejects_invalid_project_and_profile(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert main(["project", "init", str(tmp_path / "missing")]) == 1
    assert "not a directory" in capsys.readouterr().err
    assert main(["project", "init", str(tmp_path), "--profile", "not-a-profile"]) == 1
    assert "unknown profile" in capsys.readouterr().err


@pytest.mark.parametrize(
    ("options", "message"),
    [
        (["--name", " "], "name cannot be empty"),
        (["--identifier", "not valid"], "identifier must match"),
    ],
)
def test_project_init_rejects_invalid_name_and_identifier(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    options: list[str],
    message: str,
) -> None:
    assert main(["project", "init", str(tmp_path), *options]) == 1
    assert message in capsys.readouterr().err


def test_project_init_fails_if_metadata_path_is_not_a_directory(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    (tmp_path / ".arkhon").write_text("not a directory", encoding="utf-8")
    assert main(["project", "init", str(tmp_path)]) == 1
    assert "project initialization failed" in capsys.readouterr().err


def test_project_init_fails_when_schema_is_unavailable(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    profile = tmp_path / "projects" / "universal" / "profile.yaml"
    profile.parent.mkdir(parents=True)
    profile.write_text("name: universal\n", encoding="utf-8")
    monkeypatch.setattr("arkhon.cli._project_template_root", lambda: tmp_path)
    assert main(["project", "init", str(tmp_path / "project")]) == 1
    assert "not a directory" in capsys.readouterr().err
    project = tmp_path / "project"
    project.mkdir()
    assert main(["project", "init", str(project)]) == 1
    assert "schema not found" in capsys.readouterr().err


def test_project_templates_fall_back_to_packaged_resources(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from arkhon.cli import _project_template_root
    from arkhon.projects.loader import list_profiles

    monkeypatch.setattr("arkhon.cli._repo_root", lambda: tmp_path)
    templates = _project_template_root()
    assert (templates / "schemas" / "project.schema.json").is_file()
    assert {"universal", "web-application", "api-service"} <= set(list_profiles(templates))


def test_project_init_reports_schema_validation_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    def reject_schema(*, instance: object, schema: object) -> None:
        raise jsonschema.ValidationError("forced schema failure")

    monkeypatch.setattr("jsonschema.validate", reject_schema)
    assert main(["project", "init", str(tmp_path)]) == 1
    assert "forced schema failure" in capsys.readouterr().err
