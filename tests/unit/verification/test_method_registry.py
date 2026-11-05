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

    assert main(["assess", str(project)]) == 1
    output = capsys.readouterr().out
    assert "SE-SAMPLE-001: 1/2 methods implemented" in output
    assert "[UNIMPLEMENTED] not-yet-implemented" in output
    assert "human review required" in output
    assert "aggregate runner records are not accepted as per-rule proof" in output
    assert "no score or readiness level has been computed" in output
