"""Model adapter registry and public factory API."""
from __future__ import annotations

import importlib
import sys
from importlib.machinery import ModuleSpec
from pathlib import Path
from types import ModuleType
from typing import Final

_MODEL_MODULES: Final[dict[str, str]] = {
    "claude": "claude",
    "openai-o": "openai_o",
    "deepseek-coder": "deepseek_coder",
    "gpt": "gpt",
    "gemini": "gemini",
    "code-llama": "code_llama",
    "qwen-coder": "qwen_coder",
    "kimi": "kimi",
}

# The on-disk directory names follow the manifest slugs (hyphens). Expose
# Python-safe package aliases for import compatibility, e.g. openai_o.
_PACKAGE_DIR = Path(__file__).parent
for _model_id, _module_name in _MODEL_MODULES.items():
    if _module_name == _model_id:
        continue
    _qualified = f"{__name__}.{_module_name}"
    if _qualified not in sys.modules:
        _alias = ModuleType(_qualified)
        _alias.__path__ = [str(_PACKAGE_DIR / _model_id)]  # type: ignore[attr-defined]
        _alias.__package__ = _qualified
        _alias.__spec__ = ModuleSpec(_qualified, loader=None, is_package=True)
        sys.modules[_qualified] = _alias


def list_models() -> list[str]:
    """Return all registered model identifiers in stable order."""
    return sorted(_MODEL_MODULES)


def get_model_adapter(model_id: str):
    """Instantiate a registered adapter; unknown IDs fail closed."""
    if model_id not in _MODEL_MODULES:
        available = ", ".join(list_models())
        raise KeyError(f"unknown model {model_id!r}; available models: {available}")
    module_name = _MODEL_MODULES[model_id]
    module = importlib.import_module(f"{__name__}.{module_name}.adapter")
    class_name = {
        "claude": "ClaudeAdapter",
        "openai-o": "OpenAIOAdapter",
        "deepseek-coder": "DeepSeekCoderAdapter",
        "gpt": "GptAdapter",
        "gemini": "GeminiAdapter",
        "code-llama": "CodeLlamaAdapter",
        "qwen-coder": "QwenCoderAdapter",
        "kimi": "KimiAdapter",
    }[model_id]
    adapter_class = getattr(module, class_name)
    return adapter_class()


__all__ = ["get_model_adapter", "list_models"]
