"""Validate extension declarations used by the deterministic detector."""
from pathlib import Path

import yaml


def test_each_language_declares_extensions() -> None:
    data = yaml.safe_load(Path("languages/registry.yaml").read_text(encoding="utf-8"))
    for item in data["languages"]:
        extensions = item.get("detection", {}).get("extensions", [])
        assert isinstance(extensions, list) and extensions, item["id"]
        assert all(extension.startswith(".") for extension in extensions)
        profile = Path("languages") / item["profile"]
        assert profile.is_file(), f"{item['id']}: profile not found: {profile}"
