"""Claude adapter.

Sends requests to the Anthropic Messages API. Does not import the
Anthropic SDK — uses raw HTTP so Apxoh has no hard dependency on it.

All responses are treated as untrusted. The adapter only passes them
back to the caller; it never decides anything.
"""

from __future__ import annotations

import http.client
import json
import os
import ssl
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

from arkhon.core.errors import ArkhonError
from arkhon.core.logging import get_logger
from arkhon.integrations.base import (
    Integration,
    IntegrationInfo,
    IntegrationResponse,
)

logger = get_logger("integrations.models.claude")


class ClaudeError(ArkhonError):
    default_code = "CLAUDE_ERROR"


@dataclass(frozen=True)
class ClaudeConfig:
    endpoint: str = "https://api.anthropic.com/v1/messages"
    model: str = "claude-sonnet-4-5"
    max_tokens: int = 8192
    temperature: float = 0.0
    api_version: str = "2023-06-01"
    timeout_seconds: int = 120


class ClaudeAdapter(Integration):
    """Adapter for Anthropic Claude."""

    def __init__(self, config: ClaudeConfig | None = None) -> None:
        self._config = config or ClaudeConfig()
        self._prompts_dir = Path(__file__).parent / "prompts"

    @property
    def info(self) -> IntegrationInfo:
        return IntegrationInfo(
            id="claude",
            kind="model",
            provider="anthropic",
            version="1.0.0",
            capabilities=(
                "code-generation",
                "code-review",
                "long-context",
                "instruction-following",
                "structured-output",
            ),
        )

    def health_check(self) -> bool:
        return bool(os.environ.get("ANTHROPIC_API_KEY"))

    def system_prompt(self) -> str:
        path = self._prompts_dir / "system.md"
        if not path.is_file():
            return ""
        return path.read_text(encoding="utf-8")

    def governance_injection(self) -> str:
        path = self._prompts_dir / "governance-injection.md"
        if not path.is_file():
            return ""
        return path.read_text(encoding="utf-8")

    def send(self, user_message: str) -> IntegrationResponse:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            return IntegrationResponse(
                ok=False,
                reason="ANTHROPIC_API_KEY not set",
            )

        endpoint = urlsplit(self._config.endpoint)
        try:
            endpoint_port = endpoint.port
        except ValueError:
            return IntegrationResponse(
                ok=False,
                reason="Claude endpoint contains an invalid port",
            )
        if (
            endpoint_port == 0
            or any(ord(char) < 32 for char in endpoint.path)
            or endpoint.scheme != "https"
            or endpoint.hostname.lower().rstrip(".") != "api.anthropic.com"
            or endpoint.username
            or endpoint.password
            or endpoint.query
            or endpoint.fragment
        ):
            return IntegrationResponse(
                ok=False,
                reason="Claude endpoint must be HTTPS to the approved Anthropic API host without credentials or query",
            )

        payload: dict[str, Any] = {
            "model": self._config.model,
            "max_tokens": self._config.max_tokens,
            "temperature": self._config.temperature,
            "system": self.system_prompt(),
            "messages": [{"role": "user", "content": user_message}],
        }

        # Explicit default SSL context verifies peer certificates.
        # nosemgrep: python.lang.security.audit.httpsconnection-detected.httpsconnection-detected
        connection = http.client.HTTPSConnection(
            endpoint.hostname or "",
            endpoint.port or 443,
            timeout=self._config.timeout_seconds,
            context=ssl.create_default_context(),
        )
        try:
            connection.request(
                "POST",
                endpoint.path or "/",
                body=json.dumps(payload).encode("utf-8"),
                headers={
                    "x-api-key": api_key,
                    "anthropic-version": self._config.api_version,
                    "content-type": "application/json",
                },
            )
            response = connection.getresponse()
            body = response.read().decode("utf-8")
            if response.status >= 400:
                return IntegrationResponse(
                    ok=False,
                    reason=f"HTTP {response.status}: {body[:200]}",
                )
        except TimeoutError:
            return IntegrationResponse(
                ok=False,
                reason=f"timeout after {self._config.timeout_seconds}s",
            )
        except (OSError, http.client.HTTPException) as exc:
            return IntegrationResponse(
                ok=False,
                reason=f"network error: {exc}",
            )
        finally:
            connection.close()

        try:
            parsed = json.loads(body)
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            return IntegrationResponse(
                ok=False,
                reason=f"invalid JSON response: {exc}",
            )
        if not isinstance(parsed, dict):
            return IntegrationResponse(
                ok=False,
                reason="invalid response: expected JSON object",
            )

        text = ""
        content = parsed.get("content", [])
        if isinstance(content, list):
            for block in content:
                if isinstance(block, dict) and block.get("type") == "text":
                    value = block.get("text", "")
                    if isinstance(value, str):
                        text += value

        return IntegrationResponse(
            ok=True,
            payload={"text": text, "raw": parsed, "model": self._config.model},
        )
