"""Tests for arkhon.language_support.registry."""

from __future__ import annotations

from pathlib import Path

import pytest

from arkhon.core.errors import ConfigError
from arkhon.language_support.registry import (
    LanguageDefinition,
    load_registry,
)


def test_load_default_registry() -> None:
    reg = load_registry()
    assert reg.engine_language == "python"
    assert reg.version == "1.0.0"


def test_registry_has_nine_languages() -> None:
    reg = load_registry()
    assert len(reg) == 9


def test_registry_ids() -> None:
    reg = load_registry()
    expected = {
        "python",
        "javascript",
        "typescript",
        "java",
        "csharp",
        "cpp",
        "go",
        "rust",
        "ruby",
    }
    assert set(reg.ids()) == expected


def test_get_python() -> None:
    reg = load_registry()
    py = reg.get("python")
    assert isinstance(py, LanguageDefinition)
    assert py.id == "python"
    assert ".py" in py.extensions


def test_get_unknown_raises() -> None:
    reg = load_registry()
    with pytest.raises(ConfigError, match="unknown language"):
        reg.get("cobol")


def test_extension_lookup() -> None:
    reg = load_registry()
    assert reg.language_for_extension(".py") == "python"
    assert reg.language_for_extension(".ts") == "typescript"
    assert reg.language_for_extension(".go") == "go"
    assert reg.language_for_extension(".zzz") is None


def test_extension_lookup_case_insensitive() -> None:
    reg = load_registry()
    assert reg.language_for_extension(".PY") == "python"
    assert reg.language_for_extension(".Ts") == "typescript"


def test_iteration() -> None:
    reg = load_registry()
    langs = list(reg)
    assert len(langs) == 9


def test_all_returns_list() -> None:
    reg = load_registry()
    assert isinstance(reg.all(), list)
    assert len(reg.all()) == 9


def test_registry_missing_raises(tmp_path: Path) -> None:
    with pytest.raises(ConfigError, match="not found"):
        load_registry(tmp_path)


def test_registry_invalid_yaml(tmp_path: Path) -> None:
    (tmp_path / "languages").mkdir()
    (tmp_path / "languages" / "registry.yaml").write_text("- not a mapping", encoding="utf-8")
    with pytest.raises(ConfigError, match="must be a mapping"):
        load_registry(tmp_path)


def test_every_language_has_milestone() -> None:
    reg = load_registry()
    for lang in reg.all():
        assert lang.milestone >= 0


def test_registry_rejects_duplicate_extension_and_invalid_entries(tmp_path: Path) -> None:
    import yaml

    from arkhon.core.errors import ConfigError
    from arkhon.language_support.registry import _parse_language, load_registry

    folder = tmp_path / "languages"
    folder.mkdir()
    (folder / "registry.yaml").write_text(
        yaml.safe_dump({
            "languages": [
                {"id": "one", "detection": {"extensions": [".x"]}},
                {"id": "two", "detection": {"extensions": [".x"]}},
            ]
        }),
        encoding="utf-8",
    )
    with pytest.raises(ConfigError, match="assigned to multiple languages"):
        load_registry(tmp_path)
    (folder / "registry.yaml").write_text("languages: [bad]", encoding="utf-8")
    with pytest.raises(ConfigError, match="entry 0"):
        load_registry(tmp_path)
    with pytest.raises(ConfigError, match="detection and planned_tools"):
        _parse_language({"id": "broken", "detection": [], "planned_tools": {}})
