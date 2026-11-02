"""Validate the initial language profile inventory."""
from pathlib import Path

import yaml


def test_every_registered_language_has_profile_and_security_policy() -> None:
    data = yaml.safe_load(Path("languages/registry.yaml").read_text(encoding="utf-8"))
    for item in data["languages"]:
        root = Path("languages") / item["id"]
        profile_path = Path(item.get("profile_path", f"languages/{item['profile']}"))
        if not profile_path.is_absolute():
            profile_path = Path(profile_path)
        assert profile_path.is_file(), f"{item['id']}/{profile_path}"
        for name in ("tools.yaml", "testing.yaml", "security.yaml"):
            assert (root / name).is_file(), f"{item['id']}/{name}"
