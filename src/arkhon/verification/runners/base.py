"""ARKHON package module."""
from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
from arkhon.core.constants import Status
@dataclass(frozen=True)
class RunnerResult:
    status: Status
    tool: str
    message: str
    exit_code: int | None = None
class VerificationRunner(ABC):
    @abstractmethod
    def run(self,target: str) -> RunnerResult: """Run a bounded verification."""
