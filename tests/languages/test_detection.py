"""Validate extension declarations used by the deterministic detector."""
from pathlib import Path
import yaml

def test_each_language_declares_extensions():
    data=yaml.safe_load(Path("languages/registry.yaml").read_text(encoding="utf-8"))
    for item in data["languages"]:
        profile=yaml.safe_load(Path("languages",item["profile"]).read_text(encoding="utf-8"))
        assert isinstance(profile.get("extensions"),list) and profile["extensions"]
