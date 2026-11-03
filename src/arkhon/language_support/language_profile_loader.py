"""Load and validate registered language profiles."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Any

import yaml

from arkhon.config import find_repo_root
from arkhon.core.errors import ConfigError
from arkhon.language_support.registry import LanguageRegistry, load_registry

_LANGUAGE_ID = re.compile(r"^[a-z][a-z0-9-]{0,62}$")
_STATUSES = frozenset({"active", "experimental", "planned", "deprecated"})


@dataclass(frozen=True)
class LanguageProfile:
    """Validated language profile with read-only top-level sections."""

    id: str
    name: str
    family: str
    version: str
    status: str
    runtime: Any
    build_system: Any
    dependency_manager: Any
    testing: Any
    rule_domains_supported: tuple[str, ...]
    entry_points: Any
    notes: str


def _section(raw: dict[str, Any], key: str, language_id: str, *, optional: bool = False) -> dict[str, Any]:
    value = raw.get(key, {} if optional else None)
    if not isinstance(value, dict) or (not optional and not value):
        raise ConfigError(f"language profile {language_id}: {key} must be a non-empty mapping")
    return dict(value)


def _text(raw: dict[str, Any], key: str, language_id: str) -> str:
    value = raw.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ConfigError(f"language profile {language_id}: {key} must be a non-empty string")
    return value.strip()


def load_language_profile(
    language_id: str,
    root: Path | None = None,
    *,
    registry: LanguageRegistry | None = None,
) -> LanguageProfile:
    """Load a registered profile, rejecting malformed IDs and path traversal."""
    if not isinstance(language_id, str) or not _LANGUAGE_ID.fullmatch(language_id):
        raise ConfigError(f"invalid language id: {language_id!r}")
    repo_root = (root or find_repo_root()).resolve()
    language_registry = registry or load_registry(repo_root)
    definition = language_registry.get(language_id)
    relative = definition.profile_path or f"languages/{language_id}/language-profile.yaml"
    languages_root = (repo_root / "languages").resolve()
    path = (repo_root / relative).resolve()
    try:
        path.relative_to(languages_root)
    except ValueError as exc:
        raise ConfigError(f"language profile path escapes languages directory: {relative!r}") from exc
    if not path.is_file():
        raise ConfigError(f"language profile not found for {language_id}: {path}")
    try:
        with path.open("r", encoding="utf-8") as stream:
            raw = yaml.safe_load(stream)
    except (OSError, yaml.YAMLError) as exc:
        raise ConfigError(f"cannot read language profile {path}: {exc}") from exc
    if not isinstance(raw, dict):
        raise ConfigError(f"language profile must be a YAML mapping: {path}")

    declared_id = _text(raw, "id", language_id)
    if declared_id != language_id:
        raise ConfigError(f"language profile id mismatch: requested={language_id!r}, declared={declared_id!r}")
    name, family, version, status = (
        _text(raw, key, language_id) for key in ("name", "family", "version", "status")
    )
    if status not in _STATUSES:
        raise ConfigError(f"language profile {language_id}: unsupported status {status!r}")
    domains = raw.get("rule_domains_supported")
    if not isinstance(domains, list) or not domains or any(
        not isinstance(item, str) or not item.strip() for item in domains
    ):
        raise ConfigError(f"language profile {language_id}: rule_domains_supported must be a non-empty list of strings")
    if len(set(domains)) != len(domains):
        raise ConfigError(f"language profile {language_id}: duplicate rule domains")
    notes = raw.get("notes", "")
    if not isinstance(notes, str):
        raise ConfigError(f"language profile {language_id}: notes must be a string")

    sections = {
        key: MappingProxyType(_section(raw, key, language_id, optional=key == "entry_points"))
        for key in ("runtime", "build_system", "dependency_manager", "testing", "entry_points")
    }
    return LanguageProfile(
        id=language_id, name=name, family=family, version=version, status=status,
        runtime=sections["runtime"], build_system=sections["build_system"],
        dependency_manager=sections["dependency_manager"], testing=sections["testing"],
        rule_domains_supported=tuple(domains), entry_points=sections["entry_points"], notes=notes,
    )
