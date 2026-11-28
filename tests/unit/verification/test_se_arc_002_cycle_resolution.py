"""Regression tests for SE-ARC-002 package dependency cycle elimination."""

from __future__ import annotations

import importlib
from pathlib import Path
from typing import Any

from gencode_gov.config import (
    get_manifest,
    language_ids,
    model_ids,
    platform_ids,
    product_ids,
)
from gencode_gov.core.constants import STATUS_PASS
from gencode_gov.policies.loader import (
    POLICY_CATEGORIES,
    Policy,
    PolicyLoadResult,
    PolicyRegistry,
    _load_policy_file,
    load_policies,
)
from gencode_gov.rules.evaluator import RuleEvaluator
from gencode_gov.rules.loader import load_rules_dir
from gencode_gov.verification.architecture_verifier import (
    _extract_submodules,
    _find_strongly_connected_cycles,
    verify_architecture_contracts,
)
from gencode_gov.verification.domain_verifiers import evaluate_domain_method

REPO_ROOT = Path(__file__).resolve().parents[3]
PKG_ROOT = REPO_ROOT / "src" / "gencode_gov"


def _build_package_graphs() -> tuple[dict[str, set[str]], dict[str, set[str]]]:
    top_graph: dict[str, set[str]] = {}
    all_graph: dict[str, set[str]] = {}
    for py_file in sorted(PKG_ROOT.rglob("*.py")):
        rel = py_file.relative_to(PKG_ROOT)
        top_mod = rel.stem if len(rel.parts) == 1 else rel.parts[0]
        if top_mod == "__init__":
            continue
        top_graph.setdefault(top_mod, set())
        all_graph.setdefault(top_mod, set())
        src_txt = py_file.read_text(encoding="utf-8")
        top_graph[top_mod].update(
            _extract_submodules(src_txt, "gencode_gov", top_mod, top_level_only=True)
        )
        all_graph[top_mod].update(_extract_submodules(src_txt, "gencode_gov", top_mod))
    return top_graph, all_graph


def test_repository_architecture_contracts_pass_with_zero_cycles() -> None:
    report = verify_architecture_contracts(REPO_ROOT)
    assert report.status == STATUS_PASS, report.reason
    assert report.cycles == ()
    assert report.layer_violations == ()
    assert report.modules_scanned > 0
    assert "0 cycles, 0 layer violations" in report.reason


def test_eliminated_cycles_direction_and_regression_detection() -> None:
    top_graph, all_graph = _build_package_graphs()

    assert _find_strongly_connected_cycles(top_graph) == []

    # Cycle 1 resolved: core has zero top-level internal dependencies; config -> core
    assert top_graph["core"] == set()
    assert top_graph["config"] == {"core"}

    # Cycle 2 resolved: strict DAG governance -> rules -> policies -> {config, core}
    assert top_graph["policies"] == {"config", "core"}
    assert all_graph["policies"] == {"config", "core"}
    assert "governance" not in all_graph["policies"]
    assert "rules" not in all_graph["policies"]
    assert "policies" in top_graph["rules"]
    assert "governance" not in all_graph["rules"]
    assert {"policies", "rules"} <= top_graph["governance"]

    # Prove detector still catches both historical cycles if reintroduced
    regressed_cycle_1 = {k: set(v) for k, v in top_graph.items()}
    regressed_cycle_1["core"].add("config")
    assert _find_strongly_connected_cycles(regressed_cycle_1) == [("config", "core")]

    regressed_cycle_2 = {k: set(v) for k, v in top_graph.items()}
    regressed_cycle_2["policies"].add("governance")
    assert _find_strongly_connected_cycles(regressed_cycle_2) == [
        ("governance", "policies", "rules")
    ]


def test_se_arc_002_domain_methods_and_rule_evaluator_pass_on_repository() -> None:
    for method_id in ("architecture-layer-boundary-check", "module-cycle-detection"):
        status, reason = evaluate_domain_method(method_id, REPO_ROOT)
        assert status == STATUS_PASS, f"{method_id} failed: {reason}"

    loaded = load_rules_dir(REPO_ROOT / "rules")
    assert loaded.ok, loaded.errors
    se_arc_002 = next(rule for rule in loaded.rules if rule.id == "SE-ARC-002")
    evaluation = RuleEvaluator(project_root=REPO_ROOT).evaluate_rule(se_arc_002)
    assert evaluation.status == STATUS_PASS, evaluation.reason
    assert len(evaluation.methods) == 2
    assert all(m.status == STATUS_PASS for m in evaluation.methods)


def test_preserved_public_apis_across_config_core_and_policy_loaders(tmp_path: Path) -> None:
    core_constants: Any = importlib.import_module("gencode_gov.core.constants")
    gov_policy_loader: Any = importlib.import_module("gencode_gov.governance.policy_loader")

    manifest = get_manifest()
    assert model_ids() == core_constants.model_ids()
    assert platform_ids() == core_constants.platform_ids()
    assert language_ids() == core_constants.language_ids()
    assert product_ids() == core_constants.product_ids()
    assert model_ids(manifest) == model_ids()
    assert platform_ids(manifest) == platform_ids()
    assert language_ids(manifest) == language_ids()
    assert product_ids(manifest) == product_ids()

    assert gov_policy_loader.POLICY_CATEGORIES == POLICY_CATEGORIES
    assert gov_policy_loader.Policy is Policy
    assert gov_policy_loader.PolicyLoadResult is PolicyLoadResult
    assert gov_policy_loader.PolicyRegistry is PolicyRegistry
    assert gov_policy_loader._load_policy_file is _load_policy_file
    assert gov_policy_loader.load_policies is load_policies
    
    blocking_dir = tmp_path / "system" / "policies" / "blocking"
    blocking_dir.mkdir(parents=True)
(blocking_dir / "sample.yaml").write_text("id: POL-001\nenabled: true\n", encoding="utf-8")

gov_registry = gov_policy_loader.load_policies(tmp_path)
pol_registry = load_policies(tmp_path)
assert [p.id for p in gov_registry.all()] == ["POL-001"]
assert [p.id for p in pol_registry.all()] == ["POL-001"]
