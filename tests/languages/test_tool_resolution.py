"""Validate tool metadata is explicit and machine-readable."""
from pathlib import Path

import yaml


def test_tool_profiles_are_machine_readable() -> None:
    registry = yaml.safe_load(Path("languages/registry.yaml").read_text(encoding="utf-8"))
    for item in registry["languages"]:
        tool_path = Path("languages") / item["tools"]
        data = yaml.safe_load(tool_path.read_text(encoding="utf-8"))
        assert data["id"] == item["id"]
        assert isinstance(data["tools"], dict)
        assert data["tools"]
        for category, entries in data["tools"].items():
            assert isinstance(category, str)
            assert isinstance(entries, list)
            for tool in entries:
                assert isinstance(tool["name"], str) and tool["name"]
                assert isinstance(tool["role"], str) and tool["role"]
                assert isinstance(tool["required"], bool)
                assert isinstance(tool["invocation"], str) and tool["invocation"]
