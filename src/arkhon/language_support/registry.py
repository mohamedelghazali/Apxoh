"""Language registry.

Loads ``languages/registry.yaml`` and exposes it as an immutable,
typed object. Provides lookups by id, extension, and build file.
"""

from __future__ import annotations

from collections.abc import Iterator, Mapping
from dataclasses import dataclass, field
from pathlib import Path
from types import MappingProxyType
from typing import Any

import yaml

from arkhon.config import find_repo_root
from arkhon.core.errors import ConfigError
from arkhon.core.logging import get_logger

logger = get_logger("language_support.registry")


@dataclass(frozen=True)
class LanguageDefinition:
    id: str
    name: str
    family: str
    primary_use: tuple[str, ...]
    status: str
    extensions: tuple[str, ...]
    build_files: tuple[str, ...]
    lock_files: tuple[str, ...]
    planned_tools: Mapping[str, tuple[str, ...]]
    profile_path: str
    rules_path: str
    milestone: int


@dataclass(frozen=True)
class LanguageRegistry:
    engine_language: str
    version: str
    _languages: Mapping[str, LanguageDefinition] = field(default_factory=dict)
    _by_extension: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "_languages", MappingProxyType(dict(self._languages)))
        object.__setattr__(self, "_by_extension", MappingProxyType(dict(self._by_extension)))

    def get(self, lang_id: str) -> LanguageDefinition:
        try:
            return self._languages[lang_id]
        except KeyError as exc:
            raise ConfigError(f"unknown language: {lang_id}") from exc

    def all(self) -> list[LanguageDefinition]:
        return list(self._languages.values())

    def ids(self) -> list[str]:
        return sorted(self._languages)

    def language_for_extension(self, ext: str) -> str | None:
        return self._by_extension.get(ext.lower())

    def __len__(self) -> int:
        return len(self._languages)

    def __iter__(self) -> Iterator[LanguageDefinition]:
        return iter(self._languages.values())


def _parse_language(raw: dict[str, Any]) -> LanguageDefinition:
    detection = raw.get("detection", {})
    planned = raw.get("planned_tools", {})
    if not isinstance(detection, dict) or not isinstance(planned, dict):
        raise ConfigError("language detection and planned_tools must be mappings")

    lang_id = raw.get("id")
    if not isinstance(lang_id, str) or not lang_id.strip():
        raise ConfigError("language id must be a non-empty string")

    def string_tuple(value: Any, field_name: str) -> tuple[str, ...]:
        if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
            raise ConfigError(f"language {lang_id}: {field_name} must be a list of strings")
        return tuple(value)

    tools: dict[str, tuple[str, ...]] = {}
    for key, value in planned.items():
        if not isinstance(key, str) or not isinstance(value, list) or any(
            not isinstance(item, str) for item in value
        ):
            raise ConfigError(f"language {lang_id}: invalid planned_tools entry {key!r}")
        tools[key] = tuple(value)

    milestone = raw.get("milestone", 0)
    if isinstance(milestone, bool) or not isinstance(milestone, int) or milestone < 0:
        raise ConfigError(f"language {lang_id}: milestone must be a non-negative integer")

    return LanguageDefinition(
        id=lang_id,
        name=str(raw.get("name", lang_id)),
        family=str(raw.get("family", "unknown")),
        primary_use=string_tuple(raw.get("primary_use", []), "primary_use"),
        status=str(raw.get("status", "unknown")),
        extensions=tuple(ext.lower() for ext in string_tuple(detection.get("extensions", []), "extensions")),
        build_files=string_tuple(detection.get("build_files", []), "build_files"),
        lock_files=string_tuple(detection.get("lock_files", []), "lock_files"),
        planned_tools=MappingProxyType(tools),
        profile_path=str(raw.get("profile_path", "")),
        rules_path=str(raw.get("rules_path", "")),
        milestone=milestone,
    )


def load_registry(root: Path | None = None) -> LanguageRegistry:
    path = (root or find_repo_root()) / "languages" / "registry.yaml"
    if not path.is_file():
        raise ConfigError(f"language registry not found: {path}")

    try:
        with path.open("r", encoding="utf-8") as fh:
            data = yaml.safe_load(fh)
    except (OSError, yaml.YAMLError) as exc:
        raise ConfigError(f"cannot read language registry {path}: {exc}") from exc

    if not isinstance(data, dict):
        raise ConfigError(f"language registry must be a mapping: {path}")
    raw_languages = data.get("languages")
    if not isinstance(raw_languages, list) or not raw_languages:
        raise ConfigError(f"language registry must contain a non-empty languages list: {path}")

    languages: dict[str, LanguageDefinition] = {}
    by_extension: dict[str, str] = {}
    for index, raw in enumerate(raw_languages):
        if not isinstance(raw, dict):
            raise ConfigError(f"language entry {index} must be a mapping")
        lang = _parse_language(raw)
        if lang.id in languages:
            raise ConfigError(f"duplicate language id: {lang.id}")
        languages[lang.id] = lang
        for ext in lang.extensions:
            if not ext.startswith(".") or ext == ".":
                raise ConfigError(f"language {lang.id}: invalid extension {ext!r}")
            if ext in by_extension and by_extension[ext] != lang.id:
                raise ConfigError(f"extension {ext!r} is assigned to multiple languages")
            by_extension[ext] = lang.id

    return LanguageRegistry(
        engine_language=str(data.get("engine_language", "python")),
        version=str(data.get("version", "0.0.0")),
        _languages=languages,
        _by_extension=by_extension,
    )
