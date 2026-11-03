"""OpenAI o-series reasoning-model adapter."""

from __future__ import annotations

from arkhon.integrations.models._openai_compatible import (
    OpenAICompatibleAdapter,
    OpenAICompatibleConfig,
)


class OpenAIOAdapter(OpenAICompatibleAdapter):
    def __init__(self) -> None:
        super().__init__(
            OpenAICompatibleConfig(
                id="openai-o",
                provider="openai",
                endpoint="https://api.openai.com/v1/chat/completions",
                default_model="o3",
                available_models=("o3", "o4-mini"),
                max_tokens=8192,
                temperature=None,
                timeout_seconds=180,
                api_key_env="OPENAI_API_KEY",
                system_role="developer",
                max_output_field="max_completion_tokens",
            )
        )
