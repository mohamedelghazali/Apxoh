"""Resolve required language tools without treating unknown versions as available."""

from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass, field
from enum import Enum

from arkhon.core.logging import get_logger

logger = get_logger("language_support.tool_resolver")


class ToolStatus(str, Enum):
    AVAILABLE = "AVAILABLE"
    MISSING = "MISSING"
    VERSION_UNKNOWN = "VERSION_UNKNOWN"


@dataclass(frozen=True)
class ToolCheck:
    name: str
    status: ToolStatus
    version: str = ""
    path: str = ""
    reason: str = ""


@dataclass
class ToolResolution:
    language_id: str
    tools: list[ToolCheck] = field(default_factory=list)

    @property
    def all_available(self) -> bool:
        return bool(self.tools) and all(item.status == ToolStatus.AVAILABLE for item in self.tools)

    @property
    def missing(self) -> list[ToolCheck]:
        return [item for item in self.tools if item.status == ToolStatus.MISSING]

    def get(self, name: str) -> ToolCheck | None:
        return next((item for item in self.tools if item.name == name), None)


_VERSION_ARGS: dict[str, list[str]] = {
    "python": ["--version"],
    "ruff": ["--version"],
    "mypy": ["--version"],
    "pytest": ["--version"],
    "bandit": ["--version"],
    "eslint": ["--version"],
    "tsc": ["--version"],
    "jest": ["--version"],
    "go": ["version"],
    "golangci-lint": ["--version"],
    "cargo": ["--version"],
    "clippy-driver": ["--version"],
    "rubocop": ["--version"],
    "rspec": ["--version"],
    "checkstyle": ["--version"],
    "dotnet": ["--version"],
    "cmake": ["--version"],
    "clang-tidy": ["--version"],
}


def _check_tool(name: str) -> ToolCheck:
    path = shutil.which(name)
    if not path:
        return ToolCheck(name, ToolStatus.MISSING, reason="not found on PATH")

    args = _VERSION_ARGS.get(name, ["--version"])
    try:
        result = subprocess.run(  # noqa: S603 - resolved executable and allow-listed version arguments
            [path, *args],
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
        )
    except (subprocess.TimeoutExpired, OSError) as exc:
        return ToolCheck(
            name,
            ToolStatus.VERSION_UNKNOWN,
            path=path,
            reason=f"version check failed: {exc}",
        )

    output = (result.stdout or "") + (result.stderr or "")
    version = output.strip().splitlines()[0] if output.strip() else ""
    if result.returncode != 0 or not version:
        return ToolCheck(
            name,
            ToolStatus.VERSION_UNKNOWN,
            path=path,
            reason=f"version command exited {result.returncode} or returned no version",
        )
    return ToolCheck(name, ToolStatus.AVAILABLE, version=version, path=path)


def resolve_tools(language_id: str, tools: list[str]) -> ToolResolution:
    logger.debug("resolving %d tools for %s", len(tools), language_id)
    return ToolResolution(language_id, [_check_tool(name) for name in tools])
