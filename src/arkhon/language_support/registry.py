"""ARKHON package module."""
from __future__ import annotations
from pathlib import Path
import yaml
def load_registry(path: str | Path) -> dict:
    data=yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data,dict) or not isinstance(data.get("languages"),list): raise ValueError("Invalid language registry")
    return data
