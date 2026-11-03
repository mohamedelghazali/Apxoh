"""Adapter for the released TSAR CLI contract.

TSAR output is untrusted SARIF. Apxoh accepts it only after validating the
SARIF envelope, scanner identity/version, commit binding, and artifact hash.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import tempfile
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as package_version
from pathlib import Path
from typing import Any

from arkhon.core.errors import SecurityError
from arkhon.core.logging import get_logger
from arkhon.evidence.integrity import sha256_of
from arkhon.integrations.base import Integration, IntegrationInfo, IntegrationResponse

logger = get_logger("integrations.tsar.adapter")
_COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")


@dataclass(frozen=True)
class TsarConfig:
    binary: str = "tsar"
    minimum_version: str = "1.1.0"
    maximum_version_exclusive: str = "2.0.0"
    timeout_seconds: int = 1800


class TsarAdapter(Integration):
    """Invoke TSAR's supported scan/SARIF interface, never an invented audit API."""

    def __init__(self, config: TsarConfig | None = None) -> None:
        self._config = config or TsarConfig()
        if self._config.timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")

    @property
    def info(self) -> IntegrationInfo:
        return IntegrationInfo(
            id="tsar",
            kind="security",
            provider="tsar",
            version=self._config.minimum_version,
            capabilities=("secret-scanning", "static-security-review", "sarif-2.1.0"),
        )

    def _binary(self) -> str | None:
        return shutil.which(self._config.binary)

    def health_check(self) -> bool:
        binary = self._binary()
        if binary is None:
            logger.warning("TSAR binary not found: %s", self._config.binary)
            return False
        try:
            result = subprocess.run(  # noqa: S603 - resolved executable and fixed arguments
                [binary, "scan", "--help"],
                capture_output=True,
                text=True,
                timeout=30,
                check=False,
            )
        except (OSError, subprocess.SubprocessError) as exc:
            logger.warning("TSAR CLI health check failed: %s", exc)
            return False
        if result.returncode != 0 or "scan" not in (result.stdout + result.stderr).lower():
            return False
        try:
            version = self.version()
            from arkhon.integrations.tsar.verifier import _check_version

            _check_version(
                version,
                self._config.minimum_version,
                self._config.maximum_version_exclusive,
            )
        except SecurityError:
            return False
        return True

    def version(self) -> str:
        if self._binary() is None:
            raise SecurityError("TSAR binary not found")
        try:
            value = package_version("tsar-cli")
        except PackageNotFoundError as exc:
            raise SecurityError("TSAR distribution metadata is unavailable") from exc
        if not re.fullmatch(
            r"(0|[1-9][0-9]*)[.](0|[1-9][0-9]*)[.](0|[1-9][0-9]*)(?:[-+][0-9A-Za-z.-]+)?",
            value,
        ):
            raise SecurityError(f"invalid TSAR package version: {value!r}")
        return value

    @staticmethod
    def _parse_sarif(output_path: Path) -> tuple[dict[str, Any], str]:
        try:
            payload = json.loads(output_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise SecurityError(f"TSAR did not produce valid SARIF JSON: {exc}") from exc
        if not isinstance(payload, dict) or payload.get("version") != "2.1.0":
            raise SecurityError("TSAR output must be a SARIF 2.1.0 object")
        runs = payload.get("runs")
        if not isinstance(runs, list) or not runs:
            raise SecurityError("TSAR SARIF contains no runs")
        run = runs[0]
        if not isinstance(run, dict):
            raise SecurityError("TSAR SARIF run must be an object")
        tool = run.get("tool")
        driver = tool.get("driver") if isinstance(tool, dict) else None
        if not isinstance(driver, dict) or driver.get("name") != "TSAR":
            raise SecurityError("SARIF driver identity is not TSAR")
        version = driver.get("version")
        if not isinstance(version, str) or not re.fullmatch(
            r"(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:[-+][0-9A-Za-z.-]+)?",
            version,
        ):
            raise SecurityError("TSAR SARIF is missing a valid semantic version")
        rules = driver.get("rules", [])
        results = run.get("results", [])
        if not isinstance(rules, list) or not isinstance(results, list):
            raise SecurityError("TSAR SARIF rules and results must be arrays")
        for item in results:
            if not isinstance(item, dict) or not isinstance(item.get("ruleId"), str):
                raise SecurityError("TSAR SARIF contains a malformed finding")
            if item.get("level", "warning") not in {"error", "warning", "note", "none"}:
                raise SecurityError("TSAR SARIF contains an unsupported severity level")
        return payload, version

    def audit(self, project_root: Path, commit_sha: str) -> IntegrationResponse:
        """Run `tsar scan <path> --format sarif --output <file>`."""
        if not _COMMIT_RE.fullmatch(commit_sha):
            return IntegrationResponse(ok=False, reason="invalid commit SHA")
        binary = self._binary()
        if binary is None:
            return IntegrationResponse(
                ok=False, reason="TSAR binary not found — security gate is BLOCKED"
            )
        root = project_root.resolve()
        if not root.is_dir():
            return IntegrationResponse(ok=False, reason=f"project directory not found: {root}")
        evidence_dir = root / ".arkhon" / "evidence" / "security"
        try:
            evidence_dir.mkdir(parents=True, exist_ok=True)
            evidence_id = f"EVID-TSAR-{uuid.uuid4().hex[:12].upper()}"
            target = evidence_dir / f"{evidence_id}.sarif"
            with tempfile.TemporaryDirectory(prefix=".tsar-", dir=evidence_dir) as tmp:
                output_path = Path(tmp) / "scan.sarif"
                command = [
                    binary,
                    "scan",
                    str(root),
                    "--format",
                    "sarif",
                    "--output",
                    str(output_path),
                ]
                try:
                    result = subprocess.run(  # noqa: S603 - resolved executable and fixed arguments
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
                # TSAR documents 0=clean, 1=findings, 2=tooling error.
                if result.returncode not in {0, 1}:
                    return IntegrationResponse(
                        ok=False,
                        reason=f"TSAR exited with {result.returncode}: {result.stderr.strip()[:300]}",
                    )
                if not output_path.is_file():
                    return IntegrationResponse(
                        ok=False, reason="TSAR completed without producing SARIF output"
                    )
                try:
                    sarif, version = self._parse_sarif(output_path)
                    from arkhon.integrations.tsar.verifier import _check_version

                    _check_version(
                        version,
                        self._config.minimum_version,
                        self._config.maximum_version_exclusive,
                    )
                except SecurityError as exc:
                    return IntegrationResponse(ok=False, reason=f"TSAR output rejected: {exc}")
                run = sarif["runs"][0]
                driver = run["tool"]["driver"]
                results = run.get("results", [])
                counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
                for finding in results:
                    level = finding.get("level", "warning")
                    if level == "error":
                        counts["high"] += 1
                    elif level == "warning":
                        counts["medium"] += 1
                    elif level == "note":
                        counts["low"] += 1
                rule_ids = ["TSAR-SCAN-EXECUTED"]
                rule_ids.extend(
                    sorted(
                        {
                            item["id"]
                            for item in driver.get("rules", [])
                            if isinstance(item, dict) and isinstance(item.get("id"), str)
                        }
                    )
                )
                status = "FAIL" if result.returncode == 1 or counts["high"] else "PASS"
                target.write_text(
                    json.dumps(sarif, indent=2, sort_keys=True) + "\n",
                    encoding="utf-8",
                )
                relative = target.relative_to(root).as_posix()
                payload = {
                    "evidence_id": evidence_id,
                    "tsar_version": version,
                    "commit_sha": commit_sha,
                    "executed_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
                    "status": status,
                    "rule_ids": rule_ids,
                    "findings": results,
                    "summary": counts,
                    "artifacts": [{"path": relative, "sha256": sha256_of(target)}],
                }
        except OSError as exc:
            return IntegrationResponse(ok=False, reason=f"cannot persist TSAR evidence: {exc}")
        return IntegrationResponse(ok=True, payload=payload, artifacts=[target])
