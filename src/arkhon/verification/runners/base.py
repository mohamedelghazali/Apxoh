"""Runner interface for independent verification tools."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


class RunnerOutcome(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    BLOCKED = "BLOCKED"


@dataclass(frozen=True)
class RunnerResult:
    runner: str
    outcome: RunnerOutcome
    reason: str = ""
    artifacts: list[Path] = field(default_factory=list)


class Runner(ABC):
    """A deterministic runner that reports results and generated artifacts."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Stable runner identifier used in evidence."""

    @abstractmethod
    def run(self, project_root: Path) -> RunnerResult:
        """Execute verification; expected failures should be returned, not raised."""
