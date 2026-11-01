"""Read-only lookup index for loaded rules."""
from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from types import MappingProxyType
from typing import Mapping

from arkhon.core.errors import RuleError, RuleNotFoundError
from arkhon.rules.loader import Rule, load_rules_dir


class RuleRegistry:
    """Rule index with read-only mapping views."""
    __slots__ = ("_by_id", "_by_domain", "_by_enforcement", "_by_severity", "_by_status")

    def __init__(self, rules: list[Rule]) -> None:
        by_id: dict[str, Rule] = {}
        by_domain: defaultdict[str, list[Rule]] = defaultdict(list)
        by_enforcement: defaultdict[str, list[Rule]] = defaultdict(list)
        by_severity: defaultdict[str, list[Rule]] = defaultdict(list)
        by_status: defaultdict[str, list[Rule]] = defaultdict(list)
        for rule in rules:
            if rule.id in by_id:
                raise RuleError(f"duplicate rule id in registry: {rule.id}")
            by_id[rule.id] = rule
            by_domain[rule.domain].append(rule)
            by_enforcement[rule.enforcement].append(rule)
            by_severity[rule.severity].append(rule)
            by_status[rule.status].append(rule)
        self._by_id: Mapping[str, Rule] = MappingProxyType(by_id)
        self._by_domain = MappingProxyType({key: tuple(value) for key, value in by_domain.items()})
        self._by_enforcement = MappingProxyType({
            key: tuple(value) for key, value in by_enforcement.items()
        })
        self._by_severity = MappingProxyType({
            key: tuple(value) for key, value in by_severity.items()
        })
        self._by_status = MappingProxyType({key: tuple(value) for key, value in by_status.items()})

    def get(self, rule_id: str) -> Rule:
        try:
            return self._by_id[rule_id]
        except KeyError as exc:
            raise RuleNotFoundError(f"rule not found: {rule_id}") from exc

    def all(self) -> list[Rule]:
        return list(self._by_id.values())

    def by_domain(self, domain: str) -> list[Rule]:
        return list(self._by_domain.get(domain, ()))

    def by_enforcement(self, level: str) -> list[Rule]:
        return list(self._by_enforcement.get(level, ()))

    def by_severity(self, severity: str) -> list[Rule]:
        return list(self._by_severity.get(severity, ()))

    def by_status(self, status: str) -> list[Rule]:
        return list(self._by_status.get(status, ()))

    def domains(self) -> list[str]:
        return sorted(self._by_domain)

    def active(self) -> list[Rule]:
        return self.by_status("active")

    def __len__(self) -> int:
        return len(self._by_id)

    def __contains__(self, rule_id: object) -> bool:
        return isinstance(rule_id, str) and rule_id in self._by_id


def build_registry(rules_dir: Path) -> RuleRegistry:
    """Build an index, refusing to hide any load errors."""
    result = load_rules_dir(rules_dir)
    if result.errors:
        details = "; ".join(str(error) for error in result.errors)
        raise RuleError(f"cannot build registry; rule loading failed: {details}")
    if result.warnings:
        raise RuleError("cannot build registry: " + "; ".join(result.warnings))
    return RuleRegistry(result.rules)
