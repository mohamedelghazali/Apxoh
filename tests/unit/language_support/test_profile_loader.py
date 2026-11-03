"""Tests for validated language profile loading."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from arkhon.core.errors import ConfigError
from arkhon.language_support.language_profile_loader import load_language_profile
from arkhon.language_support.registry import load_registry


def _repo(tmp_path: Path, profile: dict[str, object]) -> Path:
    (tmp_path / "languages" / "python").mkdir(parents=True)
    registry = {
        "engine_language": "python",
        "version": "1.0.0",
        "languages": [
            {
                "id": "python",
                "name": "Python",
                "family": "dynamic-typed",
                "primary_use": ["testing"],
                "status": "active",
                "milestone": 2,
                "profile_path": "languages/python/language-profile.yaml",
                "rules_path": "languages/python/rules",
                "detection": {"extensions": [".py"], "build_files": [], "lock_files": []},
                "planned_tools": {},
            }
        ],
    }
    (tmp_path / "languages" / "registry.yaml").write_text(
        yaml.safe_dump(registry), encoding="utf-8"
    )
    (tmp_path / "languages" / "python" / "language-profile.yaml").write_text(
        yaml.safe_dump(profile), encoding="utf-8"
    )
    return tmp_path


def _valid_profile() -> dict[str, object]:
    return {
        "id": "python",
        "name": "Python",
        "family": "dynamic-typed",
        "version": "1.0.0",
        "status": "active",
        "runtime": {"minimum": "3.11"},
        "build_system": {"preferred": "pip"},
        "dependency_manager": {"preferred": "pip"},
        "testing": {"framework": "pytest"},
        "entry_points": {},
        "rule_domains_supported": ["testing", "security"],
        "notes": "reference profile",
    }


def test_loads_profile_for_registered_language(tmp_path: Path) -> None:
    root = _repo(tmp_path, _valid_profile())
    profile = load_language_profile("python", root)
    assert profile.id == "python"
    assert profile.status == "active"
    assert profile.runtime["minimum"] == "3.11"
    assert profile.rule_domains_supported == ("testing", "security")


def test_loads_all_repository_language_profiles() -> None:
    root = Path(__file__).resolve().parents[2]
    registry = load_registry(root)
    for language in registry:
        profile = load_language_profile(language.id, root, registry=registry)
        assert profile.id == language.id
        assert profile.status == "active"


@pytest.mark.parametrize("language_id", ["../python", "", "A", "a/" , None])
def test_rejects_invalid_language_id(language_id: object, tmp_path: Path) -> None:
    with pytest.raises(ConfigError, match="invalid language id"):
        load_language_profile(language_id, tmp_path)  # type: ignore[arg-type]


def test_rejects_profile_id_mismatch(tmp_path: Path) -> None:
    data = _valid_profile()
    data["id"] = "ruby"
    with pytest.raises(ConfigError, match="id mismatch"):
        load_language_profile("python", _repo(tmp_path, data))


def test_rejects_unknown_language(tmp_path: Path) -> None:
    root = _repo(tmp_path, _valid_profile())
    with pytest.raises(ConfigError, match="unknown language"):
        load_language_profile("ruby", root)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("name", ""),
        ("family", ""),
        ("version", ""),
        ("status", "unsupported"),
        ("runtime", []),
        ("build_system", None),
        ("dependency_manager", []),
        ("testing", []),
        ("entry_points", []),
        ("rule_domains_supported", []),
        ("rule_domains_supported", ["testing", ""]),
        ("rule_domains_supported", ["testing", "testing"]),
        ("notes", 42),
    ],
)
def test_rejects_malformed_profile_fields(
    tmp_path: Path, field: str, value: object
) -> None:
    data = _valid_profile()
    data[field] = value
    with pytest.raises(ConfigError):
        load_language_profile("python", _repo(tmp_path, data))


def test_rejects_missing_profile(tmp_path: Path) -> None:
    root = _repo(tmp_path, _valid_profile())
    (root / "languages" / "python" / "language-profile.yaml").unlink()
    with pytest.raises(ConfigError, match="not found"):
        load_language_profile("python", root)


@pytest.mark.parametrize("contents", ["[not, a, mapping]", "not: [valid"])
def test_rejects_non_mapping_or_invalid_yaml(tmp_path: Path, contents: str) -> None:
    root = _repo(tmp_path, _valid_profile())
    (root / "languages" / "python" / "language-profile.yaml").write_text(
        contents, encoding="utf-8"
    )
    with pytest.raises(ConfigError):
        load_language_profile("python", root)


def test_rejects_profile_path_escape(tmp_path: Path) -> None:
    root = _repo(tmp_path, _valid_profile())
    registry_path = root / "languages" / "registry.yaml"
    data = yaml.safe_load(registry_path.read_text(encoding="utf-8"))
    data["languages"][0]["profile_path"] = "../outside.yaml"
    registry_path.write_text(yaml.safe_dump(data), encoding="utf-8")
    with pytest.raises(ConfigError, match="escapes"):
        load_language_profile("python", root)
