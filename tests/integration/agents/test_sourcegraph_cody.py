"""Contract test for the sourcegraph-cody integration scaffold."""
from pathlib import Path
import yaml

def test_adapter_is_explicitly_scaffolded_not_verified():
    config=yaml.safe_load(Path("integrations/sourcegraph-cody/config.yaml").read_text(encoding="utf-8"))
    assert config["status"] == "scaffolded"
