from __future__ import annotations

import json
import logging
from typing import Any
from pathlib import Path
from types import SimpleNamespace

import pytest

from arkhon.assessment.decision import decide
from arkhon.assessment.gates import GateVerdict
from arkhon.assessment.scorer import Score
from arkhon.core.errors import AssessmentError, ConfigError, EvidenceError, EvidenceTamperedError, GovernanceError
from arkhon.core.logging import JsonFormatter, configure_logging, get_logger
from arkhon.evidence.store import EvidenceStore
from arkhon.governance.charter_loader import Principle, _parse_principles, load_charter
from arkhon.governance.enforcement import EnforcementEngine, RuleOutcome
from arkhon.governance.policy_loader import Policy, PolicyRegistry
from arkhon.policies.advisory import AdvisoryPolicyEvaluator
from arkhon.projects.loader import _load_yaml, list_profiles, load_profile


def score(value: float = 90) -> Score:
    return Score(value, 100)


def verdict(name: str, status: str, reason: str = "") -> GateVerdict:
    return GateVerdict(name, status, reason=reason)


@pytest.mark.parametrize(("gates", "points", "risks", "expected"), [
    ({"release_gate": verdict("release_gate", "PASS")}, 99, 0, "REJECTED"),
    ({"security_gate": verdict("security_gate", "FAIL"), "release_gate": verdict("release_gate", "PASS")}, 99, 0, "REJECTED"),
    ({"security_gate": verdict("security_gate", "BLOCKED"), "release_gate": verdict("release_gate", "PASS")}, 99, 0, "PENDING_EVIDENCE"),
    ({"security_gate": verdict("security_gate", "PASS"), "release_gate": verdict("release_gate", "PASS"), "testing_gate": verdict("testing_gate", "BLOCKED")}, 99, 0, "PENDING_EVIDENCE"),
    ({"security_gate": verdict("security_gate", "PASS"), "release_gate": verdict("release_gate", "PASS"), "testing_gate": verdict("testing_gate", "FAIL")}, 99, 0, "REJECTED"),
    ({"security_gate": verdict("security_gate", "PASS"), "release_gate": verdict("release_gate", "PASS")}, 79, 0, "REJECTED"),
    ({"security_gate": verdict("security_gate", "PASS"), "release_gate": verdict("release_gate", "PASS")}, 80, 1, "APPROVED_WITH_CONDITIONS"),
    ({"security_gate": verdict("security_gate", "PASS"), "release_gate": verdict("release_gate", "PASS")}, 100, 0, "APPROVED"),
])
def test_decision_paths(gates: dict[str, GateVerdict], points: float, risks: int, expected: str) -> None:
    assert decide(score(points), gates, risks).decision == expected


def test_decision_rejects_missing_inputs() -> None:
    with pytest.raises(AssessmentError):
        decide(score(), {})
    with pytest.raises(AssessmentError):
        decide(score(), {"security_gate": verdict("security_gate", "PASS"),
                         "release_gate": verdict("release_gate", "PASS")}, -1)


def principles() -> dict[str, Any]:
    return {"principles": [{"number": n, "statement": f"Principle {n}"} for n in range(1, 13)]}


def test_charter_validation_and_loading(tmp_path: Path) -> None:
    with pytest.raises(GovernanceError):
        Principle(0, "invalid")
    with pytest.raises(GovernanceError):
        Principle(1, " ")
    parsed = _parse_principles(principles())
    assert len(parsed) == 12
    with pytest.raises(GovernanceError):
        _parse_principles({"principles": []})
    bad = principles()
    bad["principles"][0]["number"] = True
    with pytest.raises(GovernanceError):
        _parse_principles(bad)
    base = tmp_path / "system" / "charter"
    base.mkdir(parents=True)
    (base / "ENGINEERING_CHARTER.md").write_text("# Charter", encoding="utf-8")
    import yaml
    (base / "PRINCIPLES.yaml").write_text(
        yaml.safe_dump({"version": "1.2.3", **principles()}), encoding="utf-8")
    charter = load_charter(tmp_path)
    assert charter.count == 12 and charter.version == "1.2.3"
    with pytest.raises(GovernanceError):
        charter.principle(13)


def test_profile_loader_validates_and_lists(tmp_path: Path) -> None:
    base = tmp_path / "projects" / "universal"
    base.mkdir(parents=True)
    (base / "profile.yaml").write_text(
        "name: universal\ndescription: General\nrisk_level: low\nevidence: {}\n", encoding="utf-8")
    (base / "rules.yaml").write_text("domains: [testing, security]\n", encoding="utf-8")
    (base / "gates.yaml").write_text("required: [security_gate]\n", encoding="utf-8")
    (tmp_path / "projects" / "_private").mkdir()
    loaded = load_profile("universal", tmp_path)
    assert loaded.active_domains == ["testing", "security"]
    assert loaded.required_gates == ["security_gate"]
    assert list_profiles(tmp_path) == ["universal"]
    for invalid in ("../escape", "Upper", "a/b", "", None, 42):
        with pytest.raises(ConfigError):
            load_profile(invalid, tmp_path)  # type: ignore[arg-type]


def test_profile_loader_rejects_invalid_yaml_and_profile(tmp_path: Path) -> None:
    with pytest.raises(ConfigError):
        _load_yaml(tmp_path / "missing.yaml")
    assert _load_yaml(tmp_path / "optional.yaml", required=False) == {}
    p = tmp_path / "list.yaml"
    p.write_text("- item\n", encoding="utf-8")
    with pytest.raises(ConfigError):
        _load_yaml(p)
    base = tmp_path / "projects" / "demo"
    base.mkdir(parents=True)
    (base / "profile.yaml").write_text("name: wrong\n", encoding="utf-8")
    with pytest.raises(ConfigError, match="mismatch"):
        load_profile("demo", tmp_path)
    (base / "profile.yaml").write_text("name: demo\nrisk_level: extreme\n", encoding="utf-8")
    with pytest.raises(ConfigError, match="risk_level"):
        load_profile("demo", tmp_path)
    (base / "profile.yaml").write_text("name: demo\nevidence: []\n", encoding="utf-8")
    with pytest.raises(ConfigError, match="evidence"):
        load_profile("demo", tmp_path)


def test_advisory_evaluator_filters_and_matches(tmp_path: Path) -> None:
    def policy(pid: str, enabled: bool, raw: dict[str, Any]) -> Policy:
        return Policy(pid, "advisory", Path(pid + ".yaml"), {"enabled": enabled, **raw})
    registry = PolicyRegistry([
        policy("A1", True, {"trigger_rules": ["R1"], "message": "Improve"}),
        policy("A2", False, {"trigger_rules": ["R1"]}),
        policy("A3", True, {"trigger_rules": "invalid"}),
    ])
    result = AdvisoryPolicyEvaluator(registry).evaluate(failing_rules={"R1"}, project_root=tmp_path)
    assert result.count == 1
    assert result.notes[0].message == "Improve"


def rule(rule_id: str, evidence: object, status: str = "active",
         enforcement: str = "blocking", severity: str = "low") -> SimpleNamespace:
    return SimpleNamespace(id=rule_id, raw={"evidence": evidence}, status=status,
                           enforcement=enforcement, severity=severity)


def test_enforcement_evidence_validation_and_path_safety(tmp_path: Path) -> None:
    engine = EnforcementEngine(SimpleNamespace())
    assert engine.evaluate_rule(rule("R0", {}), None).status == "PASS"
    assert engine.evaluate_rule(rule("R1", {"required": ["x"]}), None).status == "BLOCKED"
    assert engine.evaluate_rule(rule("R2", {"required": "bad"}), tmp_path).status == "BLOCKED"
    root = tmp_path / "evidence"
    root.mkdir()
    (root / "proof.txt").write_text("proof", encoding="utf-8")
    assert engine.evaluate_rule(rule("R3", {"required": ["proof.txt"]}), root).evidence_present
    assert engine.evaluate_rule(rule("R4", {"required": ["missing"]}), root).status == "BLOCKED"
    assert "escapes" in engine.evaluate_rule(rule("R5", {"required": ["../escape"]}), root).reason
    assert engine.evaluate_rule(rule("R6", {"required": [{"type": "proof"}]}), root).status == "PASS"
    assert engine.evaluate_rule(rule("R7", {"required": [{"type": ""}]}), root).status == "BLOCKED"
    assert engine.evaluate_rule(rule("R8", {"required": [None]}), root).status == "BLOCKED"


def test_enforcement_gate_ignores_inactive_and_aggregates(tmp_path: Path) -> None:
    rules = [rule("R1", {"required": ["missing"]}, enforcement="blocking"),
             rule("R2", {"required": ["missing"]}, enforcement="critical"),
             rule("R3", {}, status="disabled")]
    registry = SimpleNamespace(by_domain=lambda _domain: rules)
    result = EnforcementEngine(registry).evaluate_gate("security", ("security",), tmp_path)
    assert result.status == "FAIL"
    assert result.blocking_failures == 1 and result.critical_failures == 1
    assert len(result.outcomes) == 2
    with pytest.raises(GovernanceError):
        RuleOutcome("R4", "UNKNOWN")


def test_evidence_store_integrity_iteration_and_latest(tmp_path: Path) -> None:
    store = EvidenceStore(tmp_path)
    data = {"evidence_id": "EVID-1", "commit_sha": "a" * 40, "status": "PASS",
            "executed_at": "2026-11-01T00:00:00Z"}
    path = store.write("testing", data)
    assert store.write("testing", data) == path
    assert store.read("testing", "EVID-1").status == "PASS"
    assert len(list(store.iter_records())) == 1
    latest = store.latest_for_commit("testing", "a" * 40)
    assert latest is not None and latest.evidence_id == "EVID-1"
    assert store.latest_for_commit("testing", "b" * 40) is None
    with pytest.raises(EvidenceTamperedError):
        store.write("testing", {**data, "status": "FAIL"})
    with pytest.raises(EvidenceError):
        store.write("testing", {"evidence_id": "../escape"})
    for domain in ("../escape", ""):
        with pytest.raises(EvidenceError):
            list(store.iter_records(domain))
    with pytest.raises(EvidenceError):
        store._domain_dir(None)  # type: ignore[arg-type]
    path.write_text("{", encoding="utf-8")
    with pytest.raises(EvidenceTamperedError):
        store.read("testing", "EVID-1")


def test_evidence_store_rejects_non_mapping_and_corrupt_records(tmp_path: Path) -> None:
    store = EvidenceStore(tmp_path)
    with pytest.raises(EvidenceError):
        store.write("testing", [])  # type: ignore[arg-type]
    with pytest.raises(EvidenceError):
        store.read("testing", "missing")
    folder = store.root / "testing"
    folder.mkdir(parents=True)
    (folder / "array.json").write_text("[]", encoding="utf-8")
    with pytest.raises(EvidenceTamperedError):
        list(store.iter_records("testing"))


def test_logging_json_extras_exceptions_and_configuration() -> None:
    try:
        raise RuntimeError("expected")
    except RuntimeError:
        import sys
        record = logging.LogRecord("arkhon.test", logging.ERROR, __file__, 1, "message", (),
                                   sys.exc_info())
    setattr(record, "arkhon_extra", {"component": "test"})
    payload = json.loads(JsonFormatter().format(record))
    assert payload["extra"]["component"] == "test"
    assert "RuntimeError" in payload["exception"]
    configure_logging("warning", "json")
    assert logging.getLogger().level == logging.WARNING
    assert isinstance(logging.getLogger().handlers[-1].formatter, JsonFormatter)
    assert get_logger("unit").name == "arkhon.unit"
    with pytest.raises(ValueError):
        configure_logging("invalid")
    with pytest.raises(ValueError):
        configure_logging("info", "invalid")
