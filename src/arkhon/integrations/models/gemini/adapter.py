"""Google Gemini generateContent adapter."""
from __future__ import annotations

import http.client
import json
import os
import re
import ssl
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

from arkhon.integrations.base import Integration, IntegrationInfo, IntegrationResponse


@dataclass(frozen=True)
class GeminiConfig:
    endpoint: str = "https://generativelanguage.googleapis.com/v1beta/models"
    model: str = "gemini-2.5-flash"
    max_tokens: int = 8192
    temperature: float = 0.0
    timeout_seconds: int = 120


class GeminiAdapter(Integration):
    def __init__(self, config: GeminiConfig | None = None) -> None:
        self.config = config or GeminiConfig()
        self._prompts_dir = Path(__file__).parent / "prompts"

    @property
    def info(self) -> IntegrationInfo:
        return IntegrationInfo(
            id="gemini",
            kind="model",
            provider="google",
            version="1.0.0",
            capabilities=("code-generation", "long-context", "multimodal"),
        )

    def health_check(self) -> bool:
        return bool(os.environ.get("GOOGLE_API_KEY"))

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

    def send(self, user_message: str) -> IntegrationResponse:
        api_key = os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            return IntegrationResponse(
                ok=False,
                reason="GOOGLE_API_KEY not set",
            )

        parsed_endpoint = urlsplit(self.config.endpoint)
        try:
            endpoint_port = parsed_endpoint.port
        except ValueError:
            return IntegrationResponse(
                ok=False,
                reason="Gemini endpoint contains an invalid port",
            )
        if (
            endpoint_port == 0
            or any(ord(char) < 32 for char in parsed_endpoint.path)
            or parsed_endpoint.scheme != "https"
            or not parsed_endpoint.hostname
            or parsed_endpoint.username
            or parsed_endpoint.password
            or parsed_endpoint.query
            or parsed_endpoint.fragment
            or not re.fullmatch(r"[A-Za-z0-9._-]+", self.config.model)
        ):
            return IntegrationResponse(
                ok=False,
                reason="Gemini endpoint must be valid HTTPS and model must be a safe identifier",
            )

        payload: dict[str, Any] = {
            "contents": [
                {"role": "user", "parts": [{"text": user_message}]}
            ],
            "generationConfig": {
                "maxOutputTokens": self.config.max_tokens,
                "temperature": self.config.temperature,
            },
        }
        system = self.system_prompt()
        if system:
            payload["systemInstruction"] = {"parts": [{"text": system}]}

        connection = http.client.HTTPSConnection(
            parsed_endpoint.hostname or "",
            parsed_endpoint.port or 443,
            timeout=self.config.timeout_seconds,
            context=ssl.create_default_context(),
        )
        try:
            connection.request(
                "POST",
                f"{parsed_endpoint.path.rstrip('/')}/{self.config.model}:generateContent",
                body=json.dumps(payload).encode("utf-8"),
                headers={
                    "content-type": "application/json",
                    "x-goog-api-key": api_key,
                },
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

        text = ""
        candidates = parsed.get("candidates", [])
        if isinstance(candidates, list) and candidates:
            candidate = candidates[0]
            if isinstance(candidate, dict):
                content = candidate.get("content", {})
                if isinstance(content, dict):
                    parts = content.get("parts", [])
                    if isinstance(parts, list):
                        text = "".join(
                            part.get("text", "")
                            for part in parts
                            if isinstance(part, dict)
                            and isinstance(part.get("text", ""), str)
                        )

        return IntegrationResponse(
            ok=True,
            payload={
                "text": text,
                "raw": parsed,
                "model": self.config.model,
            },
        )
