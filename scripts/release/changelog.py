"""Changelog validation helper."""

from pathlib import Path


def main() -> int:
    path = Path("CHANGELOG.md")
    return 0 if path.is_file() and path.read_text(encoding="utf-8").strip() else 1


if __name__ == "__main__":
    raise SystemExit(main())
