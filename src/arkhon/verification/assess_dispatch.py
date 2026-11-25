"""Deterministic runner instantiation and method outcome dispatch for arkhon assess."""

from __future__ import annotations

import json
from pathlib import Path

from defusedxml import ElementTree
from defusedxml.common import DefusedXmlException

from arkhon.core.constants import STATUS_BLOCKED, STATUS_FAIL, STATUS_PASS
from arkhon.verification.runners.base import Runner, RunnerOutcome, RunnerResult
from arkhon.verification.scenario_verifier import (
    verify_negative_security_scenarios,
    verify_observability_and_crash_dump_controls,
)


def create_assess_runner(runner_name: str) -> Runner | None:
    """Instantiate a supported deterministic runner on demand."""
    if runner_name == "test-suite":
        from arkhon.verification.runners.test_suite_runner import LanguageNeutralTestRunner

        return LanguageNeutralTestRunner()
    if runner_name == "ruff":
        from arkhon.verification.runners.ruff_runner import RuffRunner

        return RuffRunner()
    return None


def inspect_junit_artifact(artifact_path: Path) -> tuple[int, int, int, int] | None:
    """Return (tests, failures, errors, skipped) from a JUnit XML artifact, or None."""
    if not artifact_path.is_file() or artifact_path.is_symlink():
        return None
    try:
        xml_root = ElementTree.parse(artifact_path, forbid_dtd=True).getroot()
        suites = (
            [xml_root]
            if xml_root.tag == "testsuite"
            else list(xml_root.findall("testsuite"))
        )
        if not suites:
            return None
        tests = sum(int(s.get("tests", "0")) for s in suites)
        failures = sum(int(s.get("failures", "0")) for s in suites)
        errors = sum(int(s.get("errors", "0")) for s in suites)
        skipped = sum(int(s.get("skipped", "0")) for s in suites)
    except (ElementTree.ParseError, DefusedXmlException, OSError, ValueError):
        return None
    if any(count < 0 for count in (tests, failures, errors, skipped)):
        return None
    return tests, failures, errors, skipped


def evaluate_extended_method(
    method_id: str,
    result: RunnerResult,
    project_root: Path,
) -> tuple[str, str] | None:
    """Evaluate language-neutral test, scenario-traceability, observability, and lint methods."""
    if result.outcome == RunnerOutcome.BLOCKED:
        return STATUS_BLOCKED, result.reason or "verification runner was blocked"

    if method_id == "negative-security-scenario-traceability":
        return verify_negative_security_scenarios(project_root)

    if method_id == "observability-behavior-test-verification":
        return verify_observability_and_crash_dump_controls(project_root)

    if method_id in {
        "automated-test-suite-execution",
        "zero-test-failures-check",
        "test-collector-analysis",
        "skip-marker-detection",
    }:
        reports = [
            Path(p) for p in result.artifacts if Path(p).name == "test-execution-report.json"
        ]
        if len(reports) != 1 or not reports[0].is_file() or reports[0].is_symlink():
            return STATUS_BLOCKED, "test-suite runner did not attach test-execution-report.json"
        try:
            payload = json.loads(reports[0].read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            return STATUS_BLOCKED, "test-execution-report.json is unreadable or malformed"
        if not isinstance(payload, dict) or not isinstance(payload.get("counts"), dict):
            return STATUS_BLOCKED, "test-execution-report.json counts are malformed"
        counts = payload["counts"]
        total = int(counts.get("total", 0))
        failed = int(counts.get("failed", 0))
        errors = int(counts.get("errors", 0))
        skipped = int(counts.get("skipped", 0))
        adapter = str(payload.get("adapter", "unknown"))
        language = str(payload.get("language", "unknown"))
        if total <= 0:
            return STATUS_BLOCKED, f"{adapter} collected zero executable tests for {language}"
        if method_id in {"automated-test-suite-execution", "test-collector-analysis"}:
            return (
                STATUS_PASS,
                f"{adapter} executed {total} test(s) for {language} with normalized evidence",
            )
        if method_id == "zero-test-failures-check":
            if result.outcome == RunnerOutcome.PASS and failed == 0 and errors == 0:
                return (
                    STATUS_PASS,
                    f"{adapter} reported 0 failures and 0 errors across {total} tests",
                )
            return STATUS_FAIL, f"{adapter} reported {failed} failure(s) and {errors} error(s)"
        if method_id == "skip-marker-detection":
            if skipped == 0:
                return (
                    STATUS_PASS,
                    f"{adapter} recorded 0 skipped tests across {total} tests",
                )
            return STATUS_FAIL, f"{adapter} recorded {skipped} skipped test(s)"

    if method_id in {"static-lint-execution", "zero-lint-errors-check"}:
        json_files = [Path(p) for p in result.artifacts if str(p).endswith(".json")]
        if len(json_files) != 1 or not json_files[0].is_file() or json_files[0].is_symlink():
            return STATUS_BLOCKED, "Ruff runner did not attach a valid JSON evidence artifact"
        try:
            issues = json.loads(json_files[0].read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            return STATUS_BLOCKED, "Ruff JSON artifact is unreadable or malformed"
        if not isinstance(issues, list):
            return STATUS_BLOCKED, "Ruff JSON artifact root is not a list"
        if method_id == "static-lint-execution":
            return STATUS_PASS, f"Ruff static analysis executed ({len(issues)} issue(s) recorded)"
        if result.outcome == RunnerOutcome.PASS and len(issues) == 0:
            return STATUS_PASS, "Ruff reported zero static analysis issues"
        return STATUS_FAIL, f"Ruff reported {len(issues)} static analysis issue(s)"

    return None
