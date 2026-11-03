"""Tests specific to OpenAI o (reasoning models).

Key differences from GPT:

  * Uses `developer` role, not `system`.

  * Does not accept `temperature`.

  * Longer default timeout (reasoning takes time).

"""

from __future__ import annotations

import json

import pytest

from arkhon.integrations.models.openai_o.adapter import OpenAIOAdapter
from tests.fixtures.mock_http import (
    make_json_response,
    patch_urlopen,
)


def test_info() -> None:

    info = OpenAIOAdapter().info

    assert info.id == "openai-o"

    assert "reasoning" in info.capabilities

def test_health_check(monkeypatch: pytest.MonkeyPatch) -> None:

    monkeypatch.setenv("OPENAI_API_KEY", "sk-...")

    assert OpenAIOAdapter().health_check() is True

def test_payload_uses_developer_role(monkeypatch: pytest.MonkeyPatch) -> None:

    """The critical difference: no `system` role."""

    monkeypatch.setenv("OPENAI_API_KEY", "sk-...")

    adapter = OpenAIOAdapter()

    captured = {}

    def _capture(request, timeout=None, **kwargs):

        captured["body"] = json.loads(request.data.decode("utf-8"))

        return make_json_response({"choices": [{"message": {"content": "ok"}}]})

    with patch_urlopen(_capture):

        adapter.send("hi")

    messages = captured["body"]["messages"]

    roles = [m["role"] for m in messages]

    assert "system" not in roles

    assert roles[0] == "developer"

def test_payload_omits_temperature(monkeypatch: pytest.MonkeyPatch) -> None:

    monkeypatch.setenv("OPENAI_API_KEY", "sk-...")

    adapter = OpenAIOAdapter()

    captured = {}

    def _capture(request, timeout=None, **kwargs):

        captured["body"] = json.loads(request.data.decode("utf-8"))

        return make_json_response({"choices": [{"message": {"content": "ok"}}]})

    with patch_urlopen(_capture):

        adapter.send("hi")

    assert "temperature" not in captured["body"]

    assert "max_completion_tokens" in captured["body"]

    assert "max_tokens" not in captured["body"]

def test_send_success(monkeypatch: pytest.MonkeyPatch) -> None:

    monkeypatch.setenv("OPENAI_API_KEY", "sk-...")

    with patch_urlopen(make_json_response({

        "choices": [{"message": {"content": "thought process..."}}],

    })):

        result = OpenAIOAdapter().send("hi")

    assert result.ok

    assert "thought" in result.payload["text"]

def test_send_missing_key(monkeypatch: pytest.MonkeyPatch) -> None:

    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    result = OpenAIOAdapter().send("hi")

    assert not result.ok
