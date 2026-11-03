# ruff: noqa: I001
from __future__ import annotations

import importlib
import runpy
from pathlib import Path

import pytest


_EMPTY_MODULES = (
    "arkhon.integrations.agents",
    "arkhon.integrations.agents.aider",
    "arkhon.integrations.agents.amazon_q",
    "arkhon.integrations.agents.claude_code",
    "arkhon.integrations.agents.cline",
    "arkhon.integrations.agents.codex_openai",
    "arkhon.integrations.agents.continue_agent",
    "arkhon.integrations.agents.cursor",
    "arkhon.integrations.agents.devin",
    "arkhon.integrations.agents.gemini",
    "arkhon.integrations.agents.gemini_cli",
    "arkhon.integrations.agents.github_copilot",
    "arkhon.integrations.agents.gpt",
    "arkhon.integrations.agents.jetbrains_ai",
    "arkhon.integrations.agents.replit_agent",
    "arkhon.integrations.agents.sourcegraph_cody",
    "arkhon.integrations.agents.tabnine",
    "arkhon.integrations.agents.windsurf",
    "arkhon.language_support.compatibility",
    "arkhon.language_support.language_profile_loader",
    "arkhon.orchestrator.task_dispatcher",
    "arkhon.reporting.html_reporter",
    "arkhon.rules.evaluator",
    "arkhon.verification.profiles",
)


@pytest.mark.parametrize("module_name", _EMPTY_MODULES)
def test_reserved_extension_modules_are_importable_and_empty(module_name: str) -> None:
    module = importlib.import_module(module_name)
    assert module.__all__ == []


@pytest.mark.parametrize(
    ("relative", "export"),
    [
        ("integrations/models/code-llama/adapter.py", "CodeLlamaAdapter"),
        ("integrations/models/deepseek-coder/adapter.py", "DeepSeekCoderAdapter"),
        ("integrations/models/openai-o/adapter.py", "OpenAIOAdapter"),
        ("integrations/models/qwen-coder/adapter.py", "QwenCoderAdapter"),
    ],
)
def test_legacy_model_adapter_shims_export_internal_implementations(
    relative: str, export: str
) -> None:
    root = Path(__file__).resolve().parents[2] / "src" / "arkhon"
    namespace = runpy.run_path(str(root / relative))
    assert export in namespace["__all__"]
    assert namespace[export].__name__ == export
