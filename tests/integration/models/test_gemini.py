"""Tests specific to the Gemini adapter (different API shape)."""

from __future__ import annotations

import pytest

from arkhon.integrations.models.gemini.adapter import GeminiAdapter
from tests.fixtures.mock_http import (
    make_http_error,
    make_json_response,
    patch_urlopen,
)


def test_info() -> None:

    adapter = GeminiAdapter()

    info = adapter.info

    assert info.id == "gemini"

    assert info.provider == "google"

    assert "multimodal" in info.capabilities

def test_health_check(monkeypatch: pytest.MonkeyPatch) -> None:

    monkeypatch.setenv("GOOGLE_API_KEY", "g-key")

    assert GeminiAdapter().health_check() is True

def test_health_check_missing(monkeypatch: pytest.MonkeyPatch) -> None:

    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)

    assert GeminiAdapter().health_check() is False

def test_system_prompt_present() -> None:

    assert GeminiAdapter().system_prompt()

def test_send_success(monkeypatch: pytest.MonkeyPatch) -> None:

    monkeypatch.setenv("GOOGLE_API_KEY", "g-key")

    adapter = GeminiAdapter()

    response = make_json_response({

        "candidates": [

            {"content": {"parts": [{"text": "gemini response"}]}},

        ],

    })

    with patch_urlopen(response):

        result = adapter.send("hello")

    assert result.ok

    assert result.payload["text"] == "gemini response"

def test_send_missing_key(monkeypatch: pytest.MonkeyPatch) -> None:

    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)

    result = GeminiAdapter().send("hello")

    assert not result.ok

    assert "GOOGLE_API_KEY" in result.reason

def test_send_http_error(monkeypatch: pytest.MonkeyPatch) -> None:

    monkeypatch.setenv("GOOGLE_API_KEY", "g-key")

    with patch_urlopen(make_http_error(403, "Forbidden")):

        result = GeminiAdapter().send("hello")

    assert not result.ok

    assert "403" in result.reason

def test_send_empty_candidates(monkeypatch: pytest.MonkeyPatch) -> None:

    monkeypatch.setenv("GOOGLE_API_KEY", "g-key")

    with patch_urlopen(make_json_response({"candidates": []})):

        result = GeminiAdapter().send("hello")

    assert result.ok

    assert result.payload["text"] == ""
