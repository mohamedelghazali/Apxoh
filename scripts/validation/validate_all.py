#!/usr/bin/env python3
"""Repository governance validation entrypoint."""

from __future__ import annotations

import sys
from pathlib import Path

from gencode_gov.validation import run_cli_validate


def main(repo_root: Path | None = None) -> int:
    root = repo_root or Path(__file__).resolve().parents[2]
    return run_cli_validate(root)


if __name__ == "__main__":
    sys.exit(main())
