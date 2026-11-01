"""Parametrized tests for all Apxoh model integrations.

Replaces 8 separate per-model test files with one parametrized suite.
"""

from __future__ import annotations

import importlib
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[3]
MODELS_DIR = REPO_ROOT / "integrations" / "models"

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


def _model_path(model_id: str) -> Path:
    return MODELS_DIR / model_id


def _load_yaml(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


@pytest.mark.parametrize("model_id", MODEL_IDS)
def test_model_directory_exists(model_id: str) -> None:
    assert _model_path(model_id).is_dir(), f"missing directory: {_model_path(model_id)}"


@pytest.mark.parametrize("model_id", MODEL_IDS)
def test_model_has_readme(model_id: str) -> None:
    readme = _model_path(model_id) / "README.md"
    assert readme.exists(), f"missing README.md in {model_id}"
    assert readme.stat().st_size > 0, f"empty README.md in {model_id}"


@pytest.mark.parametrize("model_id", MODEL_IDS)
def test_model_has_config(model_id: str) -> None:
    config = _model_path(model_id) / "config.yaml"
    assert config.exists(), f"missing config.yaml in {model_id}"
    data = _load_yaml(config)
    assert "model" in data, f"config.yaml missing 'model' key in {model_id}"
    assert "provider" in data["model"], f"config.yaml missing 'model.provider' in {model_id}"


@pytest.mark.parametrize("model_id", MODEL_IDS)
def test_model_has_adapter(model_id: str) -> None:
    adapter = _model_path(model_id) / "adapter.py"
    assert adapter.exists(), f"missing adapter.py in {model_id}"
    assert adapter.stat().st_size > 0, f"empty adapter.py in {model_id}"


@pytest.mark.parametrize("model_id", MODEL_IDS)
def test_model_has_prompts(model_id: str) -> None:
    prompts = _model_path(model_id) / "prompts"
    assert prompts.is_dir(), f"missing prompts/ in {model_id}"
    assert (prompts / "system.md").exists(), f"missing prompts/system.md in {model_id}"
    assert (prompts / "governance-injection.md").exists(), (
        f"missing prompts/governance-injection.md in {model_id}"
    )


@pytest.mark.parametrize("model_id", MODEL_IDS)
def test_model_has_skill_bindings(model_id: str) -> None:
    bindings = _model_path(model_id) / "skill-bindings.yaml"
    assert bindings.exists(), f"missing skill-bindings.yaml in {model_id}"
    data = _load_yaml(bindings)
    assert "bindings" in data or "skills" in data, (
        f"skill-bindings.yaml missing 'bindings' or 'skills' in {model_id}"
    )


@pytest.mark.parametrize("model_id", MODEL_IDS)
def test_model_has_tests_dir(model_id: str) -> None:
    tests_dir = _model_path(model_id) / "tests"
    assert tests_dir.is_dir(), f"missing tests/ in {model_id}"


@pytest.mark.parametrize("model_id", MODEL_IDS)
def test_model_adapter_source_has_no_forbidden_patterns(model_id: str) -> None:
    import re

    adapter = _model_path(model_id) / "adapter.py"
    text = adapter.read_text(encoding="utf-8")
    forbidden = {
        "eval": re.compile(r"\beval\s*\("),
        "exec": re.compile(r"\bexec\s*\("),
        "shell-true": re.compile(r"subprocess\.\w+\([^)]*shell\s*=\s*True"),
    }
    for name, pattern in forbidden.items():
        assert pattern.search(text) is None, (
            f"{model_id}/adapter.py contains forbidden pattern: {name}"
        )


@pytest.mark.parametrize("model_id", MODEL_IDS)
def test_model_adapter_importable(model_id: str) -> None:
    """Ensure adapter.py is syntactically valid Python (does not import it)."""
    import ast

    adapter = _model_path(model_id) / "adapter.py"
    source = adapter.read_text(encoding="utf-8")
    ast.parse(source, filename=str(adapter))


def test_all_expected_models_are_present() -> None:
    if not MODELS_DIR.exists():
        pytest.skip("models directory does not exist yet (Milestone 4)")
    actual = sorted(p.name for p in MODELS_DIR.iterdir() if p.is_dir())
    assert actual == sorted(MODEL_IDS), (
        f"model directories mismatch. expected={sorted(MODEL_IDS)} actual={actual}"
    )
