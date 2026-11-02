"""Contract test for the cline integration scaffold."""
from pathlib import Path
import yaml

def test_adapter_is_explicitly_scaffolded_not_verified():
    config=yaml.safe_load(Path("integrations/generic-agents/cline/config.yaml").read_text(encoding="utf-8"))
    assert config["status"] == "scaffolded"
