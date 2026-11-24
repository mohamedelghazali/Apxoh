"""Load and validate the Apxoh engineering charter."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from arkhon.config import find_repo_root
from arkhon.core.errors import GovernanceError
from arkhon.core.logging import get_logger

logger = get_logger("governance.charter")
REQUIRED_PRINCIPLES = 12


@dataclass(frozen=True)
class Principle:
    number: int
    statement: str

    def __post_init__(self) -> None:
        if self.number < 1:
            raise GovernanceError(f"principle number must be >= 1, got {self.number}")
        if not self.statement.strip():
            raise GovernanceError(f"principle {self.number}: empty statement")


@dataclass(frozen=True)
class Charter:
    path: Path
    text: str
    principles: tuple[Principle, ...]
    version: str

    def principle(self, number: int) -> Principle:
        for principle in self.principles:
            if principle.number == number:
                return principle
        raise GovernanceError(f"principle {number} not found")

    @property
    def count(self) -> int:
        return len(self.principles)


def _load_yaml(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise GovernanceError(f"charter YAML missing: {path}")
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (yaml.YAMLError, OSError) as exc:
        raise GovernanceError(f"cannot load charter YAML {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise GovernanceError(f"charter YAML must be a mapping: {path}")
    return data


def _parse_principles(data: dict[str, Any]) -> tuple[Principle, ...]:
    raw = data.get("principles")
    if not isinstance(raw, list) or len(raw) != REQUIRED_PRINCIPLES:
        count = len(raw) if isinstance(raw, list) else "not a list"
        raise GovernanceError(
            f"charter requires exactly {REQUIRED_PRINCIPLES} principles; got {count}"
        )
    principles: list[Principle] = []
    for index, item in enumerate(raw, start=1):
        if not isinstance(item, dict):
            raise GovernanceError(f"charter principle #{index} must be a mapping")
        number, statement = item.get("number", index), item.get("statement", "")
        if (
            isinstance(number, bool)
            or not isinstance(number, int)
            or not isinstance(statement, str)
        ):
            raise GovernanceError(f"charter principle #{index} has invalid fields")
        principles.append(Principle(number=number, statement=statement))
    numbers = [p.number for p in principles]
    if numbers != list(range(1, REQUIRED_PRINCIPLES + 1)):
        raise GovernanceError("charter principle numbers must be unique and ordered 1..12")
    return tuple(principles)


def load_charter(root: Path | None = None) -> Charter:
    """Load the Markdown charter and its machine-readable YAML companion."""
    base = (root or find_repo_root()) / "system" / "charter"
    md_path, yaml_path = base / "ENGINEERING_CHARTER.md", base / "PRINCIPLES.yaml"
    try:
        text = md_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise GovernanceError(f"charter markdown missing or unreadable: {md_path}: {exc}") from exc
    data = _load_yaml(yaml_path)
    principles = _parse_principles(data)
    version = data.get("version", "0.0.0")
    if not isinstance(version, str) or not version.strip():
        raise GovernanceError("charter version must be a non-empty string")
    logger.debug("loaded charter v%s with %d principles", version, len(principles))
    return Charter(path=md_path, text=text, principles=principles, version=version)
