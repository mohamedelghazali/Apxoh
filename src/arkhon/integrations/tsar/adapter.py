"""Adapter for the external TSAR CLI.

TSAR output is untrusted. The verifier must validate it before it can
contribute to a gate decision.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from arkhon.core.errors import SecurityError
from arkhon.core.logging import get_logger
from arkhon.integrations.base import Integration, IntegrationInfo, IntegrationResponse

logger = get_logger("integrations.tsar.adapter")


@dataclass(frozen=True)
class TsarConfig:
    binary: str = "tsar"
    minimum_version: str = "1.1.0"
    timeout_seconds: int = 1800


class TsarAdapter(Integration):
    """Invoke TSAR as an external executable, never as an imported library."""

    def __init__(self, config: TsarConfig | None = None) -> None:
        self._config = config or TsarConfig()

    @property
    def info(self) -> IntegrationInfo:
        return IntegrationInfo(
            id="tsar",
            kind="security",
            provider="tsar",
            version=self._config.minimum_version,
            capabilities=("audit", "sast", "dast", "sca", "secrets"),
        )

    def _binary(self) -> str | None:
        return shutil.which(self._config.binary)

    def health_check(self) -> bool:
        binary = self._binary()
        if binary is None:
            logger.warning("TSAR binary not found: %s", self._config.binary)
            return False
        try:
            result = subprocess.run(
                [binary, "--version"],
                capture_output=True,
                text=True,
                timeout=30,
                check=False,
            )
        except (OSError, subprocess.SubprocessError) as exc:
            logger.warning("TSAR version check failed: %s", exc)
            return False
        return result.returncode == 0 and bool(result.stdout.strip())

    def version(self) -> str:
        binary = self._binary()
        if binary is None:
            raise SecurityError("TSAR binary not found")
        try:
            result = subprocess.run(
                [binary, "--version"],
                capture_output=True,
                text=True,
                timeout=30,
                check=False,
            )
        except (OSError, subprocess.SubprocessError) as exc:
            raise SecurityError(f"TSAR version check failed: {exc}") from exc
        if result.returncode != 0 or not result.stdout.strip():
            raise SecurityError(f"TSAR --version failed: {result.stderr.strip()[:300]}")
        return result.stdout.strip()

    def audit(self, project_root: Path, commit_sha: str) -> IntegrationResponse:
        """Run an audit and parse the JSON document written to stdout."""
        if len(commit_sha) != 40 or any(c not in "0123456789abcdef" for c in commit_sha):
            return IntegrationResponse(ok=False, reason="invalid commit SHA")
        binary = self._binary()
        if binary is None:
            return IntegrationResponse(
                ok=False,
                reason="TSAR binary not found — security gate is BLOCKED",
            )
        root = project_root.resolve()
        if not root.is_dir():
            return IntegrationResponse(ok=False, reason=f"project directory not found: {root}")

        evidence_dir = root / ".arkhon" / "evidence" / "security"
        try:
            evidence_dir.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            return IntegrationResponse(
                ok=False, reason=f"cannot prepare TSAR evidence directory: {exc}"
            )
        target = evidence_dir / f"tsar-{commit_sha[:12]}.json"
        command = [
            binary,
            "audit",
            "--project",
            str(root),
            "--output",
            "json",
            "--commit",
            commit_sha,
            "--output-file",
            str(target),
        ]
        logger.info("running TSAR audit for commit %s", commit_sha)
        try:
            result = subprocess.run(
                command,
                cwd=root,
                capture_output=True,
                text=True,
                timeout=self._config.timeout_seconds,
                check=False,
            )
        except subprocess.TimeoutExpired:
            return IntegrationResponse(
                ok=False,
                reason=f"TSAR timed out after {self._config.timeout_seconds}s",
            )
        except OSError as exc:
            return IntegrationResponse(ok=False, reason=f"TSAR failed to start: {exc}")

        if result.returncode != 0:
            return IntegrationResponse(
                ok=False,
                reason=f"TSAR exited with {result.returncode}: {result.stderr.strip()[:300]}",
            )
        output_text = target.read_text(encoding="utf-8") if target.is_file() else result.stdout
        try:
            payload = json.loads(output_text)
        except (OSError, json.JSONDecodeError) as exc:
            return IntegrationResponse(ok=False, reason=f"TSAR output is not valid JSON: {exc}")
        if not isinstance(payload, dict):
            return IntegrationResponse(ok=False, reason="TSAR JSON output must be an object")

        try:
            # Avoid silently replacing evidence for the same commit.
            serialized = json.dumps(payload, indent=2, sort_keys=True) + "\n"
            if target.exists():
                try:
                    existing_payload = json.loads(target.read_text(encoding="utf-8"))
                except (OSError, json.JSONDecodeError) as exc:
                    return IntegrationResponse(
                        ok=False,
                        reason=f"existing TSAR evidence is invalid: {exc}",
                    )
                if existing_payload != payload:
                    return IntegrationResponse(
                        ok=False,
                        reason=f"refusing to overwrite different TSAR evidence: {target}",
                    )
            else:
                target.write_text(serialized, encoding="utf-8")
        except OSError as exc:
            return IntegrationResponse(ok=False, reason=f"cannot persist TSAR evidence: {exc}")

        return IntegrationResponse(ok=True, payload=payload, artifacts=[target])
