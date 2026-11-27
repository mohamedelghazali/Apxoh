"""Scenario-level negative-security and observability/crash-dump evidence verifiers."""

from __future__ import annotations

import ast
import json
import re
from pathlib import Path
from typing import Any

import yaml

from gencode_gov.core.constants import STATUS_BLOCKED, STATUS_FAIL, STATUS_PASS
from gencode_gov.core.errors import ConfigError
from gencode_gov.projects.matcher import match_profile

REQUIRED_SECURITY_SCENARIOS: tuple[str, ...] = (
    "unauthenticated-access",
    "privilege-escalation",
    "idor-resource-access",
    "tenant-user-isolation",
    "injection-controls",
    "csrf-state-change",
    "auth-rate-limit-abuse",
    "token-lifecycle-abuse",
)

REQUIRED_OBSERVABILITY_CHECKS: tuple[str, ...] = (
    "structured-diagnostic-logging",
    "sanitized-client-error-responses",
    "application-log-and-trace-redaction",
)

_AUTHZ_MOCK_PATTERNS = re.compile(
    r"(monkeypatch\.setattr|mock\.patch|patch\.object|@patch|dependency_overrides)"
    r"[^\n]{0,120}"
    r"(authorize|check_permission|has_permission|require_auth|verify_token|"
    r"is_authenticated|require_role|enforce_tenant|csrf_protect|verify_csrf)",
    re.IGNORECASE,
)
_NON_PY_ASSERT_RE = re.compile(
    r"\b(t\.Fatal|t\.Fatalf|t\.Error|t\.Errorf|require\.|assert\.|assert_eq!|assert!|expect\()"
)
_COOKIE_SURFACE_RE = re.compile(
    r"\b(set_cookie|session_cookie|SameSite|csrftoken|csrf_token|CookieAuthentication)\b",
    re.IGNORECASE,
)
_AUTH_API_SURFACE_RE = re.compile(
    r"(@app\.(get|post|put|delete|route)|@router\.(get|post|put|delete)|"
    r"FastAPI\(|Flask\(|express\(|http\.HandleFunc)",
)
_DOC_EXTENSIONS: frozenset[str] = frozenset({".md", ".rst", ".txt", ".adoc"})


def _safe_in_repo_file(project_root: Path, rel_path: object) -> Path | None:
    if not isinstance(rel_path, str) or not rel_path.strip():
        return None
    candidate = Path(rel_path)
    if candidate.is_absolute() or ".." in candidate.parts:
        return None
    raw = project_root / candidate
    if raw.is_symlink():
        return None
    try:
        resolved = raw.resolve()
        resolved.relative_to(project_root.resolve())
    except (OSError, ValueError):
        return None
    return resolved if resolved.is_file() else None


def _detect_attack_surface(project_root: Path) -> set[str]:
    """Infer mandatory security scenarios from declared profile and source code markers."""
    root = project_root.resolve()
    try:
        profile = match_profile(root).profile
    except (ConfigError, OSError, ValueError):
        profile = "universal"

    required: set[str] = set()
    if profile in {"web-application", "api-service", "mobile-application", "enterprise"}:
        required.update(
            {
                "unauthenticated-access",
                "privilege-escalation",
                "idor-resource-access",
                "tenant-user-isolation",
                "injection-controls",
                "auth-rate-limit-abuse",
                "token-lifecycle-abuse",
            }
        )
    if profile == "web-application":
        required.add("csrf-state-change")

    self_file = Path(__file__).resolve()
    ignored = {".git", ".gencode-gov", "tests", "test", "docs", "node_modules", ".venv", "venv"}
    for path in root.rglob("*"):
        if not path.is_file() or path.is_symlink() or path.resolve() == self_file:
            continue
        rel = path.relative_to(root)
        if any(part in ignored for part in rel.parts) or path.suffix.lower() in _DOC_EXTENSIONS:
            continue
        if path.suffix.lower() not in {".py", ".js", ".ts", ".go", ".rs", ".java", ".cs", ".rb"}:
            continue
        try:
            if path.stat().st_size > 512 * 1024:
                continue
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if _COOKIE_SURFACE_RE.search(text):
            required.add("csrf-state-change")
        if _AUTH_API_SURFACE_RE.search(text):
            required.update(
                {
                    "unauthenticated-access",
                    "privilege-escalation",
                    "idor-resource-access",
                    "injection-controls",
                }
            )
    return required


def _verify_python_test_quality(source: str, test_id: str) -> tuple[bool, str]:
    """Verify the Python test exists, asserts meaningful behavior, and does not mock authz."""
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        return False, f"syntax error in test file: {exc}"

    short_name = test_id.split("::")[-1].split("[")[0]
    target_node: ast.FunctionDef | ast.AsyncFunctionDef | None = None
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == short_name:
            target_node = node
            break
    if target_node is None:
        return False, f"test function {short_name!r} not found in AST"

    segment = ast.get_source_segment(source, target_node) or ""
    if _AUTHZ_MOCK_PATTERNS.search(segment):
        return (
            False,
            f"test {short_name!r} mocks or overrides an authentication/authorization boundary",
        )

    meaningful_assertions = 0
    for sub in ast.walk(target_node):
        if isinstance(sub, ast.Assert):
            if isinstance(sub.test, ast.Constant) and bool(sub.test.value) is True:
                continue
            if (
                isinstance(sub.test, ast.Call)
                and isinstance(sub.test.func, ast.Name)
                and sub.test.func.id == "isinstance"
            ):
                continue
            meaningful_assertions += 1
        elif isinstance(sub, ast.Call):
            func_repr = ast.unparse(sub.func) if hasattr(ast, "unparse") else ""
            if any(
                token in func_repr
                for token in ("pytest.raises", "assertRaises", "assert_status", "assertEqual")
            ):
                meaningful_assertions += 1

    if meaningful_assertions == 0:
        return False, f"test {short_name!r} contains no non-trivial behavioral assertions"
    return True, "verified"


def _verify_test_source_and_execution(
    project_root: Path,
    test_file: object,
    test_id: object,
    executed_lookup: dict[str, dict[str, str]],
) -> tuple[bool, str]:
    resolved_file = _safe_in_repo_file(project_root, test_file)
    if resolved_file is None:
        return False, f"referenced test_file {test_file!r} does not exist inside project"
    if resolved_file.suffix.lower() in _DOC_EXTENSIONS:
        return False, f"documentation file {test_file!r} cannot count as automated test evidence"
    if not isinstance(test_id, str) or not test_id.strip():
        return False, "test_id must be a non-empty string"

    try:
        source = resolved_file.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        return False, f"cannot read {test_file!r}: {exc}"

    clean_id = test_id.strip()
    short_name = clean_id.split("::")[-1].split("[")[0]
    if resolved_file.suffix.lower() == ".py":
        ok, detail = _verify_python_test_quality(source, clean_id)
        if not ok:
            return False, detail
    else:
        if short_name not in source:
            return False, f"test identifier {clean_id!r} not found in {test_file!r}"
        if _AUTHZ_MOCK_PATTERNS.search(source):
            return False, f"authorization bypass/mock pattern detected in {test_file!r}"
        if not _NON_PY_ASSERT_RE.search(source):
            return False, f"no behavioral test assertions detected in {test_file!r}"

    matched_case = executed_lookup.get(clean_id) or executed_lookup.get(short_name)
    if matched_case is None:
        return False, f"test {clean_id!r} was not executed in the current test run"
    if matched_case.get("status") != "passed":
        return (
            False,
            f"test {clean_id!r} finished with status {matched_case.get('status')!r}, not 'passed'",
        )
    return True, "executed and passed"


def _load_execution_report(project_root: Path) -> tuple[dict[str, Any] | None, str]:
    report_path = (
        project_root.resolve()
        / ".gencode-gov"
        / "evidence"
        / "testing"
        / "test-execution-report.json"
    )
    if not report_path.is_file() or report_path.is_symlink():
        return None, "missing normalized test-execution-report.json from test-suite runner"
    try:
        data = json.loads(report_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        return None, f"unreadable test-execution-report.json: {exc}"
    if not isinstance(data, dict):
        return None, "malformed test-execution-report.json"
    return data, ""


def _build_executed_lookup(report: dict[str, Any]) -> dict[str, dict[str, str]]:
    lookup: dict[str, dict[str, str]] = {}
    raw_cases = report.get("executed_tests", [])
    if not isinstance(raw_cases, list):
        return lookup
    for entry in raw_cases:
        if not isinstance(entry, dict):
            continue
        cid = entry.get("id")
        if isinstance(cid, str) and cid:
            lookup[cid] = entry
            short = cid.split("::")[-1].split("/")[-1].split("[")[0]
            lookup.setdefault(short, entry)
    return lookup


def verify_negative_security_scenarios(project_root: Path) -> tuple[str, str]:
    """Verify scenario-level negative-security test coverage and execution provenance."""
    root = project_root.resolve()
    report, err = _load_execution_report(root)
    if report is None:
        return STATUS_BLOCKED, err
    if report.get("classification") in {"unavailable", "unsupported", "zero_tests"}:
        return (
            STATUS_BLOCKED,
            str(report.get("reason") or "test runner could not execute project suite"),
        )

    matrix_path = _safe_in_repo_file(root, ".gencode-gov/security-test-matrix.yaml")
    if matrix_path is None:
        return (
            STATUS_BLOCKED,
            "missing .gencode-gov/security-test-matrix.yaml; generic test counts do not prove "
            "negative-security scenario coverage",
        )
    try:
        matrix = yaml.safe_load(matrix_path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        return STATUS_FAIL, f"invalid .gencode-gov/security-test-matrix.yaml: {exc}"
    if not isinstance(matrix, dict) or not isinstance(matrix.get("scenarios"), dict):
        return (
            STATUS_FAIL,
            ".gencode-gov/security-test-matrix.yaml must define a 'scenarios' mapping",
        )

    scenarios_map: dict[str, Any] = matrix["scenarios"]
    missing = [sid for sid in REQUIRED_SECURITY_SCENARIOS if sid not in scenarios_map]
    if missing:
        return STATUS_FAIL, f"missing required security scenario declaration(s): {missing}"

    inferred_required = _detect_attack_surface(root)
    executed_lookup = _build_executed_lookup(report)
    verified_records: list[dict[str, Any]] = []
    failures: list[str] = []

    for scenario_id in REQUIRED_SECURITY_SCENARIOS:
        spec = scenarios_map.get(scenario_id)
        if not isinstance(spec, dict):
            failures.append(f"{scenario_id}: declaration must be a mapping")
            continue
        applicable = spec.get("applicable")
        if not isinstance(applicable, bool):
            failures.append(f"{scenario_id}: 'applicable' must be a boolean")
            continue
        if not applicable:
            justification = spec.get("justification")
            if scenario_id in inferred_required:
                failures.append(
                    f"{scenario_id}: marked non-applicable despite detected project attack surface"
                )
                continue
            if not isinstance(justification, str) or len(justification.strip()) < 20:
                failures.append(
                    f"{scenario_id}: non-applicable scenario requires a substantive justification"
                )
                continue
            verified_records.append(
                {
                    "scenario": scenario_id,
                    "applicable": False,
                    "status": "NOT_APPLICABLE",
                    "justification": justification.strip(),
                }
            )
            continue

        tests_list = spec.get("tests")
        if not isinstance(tests_list, list) or not tests_list:
            failures.append(f"{scenario_id}: applicable scenario maps to zero automated tests")
            continue
        scenario_tests: list[dict[str, str]] = []
        for entry in tests_list:
            if not isinstance(entry, dict):
                failures.append(f"{scenario_id}: test entry must be a mapping")
                continue
            ok, detail = _verify_test_source_and_execution(
                root, entry.get("test_file"), entry.get("test_id"), executed_lookup
            )
            if not ok:
                failures.append(f"{scenario_id}: {detail}")
            else:
                scenario_tests.append(
                    {
                        "test_file": str(entry["test_file"]),
                        "test_id": str(entry["test_id"]),
                        "runner": str(report.get("adapter", "")),
                        "result": "passed",
                    }
                )
        verified_records.append(
            {
                "scenario": scenario_id,
                "applicable": True,
                "status": "PASS" if scenario_tests and not failures else "FAIL",
                "tests": scenario_tests,
            }
        )

    out_dir = root / ".gencode-gov" / "evidence" / "testing"
    out_dir.mkdir(parents=True, exist_ok=True)
    trace_path = out_dir / "security-scenario-traceability.json"
    if not trace_path.is_symlink():
        trace_path.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "runner_adapter": report.get("adapter"),
                    "language": report.get("language"),
                    "scenarios": verified_records,
                    "failures": failures,
                },
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )

    if failures:
        return STATUS_FAIL, "; ".join(failures[:3])
    return (
        STATUS_PASS,
        f"verified {len(verified_records)} security scenario declarations with executed evidence",
    )


def verify_observability_and_crash_dump_controls(project_root: Path) -> tuple[str, str]:
    """Verify SE-OBS-003 structured logging, sanitized errors, redaction, and crash-dump policy."""
    root = project_root.resolve()
    report, err = _load_execution_report(root)
    if report is None:
        return STATUS_BLOCKED, err
    if report.get("classification") in {"unavailable", "unsupported", "zero_tests"}:
        return (
            STATUS_BLOCKED,
            str(report.get("reason") or "test runner could not execute observability tests"),
        )

    obs_path = _safe_in_repo_file(root, ".gencode-gov/observability-verification.yaml")
    if obs_path is None:
        return (
            STATUS_BLOCKED,
            "missing .gencode-gov/observability-verification.yaml; observability and crash-dump "
            "controls are not established by lint or generic test counts",
        )
    try:
        obs_doc = yaml.safe_load(obs_path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        return STATUS_FAIL, f"invalid .gencode-gov/observability-verification.yaml: {exc}"
    if not isinstance(obs_doc, dict):
        return STATUS_FAIL, ".gencode-gov/observability-verification.yaml must be a mapping"

    checks = obs_doc.get("behavioral_checks")
    if not isinstance(checks, dict):
        return STATUS_FAIL, "missing 'behavioral_checks' mapping in observability verification"

    executed_lookup = _build_executed_lookup(report)
    failures: list[str] = []
    for check_id in REQUIRED_OBSERVABILITY_CHECKS:
        entry = checks.get(check_id)
        if not isinstance(entry, dict):
            failures.append(f"missing observability test mapping for {check_id!r}")
            continue
        ok, detail = _verify_test_source_and_execution(
            root, entry.get("test_file"), entry.get("test_id"), executed_lookup
        )
        if not ok:
            failures.append(f"{check_id}: {detail}")

    crash = obs_doc.get("crash_dump_policy")
    if not isinstance(crash, dict):
        failures.append("missing 'crash_dump_policy' section separating crash dumps from logs")
    else:
        enabled = crash.get("enabled_by_default")
        if not isinstance(enabled, bool):
            failures.append("crash_dump_policy.enabled_by_default must be a boolean")
        elif enabled is True:
            justification = crash.get("operational_justification")
            retention = crash.get("max_retention_days")
            required_bools = (
                ("least_privilege_access", True),
                ("encrypted_at_rest_and_in_transit", True),
                ("restricted_storage_and_transfer", True),
                ("secure_deletion_configured", True),
                ("access_audit_monitored", True),
                ("unrestricted_developer_or_agent_exposure", False),
            )
            if not isinstance(justification, str) or len(justification.strip()) < 20:
                failures.append(
                    "enabled crash dumps require a substantive operational_justification"
                )
            if isinstance(retention, bool) or not isinstance(retention, int) or retention <= 0:
                failures.append("enabled crash dumps require a positive integer max_retention_days")
            for field_name, expected_val in required_bools:
                if crash.get(field_name) is not expected_val:
                    failures.append(
                        f"crash_dump_policy.{field_name} must be {expected_val} when enabled"
                    )
        else:
            if crash.get("unrestricted_developer_or_agent_exposure") is not False:
                failures.append(
                    "crash_dump_policy.unrestricted_developer_or_agent_exposure must be False"
                )

    if failures:
        return STATUS_FAIL, "; ".join(failures[:3])
    return (
        STATUS_PASS,
        "verified structured logging, sanitized errors, redaction tests, and crash-dump policy",
    )
