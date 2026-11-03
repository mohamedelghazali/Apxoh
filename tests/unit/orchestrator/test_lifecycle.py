"""Tests for lifecycle and stage manager."""
from __future__ import annotations

from pathlib import Path

import pytest

from arkhon.assessment.gates import GateVerdict, RuleOutcome, evaluate_gate
from arkhon.orchestrator.lifecycle import (
    STAGE_ORDER,
    LifecycleState,
    Stage,
    next_stage,
    previous_stage,
    stage_definition,
)
from arkhon.orchestrator.stage_manager import StageManager


def test_stage_order_has_10_stages()->None:
    assert len(STAGE_ORDER)==10

def test_next_stage()->None:
    assert next_stage(Stage.PROJECT_INIT)==Stage.REQUIREMENTS
    assert next_stage(Stage.REQUIREMENTS)==Stage.ARCHITECTURE
    assert next_stage(Stage.POST_RELEASE) is None

def test_previous_stage()->None:
    assert previous_stage(Stage.PROJECT_INIT) is None
    assert previous_stage(Stage.REQUIREMENTS)==Stage.PROJECT_INIT
    assert previous_stage(Stage.RELEASE_APPROVAL)==Stage.RELEASE_REVIEW

def test_every_stage_has_definition()->None:
    for stage in STAGE_ORDER:
        definition=stage_definition(stage)
        assert definition.stage==stage
        assert definition.description

def test_state_advance()->None:
    state=LifecycleState()
    assert state.current==Stage.PROJECT_INIT
    state.advance()
    assert state.current==Stage.REQUIREMENTS
    assert state.history==[Stage.PROJECT_INIT]

def test_state_cannot_advance_beyond_end()->None:
    state=LifecycleState(current=Stage.POST_RELEASE)
    with pytest.raises(ValueError):
        state.advance()

def test_state_rewind()->None:
    state=LifecycleState(current=Stage.ARCHITECTURE)
    state.rewind()
    assert state.current==Stage.REQUIREMENTS

def _passing_gate(gate:str)->GateVerdict:
    outcome=RuleOutcome(rule_id="SE-X-001",enforcement="blocking",status="PASS")
    return evaluate_gate(gate,[outcome])

def _failing_gate(gate:str)->GateVerdict:
    outcome=RuleOutcome(rule_id="SE-X-001",enforcement="blocking",status="FAIL")
    return evaluate_gate(gate,[outcome])

def test_stage_manager_allows_when_gate_passes(tmp_path:Path)->None:
    (tmp_path/".arkhon").mkdir()
    (tmp_path/".arkhon"/"project.yaml").write_text("x: 1\n",encoding="utf-8")
    state=LifecycleState(current=Stage.REQUIREMENTS)
    manager=StageManager(state,{"requirements_gate":_passing_gate("requirements_gate")},tmp_path)
    check=manager.can_advance()
    assert check.allowed
    manager.advance()
    assert state.current==Stage.ARCHITECTURE

def test_stage_manager_blocks_when_gate_fails(tmp_path:Path)->None:
    state=LifecycleState(current=Stage.REQUIREMENTS)
    manager=StageManager(state,{"requirements_gate":_failing_gate("requirements_gate")},tmp_path)
    check=manager.can_advance()
    assert not check.allowed
    assert any("requirements_gate" in item for item in check.missing_criteria)

def test_stage_manager_blocks_on_project_init_without_file(tmp_path:Path)->None:
    state=LifecycleState(current=Stage.PROJECT_INIT)
    manager=StageManager(state,{},tmp_path)
    check=manager.can_advance()
    assert not check.allowed
    assert any(".arkhon/project.yaml" in item for item in check.missing_criteria)

def test_stage_manager_advance_raises_on_blocked(tmp_path:Path)->None:
    state=LifecycleState(current=Stage.REQUIREMENTS)
    manager=StageManager(state,{"requirements_gate":_failing_gate("requirements_gate")},tmp_path)
    with pytest.raises(RuntimeError,match="cannot advance"):
        manager.advance()
