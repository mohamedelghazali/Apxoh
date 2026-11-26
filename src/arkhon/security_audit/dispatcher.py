"""Multi-role security audit task orchestration, ownership, and workspace isolation."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path

_AGENT_ID_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{0,63}$")
_RESERVED_DEVICES = frozenset(
    {
        "con",
        "prn",
        "aux",
        "nul",
        *(f"com{i}" for i in range(1, 10)),
        *(f"lpt{i}" for i in range(1, 10)),
    }
)


def _is_valid_agent_id(agent_id: str) -> bool:
    if not _AGENT_ID_RE.fullmatch(agent_id):
        return False
    return agent_id.split(".", 1)[0] not in _RESERVED_DEVICES


class AuditRole(StrEnum):
    """Canonical specialist roles for Apxoh security audit workflows."""

    RECONNAISSANCE = "security-reconnaissance-agent"
    HUNTER = "security-hunter"
    ATTACK_CLASS_SPECIALIST = "attack-class-specialist"
    COVERAGE_ANALYST = "coverage-analyst"
    INDEPENDENT_VERIFIER = "independent-finding-verifier"
    ARTIFACT_VALIDATOR = "security-artifact-validator"
    REMEDIATION_VERIFIER = "remediation-verification-agent"


EXECUTION_MODES = frozenset(
    {
        "single_process_deterministic",
        "multi_agent_independent_sessions",
        "multi_agent_delegated",
    }
)


@dataclass(frozen=True)
class AgentAssignment:
    """Immutable ownership record binding one agent instance to assigned targets."""

    agent_id: str
    role: AuditRole
    wave: int
    owned_targets: tuple[str, ...]
    scratch_dir: Path
    artifacts_dir: Path


@dataclass
class SecurityAuditTaskDispatcher:
    """Coordinates role assignments, write isolation, and separation of duties."""

    audit_dir: Path
    execution_mode: str = "single_process_deterministic"
    assignments: list[AgentAssignment] = field(default_factory=list)
    _unit_wave_owners: dict[tuple[str, int], str] = field(default_factory=dict)
    _finding_discoverers: dict[str, str] = field(default_factory=dict)
    _finding_discoverer_sessions: dict[str, str] = field(default_factory=dict)
    _external_sessions: dict[str, dict[str, object]] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.execution_mode not in EXECUTION_MODES:
            raise ValueError(f"unsupported execution_mode: {self.execution_mode!r}")
        self.audit_dir = self.audit_dir.resolve()

    def assign(
        self,
        *,
        agent_id: str,
        role: AuditRole,
        wave: int,
        targets: tuple[str, ...],
    ) -> AgentAssignment:
        """Create an isolated workspace and record exclusive wave ownership."""
        if not _is_valid_agent_id(agent_id):
            raise ValueError(f"invalid canonical agent_id: {agent_id!r}")
        if wave < 1:
            raise ValueError("wave must be >= 1")
        if role in {AuditRole.HUNTER, AuditRole.ATTACK_CLASS_SPECIALIST}:
            for target_id in targets:
                key = (target_id, wave)
                existing_owner = self._unit_wave_owners.get(key)
                if existing_owner is not None and existing_owner != agent_id:
                    raise ValueError(
                        f"coverage unit {target_id!r} wave {wave} already owned by {existing_owner}"
                    )
                self._unit_wave_owners[key] = agent_id

        if role == AuditRole.INDEPENDENT_VERIFIER:
            for fingerprint in targets:
                discoverer = self._finding_discoverers.get(fingerprint)
                if discoverer is not None and discoverer == agent_id:
                    raise ValueError(
                        f"separation-of-duties violation: {agent_id!r} discovered {fingerprint!r}"
                    )

        agent_root = self.audit_dir / "agents" / agent_id
        scratch_dir = agent_root / "scratch"
        artifacts_dir = agent_root / "artifacts"
        scratch_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
        artifacts_dir.mkdir(parents=True, exist_ok=True, mode=0o700)

        record = AgentAssignment(
            agent_id=agent_id,
            role=role,
            wave=wave,
            owned_targets=targets,
            scratch_dir=scratch_dir,
            artifacts_dir=artifacts_dir,
        )
        self.assignments.append(record)
        return record

    def register_external_session(
        self,
        *,
        session_id: str,
        agent_id: str,
        role: AuditRole,
        runtime_id: str,
        pid: int,
        wave: int = 1,
        status: str = "completed",
    ) -> None:
        """Record an actually executed isolated external agent session."""
        if not session_id or not _is_valid_agent_id(agent_id):
            raise ValueError("session_id and canonical agent_id are required")
        self._external_sessions[session_id] = {
            "session_id": session_id,
            "agent_id": agent_id,
            "role": role.value,
            "runtime_id": runtime_id,
            "pid": pid,
            "wave": wave,
            "status": status,
        }

    def register_discovery(
        self,
        fingerprint: str,
        agent_id: str,
        *,
        session_id: str | None = None,
    ) -> None:
        """Record which hunter/specialist and session discovered a candidate fingerprint."""
        if not _is_valid_agent_id(agent_id):
            raise ValueError(f"invalid canonical agent_id: {agent_id!r}")
        self._finding_discoverers.setdefault(fingerprint, agent_id)
        if session_id is not None:
            self._finding_discoverer_sessions.setdefault(fingerprint, session_id)

    def assert_independent_verifier(
        self,
        fingerprint: str,
        verifier_id: str,
        *,
        verifier_session_id: str | None = None,
    ) -> None:
        """Verify that verifier_id and session_id are distinct from the discoverer."""
        if not _is_valid_agent_id(verifier_id):
            raise ValueError(f"invalid canonical verifier_id: {verifier_id!r}")
        discoverer = self._finding_discoverers.get(fingerprint)
        if discoverer == verifier_id:
            raise ValueError(
                f"verifier {verifier_id!r} cannot independently verify its own discovery"
            )
        disc_session = self._finding_discoverer_sessions.get(fingerprint)
        if (
            verifier_session_id is not None
            and disc_session is not None
            and verifier_session_id == disc_session
        ):
            raise ValueError(
                f"session {verifier_session_id!r} cannot verify its own discovery"
            )

    def provenance_summary(self) -> dict[str, object]:
        """Return honest orchestration metadata without claiming external agents when local."""
        verified_independent = (
            self.execution_mode == "multi_agent_independent_sessions"
            and len(self._external_sessions) >= 2
        )
        return {
            "execution_mode": self.execution_mode,
            "multi_agent_independent_sessions": verified_independent,
            "assignment_count": len(self.assignments),
            "external_session_count": len(self._external_sessions),
            "roles_invoked": sorted({a.role.value for a in self.assignments}),
        }


__all__ = [
    "EXECUTION_MODES",
    "AgentAssignment",
    "AuditRole",
    "SecurityAuditTaskDispatcher",
]
