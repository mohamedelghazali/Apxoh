"""Local Code Llama adapter using an Ollama-compatible endpoint."""
from __future__ import annotations

from arkhon.integrations.models._openai_compatible import (
    OpenAICompatibleAdapter,
    OpenAICompatibleConfig,
)


class CodeLlamaAdapter(OpenAICompatibleAdapter):
    def __init__(self) -> None:
        super().__init__(
            OpenAICompatibleConfig(
                id="code-llama",
                provider="meta",
                endpoint="http://127.0.0.1:11434/v1/chat/completions",
                default_model="codellama:13b",
                available_models=(
                    "codellama:7b",
                    "codellama:13b",
                    "codellama:34b",
                ),
                max_tokens=4096,
                temperature=0.0,
                timeout_seconds=180,
                api_key_env="CODE_LLAMA_API_KEY",
                api_key_required=False,
            )
        )
