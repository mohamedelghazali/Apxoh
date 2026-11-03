from pathlib import Path

import yaml


def test_registry():
    assert len(yaml.safe_load(Path("languages/registry.yaml").read_text())["languages"]) == 9
