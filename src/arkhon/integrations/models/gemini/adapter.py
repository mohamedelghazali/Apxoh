"""Google Gemini generateContent adapter."""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
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
        if parsed_endpoint.scheme != "https" or not parsed_endpoint.hostname:
            return IntegrationResponse(
                ok=False,
                reason="Gemini endpoint must use HTTPS",
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

        request = urllib.request.Request(
            f"{self.config.endpoint}/{self.config.model}:generateContent",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "content-type": "application/json",
                "x-goog-api-key": api_key,
            },
            method="POST",
        )
        try:
            # Gemini endpoint is required to use HTTPS above.
            with urllib.request.urlopen(  # noqa: S310
                request,
                timeout=self.config.timeout_seconds,
            ) as response:
                raw = response.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            return IntegrationResponse(
                ok=False,
                reason=f"HTTP {exc.code}: {exc.reason}",
            )
        except TimeoutError:
            return IntegrationResponse(
                ok=False,
                reason=f"timeout after {self.config.timeout_seconds}s",
            )
        except urllib.error.URLError as exc:
            return IntegrationResponse(
                ok=False,
                reason=f"network error: {exc.reason}",
            )

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
