"""DeepSeek Coder compatible Chat Completions adapter."""

from __future__ import annotations

from arkhon.integrations.models._openai_compatible import (
    OpenAICompatibleAdapter,
    OpenAICompatibleConfig,
)


class DeepSeekCoderAdapter(OpenAICompatibleAdapter):
    def __init__(self) -> None:
        super().__init__(
            OpenAICompatibleConfig(
                id="deepseek-coder",
                provider="deepseek",
                endpoint="https://api.deepseek.com/chat/completions",
                default_model="deepseek-chat",
                available_models=("deepseek-chat", "deepseek-reasoner"),
                max_tokens=8192,
                temperature=0.0,
                timeout_seconds=120,
                api_key_env="DEEPSEEK_API_KEY",
            )
        )
