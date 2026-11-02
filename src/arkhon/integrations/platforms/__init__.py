"""Platform adapter registry."""
from __future__ import annotations
from arkhon.integrations.platforms.github_copilot import GitHubCopilotAdapter
_ADAPTERS={"github-copilot":GitHubCopilotAdapter}
def list_platforms()->list[str]: return sorted(_ADAPTERS)
def get_platform_adapter(platform_id:str):
 if platform_id not in _ADAPTERS:
  raise KeyError(f"unknown platform {platform_id!r}; available platforms: {', '.join(list_platforms())}")
 return _ADAPTERS[platform_id]()
__all__=["get_platform_adapter","list_platforms"]
