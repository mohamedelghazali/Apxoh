from pathlib import Path

import yaml


def test_nine_languages():
    data=yaml.safe_load(Path("languages/registry.yaml").read_text(encoding="utf-8"))
    assert len(data["languages"])==9
