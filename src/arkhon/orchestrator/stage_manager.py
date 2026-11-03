"""Stage manager for lifecycle transitions."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from arkhon.assessment.gates import GateVerdict
from arkhon.core.logging import get_logger
from arkhon.orchestrator.lifecycle import LifecycleState, Stage, stage_definition

logger=get_logger("orchestrator.stage_manager")

@dataclass
class TransitionCheck:
    allowed: bool
    reason: str=""
    missing_criteria: list[str]=field(default_factory=list)

class StageManager:
    """Checks stage transitions and records their evidence."""
    def __init__(self,state:LifecycleState,gates:dict[str,GateVerdict],project_root:Path)->None:
        self._state=state
        self._gates=gates
        self._root=project_root

    @property
    def current(self)->Stage:
        return self._state.current

    def can_advance(self)->TransitionCheck:
        definition=stage_definition(self._state.current)
        missing=[]
        if definition.gate:
            verdict=self._gates.get(definition.gate)
            if verdict is None:
                missing.append(f"gate {definition.gate} not evaluated")
            elif not verdict.closes:
                missing.append(f"gate {definition.gate} is {verdict.status}: {verdict.reason}")
        if self._state.current==Stage.PROJECT_INIT:
            if not (self._root/".arkhon"/"project.yaml").is_file():
                missing.append("missing .arkhon/project.yaml")
        if missing:
            return TransitionCheck(False,"exit criteria not met",missing)
        return TransitionCheck(True,"exit criteria satisfied")

    def advance(self)->Stage:
        check=self.can_advance()
        if not check.allowed:
            raise RuntimeError(f"cannot advance from {self._state.current.value}: {check.reason}")
        return self._state.advance()
