"""Tests for the `arkhon inspect` command."""

from __future__ import annotations

import json

from pathlib import Path

import pytest

from arkhon.cli import main

def test_inspect_not_a_directory(

    capsys: pytest.CaptureFixture[str], tmp_path: Path,

) -> None:

    rc = main(["inspect", str(tmp_path / "nope")])

    assert rc == 1

    assert "not a directory" in capsys.readouterr().err

def test_inspect_empty_project(

    capsys: pytest.CaptureFixture[str], tmp_path: Path,

) -> None:

    rc = main(["inspect", str(tmp_path), "--json"])

    assert rc == 0

    data = json.loads(capsys.readouterr().out)

    assert data["languages"]["detected"] == []

    assert data["project"] == str(tmp_path.resolve())

def test_inspect_python_project(

    capsys: pytest.CaptureFixture[str], tmp_path: Path,

) -> None:

    (tmp_path / "src").mkdir()

    (tmp_path / "src" / "main.py").write_text("x = 1\n", encoding="utf-8")

    rc = main(["inspect", str(tmp_path), "--json"])

    assert rc == 0

    data = json.loads(capsys.readouterr().out)

    assert "python" in data["languages"]["detected"]

    assert data["profile"]["name"]

def test_inspect_multiple_languages(

    capsys: pytest.CaptureFixture[str], tmp_path: Path,

) -> None:

    (tmp_path / "src").mkdir()

    (tmp_path / "src" / "main.py").write_text("x = 1\n", encoding="utf-8")

    (tmp_path / "src" / "api.ts").write_text("export const x = 1;\n", encoding="utf-8")

    rc = main(["inspect", str(tmp_path), "--json"])

    assert rc == 0

    data = json.loads(capsys.readouterr().out)

    assert "python" in data["languages"]["detected"]

    assert "typescript" in data["languages"]["detected"]

def test_inspect_declared_profile(

    capsys: pytest.CaptureFixture[str], tmp_path: Path,

) -> None:

    (tmp_path / ".arkhon").mkdir()

    (tmp_path / ".arkhon" / "project.yaml").write_text(

        "project:\n  name: test\n  profile: enterprise\n",

        encoding="utf-8",

    )

    rc = main(["inspect", str(tmp_path), "--json"])

    assert rc == 0

    data = json.loads(capsys.readouterr().out)

    assert data["profile"]["name"] == "enterprise"

    assert data["profile"]["explicit"] is True

def test_inspect_text_output(

    capsys: pytest.CaptureFixture[str], tmp_path: Path,

) -> None:

    (tmp_path / "main.py").write_text("x = 1\n", encoding="utf-8")

    rc = main(["inspect", str(tmp_path)])

    assert rc == 0

    out = capsys.readouterr().out

    assert "Project:" in out

    assert "Profile:" in out

    assert "python" in out
