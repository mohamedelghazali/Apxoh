"""Import-safe shim; implementation lives in the Python package openai_o."""
from arkhon.integrations.models.openai_o.adapter import OpenAIOAdapter

__all__ = ["OpenAIOAdapter"]
