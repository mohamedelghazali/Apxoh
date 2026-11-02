"""Shared transport for OpenAI Chat Completions-compatible APIs."""
from __future__ import annotations
import json, os, socket, urllib.error, urllib.request
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
    token_parameter: str = "max_tokens"

class OpenAICompatibleAdapter(Integration):
    """Transport adapter; responses remain untrusted and never decide governance."""
    def __init__(self, config: OpenAICompatibleConfig) -> None:
        self.config = config
        self._prompts_dir = Path(__file__).parent / config.id / "prompts"

    @property
    def info(self) -> IntegrationInfo:
        caps = ["code-generation", "code-review", "instruction-following"]
        if self.config.id == "openai-o": caps.append("reasoning")
        return IntegrationInfo(id=self.config.id, kind="model", provider=self.config.provider,
                               version="1.0.0", capabilities=tuple(caps))

    def health_check(self) -> bool:
        return not self.config.api_key_required or bool(os.environ.get(self.config.api_key_env))

    def system_prompt(self) -> str:
        p = self._prompts_dir / "system.md"
        return p.read_text(encoding="utf-8") if p.is_file() else ""

    def governance_injection(self) -> str:
        p = self._prompts_dir / "governance-injection.md"
        return p.read_text(encoding="utf-8") if p.is_file() else ""

    @staticmethod
    def _response_text(value: Any) -> str:
        if isinstance(value, str): return value
        if isinstance(value, list):
            return "".join(x.get("text", "") for x in value
                           if isinstance(x, dict) and isinstance(x.get("text", ""), str))
        return ""

    def send(self, user_message: str) -> IntegrationResponse:
        key = os.environ.get(self.config.api_key_env)
        if self.config.api_key_required and not key:
            return IntegrationResponse(ok=False, reason=f"{self.config.api_key_env} not set")
        messages = []
        system = self.system_prompt()
        if system: messages.append({"role": self.config.system_role, "content": system})
        messages.append({"role": "user", "content": user_message})
        payload: dict[str, Any] = {"model": self.config.default_model,
                                  self.config.token_parameter: self.config.max_tokens,
                                  "messages": messages}
        if self.config.temperature is not None: payload["temperature"] = self.config.temperature
        headers = {"content-type": "application/json"}
        if key: headers["authorization"] = f"Bearer {key}"
        req = urllib.request.Request(self.config.endpoint, data=json.dumps(payload).encode(),
                                     headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=self.config.timeout_seconds) as resp:
                raw = resp.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            return IntegrationResponse(ok=False, reason=f"HTTP {exc.code}: {exc.reason}")
        except urllib.error.URLError as exc:
            return IntegrationResponse(ok=False, reason=f"network error: {exc.reason}")
        except (socket.timeout, TimeoutError):
            return IntegrationResponse(ok=False, reason=f"timeout after {self.config.timeout_seconds}s")
        try: parsed = json.loads(raw)
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            return IntegrationResponse(ok=False, reason=f"invalid JSON response: {exc}")
        if not isinstance(parsed, dict):
            return IntegrationResponse(ok=False, reason="invalid response: expected JSON object")
        choices = parsed.get("choices", [])
        content: Any = ""
        if isinstance(choices, list) and choices and isinstance(choices[0], dict):
            msg = choices[0].get("message", {})
            if isinstance(msg, dict): content = msg.get("content", "")
        return IntegrationResponse(ok=True, payload={"text": self._response_text(content),
                                  "raw": parsed, "model": self.config.default_model})
