from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from arkhon.core.errors import ConfigError, EvidenceError, EvidenceTamperedError, GovernanceError
from arkhon.evidence.store import EvidenceStore
from arkhon.governance.enforcement import EnforcementEngine, RuleOutcome
from arkhon.projects.loader import (
    _load_yaml,
    _validate_profile_data,
    list_profiles,
    load_profile,
)
from arkhon.rules.loader import Rule
from arkhon.rules.registry import RuleRegistry


def _profile_tree(root: Path, name: str = "demo") -> Path:
    base = root / "projects" / name
    base.mkdir(parents=True)
    (base / "profile.yaml").write_text(
        yaml.safe_dump({"name": name, "description": "Demo", "risk_level": "low",
                        "evidence": {"required": ["report.json"]}}),
        encoding="utf-8",
    )
    (base / "rules.yaml").write_text("domains:\n  - testing\n", encoding="utf-8")
    (base / "gates.yaml").write_text("required:\n  - testing_gate\n", encoding="utf-8")
    return base


def test_project_profile_load_validation_and_listing(tmp_path: Path) -> None:
    base = _profile_tree(tmp_path)
    profile = load_profile("demo", tmp_path)
    assert profile.active_domains == ["testing"]
    assert profile.required_gates == ["testing_gate"]
    assert profile.evidence == {"required": ["report.json"]}
    assert list_profiles(tmp_path) == ["demo"]
    (tmp_path / "projects" / "_private").mkdir()
    (tmp_path / "projects" / "UPPER").mkdir()
    (tmp_path / "projects" / "missing-profile").mkdir()
    assert list_profiles(tmp_path) == ["demo"]
    assert not list_profiles(tmp_path / "absent")
    assert base.is_dir()


def test_project_loader_rejects_bad_names_missing_and_escape(tmp_path: Path) -> None:
    for name in ("../outside", "UPPER", "", "bad_name"):
        with pytest.raises(ConfigError, match="invalid profile name"):
            load_profile(name, tmp_path)
    with pytest.raises(ConfigError, match="profile not found"):
        load_profile("missing", tmp_path)
    (tmp_path / "projects").mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    try:
        (tmp_path / "projects" / "linked").symlink_to(outside, target_is_directory=True)
    except OSError:
        pytest.skip("directory symlinks are unavailable")
    with pytest.raises(ConfigError, match="escapes"):
        load_profile("linked", tmp_path)


def test_project_loader_yaml_and_profile_validation(tmp_path: Path) -> None:
    missing = tmp_path / "missing.yaml"
    with pytest.raises(ConfigError, match="missing"):
        _load_yaml(missing)
    assert _load_yaml(missing, required=False) == {}
    empty = tmp_path / "empty.yaml"
    empty.write_text("", encoding="utf-8")
    assert _load_yaml(empty) == {}
    empty.write_text("[", encoding="utf-8")
    with pytest.raises(ConfigError, match="valid YAML"):
        _load_yaml(empty)
    empty.write_text("- item", encoding="utf-8")
    with pytest.raises(ConfigError, match="mapping"):
        _load_yaml(empty)

    with pytest.raises(ConfigError, match="name mismatch"):
        _validate_profile_data("demo", {"name": "other"}, {}, {})
    with pytest.raises(ConfigError, match="risk_level"):
        _validate_profile_data("demo", {"risk_level": "extreme"}, {}, {})
    with pytest.raises(ConfigError, match="rules.domains"):
        _validate_profile_data("demo", {}, {"domains": "testing"}, {})
    with pytest.raises(ConfigError, match="gates.required"):
        _validate_profile_data("demo", {}, {}, {"required": [None]})

    base = _profile_tree(tmp_path)
    (base / "profile.yaml").write_text("evidence: []\n", encoding="utf-8")
    with pytest.raises(ConfigError, match="evidence must be a mapping"):
        load_profile("demo", tmp_path)
    (base / "profile.yaml").write_text("name: demo\n", encoding="utf-8")
    (base / "rules.yaml").write_text("domains: []\n", encoding="utf-8")
    (base / "gates.yaml").unlink()
    assert load_profile("demo", tmp_path).required_gates == []


def test_evidence_store_read_iteration_and_latest_error_paths(tmp_path: Path, monkeypatch) -> None:
    store = EvidenceStore(tmp_path)
    with pytest.raises(EvidenceError, match="mapping"):
        store.write("testing", [])  # type: ignore[arg-type]
    with pytest.raises(EvidenceError, match="invalid or missing"):
        store.write("testing", {"evidence_id": "../escape"})
    with pytest.raises(EvidenceError, match="invalid domain"):
        store.write("../escape", {"evidence_id": "E1"})
    assert list(store.iter_records()) == []
    assert list(store.iter_records("testing")) == []
    with pytest.raises(EvidenceError, match="not found"):
        store.read("testing", "E1")

    first = {"evidence_id": "E1", "commit_sha": "a" * 40, "status": "PASS",
             "executed_at": "2026-01-01T00:00:00Z"}
    target = store.write("testing", first)
    assert store.write("testing", first) == target
    assert store.read("testing", "E1").evidence_id == "E1"
    second = {"evidence_id": "E2", "commit_sha": "a" * 40, "status": "PASS",
              "executed_at": "2026-02-01T00:00:00Z"}
    store.write("testing", second)
    assert store.latest_for_commit("testing", "a" * 40).evidence_id == "E2"
    assert store.latest_for_commit("testing", "b" * 40) is None
    assert len(list(store.iter_records())) == 2

    corrupt = store.root / "testing" / "bad.json"
    corrupt.write_text("{", encoding="utf-8")
    with pytest.raises(EvidenceTamperedError, match="unreadable"):
        store.read("testing", "bad")
    with pytest.raises(EvidenceTamperedError, match="unreadable"):
        list(store.iter_records("testing"))
    corrupt.write_text("[]", encoding="utf-8")
    with pytest.raises(EvidenceTamperedError, match="not an object"):
        store.read("testing", "bad")


def _rule(rule_id: str = "TEST-001", raw: dict | None = None, *,
          status: str = "active", enforcement: str = "blocking",
          severity: str = "medium", domain: str = "testing") -> Rule:
    metadata = {"status": status, "enforcement": enforcement,
                "severity": severity, "domain": domain}
    return Rule(rule_id, Path("rule.yaml"), raw or {"metadata": metadata})


def test_enforcement_rule_evidence_declarations(tmp_path: Path) -> None:
    engine = EnforcementEngine(RuleRegistry([]))
    with pytest.raises(GovernanceError, match="invalid outcome"):
        RuleOutcome("R1", "UNKNOWN")
    assert engine.evaluate_rule(_rule(raw={"evidence": "bad"}), tmp_path).status == "BLOCKED"
    assert engine.evaluate_rule(_rule(raw={"evidence": {"required": "bad"}}), tmp_path).status == "BLOCKED"
    assert engine.evaluate_rule(_rule(raw={"evidence": {"required": ["x"]}}), None).status == "BLOCKED"
    assert engine.evaluate_rule(_rule(raw={"evidence": {"required": ["../outside"]}}), tmp_path).reason.endswith("escapes evidence root")
    (tmp_path / "artifact.json").write_text("{}", encoding="utf-8")
    assert engine.evaluate_rule(
        _rule(raw={"evidence": {"required": ["artifact.json", {"type": "artifact"}]}}),
        tmp_path,
    ).status == "PASS"
    assert engine.evaluate_rule(
        _rule(raw={"evidence": {"required": [{"type": ""}, 1]}}), tmp_path
    ).status == "BLOCKED"
    assert engine.evaluate_rule(
        _rule(raw={"evidence": {"required": [{"type": "missing"}]}}), tmp_path
    ).status == "BLOCKED"


def test_enforcement_gate_counts_critical_blocking_and_inactive(tmp_path: Path) -> None:
    rules = [
        _rule("R1", {"evidence": {"required": ["missing"]}}, enforcement="critical"),
        _rule("R2", {"evidence": {"required": ["missing"]}}, enforcement="required"),
        _rule("R3", {"evidence": {}}, status="disabled"),
    ]
    engine = EnforcementEngine(RuleRegistry(rules))
    verdict = engine.evaluate_gate("testing", ("testing",), tmp_path)
    assert verdict.status == "FAIL"
    assert verdict.critical_failures == 1
    assert verdict.blocking_failures == 1
    assert len(verdict.outcomes) == 2
