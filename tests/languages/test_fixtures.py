"""End-to-end tests for language fixtures.

Each fixture is a real project that Apxoh must be able to detect,
inspect, and verify. If a fixture breaks, this test fails.
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
}


def _fixture_path(name: str) -> Path:
    return FIXTURES_DIR / name


@pytest.mark.parametrize(("fixture_name", "expected_lang"), list(EXPECTED_FIXTURES.items()))
def test_fixture_exists(fixture_name: str, expected_lang: str) -> None:
    path = _fixture_path(fixture_name)
    assert path.is_dir(), f"missing fixture: {path}"
    assert (path / ".arkhon" / "project.yaml").is_file()
    assert (path / "README.md").is_file()


@pytest.mark.parametrize(("fixture_name", "expected_lang"), list(EXPECTED_FIXTURES.items()))
def test_fixture_detects_language(fixture_name: str, expected_lang: str) -> None:
    path = _fixture_path(fixture_name)
    result = detect_languages(path)
    detected_ids = [d.definition.id for d in result.detected]
    assert expected_lang in detected_ids, (
        f"{fixture_name}: expected {expected_lang} in detected {detected_ids}"
    )


@pytest.mark.parametrize(("fixture_name", "expected_lang"), list(EXPECTED_FIXTURES.items()))
def test_fixture_matches_declared_profile(fixture_name: str, expected_lang: str) -> None:
    path = _fixture_path(fixture_name)
    match = match_profile(path)
    assert match.explicit is True, "fixture must declare its profile explicitly"
    assert match.profile == "universal"


@pytest.mark.parametrize(("fixture_name", "expected_lang"), list(EXPECTED_FIXTURES.items()))
def test_fixture_has_no_committed_evidence(
    fixture_name: str, expected_lang: str,
) -> None:
    """A fixture must not contain pre-generated evidence."""
    evidence_dir = _fixture_path(fixture_name) / ".arkhon" / "evidence"
    assert not evidence_dir.exists() or not any(evidence_dir.iterdir()), (
        f"{fixture_name}: fixture should not contain committed evidence"
    )


def test_inspect_cli_on_python_fixture(capsys: pytest.CaptureFixture[str]) -> None:
    fixture = _fixture_path("python-project")
    rc = main(["inspect", str(fixture), "--json"])
    assert rc == 0
    data = json.loads(capsys.readouterr().out)
    assert "python" in data["languages"]["detected"]
    assert data["profile"]["explicit"] is True
