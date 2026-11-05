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
    assert "[UNIMPLEMENTED] not-yet-implemented" in output
    assert "human review required" in output
    assert "aggregate runner records are not accepted as per-rule proof" not in output
    assert "[PASS] type-checker-execution" in output
    assert "[BLOCKED] not-yet-implemented" in output
    assert "human-review-approval" in output
    assert "[BLOCKED] no score or readiness level has been computed" in output


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
