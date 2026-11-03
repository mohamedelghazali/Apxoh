"""Validate YAML rule files for syntax."""

from pathlib import Path

import yaml


def main() -> int:
    files = list(Path("rules").rglob("*.yaml"))
    for path in files:
        yaml.safe_load(path.read_text(encoding="utf-8"))
    print(f"Validated {len(files)} rule YAML files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
