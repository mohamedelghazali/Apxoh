"""Tests for cross-language runner, scenario traceability, crash dumps, and PytestRunner XXE."""

from __future__ import annotations

import json
import socket
import subprocess
from pathlib import Path
from typing import Any

import yaml

from arkhon.verification.assess_dispatch import evaluate_extended_method, inspect_junit_artifact
from arkhon.verification.runners.base import RunnerOutcome, RunnerResult
from arkhon.verification.runners.pytest_runner import PytestRunner
from arkhon.verification.runners.test_suite_runner import (
    LanguageNeutralTestRunner,
    resolve_project_language,
)
from arkhon.verification.scenario_verifier import (
    REQUIRED_SECURITY_SCENARIOS,
    verify_negative_security_scenarios,
    verify_observability_and_crash_dump_controls,
)


def test_cross_language_selection_never_invokes_pytest_for_non_python_projects(
    tmp_path: Path,
) -> None:
    go_proj = tmp_path / "go_svc"
    go_proj.mkdir()
    (go_proj / "go.mod").write_text("module example.com/svc\ngo 1.22\n", encoding="utf-8")
    (go_proj / "main.go").write_text("package main\nfunc main() {}\n", encoding="utf-8")
    assert resolve_project_language(go_proj)[0] == "go"
    go_res = LanguageNeutralTestRunner().run(go_proj)
    assert go_res.outcome == RunnerOutcome.BLOCKED
    go_rep_path = go_proj / ".arkhon/evidence/testing/test-execution-report.json"
    report = json.loads(go_rep_path.read_text(encoding="utf-8"))
    assert report["language"] == "go"
    assert report["adapter"] == "go-test"
    assert report["classification"] == "zero_tests"

    ts_proj = tmp_path / "ts_web"
    ts_proj.mkdir()
    (ts_proj / "tsconfig.json").write_text("{}\n", encoding="utf-8")
    (ts_proj / "package.json").write_text(
        json.dumps(
            {"name": "web", "scripts": {"test": 'echo "Error: no test specified" && exit 1'}}
        ),
        encoding="utf-8",
    )
    assert resolve_project_language(ts_proj)[0] == "typescript"
    ts_res = LanguageNeutralTestRunner().run(ts_proj)
    assert ts_res.outcome == RunnerOutcome.BLOCKED
    ts_rep_path = ts_proj / ".arkhon/evidence/testing/test-execution-report.json"
    ts_report = json.loads(ts_rep_path.read_text(encoding="utf-8"))
    assert ts_report["language"] == "typescript"
    assert ts_report["classification"] == "zero_tests"

    java_proj = tmp_path / "java_app"
    java_proj.mkdir()
    (java_proj / "pom.xml").write_text("<project/>\n", encoding="utf-8")
    java_res = LanguageNeutralTestRunner().run(java_proj)
    assert java_res.outcome == RunnerOutcome.BLOCKED
    java_report = json.loads(
        (java_proj / ".arkhon/evidence/testing/test-execution-report.json").read_text()
    )
    assert java_report["language"] == "java"
    assert java_report["classification"] == "unsupported"


def test_assess_dispatch_distinguishes_passed_failed_skipped_and_zero_tests(
    tmp_path: Path,
) -> None:
    report_path = tmp_path / "test-execution-report.json"

    def write_rep(total: int, failed: int, skipped: int, outcome: RunnerOutcome) -> RunnerResult:
        report_path.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "language": "go",
                    "adapter": "go-test",
                    "classification": "passed",
                    "counts": {
                        "total": total,
                        "passed": max(0, total - failed - skipped),
                        "failed": failed,
                        "errors": 0,
                        "skipped": skipped,
                    },
                    "executed_tests": [],
                }
            ),
            encoding="utf-8",
        )
        return RunnerResult("test-suite", outcome, "", [report_path])

    def _status(method_id: str, res: RunnerResult) -> str:
        verdict = evaluate_extended_method(method_id, res, tmp_path)
        assert verdict is not None
        return verdict[0]

    res_ok = write_rep(6, 0, 0, RunnerOutcome.PASS)
    assert _status("automated-test-suite-execution", res_ok) == "PASS"
    assert _status("zero-test-failures-check", res_ok) == "PASS"
    assert _status("skip-marker-detection", res_ok) == "PASS"

    res_skip = write_rep(6, 0, 2, RunnerOutcome.PASS)
    assert _status("test-collector-analysis", res_skip) == "PASS"
    assert _status("skip-marker-detection", res_skip) == "FAIL"

    res_fail = write_rep(6, 1, 0, RunnerOutcome.FAIL)
    assert _status("automated-test-suite-execution", res_fail) == "PASS"
    assert _status("zero-test-failures-check", res_fail) == "FAIL"

    res_zero = write_rep(0, 0, 0, RunnerOutcome.PASS)
    assert _status("automated-test-suite-execution", res_zero) == "BLOCKED"


def test_negative_security_scenario_traceability_enforces_real_non_mocked_tests(
    tmp_path: Path,
) -> None:
    proj = tmp_path / "web_proj"
    (proj / ".arkhon" / "evidence" / "testing").mkdir(parents=True)
    (proj / ".arkhon" / "project.yaml").write_text(
        "project:\n  profile: web-application\nlanguages:\n  primary: python\n",
        encoding="utf-8",
    )
    (proj / "tests").mkdir()
    test_file = proj / "tests" / "test_security_boundaries.py"
    test_file.write_text(
        "\n".join(
            f"def test_{sid.replace('-', '_')}():\n"
            f"    response_code = 403\n"
            f"    assert response_code in (401, 403, 429)\n"
            for sid in REQUIRED_SECURITY_SCENARIOS
        ),
        encoding="utf-8",
    )
    executed = [
        {
            "id": f"test_{sid.replace('-', '_')}",
            "file": "tests/test_security_boundaries.py",
            "status": "passed",
        }
        for sid in REQUIRED_SECURITY_SCENARIOS
    ]
    (proj / ".arkhon/evidence/testing/test-execution-report.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "language": "python",
                "adapter": "pytest",
                "classification": "passed",
                "counts": {"total": 8, "passed": 8, "failed": 0, "errors": 0, "skipped": 0},
                "executed_tests": executed,
            }
        ),
        encoding="utf-8",
    )

    status, reason = verify_negative_security_scenarios(proj)
    assert status == "BLOCKED" and "security-test-matrix.yaml" in reason

    matrix_data: dict[str, Any] = {
        "scenarios": {
            sid: {
                "applicable": True,
                "tests": [
                    {
                        "test_file": "tests/test_security_boundaries.py",
                        "test_id": f"test_{sid.replace('-', '_')}",
                    }
                ],
            }
            for sid in REQUIRED_SECURITY_SCENARIOS
        }
    }
    matrix_path = proj / ".arkhon" / "security-test-matrix.yaml"
    matrix_path.write_text(yaml.safe_dump(matrix_data), encoding="utf-8")
    status_ok, _ = verify_negative_security_scenarios(proj)
    assert status_ok == "PASS"
    assert (proj / ".arkhon/evidence/testing/security-scenario-traceability.json").is_file()

    bad_na = json.loads(json.dumps(matrix_data))
    bad_na["scenarios"]["csrf-state-change"] = {
        "applicable": False,
        "justification": "We decided to skip CSRF testing on our web app.",
    }
    matrix_path.write_text(yaml.safe_dump(bad_na), encoding="utf-8")
    status_na, reason_na = verify_negative_security_scenarios(proj)
    assert status_na == "FAIL" and "csrf-state-change" in reason_na

    test_file.write_text(
        test_file.read_text(encoding="utf-8")
        + "\ndef test_mocked_idor(monkeypatch):\n"
        + "    monkeypatch.setattr('app.auth.check_permission', lambda *a: True)\n"
        + "    assert 1 == 1\n",
        encoding="utf-8",
    )
    executed.append(
        {
            "id": "test_mocked_idor",
            "file": "tests/test_security_boundaries.py",
            "status": "passed",
        }
    )
    (proj / ".arkhon/evidence/testing/test-execution-report.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "language": "python",
                "adapter": "pytest",
                "classification": "passed",
                "counts": {"total": 9, "passed": 9, "failed": 0, "errors": 0, "skipped": 0},
                "executed_tests": executed,
            }
        ),
        encoding="utf-8",
    )
    mocked_matrix = json.loads(json.dumps(matrix_data))
    mocked_matrix["scenarios"]["idor-resource-access"]["tests"] = [
        {"test_file": "tests/test_security_boundaries.py", "test_id": "test_mocked_idor"}
    ]
    matrix_path.write_text(yaml.safe_dump(mocked_matrix), encoding="utf-8")
    status_mock, reason_mock = verify_negative_security_scenarios(proj)
    assert status_mock == "FAIL" and "mocks or overrides" in reason_mock


def test_observability_and_crash_dump_policy_verification(tmp_path: Path) -> None:
    proj = tmp_path / "obs_proj"
    (proj / ".arkhon/evidence/testing").mkdir(parents=True)
    (proj / "tests").mkdir()
    obs_test = proj / "tests" / "test_obs.py"
    obs_test.write_text(
        "def test_structured_logs():\n    assert 'correlation_id' in {'correlation_id': '1'}\n"
        "def test_sanitized_errors():\n    assert 'Traceback' not in 'Internal error'\n"
        "def test_log_redaction():\n    assert 'secret' not in '[REDACTED]'\n",
        encoding="utf-8",
    )
    (proj / ".arkhon/evidence/testing/test-execution-report.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "language": "python",
                "adapter": "pytest",
                "classification": "passed",
                "counts": {"total": 3, "passed": 3, "failed": 0, "errors": 0, "skipped": 0},
                "executed_tests": [
                    {"id": "test_structured_logs", "status": "passed"},
                    {"id": "test_sanitized_errors", "status": "passed"},
                    {"id": "test_log_redaction", "status": "passed"},
                ],
            }
        ),
        encoding="utf-8",
    )
    obs_yaml = proj / ".arkhon" / "observability-verification.yaml"
    obs_doc: dict[str, Any] = {
        "behavioral_checks": {
            "structured-diagnostic-logging": {
                "test_file": "tests/test_obs.py",
                "test_id": "test_structured_logs",
            },
            "sanitized-client-error-responses": {
                "test_file": "tests/test_obs.py",
                "test_id": "test_sanitized_errors",
            },
            "application-log-and-trace-redaction": {
                "test_file": "tests/test_obs.py",
                "test_id": "test_log_redaction",
            },
        },
        "crash_dump_policy": {
            "enabled_by_default": False,
            "unrestricted_developer_or_agent_exposure": False,
        },
    }
    obs_yaml.write_text(yaml.safe_dump(obs_doc), encoding="utf-8")
    assert verify_observability_and_crash_dump_controls(proj)[0] == "PASS"

    obs_doc["crash_dump_policy"] = {
        "enabled_by_default": True,
        "unrestricted_developer_or_agent_exposure": False,
    }
    obs_yaml.write_text(yaml.safe_dump(obs_doc), encoding="utf-8")
    st_bad, reason_bad = verify_observability_and_crash_dump_controls(proj)
    assert st_bad == "FAIL" and "operational_justification" in reason_bad


def test_pytest_runner_direct_xxe_dtd_network_and_malformed_xml_regression(
    tmp_path: Path,
) -> None:
    proj = tmp_path / "py_xxe_proj"
    (proj / "tests").mkdir(parents=True)
    canary = tmp_path / "canary_secret.txt"
    canary.write_text("TOP_SECRET_CANARY_VALUE_9912", encoding="utf-8")

    file_uri = "file" + f"://{canary}"
    http_uri = "http" + "://127.0.0.1:9/xxe"
    payloads = [
        (
            "external_file_xxe",
            f'<!DOCTYPE foo [<!ENTITY xxe SYSTEM "{file_uri}">]>'
            '<testsuite tests="1"><testcase name="&xxe;"/></testsuite>',
        ),
        (
            "external_http_xxe",
            f'<!DOCTYPE foo [<!ENTITY ext SYSTEM "{http_uri}">]>'
            '<testsuite tests="1"><testcase name="&ext;"/></testsuite>',
        ),
        (
            "billion_laughs_entity",
            '<!DOCTYPE lolz [<!ENTITY lol "lol"><!ENTITY lol2 "&lol;&lol;">]>'
            '<testsuite tests="1"><testcase name="&lol2;"/></testsuite>',
        ),
        (
            "dtd_only",
            '<!DOCTYPE testsuite SYSTEM "evil.dtd"><testsuite tests="1"/>',
        ),
        (
            "malformed_truncated_xml",
            '<testsuite tests="1"><testcase name="broken">',
        ),
        (
            "invalid_numeric_attr",
            '<testsuite tests="not-an-int" failures="0" errors="0" skipped="0"/>',
        ),
    ]

    import arkhon.verification.runners.pytest_runner as pr_mod

    orig_run = pr_mod.subprocess.run
    orig_connect = socket.create_connection

    def forbid_network(*_args: object, **_kwargs: object) -> Any:
        raise AssertionError("unexpected outbound network socket attempted during XML parse")

    try:
        socket.create_connection = forbid_network  # type: ignore[assignment]
        for label, xml_body in payloads:
            xml_probe = tmp_path / f"{label}.xml"
            xml_probe.write_text(xml_body, encoding="utf-8")
            assert inspect_junit_artifact(xml_probe) is None, label

            def fake_pytest_subprocess(
                cmd: list[str], *_a: object, xml_content: str = xml_body, **_kw: object
            ) -> subprocess.CompletedProcess[str]:
                junit_idx = cmd.index("--junit-xml") + 1
                Path(cmd[junit_idx]).write_text(xml_content, encoding="utf-8")
                return subprocess.CompletedProcess(cmd, 0, stdout="1 passed", stderr="")

            pr_mod.subprocess.run = fake_pytest_subprocess  # type: ignore[assignment]
            result = PytestRunner().run(proj)
            assert result.outcome == RunnerOutcome.BLOCKED, f"{label}: {result}"
            assert "invalid JUnit XML" in result.reason, f"{label}: {result.reason}"
            assert "TOP_SECRET_CANARY_VALUE_9912" not in result.reason
            assert not (proj / ".arkhon" / "evidence" / "testing" / "pytest.xml").exists()
    finally:
        pr_mod.subprocess.run = orig_run
        socket.create_connection = orig_connect
