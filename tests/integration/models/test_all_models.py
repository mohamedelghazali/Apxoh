"""Parametrized tests for all Apxoh model integrations."""

from __future__ import annotations

import ast
import re
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

REQUIRED_FILES = ["README.md", "config.yaml", "adapter.py", "skill-bindings.yaml"]


def _model_dir(model_id: str) -> Path:
    return MODELS_DIR / model_id


def _existing_models() -> list[str]:
    if not MODELS_DIR.is_dir():
        return []
    return [m for m in MODEL_IDS if _model_dir(m).is_dir()]


# Only test models that exist. Others will be added in future batches.
EXISTING = _existing_models()


@pytest.mark.parametrize("model_id", EXISTING)
def test_model_has_required_files(model_id: str) -> None:
    for f in REQUIRED_FILES:
        assert (_model_dir(model_id) / f).exists(), f"{model_id} missing {f}"


@pytest.mark.parametrize("model_id", EXISTING)
def test_model_has_prompts(model_id: str) -> None:
    prompts = _model_dir(model_id) / "prompts"
    assert prompts.is_dir()
    assert (prompts / "system.md").is_file()
    assert (prompts / "governance-injection.md").is_file()


@pytest.mark.parametrize("model_id", EXISTING)
def test_config_yaml_is_valid(model_id: str) -> None:
    path = _model_dir(model_id) / "config.yaml"
    with path.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    assert isinstance(data, dict)
    assert "id" in data
    assert "model" in data
    assert "provider" in data["model"]


@pytest.mark.parametrize("model_id", EXISTING)
def test_adapter_is_valid_python(model_id: str) -> None:
    path = _model_dir(model_id) / "adapter.py"
    source = path.read_text(encoding="utf-8")
    ast.parse(source, filename=str(path))


@pytest.mark.parametrize("model_id", EXISTING)
def test_adapter_has_no_forbidden_patterns(model_id: str) -> None:
    path = _model_dir(model_id) / "adapter.py"
    text = path.read_text(encoding="utf-8")
    forbidden = {
        "eval": re.compile(r"\beval\s*\("),
        "exec": re.compile(r"\bexec\s*\("),
        "shell-true": re.compile(r"shell\s*=\s*True"),
    }
    for name, pattern in forbidden.items():
        assert pattern.search(text) is None, (
            f"{model_id}/adapter.py contains forbidden pattern: {name}"
        )


@pytest.mark.parametrize("model_id", EXISTING)
def test_readme_is_non_empty(model_id: str) -> None:
    path = _model_dir(model_id) / "README.md"
    assert path.stat().st_size > 100, f"{model_id}/README.md is too short"


def test_model_registry_matches_manifest() -> None:
    """The models listed in the manifest must match what exists on disk."""
    manifest_path = REPO_ROOT / "manifest" / "integrations.yaml"
    if not manifest_path.is_file():
        pytest.skip("manifest missing")
    with manifest_path.open("r", encoding="utf-8") as fh:
        manifest = yaml.safe_load(fh)
    declared = {m["id"] for m in manifest["integrations"]["models"]}
    actual = set(EXISTING)
    # Declared but not yet created is OK (in-progress).
    # Created but not declared is an error.
    assert actual <= declared, f"model directories not declared in manifest: {actual - declared}"
