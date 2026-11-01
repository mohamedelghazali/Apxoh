"""Contract test for the tabnine integration scaffold."""
from pathlib import Path
import yaml

def test_adapter_is_explicitly_scaffolded_not_verified():
    config=yaml.safe_load(Path("integrations/tabnine/config.yaml").read_text(encoding="utf-8"))
    assert config["status"] == "scaffolded"
