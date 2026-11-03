from __future__ import annotations

import json
from pathlib import Path

import pytest

from arkhon.integrations.models.claude.adapter import ClaudeAdapter, ClaudeConfig
from arkhon.integrations.models.gemini.adapter import GeminiAdapter, GeminiConfig


class _Response:
    def __init__(self, body: str, status: int = 200, reason: str = "OK") -> None:
        self._body = body.encode("utf-8")
        self.status = status
        self.reason = reason

    def read(self) -> bytes:
        return self._body


class _Connection:
    def __init__(self, response: _Response, error: Exception | None = None) -> None:
        self.response = response
        self.error = error
        self.closed = False
        self.request_args: tuple[object, ...] = ()

    def request(self, *args: object, **kwargs: object) -> None:
        self.request_args = args
        if self.error is not None:
            raise self.error

    def getresponse(self) -> _Response:
        return self.response

    def close(self) -> None:
        self.closed = True


def _patch_connection(
    monkeypatch: pytest.MonkeyPatch, module: str, connection: _Connection
) -> None:
    monkeypatch.setattr(
        f"{module}.http.client.HTTPSConnection",
        lambda *args, **kwargs: connection,
    )


def test_claude_key_health_endpoint_and_prompt_paths(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    adapter = ClaudeAdapter()
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    assert not adapter.health_check()
    assert not adapter.send("hello").ok
    monkeypatch.setenv("ANTHROPIC_API_KEY", "secret")
    assert adapter.health_check()
    adapter._prompts_dir = tmp_path
    assert adapter.system_prompt() == ""
    assert adapter.governance_injection() == ""
    (tmp_path / "system.md").write_text("system", encoding="utf-8")
    (tmp_path / "governance-injection.md").write_text("rules", encoding="utf-8")
    assert adapter.system_prompt() == "system"
    assert adapter.governance_injection() == "rules"


@pytest.mark.parametrize(
    "endpoint",
    [
        "http://example.com/v1",
        "https://user:pass@example.com/v1",
        "https://example.com/v1?token=x",
        "https://example.com:invalid/v1",
        "https://example.com:0/v1",
    ],
)
def test_claude_rejects_unsafe_endpoints(endpoint: str, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ANTHROPIC_API_KEY", "secret")
    adapter = ClaudeAdapter(ClaudeConfig(endpoint=endpoint))
    result = adapter.send("hello")
    assert not result.ok


def test_claude_success_and_http_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ANTHROPIC_API_KEY", "secret")
    module = "arkhon.integrations.models.claude.adapter"
    connection = _Connection(
        _Response(json.dumps({
            "content": [
                {"type": "text", "text": "hello "},
                {"type": "image", "data": "ignored"},
                {"type": "text", "text": "world"},
            ]
        }))
    )
    _patch_connection(monkeypatch, module, connection)
    result = ClaudeAdapter().send("prompt")
    assert result.ok and result.payload["text"] == "hello world"
    assert connection.closed
    _patch_connection(monkeypatch, module, _Connection(_Response("denied", 401, "Unauthorized")))
    result = ClaudeAdapter().send("prompt")
    assert not result.ok and "401" in result.reason


@pytest.mark.parametrize(
    ("error", "expected"),
    [(TimeoutError(), "timeout"), (OSError("offline"), "network error")],
)
def test_claude_transport_errors(
    monkeypatch: pytest.MonkeyPatch, error: Exception, expected: str
) -> None:
    monkeypatch.setenv("ANTHROPIC_API_KEY", "secret")
    _patch_connection(
        monkeypatch,
        "arkhon.integrations.models.claude.adapter",
        _Connection(_Response(""), error),
    )
    result = ClaudeAdapter().send("prompt")
    assert not result.ok and expected in result.reason


@pytest.mark.parametrize("body", ["not-json", "[]"])
def test_claude_rejects_invalid_response_json(
    monkeypatch: pytest.MonkeyPatch, body: str
) -> None:
    monkeypatch.setenv("ANTHROPIC_API_KEY", "secret")
    _patch_connection(
        monkeypatch,
        "arkhon.integrations.models.claude.adapter",
        _Connection(_Response(body)),
    )
    assert not ClaudeAdapter().send("prompt").ok


def test_gemini_key_health_endpoint_and_prompts(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    adapter = GeminiAdapter()
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    assert not adapter.health_check()
    assert not adapter.send("hello").ok
    monkeypatch.setenv("GOOGLE_API_KEY", "secret")
    assert adapter.health_check()
    adapter._prompts_dir = tmp_path
    assert adapter.system_prompt() == ""
    assert adapter.governance_injection() == ""
    (tmp_path / "system.md").write_text("system", encoding="utf-8")
    (tmp_path / "governance-injection.md").write_text("rules", encoding="utf-8")
    assert adapter.system_prompt() == "system"
    assert adapter.governance_injection() == "rules"


@pytest.mark.parametrize(
    ("config", "message"),
    [
        (GeminiConfig(endpoint="http://example.com"), "valid HTTPS"),
        (GeminiConfig(endpoint="https://user:pass@example.com"), "valid HTTPS"),
        (GeminiConfig(endpoint="https://example.com:bad"), "invalid port"),
        (GeminiConfig(endpoint="https://example.com:0"), "valid HTTPS"),
        (GeminiConfig(model="../unsafe"), "valid HTTPS"),
    ],
)
def test_gemini_rejects_unsafe_configuration(
    config: GeminiConfig, message: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("GOOGLE_API_KEY", "secret")
    result = GeminiAdapter(config).send("hello")
    assert not result.ok and message in result.reason


def test_gemini_success_and_http_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GOOGLE_API_KEY", "secret")
    module = "arkhon.integrations.models.gemini.adapter"
    connection = _Connection(_Response(json.dumps({
        "candidates": [{
            "content": {
                "parts": [
                    {"text": "hello "},
                    {"inlineData": "ignored"},
                    {"text": "world"},
                ]
            }
        }]
    })))
    _patch_connection(monkeypatch, module, connection)
    result = GeminiAdapter().send("prompt")
    assert result.ok and result.payload["text"] == "hello world"
    assert connection.closed
    _patch_connection(monkeypatch, module, _Connection(_Response("blocked", 429, "Rate limited")))
    result = GeminiAdapter().send("prompt")
    assert not result.ok and "429" in result.reason


@pytest.mark.parametrize(
    ("error", "expected"),
    [(TimeoutError(), "timeout"), (OSError("offline"), "network error")],
)
def test_gemini_transport_errors(
    monkeypatch: pytest.MonkeyPatch, error: Exception, expected: str
) -> None:
    monkeypatch.setenv("GOOGLE_API_KEY", "secret")
    _patch_connection(
        monkeypatch,
        "arkhon.integrations.models.gemini.adapter",
        _Connection(_Response(""), error),
    )
    result = GeminiAdapter().send("prompt")
    assert not result.ok and expected in result.reason


@pytest.mark.parametrize("body", ["not-json", "[]"])
def test_gemini_rejects_invalid_response_json(
    monkeypatch: pytest.MonkeyPatch, body: str
) -> None:
    monkeypatch.setenv("GOOGLE_API_KEY", "secret")
    _patch_connection(
        monkeypatch,
        "arkhon.integrations.models.gemini.adapter",
        _Connection(_Response(body)),
    )
    assert not GeminiAdapter().send("prompt").ok
