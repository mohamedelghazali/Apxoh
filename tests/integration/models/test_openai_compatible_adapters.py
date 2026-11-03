"""Tests for adapters that use the shared OpenAI-compatible base:

   GPT, DeepSeek-Coder, Qwen-Coder, Kimi, Code Llama.

"""

from __future__ import annotations

import pytest

from arkhon.integrations.models.code_llama.adapter import CodeLlamaAdapter
from arkhon.integrations.models.deepseek_coder.adapter import (
    DeepSeekCoderAdapter,
)
from arkhon.integrations.models.gpt.adapter import GptAdapter
from arkhon.integrations.models.kimi.adapter import KimiAdapter
from arkhon.integrations.models.qwen_coder.adapter import QwenCoderAdapter
from tests.fixtures.mock_http import make_json_response, patch_urlopen

ADAPTER_CASES = [

    ("gpt", GptAdapter, "OPENAI_API_KEY"),

    ("deepseek-coder", DeepSeekCoderAdapter, "DEEPSEEK_API_KEY"),

    ("qwen-coder", QwenCoderAdapter, "DASHSCOPE_API_KEY"),

    ("kimi", KimiAdapter, "MOONSHOT_API_KEY"),

]

@pytest.mark.parametrize(("model_id", "factory", "env_var"), ADAPTER_CASES)

def test_info(model_id: str, factory, env_var: str) -> None:

    info = factory().info

    assert info.id == model_id

    assert info.kind == "model"

@pytest.mark.parametrize(("model_id", "factory", "env_var"), ADAPTER_CASES)

def test_health_check(

    model_id: str, factory, env_var: str, monkeypatch: pytest.MonkeyPatch,

) -> None:

    monkeypatch.setenv(env_var, "test-key")

    assert factory().health_check() is True

@pytest.mark.parametrize(("model_id", "factory", "env_var"), ADAPTER_CASES)

def test_health_check_missing(

    model_id: str, factory, env_var: str, monkeypatch: pytest.MonkeyPatch,

) -> None:

    monkeypatch.delenv(env_var, raising=False)

    assert factory().health_check() is False

@pytest.mark.parametrize(("model_id", "factory", "env_var"), ADAPTER_CASES)

def test_send_success(

    model_id: str, factory, env_var: str, monkeypatch: pytest.MonkeyPatch,

) -> None:

    monkeypatch.setenv(env_var, "test-key")

    adapter = factory()

    with patch_urlopen(make_json_response({

        "choices": [{"message": {"content": "response"}}],

    })):

        result = adapter.send("hi")

    assert result.ok

    assert result.payload["text"] == "response"

@pytest.mark.parametrize(("model_id", "factory", "env_var"), ADAPTER_CASES)

def test_send_missing_key(

    model_id: str, factory, env_var: str, monkeypatch: pytest.MonkeyPatch,

) -> None:

    monkeypatch.delenv(env_var, raising=False)

    result = factory().send("hi")

    assert not result.ok

    assert env_var in result.reason

def test_code_llama_no_api_key_needed() -> None:

    """Code Llama runs locally. No API key is required."""

    adapter = CodeLlamaAdapter()

    assert adapter.health_check() is True

    assert adapter.config.api_key_required is False

def test_code_llama_send_without_key() -> None:

    adapter = CodeLlamaAdapter()

    with patch_urlopen(make_json_response({

        "choices": [{"message": {"content": "local response"}}],

    })):

        result = adapter.send("hi")

    assert result.ok
