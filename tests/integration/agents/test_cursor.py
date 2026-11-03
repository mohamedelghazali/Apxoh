"""Contract test for the cursor integration scaffold."""
from pathlib import Path

import yaml


def test_adapter_is_explicitly_scaffolded_not_verified():
    config=yaml.safe_load(Path("integrations/generic-agents/cursor/config.yaml").read_text(encoding="utf-8"))
    assert config["status"] == "scaffolded"
    assert config["requires_user_consent"] is True
    assert config["verification_required"] is True
