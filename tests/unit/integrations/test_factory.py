"""Tests for the model and platform factories."""

from __future__ import annotations

import pytest

from arkhon.integrations.models import (
    get_model_adapter,
    list_models,
)
from arkhon.integrations.platforms import (
    get_platform_adapter,
    list_platforms,
)

EXPECTED_MODELS = {

    "claude", "openai-o", "deepseek-coder", "gpt",

    "gemini", "code-llama", "qwen-coder", "kimi",

}

def test_list_models_returns_all_eight() -> None:

    models = list_models()

    assert len(models) == 8

    assert set(models) == EXPECTED_MODELS

def test_list_models_sorted() -> None:

    models = list_models()

    assert models == sorted(models)

@pytest.mark.parametrize("model_id", sorted(EXPECTED_MODELS))

def test_get_model_adapter_returns_instance(model_id: str) -> None:

    adapter = get_model_adapter(model_id)

    assert adapter.info.id == model_id

    assert adapter.info.kind == "model"

def test_get_model_adapter_unknown_raises() -> None:

    with pytest.raises(KeyError, match="unknown model"):

        get_model_adapter("cobol-llm")

def test_get_model_adapter_error_lists_available() -> None:

    try:

        get_model_adapter("nope")

    except KeyError as exc:

        assert "claude" in str(exc)

        assert "gpt" in str(exc)

def test_all_adapters_have_health_check() -> None:

    for model_id in list_models():

        adapter = get_model_adapter(model_id)

        assert hasattr(adapter, "health_check")

        result = adapter.health_check()

        assert isinstance(result, bool)

def test_list_platforms_returns_copilot() -> None:

    platforms = list_platforms()

    assert "github-copilot" in platforms

def test_get_platform_adapter() -> None:

    adapter = get_platform_adapter("github-copilot")

    assert adapter.info.id == "github-copilot"

    assert adapter.info.kind == "platform"

def test_get_platform_adapter_unknown_raises() -> None:

    with pytest.raises(KeyError, match="unknown platform"):

        get_platform_adapter("gitlab-duo")
