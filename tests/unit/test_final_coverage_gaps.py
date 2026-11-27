# ruff: noqa: I001
from __future__ import annotations

import hashlib
import runpy
from pathlib import Path

import pytest
import yaml

from gencode_gov.assessment.gates import GateVerdict
from gencode_gov.assessment.scorer import Score
from gencode_gov.cli import main
from gencode_gov.core.errors import (
    EvidenceError,
    EvidenceTamperedError,
    SecurityError,
    GateError,
)
from gencode_gov.core.logging import TextFormatter
from gencode_gov.evidence.collector import Artifact, EvidenceDraft
from gencode_gov.evidence.store import EvidenceStore
from gencode_gov.governance.enforcement import EnforcementEngine
from gencode_gov.orchestrator.lifecycle import LifecycleState, Stage
from gencode_gov.orchestrator.stage_manager import StageManager
from gencode_gov.policies.exceptions import load_exceptions
from gencode_gov.rules.loader import Rule
from gencode_gov.rules.registry import RuleRegistry
from gencode_gov.verification.engine import VerificationRun
from gencode_gov.language_support.detector import DetectionResult
from gencode_gov.integrations.tsar.verifier import _maximum_version_tuple


def _evidence_record(root: Path, evidence_id: str, status: str) -> dict[str, object]:
    artifact = root / f"{evidence_id}.txt"
    artifact.write_text(f"evidence for {evidence_id}", encoding="utf-8")
    return {
        "evidence_id": evidence_id,
        "source": "gencode-gov",
        "source_version": "0.1.0",
        "commit_sha": "a" * 40,
        "executed_at": "2026-11-01T00:00:00Z",
        "status": status,
        "artifacts": [
            {
                "path": artifact.name,
                "sha256": hashlib.sha256(artifact.read_bytes()).hexdigest(),
            }
        ],
    }


def test_gate_invalid_status_and_closes_property() -> None:
    with pytest.raises(GateError, match="invalid gate status"):
        GateVerdict("testing_gate", "UNKNOWN")
    assert GateVerdict("testing_gate", "PASS").closes is True
    assert GateVerdict("testing_gate", "BLOCKED").closes is False


def test_scorer_guard_and_lowest_level() -> None:
    module = (
        Path(__file__).resolve().parents[2] / "src" / "gencode_gov" / "assessment" / "scorer.py"
    )
    with pytest.raises(RuntimeError, match="weights must sum to 100"):
        runpy.run_path(str(module), init_globals={"sum": lambda _values: 99})
    assert Score(-1.0, 100.0).level == "development"


def test_cli_assess_fails_closed_with_aggregate_evidence_and_verify_missing_project(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    store = EvidenceStore(tmp_path)
    store.write("testing", _evidence_record(tmp_path, "EVID-ASSESS-PASS", "PASS"))
    store.write("testing", _evidence_record(tmp_path, "EVID-ASSESS-FAIL", "FAIL"))
    store.write("unknown-domain", _evidence_record(tmp_path, "EVID-ASSESS-OTHER", "PASS"))
    assert main(["assess", str(tmp_path)]) == 1
    output = capsys.readouterr().out
    assert "Evidence records inspected: 3" in output
    assert "[BLOCKED] one or more rules lack complete, commit-bound verification" in output
    assert "no score or readiness level has been computed" in output
    assert "Gates:" in output
    assert "Score:" not in output and "Level:" not in output
    assert main(["verify", str(tmp_path / "missing"), "--domain", "testing"]) == 1
    assert "not a directory" in capsys.readouterr().err


def test_text_formatter_and_collector_source_version_validation(tmp_path: Path) -> None:
    assert isinstance(TextFormatter(), __import__("logging").Formatter)
    artifact_path = tmp_path / "artifact.txt"
    artifact_path.write_text("evidence", encoding="utf-8")
    draft = EvidenceDraft(
        evidence_id="EVID-EMPTY-VERSION",
        source="gencode-gov",
        source_version=" ",
        commit_sha="a" * 40,
        status="PASS",
        artifacts=[Artifact(artifact_path, "a" * 64)],
    )
    with pytest.raises(EvidenceError, match="source_version"):
        draft.to_evidence()


def test_evidence_store_detects_concurrent_collision(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    store = EvidenceStore(tmp_path)
    target = store.root / "testing" / "EVID-RACE.json"

    def racing_link(source: Path, destination: Path) -> None:
        if destination == target:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(b'{"other":"writer"}')
            raise FileExistsError(target)
        raise AssertionError("unexpected hard-link destination")

    monkeypatch.setattr("gencode_gov.evidence.store.os.link", racing_link)
    with pytest.raises(EvidenceTamperedError, match="concurrent evidence collision"):
        store.write("testing", {"evidence_id": "EVID-RACE", "status": "PASS"})


def test_enforcement_gate_continues_pass_and_counts_high_severity_block(
    tmp_path: Path,
) -> None:
    passing = Rule(
        id="RULE-PASS",
        path=tmp_path / "pass.yaml",
        raw={
            "metadata": {
                "domain": "testing",
                "status": "active",
                "severity": "low",
                "enforcement": "advisory",
            },
            "evidence": {"required": []},
        },
    )
    blocked_high = Rule(
        id="RULE-HIGH",
        path=tmp_path / "high.yaml",
        raw={
            "metadata": {
                "domain": "testing",
                "status": "active",
                "severity": "high",
                "enforcement": "advisory",
            },
            "evidence": {"required": ["missing.json"]},
        },
    )
    engine = EnforcementEngine(RuleRegistry([passing, blocked_high]))
    verdict = engine.evaluate_gate("testing_gate", ("testing",), tmp_path)
    assert verdict.outcomes[0].status == "BLOCKED"
    assert verdict.outcomes[1].status == "BLOCKED"
    assert verdict.status == "FAIL"
    assert verdict.critical_failures == 1
    assert verdict.closes is False


def test_detector_primary_empty_and_stage_missing_gate(tmp_path: Path) -> None:
    assert DetectionResult(tmp_path).primary is None
    manager = StageManager(
        LifecycleState(current=Stage.REQUIREMENTS),
        gates={},
        project_root=tmp_path,
    )
    assert manager.current is Stage.REQUIREMENTS
    check = manager.can_advance()
    assert check.allowed is False
    assert "requirements_gate not evaluated" in check.missing_criteria[0]


def test_exception_loader_skips_non_mapping_scope(tmp_path: Path) -> None:
    path = tmp_path / "exceptions.yaml"
    path.write_text(
        yaml.safe_dump(
            {
                "exceptions": [
                    {
                        "exception_id": "EX-1",
                        "rule_id": "RULE-1",
                        "scope": ["project"],
                        "rationale": "test",
                        "owner": "owner",
                        "approver": "approver",
                        "approved_at": "2026-11-01T00:00:00Z",
                        "expires_at": "2026-12-01T00:00:00Z",
                        "compensating_control": "control",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    assert load_exceptions(path).exceptions == []


def test_rule_version_default_and_verification_run_failure_property(tmp_path: Path) -> None:
    rule = Rule(id="RULE-VERSION", path=tmp_path / "rule.yaml", raw={})
    assert rule.version == "0.0.0"
    run = VerificationRun(
        run_id="RUN-1",
        domain="testing",
        commit_sha="a" * 40,
        status="BLOCKED",
    )
    assert run.has_failures is True


def test_tsar_version_bound_requires_three_components() -> None:
    with pytest.raises(SecurityError, match="invalid version bound"):
        _maximum_version_tuple("1.2")
