"""Tests for the shared OpenAI-compatible adapter base."""

from __future__ import annotations

import os

import urllib.error

import pytest

from arkhon.integrations.models._openai_compatible import (

    OpenAICompatibleAdapter,

    OpenAICompatibleConfig,

)

from tests.fixtures.mock_http import (

    make_http_error,

    make_json_response,

    patch_urlopen,

)

def _config(api_key_required: bool = True) -> OpenAICompatibleConfig:

    return OpenAICompatibleConfig(

        id="test-model",

        provider="test-provider",

        endpoint="https://example.com/v1/chat/completions",

        default_model="test-model-1",

        available_models=("test-model-1", "test-model-2"),

        max_tokens=1024,

        temperature=0.0,

        timeout_seconds=10,

        api_key_env="TEST_API_KEY",

        api_key_required=api_key_required,

    )

def test_info() -> None:

    adapter = OpenAICompatibleAdapter(_config())

    info = adapter.info

    assert info.id == "test-model"

    assert info.kind == "model"

    assert info.provider == "test-provider"

def test_health_check_with_key(monkeypatch: pytest.MonkeyPatch) -> None:

    monkeypatch.setenv("TEST_API_KEY", "sk-test")

    adapter = OpenAICompatibleAdapter(_config())

    assert adapter.health_check() is True

def test_health_check_without_key(monkeypatch: pytest.MonkeyPatch) -> None:

    monkeypatch.delenv("TEST_API_KEY", raising=False)

    adapter = OpenAICompatibleAdapter(_config())

    assert adapter.health_check() is False

def test_health_check_not_required() -> None:

    adapter = OpenAICompatibleAdapter(_config(api_key_required=False))

    assert adapter.health_check() is True

def test_send_success(monkeypatch: pytest.MonkeyPatch) -> None:

    monkeypatch.setenv("TEST_API_KEY", "sk-test")

    adapter = OpenAICompatibleAdapter(_config())

    response = make_json_response({

        "choices": [{"message": {"content": "hello"}}],

    })

    with patch_urlopen(response):

        result = adapter.send("hi")

    assert result.ok is True

    assert result.payload["text"] == "hello"

    assert result.payload["model"] == "test-model-1"

def test_send_missing_key(monkeypatch: pytest.MonkeyPatch) -> None:

    monkeypatch.delenv("TEST_API_KEY", raising=False)

    adapter = OpenAICompatibleAdapter(_config())

    result = adapter.send("hi")

    assert result.ok is False

    assert "TEST_API_KEY" in result.reason

def test_send_http_error(monkeypatch: pytest.MonkeyPatch) -> None:

    monkeypatch.setenv("TEST_API_KEY", "sk-test")

    adapter = OpenAICompatibleAdapter(_config())

    with patch_urlopen(make_http_error(401, "Unauthorized", "invalid key")):

        result = adapter.send("hi")

    assert result.ok is False

    assert "401" in result.reason

def test_send_network_error(monkeypatch: pytest.MonkeyPatch) -> None:

    monkeypatch.setenv("TEST_API_KEY", "sk-test")

    adapter = OpenAICompatibleAdapter(_config())

    with patch_urlopen(urllib.error.URLError("connection refused")):

        result = adapter.send("hi")

    assert result.ok is False

    assert "network error" in result.reason

def test_send_timeout(monkeypatch: pytest.MonkeyPatch) -> None:

    monkeypatch.setenv("TEST_API_KEY", "sk-test")

    adapter = OpenAICompatibleAdapter(_config())

    with patch_urlopen(TimeoutError()):

        result = adapter.send("hi")

    assert result.ok is False

    assert "timeout" in result.reason.lower()

def test_send_invalid_json(monkeypatch: pytest.MonkeyPatch) -> None:

    monkeypatch.setenv("TEST_API_KEY", "sk-test")

    adapter = OpenAICompatibleAdapter(_config())

    from tests.fixtures.mock_http import make_raw_response

    with patch_urlopen(make_raw_response("not json", status=200)):

        result = adapter.send("hi")

    assert result.ok is False

    assert "invalid JSON" in result.reason

def test_send_does_not_leak_key(monkeypatch: pytest.MonkeyPatch) -> None:

    """The adapter must never log or echo the API key."""

    monkeypatch.setenv("TEST_API_KEY", "sk-very-secret-key")

    adapter = OpenAICompatibleAdapter(_config())

    with patch_urlopen(make_http_error(500, "Internal Error")):

        result = adapter.send("hi")

    assert "sk-very-secret-key" not in result.reason
