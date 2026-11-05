"""Tests for the explicit verification method inventory."""

from __future__ import annotations

from pathlib import Path

import pytest

from arkhon.verification.methods import METHOD_REGISTRY, resolve_method, resolve_methods


def test_registry_contains_only_explicit_implementations() -> None:
    assert resolve_method("type-checker-execution") == METHOD_REGISTRY["type-checker-execution"]
    implementation = resolve_method("zero-type-errors-check")
    assert implementation is not None and implementation.runner == "mypy"
    implementation = resolve_method("tsar-audit-invocation")
    assert implementation is not None and implementation.runner == "tsar"
    for method_id in (
        "evidence-integrity-check",
        "evidence-commit-match",
        "evidence-freshness-check",
        "timestamp-verification",
    ):
        implementation = resolve_method(method_id)
        assert implementation is not None
        assert implementation.component == "verify_tsar_evidence"


def test_unknown_method_is_not_claimed_as_implemented() -> None:
    assert resolve_method("load-test-execution") is None


@pytest.mark.parametrize("value", ["", None])
def test_resolve_method_rejects_invalid_identifier(value: object) -> None:
    with pytest.raises(ValueError, match="non-empty string"):
        resolve_method(value)  # type: ignore[arg-type]


def test_resolve_methods_preserves_supported_and_unsupported_methods() -> None:
    result = resolve_methods(["type-checker-execution", "api-contract-analysis"])
    assert result[0][1] is not None
    assert result[1] == ("api-contract-analysis", None)


@pytest.mark.parametrize(
    ("value", "message"),
    [
        (None, "must be a list"),
        (["valid", ""], "non-empty strings"),
        (["valid", 3], "non-empty strings"),
        (["valid", "valid"], "must not contain duplicates"),
    ],
)
def test_resolve_methods_rejects_malformed_lists(value: object, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        resolve_methods(value)


def test_assess_reports_implementation_coverage_but_never_passes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    from arkhon.cli import main

    project = tmp_path / "project"
    project.mkdir()
    repository = tmp_path / "repository"
    rules = repository / "rules"
    rules.mkdir(parents=True)
    (rules / "sample.yaml").write_text(
        """id: SE-SAMPLE-001
metadata:
  domain: testing
  status: active
  enforcement: blocking
  severity: high
verification:
  methods: [type-checker-execution, not-yet-implemented]
human_review:
  required: true
""",
        encoding="utf-8",
    )
    monkeypatch.setattr("arkhon.cli._repo_root", lambda: repository)
    monkeypatch.setattr("arkhon.cli._commit_sha", lambda _project: "a" * 40)

    from arkhon.verification.runners.base import RunnerOutcome, RunnerResult
    from arkhon.verification.runners.mypy_runner import MypyRunner

    def fake_mypy(self: MypyRunner, root: Path) -> RunnerResult:
        artifact = root / ".arkhon" / "reports" / "mypy.txt"
        artifact.parent.mkdir(parents=True, exist_ok=True)
        artifact.write_text("Success: no issues found", encoding="utf-8")
        return RunnerResult(self.name, RunnerOutcome.PASS, artifacts=[artifact])

    monkeypatch.setattr(MypyRunner, "run", fake_mypy)

    assert main(["assess", str(project)]) == 1
    output = capsys.readouterr().out
    assert "SE-SAMPLE-001: 1/2 methods implemented" in output
    assert "not-yet-implemented: no executable implementation is registered" in output
    assert "human review required" in output
    assert "aggregate runner records are not accepted as per-rule proof" not in output
    assert "[PASS] type-checker-execution" in output
    assert "[BLOCKED] not-yet-implemented" in output
    assert "human-review-approval" in output
    assert "[BLOCKED] no score or readiness level has been computed" in output

    from arkhon.evidence.store import EvidenceStore

    records = list(EvidenceStore(project).iter_records())
    assert len(records) == 1
    assert records[0].commit_sha == "a" * 40
    assert records[0].data["rule_ids"] == ["SE-SAMPLE-001"]
    assert records[0].status == "BLOCKED"


def test_assess_blocks_malformed_method_declaration(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    from arkhon.cli import main

    project = tmp_path / "project"
    project.mkdir()
    repository = tmp_path / "repository"
    rules = repository / "rules"
    rules.mkdir(parents=True)
    (rules / "sample.yaml").write_text(
        """id: SE-SAMPLE-002
metadata:
  domain: testing
  status: active
  enforcement: blocking
verification:
  methods: invalid
human_review:
  required: false
""",
        encoding="utf-8",
    )
    monkeypatch.setattr("arkhon.cli._repo_root", lambda: repository)
    monkeypatch.setattr("arkhon.cli._commit_sha", lambda _project: "a" * 40)

    assert main(["assess", str(project)]) == 1
    output = capsys.readouterr().out
    assert "SE-SAMPLE-002: BLOCKED" in output
    assert "malformed rule declarations: 1" in output
    assert "rules requiring human review: 0" in output


def test_assess_rejects_invalid_rule_registry(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    from arkhon.cli import main

    project = tmp_path / "project"
    project.mkdir()
    repository = tmp_path / "repository"
    rules = repository / "rules"
    rules.mkdir(parents=True)
    (rules / "broken.yaml").write_text("[", encoding="utf-8")
    monkeypatch.setattr("arkhon.cli._repo_root", lambda: repository)

    assert main(["assess", str(project)]) == 1
    assert "rule load errors" in capsys.readouterr().err


def test_assess_rejects_tampered_evidence_store(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    from arkhon.cli import main

    project = tmp_path / "project"
    project.mkdir()
    repository = tmp_path / "repository"
    rules = repository / "rules"
    rules.mkdir(parents=True)
    (rules / "sample.yaml").write_text(
        """id: SE-SAMPLE-003
metadata:
  domain: testing
  status: active
verification:
  methods: [unknown-method]
""",
        encoding="utf-8",
    )
    evidence_dir = project / ".arkhon" / "evidence" / "testing"
    evidence_dir.mkdir(parents=True)
    (evidence_dir / "EVID-TAMPER.json").write_text("{", encoding="utf-8")
    monkeypatch.setattr("arkhon.cli._repo_root", lambda: repository)

    assert main(["assess", str(project)]) == 1
    assert "evidence integrity check failed" in capsys.readouterr().err

def _write_assessment_rule(
    rules: Path,
    rule_id: str,
    domain: str,
    methods: str,
    *,
    enforcement: str = "blocking",
    human_review: bool = False,
    scope: str = "all",
) -> None:
    (rules / f"{rule_id}.yaml").write_text(
        f"""id: {rule_id}
metadata:
  domain: {domain}
  status: active
  enforcement: {enforcement}
  severity: high
scope:
  project_types: [{scope}]
verification:
  methods: {methods}
human_review:
  required: {str(human_review).lower()}
""",
        encoding="utf-8",
    )


def test_assess_distinguishes_tool_execution_from_zero_type_errors(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    from arkhon.cli import main
    from arkhon.verification.runners.base import RunnerOutcome, RunnerResult
    from arkhon.verification.runners.mypy_runner import MypyRunner

    project = tmp_path / "project"
    project.mkdir()
    repository = tmp_path / "repository"
    rules = repository / "rules"
    rules.mkdir(parents=True)
    _write_assessment_rule(
        rules,
        "SE-CQ-002",
        "code-quality",
        "[type-checker-execution, zero-type-errors-check]",
    )
    monkeypatch.setattr("arkhon.cli._repo_root", lambda: repository)
    monkeypatch.setattr("arkhon.cli._commit_sha", lambda _project: "a" * 40)

    def failed_mypy(self: MypyRunner, root: Path) -> RunnerResult:
        artifact = root / ".arkhon" / "reports" / "mypy.txt"
        artifact.parent.mkdir(parents=True, exist_ok=True)
        artifact.write_text("src/app.py:1: error: incompatible type", encoding="utf-8")
        return RunnerResult(self.name, RunnerOutcome.FAIL, "mypy reported type errors", [artifact])

    monkeypatch.setattr(MypyRunner, "run", failed_mypy)

    assert main(["assess", str(project)]) == 1
    output = capsys.readouterr().out
    assert "[PASS] type-checker-execution" in output
    assert "[FAIL] zero-type-errors-check" in output
    assert "SE-CQ-002: FAIL" in output


def test_assess_blocks_runner_exception_and_invalid_artifact(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    from arkhon.cli import main
    from arkhon.verification.runners.base import RunnerOutcome, RunnerResult
    from arkhon.verification.runners.mypy_runner import MypyRunner

    project = tmp_path / "project"
    project.mkdir()
    repository = tmp_path / "repository"
    rules = repository / "rules"
    rules.mkdir(parents=True)
    _write_assessment_rule(rules, "SE-CQ-002", "code-quality", "[type-checker-execution]")
    monkeypatch.setattr("arkhon.cli._repo_root", lambda: repository)
    monkeypatch.setattr("arkhon.cli._commit_sha", lambda _project: "a" * 40)

    def outside_artifact(self: MypyRunner, root: Path) -> RunnerResult:
        artifact = tmp_path / "outside.txt"
        artifact.write_text("not project evidence", encoding="utf-8")
        return RunnerResult(self.name, RunnerOutcome.PASS, artifacts=[artifact])

    monkeypatch.setattr(MypyRunner, "run", outside_artifact)
    assert main(["assess", str(project)]) == 1
    assert "outside project root" in capsys.readouterr().out

    def crashing_runner(self: MypyRunner, root: Path) -> RunnerResult:
        raise RuntimeError("runner fixture crash")

    monkeypatch.setattr(MypyRunner, "run", crashing_runner)
    assert main(["assess", str(project)]) == 1
    assert "runner crashed: RuntimeError: runner fixture crash" in capsys.readouterr().out


def test_assess_blocks_when_project_head_changes_during_verification(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    from arkhon.cli import main
    from arkhon.verification.runners.base import RunnerOutcome, RunnerResult
    from arkhon.verification.runners.mypy_runner import MypyRunner

    project = tmp_path / "project"
    project.mkdir()
    repository = tmp_path / "repository"
    rules = repository / "rules"
    rules.mkdir(parents=True)
    _write_assessment_rule(rules, "SE-CQ-002", "code-quality", "[type-checker-execution]")
    monkeypatch.setattr("arkhon.cli._repo_root", lambda: repository)
    commits = iter(["a" * 40, "b" * 40])
    monkeypatch.setattr("arkhon.cli._commit_sha", lambda _project: next(commits))

    def passing_mypy(self: MypyRunner, root: Path) -> RunnerResult:
        artifact = root / ".arkhon" / "reports" / "mypy.txt"
        artifact.parent.mkdir(parents=True, exist_ok=True)
        artifact.write_text("Success", encoding="utf-8")
        return RunnerResult(self.name, RunnerOutcome.PASS, artifacts=[artifact])

    monkeypatch.setattr(MypyRunner, "run", passing_mypy)
    assert main(["assess", str(project)]) == 1
    assert "HEAD changed during assessment" in capsys.readouterr().out


def test_assess_marks_out_of_scope_rule_not_applicable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    from arkhon.cli import main

    project = tmp_path / "project"
    (project / ".arkhon").mkdir(parents=True)
    (project / ".arkhon" / "project.yaml").write_text(
        "project:\n  profile: web-application\n", encoding="utf-8"
    )
    repository = tmp_path / "repository"
    rules = repository / "rules"
    rules.mkdir(parents=True)
    _write_assessment_rule(
        rules, "SE-API-001", "api-integration", "[api-contract-analysis]", scope="api-service"
    )
    monkeypatch.setattr("arkhon.cli._repo_root", lambda: repository)
    monkeypatch.setattr("arkhon.cli._commit_sha", lambda _project: "a" * 40)

    assert main(["assess", str(project)]) == 1
    assert "SE-API-001: NOT_APPLICABLE" in capsys.readouterr().out


def test_assess_computes_score_only_after_all_rules_and_gates_pass(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    from arkhon.cli import main
    from arkhon.verification.runners.base import RunnerOutcome, RunnerResult
    from arkhon.verification.runners.mypy_runner import MypyRunner

    project = tmp_path / "project"
    project.mkdir()
    repository = tmp_path / "repository"
    rules = repository / "rules"
    rules.mkdir(parents=True)
    domains = [
        "requirements",
        "architecture",
        "testing",
        "software-security",
        "performance",
        "reliability",
        "scalability",
        "devops",
    ]
    for index, domain in enumerate(domains):
        _write_assessment_rule(
            rules, f"SE-TEST-{index:03d}", domain, "[type-checker-execution]"
        )
    monkeypatch.setattr("arkhon.cli._repo_root", lambda: repository)
    monkeypatch.setattr("arkhon.cli._commit_sha", lambda _project: "a" * 40)
    def passing_mypy(self: MypyRunner, root: Path) -> RunnerResult:
        artifact = root / ".arkhon" / "reports" / "mypy.txt"
        artifact.parent.mkdir(parents=True, exist_ok=True)
        artifact.write_text("Success", encoding="utf-8")
        return RunnerResult(self.name, RunnerOutcome.PASS, artifacts=[artifact])

    monkeypatch.setattr(MypyRunner, "run", passing_mypy)
    assert main(["assess", str(project)]) == 0
    output = capsys.readouterr().out
    assert "Engineering score: 100.00/100" in output
    assert "Readiness level: hyperscale-validated" in output
    assert "Decision: APPROVED" in output

