"""Contract test for the replit-agent integration scaffold."""

from pathlib import Path

import yaml


def test_adapter_is_explicitly_scaffolded_not_verified():
    config = yaml.safe_load(
        Path("integrations/generic-agents/replit-agent/config.yaml").read_text(encoding="utf-8")
    )
    assert config["status"] == "scaffolded"
