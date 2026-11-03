"""Model adapter registry and factory."""
from __future__ import annotations

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
    # Keep imports static: model identifiers are external input and must never
    # be interpreted as arbitrary Python module paths.
    if model_id == "claude":
        from arkhon.integrations.models.claude.adapter import ClaudeAdapter

        adapter = ClaudeAdapter()
    elif model_id == "openai-o":
        from arkhon.integrations.models.openai_o.adapter import OpenAIOAdapter

        adapter = OpenAIOAdapter()
    elif model_id == "deepseek-coder":
        from arkhon.integrations.models.deepseek_coder.adapter import (\n            DeepSeekCoderAdapter,\n        )

        adapter = DeepSeekCoderAdapter()
    elif model_id == "gpt":
        from arkhon.integrations.models.gpt.adapter import GptAdapter

        adapter = GptAdapter()
    elif model_id == "gemini":
        from arkhon.integrations.models.gemini.adapter import GeminiAdapter

        adapter = GeminiAdapter()
    elif model_id == "code-llama":
        from arkhon.integrations.models.code_llama.adapter import CodeLlamaAdapter

        adapter = CodeLlamaAdapter()
    elif model_id == "qwen-coder":
        from arkhon.integrations.models.qwen_coder.adapter import QwenCoderAdapter

        adapter = QwenCoderAdapter()
    else:
        from arkhon.integrations.models.kimi.adapter import KimiAdapter

        adapter = KimiAdapter()
    return cast(Integration, adapter)


__all__ = ["get_model_adapter", "list_models"]
