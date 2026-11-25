"""Language-neutral test suite runner normalizing execution evidence across ecosystems."""

from __future__ import annotations

import contextlib
import json
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any

import yaml
from defusedxml import ElementTree
from defusedxml.common import DefusedXmlException

from arkhon.core.errors import ConfigError
from arkhon.core.logging import get_logger
from arkhon.language_support.detector import detect_languages
from arkhon.language_support.registry import load_registry
from arkhon.verification.runners.base import Runner, RunnerOutcome, RunnerResult
from arkhon.verification.runners.pytest_runner import PytestRunner

logger = get_logger("verification.runners.test_suite")

_CARGO_CASE_RE = re.compile(r"^test\s+(\S+)\s+\.\.\.\s+(ok|FAILED|ignored)\s*$")
_NODE_CASE_RE = re.compile(r"^\s*(ok|not ok)\s+\d+\s+-\s+(.+?)(?:\s+#\s*(SKIP|TODO).*)?$")


def _declared_primary_language(project_root: Path) -> str | None:
    decl = project_root / ".arkhon" / "project.yaml"
    if not decl.is_file() or decl.is_symlink():
        return None
    try:
        data = yaml.safe_load(decl.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError):
        return None
    if not isinstance(data, dict):
        return None
    languages = data.get("languages")
    if not isinstance(languages, dict):
        return None
    primary = languages.get("primary")
    if isinstance(primary, str) and primary.strip():
        return primary.strip().lower()
    return None


def resolve_project_language(project_root: Path) -> tuple[str, str]:
    """Resolve primary project language from explicit declaration or project evidence."""
    root = project_root.resolve()
    try:
        known_ids = set(load_registry().ids())
    except ConfigError:
        known_ids = {
            "python",
            "javascript",
            "typescript",
            "java",
            "csharp",
            "cpp",
            "go",
            "rust",
            "ruby",
        }

    declared = _declared_primary_language(root)
    if declared is not None:
        if declared in known_ids:
            return declared, "declared in .arkhon/project.yaml"
        return declared, "unregistered language declared in .arkhon/project.yaml"

    manifest_markers: tuple[tuple[str, tuple[str, ...]], ...] = (
        ("go", ("go.mod",)),
        ("rust", ("Cargo.toml",)),
        ("typescript", ("tsconfig.json",)),
        ("javascript", ("package.json",)),
        ("python", ("pyproject.toml", "pytest.ini", "setup.py", "setup.cfg")),
        ("java", ("pom.xml", "build.gradle", "build.gradle.kts")),
        ("cpp", ("CMakeLists.txt", "meson.build")),
        ("ruby", ("Gemfile",)),
    )
    for lang_id, files in manifest_markers:
        if any((root / name).is_file() for name in files):
            return lang_id, f"detected {lang_id} build manifest"
    if list(root.glob("*.csproj")) or list(root.glob("*.sln")):
        return "csharp", "detected .NET project file"

    with contextlib.suppress(ConfigError, OSError, ValueError):
        detection = detect_languages(root)
        if detection.primary is not None:
            return detection.primary, "inferred from source file extensions"
    return "unknown", "no project language markers detected"


def _persist_normalized_report(
    project_root: Path,
    payload: dict[str, Any],
) -> Path | None:
    target_dir = project_root.resolve() / ".arkhon" / "evidence" / "testing"
    try:
        target_dir.mkdir(parents=True, exist_ok=True)
        resolved_dir = target_dir.resolve()
        resolved_dir.relative_to(project_root.resolve())
        report_path = resolved_dir / "test-execution-report.json"
        if report_path.is_symlink():
            return None
        report_path.write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        return report_path
    except (OSError, ValueError):
        return None


def _parse_junit_cases(junit_path: Path) -> tuple[dict[str, int], list[dict[str, str]]] | None:
    if not junit_path.is_file() or junit_path.is_symlink():
        return None
    try:
        xml_root = ElementTree.parse(junit_path, forbid_dtd=True).getroot()
        if xml_root is None:
            return None
        suites = (
            [xml_root]
            if xml_root.tag == "testsuite"
            else list(xml_root.findall("testsuite"))
        )
        if not suites:
            return None
        total = sum(int(s.get("tests", "0")) for s in suites)
        failed = sum(int(s.get("failures", "0")) for s in suites)
        errors = sum(int(s.get("errors", "0")) for s in suites)
        skipped = sum(int(s.get("skipped", "0")) for s in suites)
    except (ElementTree.ParseError, DefusedXmlException, OSError, ValueError):
        return None
    if any(c < 0 for c in (total, failed, errors, skipped)):
        return None

    cases: list[dict[str, str]] = []
    for suite in suites:
        for tc in suite.findall("testcase"):
            name = tc.get("name", "")
            classname = tc.get("classname", "")
            file_attr = tc.get("file", "")
            if tc.find("failure") is not None or tc.find("error") is not None:
                status = "failed"
            elif tc.find("skipped") is not None:
                status = "skipped"
            else:
                status = "passed"
            if name:
                cases.append(
                    {
                        "id": name,
                        "classname": classname,
                        "file": file_attr,
                        "status": status,
                    }
                )
    passed = max(0, total - failed - errors - skipped)
    counts = {
        "total": total,
        "passed": passed,
        "failed": failed,
        "errors": errors,
        "skipped": skipped,
    }
    return counts, cases


class LanguageNeutralTestRunner(Runner):
    """Execute the appropriate verified ecosystem test adapter for the project."""

    def __init__(self, timeout_seconds: int = 900) -> None:
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        self._timeout = timeout_seconds

    @property
    def name(self) -> str:
        return "test-suite"

    def run(self, project_root: Path) -> RunnerResult:
        root = project_root.resolve()
        if not root.is_dir():
            return RunnerResult(self.name, RunnerOutcome.BLOCKED, "project root is not a directory")

        language, language_reason = resolve_project_language(root)
        if language == "python":
            return self._run_python(root, language_reason)
        if language == "go":
            return self._run_go(root, language_reason)
        if language == "rust":
            return self._run_rust(root, language_reason)
        if language in {"javascript", "typescript"}:
            return self._run_js_ts(root, language, language_reason)
        if language == "unknown":
            return self._finalize(
                root,
                language=language,
                language_reason=language_reason,
                adapter="none",
                classification="zero_tests",
                counts={"total": 0, "passed": 0, "failed": 0, "errors": 0, "skipped": 0},
                cases=[],
                reason="no supported project language or test suite markers detected",
                extra_artifacts=[],
            )
        return self._finalize(
            root,
            language=language,
            language_reason=language_reason,
            adapter="none",
            classification="unsupported",
            counts={"total": 0, "passed": 0, "failed": 0, "errors": 0, "skipped": 0},
            cases=[],
            reason=(
                f"no verified deterministic test-runner adapter is implemented "
                f"for language '{language}'"
            ),
            extra_artifacts=[],
        )

    def _run_python(self, root: Path, language_reason: str) -> RunnerResult:
        pytest_runner = PytestRunner(timeout_seconds=self._timeout)
        sub_result = pytest_runner.run(root)
        junit_files = [Path(p) for p in sub_result.artifacts if str(p).endswith(".xml")]
        if sub_result.outcome == RunnerOutcome.BLOCKED or len(junit_files) != 1:
            reason = sub_result.reason or "Pytest runner could not execute project tests"
            classification = (
                "zero_tests"
                if "no tests" in reason or "collected no tests" in reason
                else "unavailable"
            )
            return self._finalize(
                root,
                language="python",
                language_reason=language_reason,
                adapter="pytest",
                classification=classification,
                counts={"total": 0, "passed": 0, "failed": 0, "errors": 0, "skipped": 0},
                cases=[],
                reason=reason,
                extra_artifacts=[],
            )
        parsed = _parse_junit_cases(junit_files[0])
        if parsed is None:
            return self._finalize(
                root,
                language="python",
                language_reason=language_reason,
                adapter="pytest",
                classification="unavailable",
                counts={"total": 0, "passed": 0, "failed": 0, "errors": 0, "skipped": 0},
                cases=[],
                reason="JUnit XML artifact is unreadable or malformed",
                extra_artifacts=[],
            )
        counts, cases = parsed
        if counts["total"] <= 0:
            classification = "zero_tests"
        elif (
            counts["failed"] > 0
            or counts["errors"] > 0
            or sub_result.outcome == RunnerOutcome.FAIL
        ):
            classification = "failed"
        elif counts["skipped"] > 0:
            classification = "skipped"
        else:
            classification = "passed"
        return self._finalize(
            root,
            language="python",
            language_reason=language_reason,
            adapter="pytest",
            classification=classification,
            counts=counts,
            cases=cases,
            reason=sub_result.reason,
            extra_artifacts=[junit_files[0]],
        )

    def _run_go(self, root: Path, language_reason: str) -> RunnerResult:
        if not (root / "go.mod").is_file():
            return self._finalize(
                root,
                language="go",
                language_reason=language_reason,
                adapter="go-test",
                classification="zero_tests",
                counts={"total": 0, "passed": 0, "failed": 0, "errors": 0, "skipped": 0},
                cases=[],
                reason="Go project is missing go.mod",
                extra_artifacts=[],
            )
        if not list(root.rglob("*_test.go")):
            return self._finalize(
                root,
                language="go",
                language_reason=language_reason,
                adapter="go-test",
                classification="zero_tests",
                counts={"total": 0, "passed": 0, "failed": 0, "errors": 0, "skipped": 0},
                cases=[],
                reason="Go project contains no *_test.go files",
                extra_artifacts=[],
            )
        go_bin = shutil.which("go")
        if go_bin is None:
            return self._finalize(
                root,
                language="go",
                language_reason=language_reason,
                adapter="go-test",
                classification="unavailable",
                counts={"total": 0, "passed": 0, "failed": 0, "errors": 0, "skipped": 0},
                cases=[],
                reason="go toolchain executable not found on PATH",
                extra_artifacts=[],
            )
        try:
            proc = subprocess.run(  # noqa: S603 - resolved go binary and fixed arguments
                [go_bin, "test", "-json", "./..."],
                cwd=root,
                capture_output=True,
                text=True,
                timeout=self._timeout,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            return self._finalize(
                root,
                language="go",
                language_reason=language_reason,
                adapter="go-test",
                classification="unavailable",
                counts={"total": 0, "passed": 0, "failed": 0, "errors": 0, "skipped": 0},
                cases=[],
                reason=f"go test failed to execute: {exc}",
                extra_artifacts=[],
            )

        cases: list[dict[str, str]] = []
        passed = failed = skipped = 0
        for line in (proc.stdout or "").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            if not isinstance(event, dict) or "Test" not in event:
                continue
            test_name = str(event["Test"])
            pkg = str(event.get("Package", ""))
            action = str(event.get("Action", ""))
            if action == "pass":
                passed += 1
                cases.append({"id": test_name, "classname": pkg, "file": "", "status": "passed"})
            elif action == "fail":
                failed += 1
                cases.append({"id": test_name, "classname": pkg, "file": "", "status": "failed"})
            elif action == "skip":
                skipped += 1
                cases.append({"id": test_name, "classname": pkg, "file": "", "status": "skipped"})

        total = passed + failed + skipped
        errors = 1 if proc.returncode != 0 and failed == 0 else 0
        counts = {
            "total": total,
            "passed": passed,
            "failed": failed,
            "errors": errors,
            "skipped": skipped,
        }
        raw_dir = root / ".arkhon" / "evidence" / "testing"
        raw_dir.mkdir(parents=True, exist_ok=True)
        raw_path = raw_dir / "go-test.jsonl"
        raw_path.write_text(proc.stdout or "", encoding="utf-8")
        if total == 0 and proc.returncode == 0:
            classification = "zero_tests"
            reason = "go test collected zero tests"
        elif proc.returncode != 0 or failed > 0 or errors > 0:
            classification = "failed"
            reason = f"go test reported {failed} failure(s) and exit code {proc.returncode}"
        elif skipped > 0:
            classification = "skipped"
            reason = f"go test recorded {skipped} skipped test(s)"
        else:
            classification = "passed"
            reason = ""
        return self._finalize(
            root,
            language="go",
            language_reason=language_reason,
            adapter="go-test",
            classification=classification,
            counts=counts,
            cases=cases,
            reason=reason,
            extra_artifacts=[raw_path],
        )

    def _run_rust(self, root: Path, language_reason: str) -> RunnerResult:
        if not (root / "Cargo.toml").is_file():
            return self._finalize(
                root,
                language="rust",
                language_reason=language_reason,
                adapter="cargo-test",
                classification="zero_tests",
                counts={"total": 0, "passed": 0, "failed": 0, "errors": 0, "skipped": 0},
                cases=[],
                reason="Rust project is missing Cargo.toml",
                extra_artifacts=[],
            )
        cargo_bin = shutil.which("cargo")
        if cargo_bin is None:
            return self._finalize(
                root,
                language="rust",
                language_reason=language_reason,
                adapter="cargo-test",
                classification="unavailable",
                counts={"total": 0, "passed": 0, "failed": 0, "errors": 0, "skipped": 0},
                cases=[],
                reason="cargo toolchain executable not found on PATH",
                extra_artifacts=[],
            )
        try:
            proc = subprocess.run(  # noqa: S603 - resolved cargo binary and fixed arguments
                [cargo_bin, "test", "--no-fail-fast", "--", "--color=never"],
                cwd=root,
                capture_output=True,
                text=True,
                timeout=self._timeout,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            return self._finalize(
                root,
                language="rust",
                language_reason=language_reason,
                adapter="cargo-test",
                classification="unavailable",
                counts={"total": 0, "passed": 0, "failed": 0, "errors": 0, "skipped": 0},
                cases=[],
                reason=f"cargo test failed to execute: {exc}",
                extra_artifacts=[],
            )

        cases: list[dict[str, str]] = []
        passed = failed = skipped = 0
        combined = (proc.stdout or "") + "\n" + (proc.stderr or "")
        for line in combined.splitlines():
            match = _CARGO_CASE_RE.match(line.strip())
            if not match:
                continue
            test_name, verdict = match.group(1), match.group(2)
            if verdict == "ok":
                passed += 1
                cases.append({"id": test_name, "classname": "", "file": "", "status": "passed"})
            elif verdict == "FAILED":
                failed += 1
                cases.append({"id": test_name, "classname": "", "file": "", "status": "failed"})
            else:
                skipped += 1
                cases.append({"id": test_name, "classname": "", "file": "", "status": "skipped"})

        total = passed + failed + skipped
        errors = 1 if proc.returncode != 0 and failed == 0 else 0
        counts = {
            "total": total,
            "passed": passed,
            "failed": failed,
            "errors": errors,
            "skipped": skipped,
        }
        raw_dir = root / ".arkhon" / "evidence" / "testing"
        raw_dir.mkdir(parents=True, exist_ok=True)
        raw_path = raw_dir / "cargo-test.txt"
        raw_path.write_text(combined, encoding="utf-8")
        if total == 0 and proc.returncode == 0:
            classification = "zero_tests"
            reason = "cargo test collected zero tests"
        elif proc.returncode != 0 or failed > 0 or errors > 0:
            classification = "failed"
            reason = f"cargo test reported {failed} failure(s) and exit code {proc.returncode}"
        elif skipped > 0:
            classification = "skipped"
            reason = f"cargo test recorded {skipped} ignored test(s)"
        else:
            classification = "passed"
            reason = ""
        return self._finalize(
            root,
            language="rust",
            language_reason=language_reason,
            adapter="cargo-test",
            classification=classification,
            counts=counts,
            cases=cases,
            reason=reason,
            extra_artifacts=[raw_path],
        )

    def _run_js_ts(self, root: Path, language: str, language_reason: str) -> RunnerResult:
        pkg_path = root / "package.json"
        if not pkg_path.is_file():
            return self._finalize(
                root,
                language=language,
                language_reason=language_reason,
                adapter="none",
                classification="zero_tests",
                counts={"total": 0, "passed": 0, "failed": 0, "errors": 0, "skipped": 0},
                cases=[],
                reason=f"{language} project is missing package.json",
                extra_artifacts=[],
            )
        try:
            pkg = json.loads(pkg_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            return self._finalize(
                root,
                language=language,
                language_reason=language_reason,
                adapter="none",
                classification="unavailable",
                counts={"total": 0, "passed": 0, "failed": 0, "errors": 0, "skipped": 0},
                cases=[],
                reason=f"invalid package.json: {exc}",
                extra_artifacts=[],
            )
        scripts = pkg.get("scripts") if isinstance(pkg, dict) else None
        test_script = scripts.get("test", "") if isinstance(scripts, dict) else ""
        if not isinstance(test_script, str) or not test_script.strip() or (
            "no test specified" in test_script.lower()
        ):
            return self._finalize(
                root,
                language=language,
                language_reason=language_reason,
                adapter="none",
                classification="zero_tests",
                counts={"total": 0, "passed": 0, "failed": 0, "errors": 0, "skipped": 0},
                cases=[],
                reason="package.json defines no executable test script",
                extra_artifacts=[],
            )

        if "node --test" in test_script:
            node_bin = shutil.which("node")
            if node_bin is None:
                return self._finalize(
                    root,
                    language=language,
                    language_reason=language_reason,
                    adapter="node-test",
                    classification="unavailable",
                    counts={"total": 0, "passed": 0, "failed": 0, "errors": 0, "skipped": 0},
                    cases=[],
                    reason="node runtime not found on PATH",
                    extra_artifacts=[],
                )
            try:
                proc = subprocess.run(  # noqa: S603 - resolved node binary and fixed TAP reporter
                    [node_bin, "--test", "--test-reporter=tap"],
                    cwd=root,
                    capture_output=True,
                    text=True,
                    timeout=self._timeout,
                    check=False,
                )
            except (OSError, subprocess.TimeoutExpired) as exc:
                return self._finalize(
                    root,
                    language=language,
                    language_reason=language_reason,
                    adapter="node-test",
                    classification="unavailable",
                    counts={"total": 0, "passed": 0, "failed": 0, "errors": 0, "skipped": 0},
                    cases=[],
                    reason=f"node --test failed to execute: {exc}",
                    extra_artifacts=[],
                )
            cases: list[dict[str, str]] = []
            passed = failed = skipped = 0
            for line in (proc.stdout or "").splitlines():
                m = _NODE_CASE_RE.match(line)
                if not m:
                    continue
                verdict, name, directive = m.group(1), m.group(2).strip(), m.group(3)
                if directive in {"SKIP", "TODO"}:
                    skipped += 1
                    cases.append({"id": name, "classname": "", "file": "", "status": "skipped"})
                elif verdict == "ok":
                    passed += 1
                    cases.append({"id": name, "classname": "", "file": "", "status": "passed"})
                else:
                    failed += 1
                    cases.append({"id": name, "classname": "", "file": "", "status": "failed"})
            total = passed + failed + skipped
            errors = 1 if proc.returncode != 0 and failed == 0 else 0
            counts = {
                "total": total,
                "passed": passed,
                "failed": failed,
                "errors": errors,
                "skipped": skipped,
            }
            raw_dir = root / ".arkhon" / "evidence" / "testing"
            raw_dir.mkdir(parents=True, exist_ok=True)
            raw_path = raw_dir / "node-test.tap"
            raw_path.write_text(proc.stdout or "", encoding="utf-8")
            if total == 0:
                classification = "zero_tests"
                reason = "node --test executed zero test cases"
            elif proc.returncode != 0 or failed > 0 or errors > 0:
                classification = "failed"
                reason = f"node --test reported {failed} failure(s)"
            elif skipped > 0:
                classification = "skipped"
                reason = f"node --test recorded {skipped} skipped test(s)"
            else:
                classification = "passed"
                reason = ""
            return self._finalize(
                root,
                language=language,
                language_reason=language_reason,
                adapter="node-test",
                classification=classification,
                counts=counts,
                cases=cases,
                reason=reason,
                extra_artifacts=[raw_path],
            )

        return self._finalize(
            root,
            language=language,
            language_reason=language_reason,
            adapter="none",
            classification="unavailable",
            counts={"total": 0, "passed": 0, "failed": 0, "errors": 0, "skipped": 0},
            cases=[],
            reason=(
                f"no verified local test runner available for {language} script "
                f"{test_script!r}"
            ),
            extra_artifacts=[],
        )

    def _finalize(
        self,
        root: Path,
        *,
        language: str,
        language_reason: str,
        adapter: str,
        classification: str,
        counts: dict[str, int],
        cases: list[dict[str, str]],
        reason: str,
        extra_artifacts: list[Path],
    ) -> RunnerResult:
        payload: dict[str, Any] = {
            "schema_version": 1,
            "language": language,
            "language_reason": language_reason,
            "adapter": adapter,
            "classification": classification,
            "counts": counts,
            "executed_tests": cases,
            "reason": reason,
        }
        report_path = _persist_normalized_report(root, payload)
        if report_path is None:
            return RunnerResult(
                self.name,
                RunnerOutcome.BLOCKED,
                "cannot persist normalized test execution report",
            )
        artifacts = [report_path, *extra_artifacts]
        if classification in {"zero_tests", "unavailable", "unsupported"}:
            return RunnerResult(self.name, RunnerOutcome.BLOCKED, reason, artifacts)
        if classification == "failed":
            return RunnerResult(self.name, RunnerOutcome.FAIL, reason, artifacts)
        return RunnerResult(self.name, RunnerOutcome.PASS, reason, artifacts)
