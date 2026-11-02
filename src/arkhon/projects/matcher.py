"""Select an explicit project profile or infer a conservative default."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from arkhon.core.errors import ConfigError
from arkhon.core.logging import get_logger

logger = get_logger("projects.matcher")


@dataclass(frozen=True)
class Match:
    profile: str
    reason: str
    explicit: bool


def _read_declared_profile(project_root: Path) -> str | None:
    path = project_root / ".arkhon" / "project.yaml"
    if not path.is_file():
        return None
    try:
        with path.open("r", encoding="utf-8") as stream:
            data = yaml.safe_load(stream)
    except (yaml.YAMLError, OSError) as exc:
        raise ConfigError(f"cannot read project declaration {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise ConfigError(f"project declaration must be a YAML mapping: {path}")
    project: Any = data.get("project")
    if not isinstance(project, dict):
        raise ConfigError(f"project declaration is missing its 'project' mapping: {path}")
    profile = project.get("profile")
    if not isinstance(profile, str) or not profile.strip():
        raise ConfigError(f"project declaration has an invalid profile: {path}")
    return profile.strip()


def _infer_profile(project_root: Path) -> Match:
    """Heuristics are advisory; callers should require confirmation when uncertain."""
    if (project_root / "android").is_dir() or (project_root / "ios").is_dir():
        return Match("mobile-application", "found android/ or ios/", False)
    if (project_root / "electron").is_dir() or (project_root / "tauri").is_dir():
        return Match("desktop-application", "found electron/ or tauri/", False)
    if ((project_root / "k8s").is_dir() or (project_root / "helm").is_dir()
            or (project_root / "docker-compose.yml").is_file()
            or (project_root / "docker-compose.yaml").is_file()):
        return Match("distributed-system", "found Kubernetes or Compose markers", False)
    if ((project_root / "openapi.yaml").is_file()
            or (project_root / "openapi.yml").is_file()
            or (project_root / "openapi.json").is_file()):
        return Match("api-service", "found OpenAPI specification", False)
    if (project_root / "public").is_dir() or (project_root / "static").is_dir():
        return Match("web-application", "found public/ or static/", False)
    return Match("universal", "no specific project markers found", False)


def match_profile(project_root: Path) -> Match:
    """Return the explicit profile if declared; otherwise return a heuristic match."""
    root = project_root.resolve()
    if not root.is_dir():
        raise ConfigError(f"project root is not a directory: {root}")
    declared = _read_declared_profile(root)
    if declared is not None:
        logger.debug("project declares profile: %s", declared)
        return Match(declared, "declared in .arkhon/project.yaml", True)
    inferred = _infer_profile(root)
    logger.debug("inferred profile: %s (%s)", inferred.profile, inferred.reason)
    return inferred


def validate_profile_name(name: str, available: list[str]) -> None:
    if name not in available:
        raise ConfigError(f"unknown profile {name!r}; available profiles: {sorted(available)}")
