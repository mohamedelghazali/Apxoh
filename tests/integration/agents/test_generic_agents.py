"""Contract test for the generic-agents integration scaffold."""

from pathlib import Path

import yaml


def test_adapter_is_explicitly_scaffolded_not_verified():
    config = yaml.safe_load(
        Path("integrations/generic-agents/config.yaml").read_text(encoding="utf-8")
    )
    assert config["status"] == "manual"
