"""Parametrized cross-model tests.

Ensures every model integration satisfies the same structural contract.

Model-specific behavior lives in the per-model test files.

"""

from __future__ import annotations

import ast

import re

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

REQUIRED_FILES = [

    "README.md",

    "config.yaml",

    "adapter.py",

    "prompts/system.md",

    "prompts/governance-injection.md",

]

def _model_dir(model_id: str) -> Path:

    return MODELS_DIR / model_id

@pytest.mark.parametrize("model_id", MODEL_IDS)

def test_model_directory_exists(model_id: str) -> None:

    assert _model_dir(model_id).is_dir()

@pytest.mark.parametrize("model_id", MODEL_IDS)

def test_required_files_present(model_id: str) -> None:

    for rel in REQUIRED_FILES:

        path = _model_dir(model_id) / rel

        assert path.is_file(), f"{model_id}: missing {rel}"

        assert path.stat().st_size > 0, f"{model_id}: empty {rel}"

@pytest.mark.parametrize("model_id", MODEL_IDS)

def test_config_yaml_structure(model_id: str) -> None:

    with (_model_dir(model_id) / "config.yaml").open("r", encoding="utf-8") as fh:

        data = yaml.safe_load(fh)

    assert isinstance(data, dict)

    assert data["id"] == model_id

    assert "model" in data

    assert "provider" in data["model"]

    assert "endpoint" in data["model"]

    assert "governance" in data

    assert "verification" in data

@pytest.mark.parametrize("model_id", MODEL_IDS)

def test_adapter_is_valid_python(model_id: str) -> None:

    path = _model_dir(model_id) / "adapter.py"

    source = path.read_text(encoding="utf-8")

    ast.parse(source, filename=str(path))

@pytest.mark.parametrize("model_id", MODEL_IDS)

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

            f"{model_id}/adapter.py contains forbidden: {name}"

        )

@pytest.mark.parametrize("model_id", MODEL_IDS)

def test_system_prompt_mentions_apxoh(model_id: str) -> None:

    path = _model_dir(model_id) / "prompts" / "system.md"

    text = path.read_text(encoding="utf-8")

    assert "Apxoh" in text or "apxoh" in text.lower()

@pytest.mark.parametrize("model_id", MODEL_IDS)

def test_governance_injection_mentions_untrusted(model_id: str) -> None:

    path = _model_dir(model_id) / "prompts" / "governance-injection.md"

    text = path.read_text(encoding="utf-8")

    assert "UNTRUSTED" in text.upper()

@pytest.mark.parametrize("model_id", MODEL_IDS)

def test_readme_mentions_verification_level(model_id: str) -> None:

    path = _model_dir(model_id) / "README.md"

    text = path.read_text(encoding="utf-8")

    assert "verification level" in text.lower() or "max verification" in text.lower()

@pytest.mark.parametrize("model_id", MODEL_IDS)

def test_config_declares_max_verification(model_id: str) -> None:

    with (_model_dir(model_id) / "config.yaml").open("r", encoding="utf-8") as fh:

        data = yaml.safe_load(fh)

    assert "max_reachable_level" in data["verification"]

    assert data["verification"]["max_reachable_level"] in {

        "installed", "discoverable", "activated", "configured", "verified",

    }

def test_all_eight_models_present() -> None:

    actual = sorted(p.name for p in MODELS_DIR.iterdir() if p.is_dir() and not p.name.startswith("_"))

    assert actual == sorted(MODEL_IDS)

def test_manifest_lists_all_models() -> None:

    manifest_path = REPO_ROOT / "manifest" / "integrations.yaml"

    with manifest_path.open("r", encoding="utf-8") as fh:

        manifest = yaml.safe_load(fh)

    declared = {m["id"] for m in manifest["integrations"]["models"]}

    assert declared == set(MODEL_IDS)
