import json
from pathlib import Path


def test_schema_files_parse():
    for p in Path("schemas").glob("*.schema.json"):
        assert json.loads(p.read_text())["type"] == "object"
