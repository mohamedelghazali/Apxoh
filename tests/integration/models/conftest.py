"""Shared fixtures for model integration tests."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[3]

MODELS_DIR = REPO_ROOT / "src" / "arkhon" / "integrations" / "models"

MODEL_IDS = [

    "claude",

    "openai-o",

    "deepseek-coder",

    "gpt",

    "gemini",

    "code-llama",

    "qwen-coder",

    "kimi",

]

@pytest.fixture(scope="session")

def models_root() -> Path:

    return MODELS_DIR

@pytest.fixture(scope="session", params=MODEL_IDS)

def model_id(request: pytest.FixtureRequest) -> str:

    return request.param

@pytest.fixture

def model_dir(models_root: Path, model_id: str) -> Path:

    path = models_root / model_id

    if not path.is_dir():

        pytest.skip(f"model not yet present: {model_id}")

    return path

@pytest.fixture

def model_config(model_dir: Path) -> dict:

    with (model_dir / "config.yaml").open("r", encoding="utf-8") as fh:

        return yaml.safe_load(fh)
