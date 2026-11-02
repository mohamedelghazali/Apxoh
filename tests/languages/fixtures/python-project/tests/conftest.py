"""Add the isolated fixture source directory for its local tests."""
from __future__ import annotations

import sys
from pathlib import Path

FIXTURE_SOURCE = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(FIXTURE_SOURCE))
