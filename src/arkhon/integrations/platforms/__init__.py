"""Platform adapter registry."""
from __future__ import annotations

from arkhon.integrations.platforms.github_copilot import GitHubCopilotAdapter

_PLATFORM_ADAPTERS = {
    "github-copilot": GitHubCopilotAdapter,
}


def list_platforms() -> list[str]:
    """Return registered platform identifiers in stable order."""
    return sorted(_PLATFORM_ADAPTERS)


def get_platform_adapter(platform_id: str):
    """Instantiate a registered platform adapter."""
    if platform_id not in _PLATFORM_ADAPTERS:
        available = ", ".join(list_platforms())
        raise KeyError(
            f"unknown platform {platform_id!r}; available platforms: {available}"
        )
    return _PLATFORM_ADAPTERS[platform_id]()


__all__ = ["get_platform_adapter", "list_platforms"]
