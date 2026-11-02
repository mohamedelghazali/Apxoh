"""Model adapter registry and factory."""
from __future__ import annotations
import importlib, sys
from importlib.machinery import ModuleSpec
from pathlib import Path
from types import ModuleType
from typing import Final
_MODEL_MODULES: Final = {"claude":"claude","openai-o":"openai_o","deepseek-coder":"deepseek_coder",
 "gpt":"gpt","gemini":"gemini","code-llama":"code_llama","qwen-coder":"qwen_coder","kimi":"kimi"}
_ADAPTER_CLASSES: Final = {"claude":"ClaudeAdapter","openai-o":"OpenAIOAdapter",
 "deepseek-coder":"DeepSeekCoderAdapter","gpt":"GptAdapter","gemini":"GeminiAdapter",
 "code-llama":"CodeLlamaAdapter","qwen-coder":"QwenCoderAdapter","kimi":"KimiAdapter"}
_ROOT=Path(__file__).parent
for _ident,_module in _MODEL_MODULES.items():
 if _ident != _module:
  _name=f"{__name__}.{_module}"
  if _name not in sys.modules:
   _alias=ModuleType(_name)
   _alias.__path__=[str(_ROOT/_ident)]  # type: ignore[attr-defined]
   _alias.__package__=_name
   _alias.__spec__=ModuleSpec(_name,loader=None,is_package=True)
   sys.modules[_name]=_alias
def list_models() -> list[str]:
 return sorted(_MODEL_MODULES)
def get_model_adapter(model_id: str):
 if model_id not in _MODEL_MODULES:
  raise KeyError(f"unknown model {model_id!r}; available models: {', '.join(list_models())}")
 module=importlib.import_module(f"{__name__}.{_MODEL_MODULES[model_id]}.adapter")
 return getattr(module,_ADAPTER_CLASSES[model_id])()
__all__=["get_model_adapter","list_models"]
