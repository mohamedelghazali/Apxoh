"""Model adapter registry and factory."""
from __future__ import annotations

import importlib
from typing import cast

from arkhon.integrations.base import Integration

_MODEL_MODULES = {
    "claude": "claude",
    "openai-o": "openai_o",
    "deepseek-coder": "deepseek_coder",
    "gpt": "gpt",
    "gemini": "gemini",
    "code-llama": "code_llama",
    "qwen-coder": "qwen_coder",
    "kimi": "kimi",
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

    module_name = _MODEL_MODULES[model_id]
    module = importlib.import_module(
        f"{__name__}.{module_name}.adapter"
    )
    adapter_class = getattr(module, _ADAPTER_CLASSES[model_id])
    return cast(Integration, adapter_class())


__all__ = ["get_model_adapter", "list_models"]
