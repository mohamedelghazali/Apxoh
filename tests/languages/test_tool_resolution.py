"""Validate tool metadata is explicit and does not imply installation."""
from pathlib import Path
import yaml

def test_tool_profiles_are_optional_and_machine_readable():
    data=yaml.safe_load(Path("languages/registry.yaml").read_text(encoding="utf-8"))
    for item in data["languages"]:
        tools=yaml.safe_load((Path("languages")/item["tools"]).read_text(encoding="utf-8"))
        assert tools["required"] is False
        assert isinstance(tools["tools"],list)
