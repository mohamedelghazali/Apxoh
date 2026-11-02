"""Platform adapter registry."""
from __future__ import annotations

from arkhon.integrations.platforms.github_copilot import GitHubCopilotAdapter

_PLATFORM_FACTORIES = {"github-copilot": GitHubCopilotAdapter}


def list_platforms() -> list[str]:
    return sorted(_PLATFORM_FACTORIES)


def get_platform_adapter(platform_id: str):
    if platform_id not in _PLATFORM_FACTORIES:
        available = ", ".join(list_platforms())
        raise KeyError(f"unknown platform {platform_id!r}; available platforms: {available}")
    return _PLATFORM_FACTORIES[platform_id]()


__all__ = ["get_platform_adapter", "list_platforms"]
