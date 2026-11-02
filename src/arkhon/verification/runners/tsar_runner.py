"""TSAR runner — delegates security scanning and verifies its evidence."""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

from arkhon.core.logging import get_logger
from arkhon.integrations.tsar.adapter import TsarAdapter, TsarConfig
from arkhon.integrations.tsar.verifier import verify_tsar_evidence
from arkhon.verification.runners.base import Runner, RunnerOutcome, RunnerResult

logger = get_logger("verification.runners.tsar")


class TsarRunner(Runner):
    def __init__(self, timeout_seconds: int = 1800) -> None:
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        self._adapter = TsarAdapter(TsarConfig(timeout_seconds=timeout_seconds))

    @property
    def name(self) -> str:
        return "tsar"

    def run(self, project_root: Path) -> RunnerResult:
        try:
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"], cwd=project_root,
                capture_output=True, text=True, timeout=10, check=True,
            )
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, OSError) as exc:
            return RunnerResult(
                runner=self.name, outcome=RunnerOutcome.BLOCKED,
                reason=f"cannot resolve commit SHA: {exc}",
            )
        commit_sha = result.stdout.strip()
        if not re.fullmatch(r"[0-9a-f]{40}", commit_sha):
            return RunnerResult(
                runner=self.name, outcome=RunnerOutcome.BLOCKED,
                reason=f"invalid commit SHA: {commit_sha!r}",
            )
        response = self._adapter.audit(project_root, commit_sha)
        if not response.ok:
            return RunnerResult(
                runner=self.name, outcome=RunnerOutcome.BLOCKED,
                reason=response.reason or "TSAR audit failed",
            )
        try:
            evidence = verify_tsar_evidence(
                response.payload, expected_commit_sha=commit_sha,
                evidence_root=project_root,
            )
        except Exception as exc:
            logger.warning("TSAR evidence verification failed: %s", exc)
            return RunnerResult(
                runner=self.name, outcome=RunnerOutcome.BLOCKED,
                reason=f"TSAR evidence verification failed: {exc}",
                artifacts=response.artifacts,
            )
        if evidence.status == "FAIL":
            return RunnerResult(
                runner=self.name, outcome=RunnerOutcome.FAIL,
                reason="TSAR reported FAIL", artifacts=response.artifacts,
            )
        if evidence.status == "BLOCKED":
            return RunnerResult(
                runner=self.name, outcome=RunnerOutcome.BLOCKED,
                reason="TSAR reported BLOCKED", artifacts=response.artifacts,
            )
        return RunnerResult(
            runner=self.name, outcome=RunnerOutcome.PASS, artifacts=response.artifacts,
        )
