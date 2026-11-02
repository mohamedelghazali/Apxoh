"""Conservative GitHub Copilot platform boundary."""
from __future__ import annotations
from arkhon.integrations.base import Integration, IntegrationInfo
class GitHubCopilotAdapter(Integration):
 @property
 def info(self)->IntegrationInfo:
  return IntegrationInfo(id="github-copilot",kind="platform",provider="github-microsoft",
   version="1.0.0",capabilities=("instruction-discovery",))
 def health_check(self)->bool:
  # Scaffolded integration requires explicit platform-side configuration.
  return False
