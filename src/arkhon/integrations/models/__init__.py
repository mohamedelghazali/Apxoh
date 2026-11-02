"""Model adapter registry and factory."""
from __future__ import annotations

import importlib
import sys
from importlib.machinery import ModuleSpec
from pathlib import Path
from types import ModuleType
from typing import cast

from arkhon.integrations.base import Integration

_MODEL_MODULES = {
    "claude": "arkhon.integrations.models.claude.adapter",
    "openai-o": "arkhon.integrations._model_impl.openai_o.adapter",
    "deepseek-coder": "arkhon.integrations._model_impl.deepseek_coder.adapter",
    "gpt": "arkhon.integrations.models.gpt.adapter",
    "gemini": "arkhon.integrations.models.gemini.adapter",
    "code-llama": "arkhon.integrations._model_impl.code_llama.adapter",
    "qwen-coder": "arkhon.integrations._model_impl.qwen_coder.adapter",
    "kimi": "arkhon.integrations.models.kimi.adapter",
}
_ADAPTER_CLASSES = {
    "claude": "ClaudeAdapter",
    "openai-o": "OpenAIOAdapter",
    "deepseek-coder": "DeepSeekCoderAdapter",
    "gpt": "GptAdapter",
    "gemini": "GeminiAdapter",
    "code-llama": "CodeLlamaAdapter",
    "qwen-coder": "QwenCoderAdapter",
    "kimi": "KimiAdapter",
}

# Public import aliases preserve Python-safe module names while keeping the
# provider's manifest slug directories intact for discovery and packaging.
_IMPL_ROOT = Path(__file__).parent.parent / "_model_impl"
_ALIASES = {
    "openai_o": "openai_o",
    "deepseek_coder": "deepseek_coder",
    "code_llama": "code_llama",
    "qwen_coder": "qwen_coder",
}
for _alias_name, _directory in _ALIASES.items():
    _qualified_name = f"{__name__}.{_alias_name}"
    if _qualified_name not in sys.modules:
        _package = ModuleType(_qualified_name)
        _package.__path__ = [str(_IMPL_ROOT / _directory)]
        _package.__package__ = _qualified_name
        _package.__spec__ = ModuleSpec(
            _qualified_name,
            loader=None,
            is_package=True,
        )
        sys.modules[_qualified_name] = _package


def list_models() -> list[str]:
    """Return registered model IDs in deterministic order."""
    return sorted(_MODEL_MODULES)


def get_model_adapter(model_id: str) -> Integration:
    """Instantiate one registered adapter, rejecting unknown identifiers."""
    if model_id not in _MODEL_MODULES:
        available = ", ".join(list_models())
        raise KeyError(
            f"unknown model {model_id!r}; available models: {available}"
        )
    module = importlib.import_module(_MODEL_MODULES[model_id])
    adapter_class = getattr(module, _ADAPTER_CLASSES[model_id])
    return cast(Integration, adapter_class())


__all__ = ["get_model_adapter", "list_models"]
