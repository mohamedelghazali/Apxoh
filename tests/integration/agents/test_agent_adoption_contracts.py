"""Repository-level contracts for AI-agent adoption metadata.

These tests validate repository structure and truthful status declarations only.
They do not claim external agents loaded or obeyed Apxoh instructions.
"""

from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[3]


def _load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def test_model_registry_paths_resolve_to_packaged_adapters() -> None:
    registry = _load_yaml(ROOT / "manifest" / "integrations.yaml")
    models = registry["integrations"]["models"]
    assert len(models) == registry["totals"]["models"]
    for model in models:
        adapter_dir = ROOT / model["integration_path"]
        assert adapter_dir.is_dir(), model["id"]
        assert (adapter_dir / "adapter.py").is_file(), model["id"]
        assert (adapter_dir / "config.yaml").is_file(), model["id"]


def test_copilot_registry_separates_docs_from_runtime_adapter() -> None:
    registry = _load_yaml(ROOT / "manifest" / "integrations.yaml")
    copilot = registry["integrations"]["platforms"][0]
    assert copilot["id"] == "github-copilot"
    assert (ROOT / copilot["integration_path"]).is_dir()
    assert (ROOT / copilot["runtime_adapter"]).is_file()
    assert copilot["status"] == "scaffolded"


def test_generic_fallback_is_not_misreported_as_supported_behavior() -> None:
    registry = _load_yaml(ROOT / "manifest" / "integrations.yaml")
    generic = registry["integrations"]["generic"][0]
    assert generic["status"] == "manual"
    assert (ROOT / generic["integration_path"]).is_dir()


def test_generic_agent_scaffolds_require_consent_and_verification() -> None:
    root = ROOT / "integrations" / "generic-agents"
    adapters = sorted(path for path in root.iterdir() if path.is_dir() and path.name != "prompts")
    assert adapters
    for adapter in adapters:
        config_path = adapter / "config.yaml"
        assert config_path.is_file(), adapter.name
        config = _load_yaml(config_path)
        assert config["status"] == "scaffolded", adapter.name
        assert config["requires_user_consent"] is True, adapter.name
        assert config["verification_required"] is True, adapter.name
