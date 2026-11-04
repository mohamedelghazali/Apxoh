"""Moonshot Kimi compatible Chat Completions adapter."""

from __future__ import annotations

from arkhon.integrations.models._openai_compatible import (
    OpenAICompatibleAdapter,
    OpenAICompatibleConfig,
)


class KimiAdapter(OpenAICompatibleAdapter):
    def __init__(self) -> None:
        super().__init__(
            OpenAICompatibleConfig(
                id="kimi",
                provider="moonshot",
                endpoint="https://api.moonshot.ai/v1/chat/completions",
                default_model="kimi-k2",
                available_models=("kimi-k2", "moonshot-v1-128k"),
                max_tokens=8192,
                temperature=0.0,
                timeout_seconds=180,
                api_key_env="MOONSHOT_API_KEY",
                allowed_hosts=("api.moonshot.ai",),
            )
        )
