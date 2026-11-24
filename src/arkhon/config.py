"""Manifest loader for Apxoh.

The manifest is split across manifest/*.yaml. This module is the only
place that knows how to load and combine the files.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

from arkhon.core.errors import ManifestError

_MANIFEST_FILES = (
    "system",
    "products",
    "integrations",
    "languages",
    "standards",
    "compatibility",
)


def find_repo_root() -> Path:
    """Locate the repository using APXOH_ROOT or this package's parents."""
    env = os.environ.get("APXOH_ROOT")
    if env:
        candidate = Path(env).expanduser().resolve()
        if (candidate / "manifest" / "index.yaml").is_file():
            return candidate
        raise ManifestError(f"APXOH_ROOT does not contain manifest/index.yaml: {candidate}")

    current = Path(__file__).resolve().parent
    for _ in range(12):
        if (current / "manifest" / "index.yaml").is_file():
            return current
        if current.parent == current:
            break
        current = current.parent
    raise ManifestError(
        "Could not locate Apxoh repository root. Set APXOH_ROOT or run from a checkout."
    )


def _load_yaml(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise ManifestError(f"manifest file missing: {path}")
    try:
        with path.open("r", encoding="utf-8") as fh:
            data = yaml.safe_load(fh)
    except (yaml.YAMLError, OSError) as exc:
        raise ManifestError(f"could not read valid YAML from {path}: {exc}") from exc
    if data is None:
        raise ManifestError(f"manifest file is empty: {path}")
    if not isinstance(data, dict):
        raise ManifestError(f"manifest file must be a mapping: {path}")
    return data


@dataclass(frozen=True)
class Manifest:
    """Combined manifest. Nested dictionaries are not deeply immutable."""

    index: dict[str, Any]
    system: dict[str, Any]
    products: dict[str, Any]
    integrations: dict[str, Any]
    languages: dict[str, Any]
    standards: dict[str, Any]
    compatibility: dict[str, Any]

    @property
    def name(self) -> str:
        try:
            return str(self.system["system"]["name"])
        except (KeyError, TypeError) as exc:
            raise ManifestError("manifest system.name is missing") from exc

    @property
    def identifier(self) -> str:
        try:
            return str(self.system["system"]["identifier"])
        except (KeyError, TypeError) as exc:
            raise ManifestError("manifest system.identifier is missing") from exc

    @property
    def version(self) -> str:
        try:
            return str(self.system["system"]["version"])
        except (KeyError, TypeError) as exc:
            raise ManifestError("manifest system.version is missing") from exc

    def to_dict(self) -> dict[str, Any]:
        return {
            "index": self.index,
            "system": self.system,
            "products": self.products,
            "integrations": self.integrations,
            "languages": self.languages,
            "standards": self.standards,
            "compatibility": self.compatibility,
        }


def load_manifest(root: Path | None = None) -> Manifest:
    """Load referenced manifest files while preventing path traversal."""
    base = ((root or find_repo_root()).resolve() / "manifest").resolve()
    index = _load_yaml(base / "index.yaml")
    files = index.get("files")
    if not isinstance(files, dict):
        raise ManifestError("manifest/index.yaml: missing or invalid 'files' map")

    missing = [key for key in _MANIFEST_FILES if key not in files]
    if missing:
        raise ManifestError(f"manifest/index.yaml missing references: {', '.join(missing)}")

    loaded: dict[str, dict[str, Any]] = {}
    for key in _MANIFEST_FILES:
        rel = files[key]
        if not isinstance(rel, str) or not rel.strip():
            raise ManifestError(f"manifest/index.yaml: files.{key} must be a non-empty string")
        candidate = (base / rel).resolve()
        if candidate != base and base not in candidate.parents:
            raise ManifestError(f"manifest/index.yaml: files.{key} escapes manifest directory")
        loaded[key] = _load_yaml(candidate)
    return Manifest(index=index, **loaded)


@lru_cache(maxsize=1)
def get_manifest() -> Manifest:
    """Return the process-cached manifest."""
    return load_manifest()
