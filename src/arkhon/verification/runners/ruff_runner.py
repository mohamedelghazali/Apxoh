"""Ruff runner — static analysis through the Ruff CLI."""
from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from pathlib import Path

from arkhon.core.logging import get_logger
from arkhon.verification.runners.base import Runner, RunnerOutcome, RunnerResult

logger = get_logger("verification.runners.ruff")


class RuffRunner(Runner):
    def __init__(self, timeout_seconds: int = 300) -> None:
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        self._timeout = timeout_seconds

    @property
    def name(self) -> str:
        return "ruff"

    def run(self, project_root: Path) -> RunnerResult:
        binary = shutil.which("ruff")
        if binary is None:
            return RunnerResult(
                runner=self.name, outcome=RunnerOutcome.BLOCKED,
                reason="ruff not found on PATH",
            )
        root = project_root.resolve()
        with tempfile.TemporaryDirectory(prefix="apxoh-ruff-") as tmp:
            output = Path(tmp) / "ruff.json"
            command = [binary, "check", "--output-format=json", "--no-fix", "."]
            try:
                result = subprocess.run(
                    command, cwd=root, capture_output=True, text=True,
                    timeout=self._timeout, check=False,
                )
            except subprocess.TimeoutExpired:
                return RunnerResult(
                    runner=self.name, outcome=RunnerOutcome.BLOCKED,
                    reason=f"ruff timed out after {self._timeout}s",
                )
            except OSError as exc:
                return RunnerResult(
                    runner=self.name, outcome=RunnerOutcome.BLOCKED,
                    reason=f"ruff failed to start: {exc}",
                )
            try:
                issues = json.loads(result.stdout or "[]")
                if not isinstance(issues, list):
                    raise ValueError("JSON root is not an array")
            except (json.JSONDecodeError, ValueError) as exc:
                return RunnerResult(
                    runner=self.name, outcome=RunnerOutcome.BLOCKED,
                    reason=f"invalid Ruff JSON output: {exc}",
                )
            target_dir = root / ".arkhon" / "evidence" / "code-quality"
            try:
                target_dir.mkdir(parents=True, exist_ok=True)
                target = target_dir / "ruff.json"
                output.write_text(json.dumps(issues, indent=2) + "\n", encoding="utf-8")
                shutil.copy2(output, target)
            except OSError as exc:
                return RunnerResult(
                    runner=self.name, outcome=RunnerOutcome.BLOCKED,
                    reason=f"cannot persist Ruff evidence: {exc}",
                )
            if result.returncode == 0 and not issues:
                return RunnerResult(runner=self.name, outcome=RunnerOutcome.PASS, artifacts=[target])
            if result.returncode == 1:
                return RunnerResult(
                    runner=self.name, outcome=RunnerOutcome.FAIL,
                    reason=f"ruff found {len(issues)} issue(s)", artifacts=[target],
                )
            return RunnerResult(
                runner=self.name, outcome=RunnerOutcome.BLOCKED,
                reason=f"ruff exited unexpectedly with code {result.returncode}: {result.stderr[:300]}",
                artifacts=[target],
            )
