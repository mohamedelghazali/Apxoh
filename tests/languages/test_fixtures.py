"""End-to-end tests for all language fixtures.

Every fixture is a real project. Apxoh must detect its language, match
its declared profile, and (where tools are present) verify it.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from arkhon.cli import main
from arkhon.language_support.detector import detect_languages
from arkhon.projects.matcher import match_profile

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURES_DIR = REPO_ROOT / "tests" / "languages" / "fixtures"

EXPECTED_FIXTURES = {
    "python-project": "python",
    "javascript-project": "javascript",
    "typescript-project": "typescript",
    "java-project": "java",
    "csharp-project": "csharp",
    "cpp-project": "cpp",
    "go-project": "go",
    "rust-project": "rust",
    "ruby-project": "ruby",
}


def _fixture_path(name: str) -> Path:
    return FIXTURES_DIR / name


@pytest.mark.parametrize(("fixture_name", "lang"), list(EXPECTED_FIXTURES.items()))
def test_fixture_exists(fixture_name: str, lang: str) -> None:
    path = _fixture_path(fixture_name)
    assert path.is_dir(), f"missing fixture: {path}"
    assert (path / ".arkhon" / "project.yaml").is_file()
    assert (path / "README.md").is_file()


@pytest.mark.parametrize(("fixture_name", "lang"), list(EXPECTED_FIXTURES.items()))
def test_fixture_detects_language(fixture_name: str, lang: str) -> None:
    path = _fixture_path(fixture_name)
    if not path.is_dir():
        pytest.skip(f"fixture not present: {fixture_name}")
    result = detect_languages(path)
    detected = [d.definition.id for d in result.detected]
    assert lang in detected, f"{fixture_name}: expected {lang}, got {detected}"


@pytest.mark.parametrize(("fixture_name", "lang"), list(EXPECTED_FIXTURES.items()))
def test_fixture_declared_profile(fixture_name: str, lang: str) -> None:
    path = _fixture_path(fixture_name)
    if not path.is_dir():
        pytest.skip(f"fixture not present: {fixture_name}")
    match = match_profile(path)
    assert match.explicit is True
    assert match.profile == "universal"


@pytest.mark.parametrize(("fixture_name", "lang"), list(EXPECTED_FIXTURES.items()))
def test_fixture_has_no_committed_evidence(fixture_name: str, lang: str) -> None:
    path = _fixture_path(fixture_name)
    if not path.is_dir():
        pytest.skip(f"fixture not present: {fixture_name}")
    evidence = path / ".arkhon" / "evidence"
    assert not evidence.exists() or not any(evidence.iterdir())


@pytest.mark.parametrize(("fixture_name", "lang"), list(EXPECTED_FIXTURES.items()))
def test_fixture_has_build_file(fixture_name: str, lang: str) -> None:
    """Each fixture must have at least one build file for its language."""
    path = _fixture_path(fixture_name)
    if not path.is_dir():
        pytest.skip(f"fixture not present: {fixture_name}")
    expected_build_files = {
        "python-project": ["pyproject.toml"],
        "javascript-project": ["package.json"],
        "typescript-project": ["package.json", "tsconfig.json"],
        "java-project": ["pom.xml"],
        "csharp-project": ["Calc.csproj"],
        "cpp-project": ["CMakeLists.txt"],
        "go-project": ["go.mod"],
        "rust-project": ["Cargo.toml"],
        "ruby-project": ["Gemfile"],
    }
    for bf in expected_build_files[fixture_name]:
        assert (path / bf).is_file(), f"{fixture_name}: missing {bf}"


def test_all_nine_fixtures_present() -> None:
    actual = (
        {p.name for p in FIXTURES_DIR.iterdir() if p.is_dir()} if FIXTURES_DIR.is_dir() else set()
    )
    assert actual >= set(EXPECTED_FIXTURES.keys())


def test_inspect_cli_on_all_fixtures(capsys: pytest.CaptureFixture[str]) -> None:
    for name, lang in EXPECTED_FIXTURES.items():
        path = _fixture_path(name)
        if not path.is_dir():
            continue
        capsys.readouterr()  # clear
        rc = main(["inspect", str(path), "--json"])
        assert rc == 0, f"{name}: inspect failed"
        data = json.loads(capsys.readouterr().out)
        assert lang in data["languages"]["detected"], f"{name}: {lang} not detected"
