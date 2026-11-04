"""Alibaba Qwen Coder compatible Chat Completions adapter."""

from __future__ import annotations

from arkhon.integrations.models._openai_compatible import (
    OpenAICompatibleAdapter,
    OpenAICompatibleConfig,
)


class QwenCoderAdapter(OpenAICompatibleAdapter):
    def __init__(self) -> None:
        super().__init__(
            OpenAICompatibleConfig(
                id="qwen-coder",
                provider="alibaba",
                endpoint=("https://dashscope.aliyuncs.com/compatible-mode/v1/" "chat/completions"),
                default_model="qwen3-coder-plus",
                available_models=(
                    "qwen3-coder-plus",
                    "qwen2.5-coder-32b-instruct",
                ),
                max_tokens=8192,
                temperature=0.0,
                timeout_seconds=120,
                api_key_env="DASHSCOPE_API_KEY",
                allowed_hosts=("dashscope.aliyuncs.com",),
            )
        )
