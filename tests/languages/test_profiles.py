"""Validate the initial language profile inventory."""
from pathlib import Path
import yaml

def test_every_registered_language_has_profile_and_security_policy():
    data=yaml.safe_load(Path("languages/registry.yaml").read_text(encoding="utf-8"))
    for item in data["languages"]:
        root=Path("languages")/item["id"]
        for name in ("profile.yaml","tools.yaml","testing.yaml","security.yaml"):
            assert (root/name).is_file(), f"{item['id']}/{name}"
