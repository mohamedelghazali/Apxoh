"""OpenAI GPT Chat Completions adapter."""
from __future__ import annotations

from arkhon.integrations.models._openai_compatible import (
    OpenAICompatibleAdapter,
    OpenAICompatibleConfig,
)


class GptAdapter(OpenAICompatibleAdapter):
    def __init__(self) -> None:
        super().__init__(
            OpenAICompatibleConfig(
                id="gpt",
                provider="openai",
                endpoint="https://api.openai.com/v1/chat/completions",
                default_model="gpt-4.1",
                available_models=(
                    "gpt-4.1",
                    "gpt-4.1-mini",
                    "gpt-4.1-nano",
                ),
                max_tokens=8192,
                temperature=0.0,
                timeout_seconds=120,
                api_key_env="OPENAI_API_KEY",
            )
        )
