"""Pytest runner producing JUnit XML evidence."""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from defusedxml import ElementTree

from arkhon.core.logging import get_logger
from arkhon.verification.runners.base import Runner, RunnerOutcome, RunnerResult

logger = get_logger("verification.runners.pytest")


class PytestRunner(Runner):
    def __init__(self, timeout_seconds: int = 900) -> None:
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        self._timeout = timeout_seconds

    @property
    def name(self) -> str:
        return "pytest"

    def run(self, project_root: Path) -> RunnerResult:
        root = project_root.resolve()
        if not root.is_dir() or not (root / "tests").is_dir():
            return RunnerResult(
                runner=self.name,
                outcome=RunnerOutcome.BLOCKED,
                reason="project has no tests/ directory",
            )
        with tempfile.TemporaryDirectory(prefix="apxoh-pytest-") as tmp:
            junit = Path(tmp) / "pytest.xml"
            command = [
                sys.executable,
                "-m",
                "pytest",
                "tests",
                "--junit-xml",
                str(junit),
                "-q",
                "--no-header",
                "-p",
                "no:cacheprovider",
            ]
            try:
                result = subprocess.run(  # noqa: S603 - current Python interpreter and fixed pytest arguments
                    command,
                    cwd=root,
                    capture_output=True,
                    text=True,
                    timeout=self._timeout,
                    check=False,
                )
            except subprocess.TimeoutExpired:
                return RunnerResult(
                    runner=self.name,
                    outcome=RunnerOutcome.BLOCKED,
                    reason=f"pytest timed out after {self._timeout}s",
                )
            except OSError as exc:
                return RunnerResult(
                    runner=self.name,
                    outcome=RunnerOutcome.BLOCKED,
                    reason=f"pytest failed to start: {exc}",
                )
            if not junit.is_file():
                detail = (result.stderr or result.stdout).strip()[:300]
                return RunnerResult(
                    runner=self.name,
                    outcome=RunnerOutcome.BLOCKED,
                    reason=f"pytest produced no JUnit XML (exit={result.returncode}): {detail}",
                )
            try:
                xml_root = ElementTree.parse(junit).getroot()
                suites = (
                    [xml_root]
                    if xml_root.tag == "testsuite"
                    else list(xml_root.findall("testsuite"))
                )
                tests = sum(int(suite.get("tests", "0")) for suite in suites)
                failures = sum(int(suite.get("failures", "0")) for suite in suites)
                errors = sum(int(suite.get("errors", "0")) for suite in suites)
                skipped = sum(int(suite.get("skipped", "0")) for suite in suites)
            except (ElementTree.ParseError, ValueError) as exc:
                return RunnerResult(
                    runner=self.name,
                    outcome=RunnerOutcome.BLOCKED,
                    reason=f"invalid JUnit XML: {exc}",
                )
            if tests == 0:
                return RunnerResult(
                    runner=self.name,
                    outcome=RunnerOutcome.BLOCKED,
                    reason="pytest collected no tests",
                )
            target_dir = root / ".arkhon" / "evidence" / "testing"
            try:
                target_dir.mkdir(parents=True, exist_ok=True)
                target = target_dir / "pytest.xml"
                shutil.copy2(junit, target)
            except OSError as exc:
                return RunnerResult(
                    runner=self.name,
                    outcome=RunnerOutcome.BLOCKED,
                    reason=f"cannot persist pytest evidence: {exc}",
                )
            if failures or errors or result.returncode != 0:
                return RunnerResult(
                    runner=self.name,
                    outcome=RunnerOutcome.FAIL,
                    reason=f"pytest: {failures} failure(s), {errors} error(s), {skipped} skipped",
                    artifacts=[target],
                )
            return RunnerResult(runner=self.name, outcome=RunnerOutcome.PASS, artifacts=[target])
