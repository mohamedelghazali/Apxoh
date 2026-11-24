"""Load and index Apxoh enforcement policies."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from types import MappingProxyType
from typing import Any

import yaml

from arkhon.config import find_repo_root
from arkhon.core.errors import GovernanceError
from arkhon.core.logging import get_logger

logger = get_logger("governance.policy")
POLICY_CATEGORIES = ("blocking", "advisory", "exceptions")


@dataclass(frozen=True)
class Policy:
    id: str
    category: str
    path: Path
    raw: Mapping[str, Any]

    @property
    def title(self) -> str:
        return str(self.raw.get("title", self.id))

    @property
    def enabled(self) -> bool:
        return self.raw.get("enabled", True) is True

    @property
    def description(self) -> str:
        return str(self.raw.get("description", ""))


@dataclass
class PolicyLoadResult:
    policies: list[Policy] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors


class PolicyRegistry:
    """Read-only index of loaded policies."""

    __slots__ = ("_by_id", "_by_category")

    def __init__(self, policies: list[Policy]) -> None:
        by_id: dict[str, Policy] = {}
        by_category: dict[str, list[Policy]] = {c: [] for c in POLICY_CATEGORIES}
        for policy in policies:
            if policy.category not in POLICY_CATEGORIES:
                raise GovernanceError(f"unknown policy category: {policy.category}")
            if policy.id in by_id:
                raise GovernanceError(f"duplicate policy id '{policy.id}'")
            by_id[policy.id] = policy
            by_category[policy.category].append(policy)
        self._by_id = MappingProxyType(by_id)
        self._by_category = MappingProxyType(
            {key: tuple(value) for key, value in by_category.items()}
        )

    def get(self, policy_id: str) -> Policy:
        try:
            return self._by_id[policy_id]
        except KeyError as exc:
            raise GovernanceError(f"policy not found: {policy_id}") from exc

    def all(self) -> list[Policy]:
        return list(self._by_id.values())

    def _enabled(self, category: str) -> list[Policy]:
        return [p for p in self._by_category.get(category, ()) if p.enabled]

    def blocking(self) -> list[Policy]:
        return self._enabled("blocking")

    def advisory(self) -> list[Policy]:
        return self._enabled("advisory")

    def exceptions(self) -> list[Policy]:
        return self._enabled("exceptions")

    def __len__(self) -> int:
        return len(self._by_id)


def _load_policy_file(path: Path, category: str) -> Policy:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (yaml.YAMLError, OSError) as exc:
        raise GovernanceError(f"cannot load policy {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise GovernanceError(f"policy must be a mapping: {path}")
    policy_id = data.get("id")
    if not isinstance(policy_id, str) or not policy_id.strip():
        raise GovernanceError(f"policy missing valid 'id': {path}")
    enabled = data.get("enabled", True)
    if not isinstance(enabled, bool):
        raise GovernanceError(f"policy 'enabled' must be boolean: {path}")
    # Copy the top-level mapping so callers cannot mutate the loader's source object.
    return Policy(id=policy_id, category=category, path=path, raw=MappingProxyType(dict(data)))


def load_policies(root: Path | None = None) -> PolicyRegistry:
    """Load policies; fail closed if any discovered policy is malformed."""
    base = (root or find_repo_root()) / "system" / "policies"
    if not base.is_dir():
        raise GovernanceError(f"policies directory missing: {base}")
    policies: list[Policy] = []
    errors: list[str] = []
    for category in POLICY_CATEGORIES:
        category_dir = base / category
        if not category_dir.exists():
            continue
        if not category_dir.is_dir():
            errors.append(f"policy category path is not a directory: {category_dir}")
            continue
        for path in sorted((*category_dir.glob("*.yaml"), *category_dir.glob("*.yml"))):
            try:
                policies.append(_load_policy_file(path, category))
            except GovernanceError as exc:
                errors.append(str(exc))
    if errors:
        raise GovernanceError("policy loading failed: " + "; ".join(errors))
    registry = PolicyRegistry(policies)
    logger.debug("loaded %d policies", len(registry))
    return registry
