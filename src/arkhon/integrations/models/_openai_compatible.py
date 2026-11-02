"""Shared adapter for OpenAI Chat Completions-compatible APIs.

Responses are untrusted and no governance decision is made here. API keys
are read from the environment and are never included in returned errors.
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any

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
    max_tokens_field: str = "max_tokens"


class OpenAICompatibleAdapter(Integration):
    """Configurable adapter for providers implementing Chat Completions."""

    def __init__(self, config: OpenAICompatibleConfig) -> None:
        self.config = config
        self._prompts_dir = Path(__file__).parent / config.id / "prompts"

    @property
    def info(self) -> IntegrationInfo:
        return IntegrationInfo(
            id=self.config.id, kind="model", provider=self.config.provider,
            version="1.0.0",
            capabilities=("code-generation", "code-review", "instruction-following"),
        )

    def health_check(self) -> bool:
        return not self.config.api_key_required or bool(os.environ.get(self.config.api_key_env))

    def system_prompt(self) -> str:
        path = self._prompts_dir / "system.md"
        return path.read_text(encoding="utf-8") if path.is_file() else ""

    def governance_injection(self) -> str:
        path = self._prompts_dir / "governance-injection.md"
        return path.read_text(encoding="utf-8") if path.is_file() else ""

    @staticmethod
    def _content_text(value: Any) -> str:
        if isinstance(value, str):
            return value
        if isinstance(value, list):
            return "".join(
                item.get("text", "") for item in value
                if isinstance(item, dict) and isinstance(item.get("text", ""), str)
            )
        return ""

    def send(self, user_message: str) -> IntegrationResponse:
        api_key = os.environ.get(self.config.api_key_env)
        if self.config.api_key_required and not api_key:
            return IntegrationResponse(ok=False, reason=f"{self.config.api_key_env} not set")

        messages: list[dict[str, str]] = []
        system = self.system_prompt()
        if system:
            messages.append({"role": self.config.system_role, "content": system})
        messages.append({"role": "user", "content": user_message})
        payload: dict[str, Any] = {
            "model": self.config.default_model,
            self.config.max_tokens_field: self.config.max_tokens,
            "messages": messages,
        }
        if self.config.temperature is not None:
            payload["temperature"] = self.config.temperature

        headers = {"content-type": "application/json"}
        if api_key:
            headers["authorization"] = f"Bearer {api_key}"
        request = urllib.request.Request(
            self.config.endpoint, data=json.dumps(payload).encode("utf-8"),
            headers=headers, method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.config.timeout_seconds) as response:
                body = response.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            return IntegrationResponse(ok=False, reason=f"HTTP {exc.code}: {exc.reason}")
        except TimeoutError:
            return IntegrationResponse(ok=False, reason=f"timeout after {self.config.timeout_seconds}s")
        except urllib.error.URLError as exc:
            return IntegrationResponse(ok=False, reason=f"network error: {exc}")

        try:
            parsed = json.loads(body)
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            return IntegrationResponse(ok=False, reason=f"invalid JSON response: {exc}")

        choices = parsed.get("choices", [])
        text = ""
        if choices and isinstance(choices[0], dict):
            message = choices[0].get("message", {})
            if isinstance(message, dict):
                text = self._content_text(message.get("content", ""))
        return IntegrationResponse(
            ok=True, payload={"text": text, "raw": parsed, "model": self.config.default_model},
        )
