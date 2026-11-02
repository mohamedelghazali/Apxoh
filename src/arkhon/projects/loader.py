"""Load and validate Apxoh project profiles from projects/<name>/."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from arkhon.config import find_repo_root
from arkhon.core.errors import ConfigError
from arkhon.core.logging import get_logger

logger = get_logger("projects.loader")
_PROFILE_NAME = re.compile(r"^[a-z][a-z0-9-]{0,62}$")


@dataclass(frozen=True)
class ProjectProfile:
    """A loaded profile; nested mappings are treated as read-only by convention."""

    name: str
    description: str
    risk_level: str
    rules: dict[str, Any] = field(default_factory=dict)
    gates: dict[str, Any] = field(default_factory=dict)
    evidence: dict[str, Any] = field(default_factory=dict)

    @property
    def active_domains(self) -> list[str]:
        domains = self.rules.get("domains", [])
        return list(domains) if isinstance(domains, list) else []

    @property
    def required_gates(self) -> list[str]:
        required = self.gates.get("required", [])
        return list(required) if isinstance(required, list) else []


def _load_yaml(path: Path, *, required: bool = True) -> dict[str, Any]:
    if not path.is_file():
        if required:
            raise ConfigError(f"profile file missing: {path}")
        return {}
    try:
        with path.open("r", encoding="utf-8") as stream:
            data = yaml.safe_load(stream)
    except (yaml.YAMLError, OSError) as exc:
        raise ConfigError(f"cannot read valid YAML from {path}: {exc}") from exc
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise ConfigError(f"profile file must contain a YAML mapping: {path}")
    return data


def _validate_profile_data(name: str, profile: dict[str, Any], rules: dict[str, Any],
                           gates: dict[str, Any]) -> None:
    declared = profile.get("name", name)
    if declared != name:
        raise ConfigError(f"profile name mismatch: directory={name!r}, file={declared!r}")
    risk = profile.get("risk_level", "medium")
    if risk not in {"low", "medium", "high", "critical"}:
        raise ConfigError(f"profile {name!r} has invalid risk_level: {risk!r}")
    domains = rules.get("domains", [])
    if not isinstance(domains, list) or not all(isinstance(item, str) and item for item in domains):
        raise ConfigError(f"profile {name!r}: rules.domains must be a list of non-empty strings")
    required = gates.get("required", [])
    if not isinstance(required, list) or not all(isinstance(item, str) and item for item in required):
        raise ConfigError(f"profile {name!r}: gates.required must be a list of non-empty strings")


def load_profile(name: str, root: Path | None = None) -> ProjectProfile:
    """Load a profile by safe directory name; reject traversal and malformed data."""
    if not _PROFILE_NAME.fullmatch(name):
        raise ConfigError(f"invalid profile name: {name!r}")
    repo_root = (root or find_repo_root()).resolve()
    profiles_root = (repo_root / "projects").resolve()
    base = (profiles_root / name).resolve()
    try:
        base.relative_to(profiles_root)
    except ValueError as exc:
        raise ConfigError(f"profile path escapes projects directory: {name!r}") from exc
    if not base.is_dir():
        raise ConfigError(f"profile not found: {name}")
    profile_data = _load_yaml(base / "profile.yaml")
    rules_data = _load_yaml(base / "rules.yaml", required=False)
    gates_data = _load_yaml(base / "gates.yaml", required=False)
    _validate_profile_data(name, profile_data, rules_data, gates_data)

    evidence = profile_data.get("evidence", {})
    if not isinstance(evidence, dict):
        raise ConfigError(f"profile {name!r}: evidence must be a mapping")
    result = ProjectProfile(
        name=name,
        description=str(profile_data.get("description", "")),
        risk_level=str(profile_data.get("risk_level", "medium")),
        rules=rules_data,
        gates=gates_data,
        evidence=evidence,
    )
    logger.debug("loaded profile %s (risk=%s)", name, result.risk_level)
    return result


def list_profiles(root: Path | None = None) -> list[str]:
    """List profile directories containing profile.yaml; ignore private directories."""
    profiles_root = ((root or find_repo_root()).resolve() / "projects").resolve()
    if not profiles_root.is_dir():
        return []
    return sorted(
        path.name for path in profiles_root.iterdir()
        if path.is_dir() and not path.name.startswith("_")
        and _PROFILE_NAME.fullmatch(path.name)
        and (path / "profile.yaml").is_file()
    )
