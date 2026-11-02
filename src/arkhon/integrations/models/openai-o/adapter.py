"""Import-safe shim; implementation lives in the internal model package."""
from arkhon.integrations._model_impl.openai_o.adapter import OpenAIOAdapter

__all__ = ["OpenAIOAdapter"]
