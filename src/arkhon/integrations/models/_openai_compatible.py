"""Shared transport for OpenAI Chat Completions-compatible APIs."""

from __future__ import annotations

import http.client
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

from arkhon.integrations.base import Integration, IntegrationInfo, IntegrationResponse


@dataclass(frozen=True)
class OpenAICompatibleConfig:
    id: str
    provider: str
    endpoint: str
    default_model: str
    available_models: tuple[str, ...]
    max_tokens: int
    temperature: float | None
    timeout_seconds: int
    api_key_env: str
    api_key_required: bool = True
    system_role: str = "system"
    max_output_field: str = "max_tokens"


class OpenAICompatibleAdapter(Integration):
    """Transport adapter; provider responses remain untrusted input."""

    def __init__(self, config: OpenAICompatibleConfig) -> None:
        self.config = config
        self._prompts_dir = Path(__file__).parent / config.id / "prompts"

    @property
    def info(self) -> IntegrationInfo:
        capabilities = ["code-generation", "code-review", "instruction-following"]
        if self.config.id == "openai-o":
            capabilities.append("reasoning")
        return IntegrationInfo(
            id=self.config.id,
            kind="model",
            provider=self.config.provider,
            version="1.0.0",
            capabilities=tuple(capabilities),
        )

    def health_check(self) -> bool:
        return not self.config.api_key_required or bool(os.environ.get(self.config.api_key_env))

    def system_prompt(self) -> str:
        prompt_path = self._prompts_dir / "system.md"
        if not prompt_path.is_file():
            return ""
        return prompt_path.read_text(encoding="utf-8")

    def governance_injection(self) -> str:
        prompt_path = self._prompts_dir / "governance-injection.md"
        if not prompt_path.is_file():
            return ""
        return prompt_path.read_text(encoding="utf-8")

    @staticmethod
    def _response_text(value: Any) -> str:
        if isinstance(value, str):
            return value
        if isinstance(value, list):
            return "".join(
                item.get("text", "")
                for item in value
                if isinstance(item, dict) and isinstance(item.get("text", ""), str)
            )
        return ""

    def _endpoint_is_allowed(self) -> bool:
        parsed = urlsplit(self.config.endpoint)
        if parsed.username or parsed.password or parsed.query or parsed.fragment:
            return False
        if not parsed.hostname:
            return False
        try:
            port = parsed.port
        except ValueError:
            return False
        if port == 0 or any(ord(char) < 32 for char in parsed.path):
            return False
        if parsed.scheme == "https":
            return True
        return parsed.scheme == "http" and parsed.hostname in {
            "127.0.0.1",
            "localhost",
            "::1",
        }

    def send(self, user_message: str) -> IntegrationResponse:
        if not self._endpoint_is_allowed():
            return IntegrationResponse(
                ok=False,
                reason="provider endpoint must use HTTPS or loopback HTTP",
            )

        api_key = os.environ.get(self.config.api_key_env)
        if self.config.api_key_required and not api_key:
            return IntegrationResponse(
                ok=False,
                reason=f"{self.config.api_key_env} not set",
            )

        messages: list[dict[str, str]] = []
        system = self.system_prompt()
        if system:
            messages.append({"role": self.config.system_role, "content": system})
        messages.append({"role": "user", "content": user_message})

        payload: dict[str, Any] = {
            "model": self.config.default_model,
            self.config.max_output_field: self.config.max_tokens,
            "messages": messages,
        }
        if self.config.temperature is not None:
            payload["temperature"] = self.config.temperature

        headers = {"content-type": "application/json"}
        if api_key:
            headers["authorization"] = f"Bearer {api_key}"

        endpoint = urlsplit(self.config.endpoint)
        connection_type = (
            http.client.HTTPSConnection
            if endpoint.scheme == "https"
            else http.client.HTTPConnection
        )
        connection = connection_type(
            endpoint.hostname or "",
            endpoint.port,
            timeout=self.config.timeout_seconds,
        )
        try:
            connection.request(
                "POST",
                endpoint.path or "/",
                body=json.dumps(payload).encode("utf-8"),
                headers=headers,
            )
            response = connection.getresponse()
            raw = response.read().decode("utf-8")
            if response.status >= 400:
                return IntegrationResponse(
                    ok=False,
                    reason=f"HTTP {response.status}: {response.reason}",
                )
        except TimeoutError:
            return IntegrationResponse(
                ok=False,
                reason=f"timeout after {self.config.timeout_seconds}s",
            )
        except (OSError, http.client.HTTPException) as exc:
            return IntegrationResponse(
                ok=False,
                reason=f"network error: {exc}",
            )
        finally:
            connection.close()

        try:
            parsed = json.loads(raw)
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

        choices = parsed.get("choices", [])
        content: Any = ""
        if isinstance(choices, list) and choices and isinstance(choices[0], dict):
            message = choices[0].get("message", {})
            if isinstance(message, dict):
                content = message.get("content", "")

        return IntegrationResponse(
            ok=True,
            payload={
                "text": self._response_text(content),
                "raw": parsed,
                "model": self.config.default_model,
            },
        )
