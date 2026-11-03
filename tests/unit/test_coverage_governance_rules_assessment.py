# ruff: noqa: I001
from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from arkhon.assessment.decision import decide
from arkhon.assessment.gates import (
    GateVerdict,
    RuleOutcome as AssessmentOutcome,
    evaluate_all_gates,
    evaluate_gate,
)
from arkhon.assessment.scorer import Score, ScoreBreakdown, score_from_ratios
from arkhon.core.errors import AssessmentError, GateError, GovernanceError, RuleError
from arkhon.governance.charter_loader import (
    Principle,
    _load_yaml as load_charter_yaml,
    _parse_principles,
    load_charter,
)
from arkhon.governance.policy_loader import (
    Policy,
    PolicyRegistry,
    _load_policy_file,
    load_policies,
)
from arkhon.orchestrator.lifecycle import LifecycleState, Stage, next_stage, previous_stage
from arkhon.rules.loader import load_rules_dir
from arkhon.rules.registry import RuleRegistry, build_registry


def _charter_yaml(root: Path) -> Path:
    folder = root / "system" / "charter"
    folder.mkdir(parents=True)
    (folder / "ENGINEERING_CHARTER.md").write_text("# Charter", encoding="utf-8")
    path = folder / "PRINCIPLES.yaml"
    path.write_text(
        yaml.safe_dump({
            "version": "1.0.0",
            "principles": [
                {"number": index, "statement": f"Principle {index}"}
                for index in range(1, 13)
            ],
        }),
        encoding="utf-8",
    )
    return path


def test_charter_load_and_validation_edges(tmp_path: Path) -> None:
    path = _charter_yaml(tmp_path)
    charter = load_charter(tmp_path)
    assert charter.count == 12
    assert charter.principle(12).statement == "Principle 12"
    with pytest.raises(GovernanceError, match="not found"):
        charter.principle(13)
    with pytest.raises(GovernanceError, match=">= 1"):
        Principle(0, "bad")
    with pytest.raises(GovernanceError, match="empty"):
        Principle(1, "  ")
    with pytest.raises(GovernanceError, match="missing"):
        load_charter_yaml(tmp_path / "missing.yaml")
    bad = tmp_path / "bad.yaml"
    bad.write_text("[]", encoding="utf-8")
    with pytest.raises(GovernanceError, match="mapping"):
        load_charter_yaml(bad)
    bad.write_text("[", encoding="utf-8")
    with pytest.raises(GovernanceError, match="cannot load"):
        load_charter_yaml(bad)
    with pytest.raises(GovernanceError, match="exactly 12"):
        _parse_principles({"principles": []})
    valid = yaml.safe_load(path.read_text(encoding="utf-8"))["principles"]
    valid[0]["number"] = True
    with pytest.raises(GovernanceError, match="invalid fields"):
        _parse_principles({"principles": valid})
    valid[0]["number"] = 1
    valid[0]["statement"] = 5
    with pytest.raises(GovernanceError, match="invalid fields"):
        _parse_principles({"principles": valid})
    valid[0] = "bad"
    with pytest.raises(GovernanceError, match="must be a mapping"):
        _parse_principles({"principles": valid})
    valid = [
        {"number": index, "statement": f"Principle {index}"}
        for index in range(1, 13)
    ]
    valid[0]["number"] = 2
    with pytest.raises(GovernanceError, match="unique and ordered"):
        _parse_principles({"principles": valid})
    path.write_text(
        yaml.safe_dump({
            "version": "",
            "principles": [
                {"number": index, "statement": f"Principle {index}"}
                for index in range(1, 13)
            ],
        }),
        encoding="utf-8",
    )
    with pytest.raises(GovernanceError, match="version"):
        load_charter(tmp_path)
    missing_markdown = tmp_path / "missing-markdown"
    charter_dir = missing_markdown / "system" / "charter"
    charter_dir.mkdir(parents=True)
    (charter_dir / "PRINCIPLES.yaml").write_text(
        yaml.safe_dump({"principles": [
            {"number": index, "statement": f"Principle {index}"}
            for index in range(1, 13)
        ]}),
        encoding="utf-8",
    )
    with pytest.raises(GovernanceError, match="markdown missing"):
        load_charter(missing_markdown)


def test_policy_loader_registry_and_fail_closed(tmp_path: Path) -> None:
    with pytest.raises(GovernanceError, match="directory missing"):
        load_policies(tmp_path)
    base = tmp_path / "system" / "policies"
    base.mkdir(parents=True)
    (base / "blocking").write_text("not a directory", encoding="utf-8")
    with pytest.raises(GovernanceError, match="not a directory"):
        load_policies(tmp_path)
    (base / "blocking").unlink()
    for category in ("blocking", "advisory", "exceptions"):
        (base / category).mkdir()
    (base / "blocking" / "a.yaml").write_text(
        "id: BLOCK-1\ntitle: Blocker\nenabled: true\n", encoding="utf-8"
    )
    (base / "advisory" / "b.yml").write_text(
        "id: ADV-1\nenabled: false\n", encoding="utf-8"
    )
    (base / "exceptions" / "c.yaml").write_text("id: EX-1\n", encoding="utf-8")
    registry = load_policies(tmp_path)
    assert len(registry) == 3
    assert registry.blocking()[0].title == "Blocker"
    assert registry.advisory() == []
    assert registry.exceptions()[0].enabled
    with pytest.raises(GovernanceError, match="not found"):
        registry.get("missing")
    with pytest.raises(TypeError):
        registry.get("BLOCK-1").raw["title"] = "mutated"
    with pytest.raises(GovernanceError, match="unknown policy category"):
        PolicyRegistry([Policy("x", "other", Path("x"), {})])
    with pytest.raises(GovernanceError, match="duplicate policy"):
        PolicyRegistry([
            Policy("x", "blocking", Path("x"), {}),
            Policy("x", "advisory", Path("y"), {}),
        ])
    bad = tmp_path / "bad.yaml"
    bad.write_text("[]", encoding="utf-8")
    with pytest.raises(GovernanceError, match="mapping"):
        _load_policy_file(bad, "blocking")
    bad.write_text("id: ''", encoding="utf-8")
    with pytest.raises(GovernanceError, match="valid 'id'"):
        _load_policy_file(bad, "blocking")
    bad.write_text("id: X\nenabled: yes-no", encoding="utf-8")
    with pytest.raises(GovernanceError, match="must be boolean"):
        _load_policy_file(bad, "blocking")
    (base / "blocking" / "bad.yaml").write_text("id: X\nenabled: yes-no", encoding="utf-8")
    with pytest.raises(GovernanceError, match="policy loading failed"):
        load_policies(tmp_path)


def test_rule_loader_and_registry_error_paths(tmp_path: Path) -> None:
    missing = tmp_path / "missing"
    assert load_rules_dir(missing).warnings
    not_dir = tmp_path / "file"
    not_dir.write_text("x", encoding="utf-8")
    assert load_rules_dir(not_dir).errors
    rules = tmp_path / "rules"
    rules.mkdir()
    (rules / "_template.yaml").write_text("bad: [", encoding="utf-8")
    (rules / "broken.yaml").write_text("id: ''", encoding="utf-8")
    result = load_rules_dir(rules)
    assert result.errors and not result.rules
    (rules / "broken.yaml").write_text(
        "id: RULE-1\nmetadata:\n  domain: testing\n", encoding="utf-8"
    )
    (rules / "duplicate.yml").write_text(
        "id: RULE-1\nmetadata:\n  domain: testing\n", encoding="utf-8"
    )
    assert any("duplicate rule id" in str(error) for error in load_rules_dir(rules).errors)
    with pytest.raises(RuleError, match="rule loading failed"):
        build_registry(rules)
    with pytest.raises(RuleError, match="does not exist"):
        build_registry(missing)
    loaded = load_rules_dir(rules, recursive=False)
    assert len(loaded.rules) == 1
    rule = load_rules_dir(rules).rules[0]
    registry = RuleRegistry([rule])
    assert registry.get(rule.id) == rule
    assert registry.by_domain("testing") == [rule]
    assert registry.by_domain("missing") == []
    assert registry.by_status("active") == []
    assert registry.domains() == ["testing"]
    assert rule.id in registry and "missing" not in registry
    with pytest.raises(RuleError, match="duplicate rule id"):
        RuleRegistry([rule, rule])


def test_scoring_and_gate_validation_edges() -> None:
    with pytest.raises(AssessmentError, match="finite"):
        ScoreBreakdown("x", float("nan"), 1)
    with pytest.raises(AssessmentError, match="not in"):
        ScoreBreakdown("x", 2, 1)
    with pytest.raises(AssessmentError, match="numeric"):
        score_from_ratios({**{k: 0.5 for k in (
            "requirements", "architecture_and_code_quality", "testing", "security",
            "performance", "reliability", "scalability",
            "documentation_deployment_maintenance",
        )}, "testing": "not-a-number"})
    with pytest.raises(AssessmentError, match="finite"):
        score_from_ratios({k: float("inf") if k == "security" else 0.5 for k in (
            "requirements", "architecture_and_code_quality", "testing", "security",
            "performance", "reliability", "scalability",
            "documentation_deployment_maintenance",
        )})
    with pytest.raises(AssessmentError, match="no gate verdicts"):
        decide(Score(100, 100), {})
    approved = decide(
        Score(100, 100),
        {"security_gate": GateVerdict("security_gate", "PASS"),
         "release_gate": GateVerdict("release_gate", "PASS")},
    )
    assert approved.decision == "APPROVED"
    assert approved.to_dict()["decision"] == "APPROVED"
    with pytest.raises(GateError, match="unknown gate"):
        evaluate_gate("unknown_gate", [])
    with pytest.raises(GateError, match="unknown outcome domains"):
        evaluate_all_gates({"unknown-domain": []})
    with pytest.raises(GateError, match="unsupported outcome status"):
        evaluate_gate("security_gate", [AssessmentOutcome("R1", "blocking", "UNKNOWN")])


def test_lifecycle_invalid_stage_and_rewind_edges() -> None:
    assert next_stage("unknown") is None  # type: ignore[arg-type]
    assert previous_stage("unknown") is None  # type: ignore[arg-type]
    state = LifecycleState()
    with pytest.raises(ValueError, match="no previous stage"):
        state.rewind()
    state.current = Stage.POST_RELEASE
    with pytest.raises(ValueError, match="no next stage"):
        state.advance()


def test_policy_loader_rejects_yaml_syntax_errors(tmp_path: Path) -> None:
    bad = tmp_path / "malformed-policy.yaml"
    bad.write_text("[", encoding="utf-8")
    with pytest.raises(GovernanceError, match="cannot load policy"):
        _load_policy_file(bad, "blocking")


def test_charter_rejects_blank_principle_statement(tmp_path: Path) -> None:
    principles = [
        {"number": index, "statement": f"Principle {index}"}
        for index in range(1, 13)
    ]
    principles[0]["statement"] = " "
    with pytest.raises(GovernanceError, match="empty statement"):
        _parse_principles({"principles": principles})
