"""Tests specific to the Claude adapter."""

from __future__ import annotations

import pytest

from arkhon.integrations.models.claude.adapter import (
    ClaudeAdapter,
    ClaudeConfig,
)
from tests.fixtures.mock_http import (
    make_http_error,
    make_json_response,
    patch_urlopen,
)


def test_info() -> None:

    adapter = ClaudeAdapter()

    info = adapter.info

    assert info.id == "claude"

    assert info.provider == "anthropic"

    assert "code-generation" in info.capabilities

def test_health_check_ok(monkeypatch: pytest.MonkeyPatch) -> None:

    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant")

    assert ClaudeAdapter().health_check() is True

def test_health_check_missing(monkeypatch: pytest.MonkeyPatch) -> None:

    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    assert ClaudeAdapter().health_check() is False

def test_system_prompt_present() -> None:

    adapter = ClaudeAdapter()

    prompt = adapter.system_prompt()

    assert prompt

    assert "Apxoh" in prompt or "governance" in prompt.lower()

def test_governance_injection_present() -> None:

    adapter = ClaudeAdapter()

    injection = adapter.governance_injection()

    assert injection

    assert "UNTRUSTED" in injection or "untrusted" in injection

def test_send_success(monkeypatch: pytest.MonkeyPatch) -> None:

    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant")

    adapter = ClaudeAdapter()

    response = make_json_response({

        "content": [{"type": "text", "text": "response"}],

    })

    with patch_urlopen(response):

        result = adapter.send("hello")

    assert result.ok

    assert result.payload["text"] == "response"

def test_send_missing_key(monkeypatch: pytest.MonkeyPatch) -> None:

    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    result = ClaudeAdapter().send("hello")

    assert not result.ok

    assert "ANTHROPIC_API_KEY" in result.reason

def test_send_http_error(monkeypatch: pytest.MonkeyPatch) -> None:

    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant")

    with patch_urlopen(make_http_error(401, "Unauthorized")):

        result = ClaudeAdapter().send("hello")

    assert not result.ok

    assert "401" in result.reason

def test_send_does_not_leak_key(monkeypatch: pytest.MonkeyPatch) -> None:

    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-secret-value")

    with patch_urlopen(make_http_error(500, "Server Error")):

        result = ClaudeAdapter().send("hello")

    assert "sk-ant-secret-value" not in result.reason

def test_config_defaults() -> None:

    cfg = ClaudeConfig()

    assert cfg.endpoint == "https://api.anthropic.com/v1/messages"

    assert "claude" in cfg.model
