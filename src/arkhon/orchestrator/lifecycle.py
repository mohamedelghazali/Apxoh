"""Apxoh lifecycle.

The lifecycle is the ordered set of stages a governed project passes
through. Each stage has entry criteria, exit criteria, and a gate.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class Stage(str, Enum):
    PROJECT_INIT = "project-initialization"
    REQUIREMENTS = "requirements-engineering"
    ARCHITECTURE = "architecture-design"
    IMPLEMENTATION_PLANNING = "implementation-planning"
    DEVELOPMENT = "controlled-development"
    VERIFICATION = "independent-verification"
    REMEDIATION = "remediation"
    RELEASE_REVIEW = "release-readiness-review"
    RELEASE_APPROVAL = "release-approval"
    POST_RELEASE = "post-release-monitoring"


STAGE_ORDER = (
    Stage.PROJECT_INIT,
    Stage.REQUIREMENTS,
    Stage.ARCHITECTURE,
    Stage.IMPLEMENTATION_PLANNING,
    Stage.DEVELOPMENT,
    Stage.VERIFICATION,
    Stage.REMEDIATION,
    Stage.RELEASE_REVIEW,
    Stage.RELEASE_APPROVAL,
    Stage.POST_RELEASE,
)


@dataclass(frozen=True)
class StageDefinition:
    stage: Stage
    description: str
    entry_criteria: tuple[str, ...]
    exit_criteria: tuple[str, ...]
    gate: str | None


STAGE_DEFINITIONS = {
    Stage.PROJECT_INIT: StageDefinition(
        Stage.PROJECT_INIT,
        "Register project, languages, profile, and risk level.",
        (),
        (".arkhon/project.yaml valid", "profile resolved"),
        None,
    ),
    Stage.REQUIREMENTS: StageDefinition(
        Stage.REQUIREMENTS,
        "Extract, refine, and verify requirements.",
        ("project initialized",),
        ("all requirements have acceptance criteria",),
        "requirements_gate",
    ),
    Stage.ARCHITECTURE: StageDefinition(
        Stage.ARCHITECTURE,
        "Design architecture, document decisions, threat model.",
        ("requirements gate closed",),
        ("architecture reviewed", "threat model documented"),
        "architecture_gate",
    ),
    Stage.IMPLEMENTATION_PLANNING: StageDefinition(
        Stage.IMPLEMENTATION_PLANNING,
        "Break work into tasks, link to rules.",
        ("architecture gate closed",),
        ("all tasks have rule bindings",),
        None,
    ),
    Stage.DEVELOPMENT: StageDefinition(
        Stage.DEVELOPMENT,
        "Write code, apply rules, run local verification.",
        ("implementation plan ready",),
        ("code compiles", "no critical local findings"),
        None,
    ),
    Stage.VERIFICATION: StageDefinition(
        Stage.VERIFICATION,
        "Independent verification of the produced code.",
        ("development complete",),
        ("all required runners pass",),
        "testing_gate",
    ),
    Stage.REMEDIATION: StageDefinition(
        Stage.REMEDIATION,
        "Fix failing findings, re-verify.",
        ("verification found failures",),
        ("all failures resolved or accepted with approval",),
        None,
    ),
    Stage.RELEASE_REVIEW: StageDefinition(
        Stage.RELEASE_REVIEW,
        "Production readiness review.",
        ("verification passed",),
        ("PRR checklist complete",),
        "release_gate",
    ),
    Stage.RELEASE_APPROVAL: StageDefinition(
        Stage.RELEASE_APPROVAL,
        "Final decision: approve, approve-with-conditions, reject.",
        ("release review complete",),
        ("decision recorded",),
        None,
    ),
    Stage.POST_RELEASE: StageDefinition(
        Stage.POST_RELEASE,
        "Monitor, measure, respond to incidents.",
        ("release approved",),
        (),
        None,
    ),
}


def next_stage(current: Stage) -> Stage | None:
    try:
        idx = STAGE_ORDER.index(current)
    except ValueError:
        return None
    return STAGE_ORDER[idx + 1] if idx + 1 < len(STAGE_ORDER) else None


def previous_stage(current: Stage) -> Stage | None:
    try:
        idx = STAGE_ORDER.index(current)
    except ValueError:
        return None
    return STAGE_ORDER[idx - 1] if idx > 0 else None


def stage_definition(stage: Stage) -> StageDefinition:
    return STAGE_DEFINITIONS[stage]


@dataclass
class LifecycleState:
    current: Stage = Stage.PROJECT_INIT
    history: list[Stage] = field(default_factory=list)

    def advance(self) -> Stage:
        nxt = next_stage(self.current)
        if nxt is None:
            raise ValueError(f"no next stage after {self.current.value}")
        self.history.append(self.current)
        self.current = nxt
        return nxt

    def rewind(self) -> Stage:
        prev = previous_stage(self.current)
        if prev is None:
            raise ValueError(f"no previous stage before {self.current.value}")
        self.history.append(self.current)
        self.current = prev
        return prev
