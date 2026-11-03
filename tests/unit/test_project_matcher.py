from __future__ import annotations

from pathlib import Path

import pytest

from arkhon.core.errors import ConfigError
from arkhon.projects.matcher import (
    Match,
    _read_declared_profile,
    match_profile,
    validate_profile_name,
)


def test_match_profile_explicit_and_default(tmp_path: Path) -> None:
    (tmp_path / ".arkhon").mkdir()
    (tmp_path / ".arkhon" / "project.yaml").write_text(
        "project:\n  profile: enterprise\n", encoding="utf-8"
    )
    explicit = match_profile(tmp_path)
    assert explicit == Match("enterprise", "declared in .arkhon/project.yaml", True)
    (tmp_path / ".arkhon" / "project.yaml").unlink()
    assert match_profile(tmp_path).profile == "universal"


@pytest.mark.parametrize(
    ("marker", "expected"),
    [
        ("android", "mobile-application"),
        ("electron", "desktop-application"),
        ("k8s", "distributed-system"),
        ("openapi.yaml", "api-service"),
        ("public", "web-application"),
    ],
)
def test_profile_inference_markers(tmp_path: Path, marker: str, expected: str) -> None:
    path = tmp_path / marker
    if "." in marker:
        path.write_text("openapi: 3.0.0", encoding="utf-8")
    else:
        path.mkdir()
    assert match_profile(tmp_path).profile == expected


def test_profile_inference_compose_and_openapi_variants(tmp_path: Path) -> None:
    (tmp_path / "docker-compose.yaml").write_text("services: {}", encoding="utf-8")
    assert match_profile(tmp_path).profile == "distributed-system"
    (tmp_path / "docker-compose.yaml").unlink()
    (tmp_path / "openapi.json").write_text("{}", encoding="utf-8")
    assert match_profile(tmp_path).profile == "api-service"


def test_profile_declaration_errors_and_validation(tmp_path: Path) -> None:
    folder = tmp_path / ".arkhon"
    folder.mkdir()
    declaration = folder / "project.yaml"
    declaration.write_text("- invalid", encoding="utf-8")
    with pytest.raises(ConfigError, match="mapping"):
        _read_declared_profile(tmp_path)
    declaration.write_text("project: []", encoding="utf-8")
    with pytest.raises(ConfigError, match="project"):
        _read_declared_profile(tmp_path)
    declaration.write_text("project:\n  profile: ''", encoding="utf-8")
    with pytest.raises(ConfigError, match="invalid profile"):
        _read_declared_profile(tmp_path)
    declaration.write_text("[", encoding="utf-8")
    with pytest.raises(ConfigError, match="cannot read"):
        _read_declared_profile(tmp_path)
    with pytest.raises(ConfigError, match="not a directory"):
        match_profile(tmp_path / "missing")
    with pytest.raises(ConfigError, match="unknown profile"):
        validate_profile_name("missing", ["universal"])
    validate_profile_name("universal", ["universal"])
