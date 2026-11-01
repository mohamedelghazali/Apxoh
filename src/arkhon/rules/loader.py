"""Load YAML rule documents from a rules directory."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from arkhon.core.errors import RuleDuplicateError, RuleError, RuleValidationError
from arkhon.core.logging import get_logger

logger = get_logger("rules.loader")


@dataclass(frozen=True)
class Rule:
    """Loaded rule; raw data is a parsed mapping."""
    id: str
    path: Path
    raw: dict[str, Any]

    @property
    def metadata(self) -> dict[str, Any]:
        value = self.raw.get("metadata", {})
        return value if isinstance(value, dict) else {}

    @property
    def title(self) -> str:
        return str(self.metadata.get("title", ""))

    @property
    def domain(self) -> str:
        return str(self.metadata.get("domain", ""))

    @property
    def version(self) -> str:
        return str(self.metadata.get("version", "0.0.0"))

    @property
    def status(self) -> str:
        return str(self.metadata.get("status", ""))

    @property
    def severity(self) -> str:
        return str(self.metadata.get("severity", ""))

    @property
    def enforcement(self) -> str:
        return str(self.metadata.get("enforcement", ""))


@dataclass
class LoadResult:
    """Result of loading a rules directory."""
    rules: list[Rule] = field(default_factory=list)
    errors: list[RuleError] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors


def _read_yaml(path: Path) -> dict[str, Any]:
    try:
        with path.open("r", encoding="utf-8") as fh:
            data = yaml.safe_load(fh)
    except (yaml.YAMLError, OSError) as exc:
        raise RuleValidationError(f"could not read valid YAML from {path}: {exc}") from exc
    if data is None:
        raise RuleValidationError(f"empty YAML file: {path}")
    if not isinstance(data, dict):
        raise RuleValidationError(f"rule file must be a mapping: {path}")
    return data


def load_rule_file(path: Path) -> Rule:
    """Load one YAML rule file."""
    if not path.is_file():
        raise RuleError(f"rule file not found: {path}")
    if path.suffix.lower() not in {".yaml", ".yml"}:
        raise RuleError(f"rule file must be YAML (.yaml/.yml): {path}")
    raw = _read_yaml(path)
    rule_id = raw.get("id")
    if not isinstance(rule_id, str) or not rule_id.strip():
        raise RuleValidationError(f"rule is missing a valid 'id': {path}")
    return Rule(id=rule_id, path=path, raw=raw)


def load_rules_dir(directory: Path, *, recursive: bool = True) -> LoadResult:
    """Load .yaml and .yml rules; underscore-prefixed files are templates."""
    result = LoadResult()
    if not directory.exists():
        result.warnings.append(f"rules directory does not exist: {directory}")
        return result
    if not directory.is_dir():
        result.errors.append(RuleError(f"not a directory: {directory}"))
        return result

    patterns = ("**/*.yaml", "**/*.yml") if recursive else ("*.yaml", "*.yml")
    files = sorted({path for pattern in patterns for path in directory.glob(pattern)})
    seen: dict[str, Path] = {}
    for path in files:
        if path.name.startswith("_"):
            continue
        try:
            rule = load_rule_file(path)
        except RuleError as exc:
            result.errors.append(exc)
            continue
        if rule.id in seen:
            result.errors.append(RuleDuplicateError(
                f"duplicate rule id '{rule.id}': {path} and {seen[rule.id]}"
            ))
            continue
        seen[rule.id] = path
        result.rules.append(rule)
        logger.debug("loaded rule %s from %s", rule.id, path)
    return result
