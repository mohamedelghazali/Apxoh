"""Base interfaces for Apxoh integrations.

Integrations collect external results. They never make governance or release
decisions; Apxoh validates every returned artifact and claim.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class IntegrationInfo:
    """Static, descriptive metadata for an integration."""

    id: str
    kind: str
    provider: str
    version: str
    capabilities: tuple[str, ...] = ()


@dataclass
class IntegrationResponse:
    """Untrusted result returned by an integration."""

    ok: bool
    payload: dict[str, Any] = field(default_factory=dict)
    artifacts: list[Path] = field(default_factory=list)
    reason: str = ""


class Integration(ABC):
    """Base class for model, platform, security, and generic integrations."""

    @property
    @abstractmethod
    def info(self) -> IntegrationInfo:
        """Return static integration metadata."""

    @abstractmethod
    def health_check(self) -> bool:
        """Return whether the integration is reachable and configured."""

    def __repr__(self) -> str:
        info = self.info
        return f"<{type(self).__name__} id={info.id!r} kind={info.kind!r}>"
