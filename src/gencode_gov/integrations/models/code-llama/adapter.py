"""Import-safe shim; implementation lives in the internal model package."""

from gencode_gov.integrations._model_impl.code_llama.adapter import CodeLlamaAdapter

__all__ = ["CodeLlamaAdapter"]
