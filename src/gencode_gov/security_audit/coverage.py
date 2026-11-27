"""Persistent machine-readable security coverage ledger and cross-run comparison."""

from __future__ import annotations

import contextlib
import json
import os
import tempfile
import threading
import time
import unicodedata
from collections.abc import Callable, Iterator
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from urllib.parse import quote

COVERAGE_SCHEMA_VERSION = "1.0.0"

UNIT_STATUSES = frozenset(
    {
        "planned",
        "in_progress",
        "examined",
        "partially_examined",
        "not_examined",
        "blocked",
        "not_applicable",
    }
)

PRIOR_STATUSES = frozenset(
    {
        "none",
        "new",
        "prior_examined_same_source",
        "prior_examined_changed_source",
        "prior_confirmed_same_source",
        "prior_confirmed_changed_source",
        "prior_needs_validation",
        "prior_partially_examined",
        "prior_not_examined",
        "prior_blocked",
    }
)

AUDIT_RUN_STATUSES = frozenset({"initiated", "partially_completed", "completed", "blocked"})


def _encode_ref_part(value: str) -> str:
    normalized = unicodedata.normalize("NFC", value.strip())
    if not normalized:
        raise ValueError("canonical coverage reference component must be non-empty")
    return quote(normalized.encode("utf-8"), safe="-._~")


def build_canonical_coverage_id(
    *,
    entry_point: str,
    trust_boundary: str,
    component: str,
    attack_class: str,
    interface: str = "internal",
    lifecycle: str | None = None,
) -> str:
    """Compute deterministic RFC-3986 percent-encoded canonical coverage_id."""
    parts = [
        _encode_ref_part(entry_point),
        _encode_ref_part(trust_boundary),
        _encode_ref_part(component),
        _encode_ref_part(attack_class),
        _encode_ref_part(interface),
    ]
    if lifecycle is not None:
        parts.append(_encode_ref_part(lifecycle))
    return "::".join(parts)


@dataclass(frozen=True)
class CoverageCheck:
    """Single source or sandboxed-local check owned by an investigator."""

    investigator_id: str
    method: str
    reviewed_paths: tuple[str, ...]
    invariant: str
    result: str
    evidence_refs: tuple[str, ...]
    artifact_path: str | None
    timestamp: str
    session_id: str | None = None
    runtime_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {
            "investigator_id": self.investigator_id,
            "method": self.method,
            "reviewed_paths": list(self.reviewed_paths),
            "invariant": self.invariant,
            "result": self.result,
            "evidence_refs": list(self.evidence_refs),
            "artifact_path": self.artifact_path,
            "timestamp": self.timestamp,
        }
        if self.session_id is not None:
            out["session_id"] = self.session_id
        if self.runtime_id is not None:
            out["runtime_id"] = self.runtime_id
        return out

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> CoverageCheck:
        return cls(
            investigator_id=str(payload["investigator_id"]),
            method=str(payload["method"]),
            reviewed_paths=tuple(str(p) for p in payload["reviewed_paths"]),
            invariant=str(payload["invariant"]),
            result=str(payload["result"]),
            evidence_refs=tuple(str(e) for e in payload["evidence_refs"]),
            artifact_path=(
                None if payload.get("artifact_path") is None else str(payload["artifact_path"])
            ),
            timestamp=str(payload["timestamp"]),
            session_id=(None if payload.get("session_id") is None else str(payload["session_id"])),
            runtime_id=(None if payload.get("runtime_id") is None else str(payload["runtime_id"])),
        )


@dataclass(frozen=True)
class CoverageAttempt:
    """Archived wave attempt preserved when a coverage unit is reassigned."""

    wave: int
    status: str
    investigator_id: str
    reviewed_paths: tuple[str, ...]
    checks: tuple[CoverageCheck, ...]
    finding_ids: tuple[str, ...]
    candidate_fingerprints: tuple[str, ...]
    limitations: tuple[str, ...]
    reassignment_reason: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "wave": self.wave,
            "status": self.status,
            "investigator_id": self.investigator_id,
            "reviewed_paths": list(self.reviewed_paths),
            "checks": [c.to_dict() for c in self.checks],
            "finding_ids": list(self.finding_ids),
            "candidate_fingerprints": list(self.candidate_fingerprints),
            "limitations": list(self.limitations),
            "reassignment_reason": self.reassignment_reason,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> CoverageAttempt:
        return cls(
            wave=int(payload["wave"]),
            status=str(payload["status"]),
            investigator_id=str(payload["investigator_id"]),
            reviewed_paths=tuple(str(p) for p in payload["reviewed_paths"]),
            checks=tuple(CoverageCheck.from_dict(c) for c in payload["checks"]),
            finding_ids=tuple(str(f) for f in payload["finding_ids"]),
            candidate_fingerprints=tuple(str(fp) for fp in payload["candidate_fingerprints"]),
            limitations=tuple(str(lim) for lim in payload["limitations"]),
            reassignment_reason=str(payload["reassignment_reason"]),
        )


@dataclass
class CoverageUnit:
    """Deterministic unit of security audit coverage."""

    coverage_id: str
    component: str
    attack_class: str
    trust_boundary: str
    entry_point: str
    interface: str
    starting_paths: list[str]
    status: str = "planned"
    prior_status: str = "new"
    wave: int = 1
    investigator_id: str | None = None
    reviewed_paths: list[str] = field(default_factory=list)
    checks: list[CoverageCheck] = field(default_factory=list)
    finding_ids: list[str] = field(default_factory=list)
    candidate_fingerprints: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)
    attempts: list[CoverageAttempt] = field(default_factory=list)
    lifecycle: str | None = None

    def reassign(self, reason: str) -> None:
        """Archive the current wave attempt and reset live fields for a fresh investigator."""
        if self.investigator_id is None or self.status not in {
            "examined",
            "partially_examined",
            "blocked",
        }:
            raise ValueError("only owned terminal wave attempts can be archived for reassignment")
        self.attempts.append(
            CoverageAttempt(
                wave=self.wave,
                status=self.status,
                investigator_id=self.investigator_id,
                reviewed_paths=tuple(self.reviewed_paths),
                checks=tuple(self.checks),
                finding_ids=tuple(self.finding_ids),
                candidate_fingerprints=tuple(self.candidate_fingerprints),
                limitations=tuple(self.limitations),
                reassignment_reason=reason,
            )
        )
        self.wave += 1
        self.status = "planned"
        self.investigator_id = None
        self.reviewed_paths = []
        self.checks = []
        self.finding_ids = []
        self.candidate_fingerprints = []
        self.limitations = []

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "coverage_id": self.coverage_id,
            "component": self.component,
            "attack_class": self.attack_class,
            "trust_boundary": self.trust_boundary,
            "entry_point": self.entry_point,
            "interface": self.interface,
            "starting_paths": list(self.starting_paths),
            "status": self.status,
            "prior_status": self.prior_status,
            "wave": self.wave,
            "investigator_id": self.investigator_id,
            "reviewed_paths": list(self.reviewed_paths),
            "checks": [c.to_dict() for c in self.checks],
            "finding_ids": list(self.finding_ids),
            "candidate_fingerprints": list(self.candidate_fingerprints),
            "limitations": list(self.limitations),
            "attempts": [a.to_dict() for a in self.attempts],
        }
        if self.lifecycle is not None:
            data["lifecycle"] = self.lifecycle
        return data

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> CoverageUnit:
        return cls(
            coverage_id=str(payload["coverage_id"]),
            component=str(payload["component"]),
            attack_class=str(payload["attack_class"]),
            trust_boundary=str(payload["trust_boundary"]),
            entry_point=str(payload["entry_point"]),
            interface=str(payload["interface"]),
            starting_paths=[str(p) for p in payload["starting_paths"]],
            status=str(payload["status"]),
            prior_status=str(payload["prior_status"]),
            wave=int(payload["wave"]),
            investigator_id=(
                None if payload.get("investigator_id") is None else str(payload["investigator_id"])
            ),
            reviewed_paths=[str(p) for p in payload["reviewed_paths"]],
            checks=[CoverageCheck.from_dict(c) for c in payload["checks"]],
            finding_ids=[str(f) for f in payload["finding_ids"]],
            candidate_fingerprints=[str(fp) for fp in payload["candidate_fingerprints"]],
            limitations=[str(lim) for lim in payload["limitations"]],
            attempts=[CoverageAttempt.from_dict(a) for a in payload["attempts"]],
            lifecycle=(None if payload.get("lifecycle") is None else str(payload["lifecycle"])),
        )


@dataclass
class CoverageLedger:
    """Persistent machine-readable coverage ledger across audit waves and runs."""

    ledger_id: str
    audit_run_id: str
    project: str
    commit_sha: str
    profile: str
    audit_status: str
    execution_mode: str
    scope_paths: list[str]
    units: list[CoverageUnit] = field(default_factory=list)
    orchestration: dict[str, Any] | None = None

    def sort_units(self) -> None:
        self.units.sort(key=lambda u: u.coverage_id)

    def compute_completeness(self) -> dict[str, Any]:
        """Compute exact status counts; planned/unexamined/blocked NEVER count as complete."""
        counts = dict.fromkeys(UNIT_STATUSES, 0)
        for unit in self.units:
            if unit.status not in counts:
                raise ValueError(f"invalid unit status: {unit.status!r}")
            counts[unit.status] += 1
        total = len(self.units)
        incomplete_count = (
            counts["planned"]
            + counts["in_progress"]
            + counts["partially_examined"]
            + counts["not_examined"]
            + counts["blocked"]
        )
        is_complete = total > 0 and counts["examined"] > 0 and incomplete_count == 0
        return {
            "total_units": total,
            "examined": counts["examined"],
            "partially_examined": counts["partially_examined"],
            "planned": counts["planned"],
            "in_progress": counts["in_progress"],
            "not_examined": counts["not_examined"],
            "blocked": counts["blocked"],
            "not_applicable": counts["not_applicable"],
            "is_complete": is_complete,
        }

    def detect_gaps(self) -> list[dict[str, str]]:
        """Return every unit that is not fully examined or justified not_applicable."""
        gaps: list[dict[str, str]] = []
        for unit in sorted(self.units, key=lambda u: u.coverage_id):
            if unit.status in {"examined", "not_applicable"}:
                continue
            detail = (
                "; ".join(unit.limitations)
                if unit.limitations
                else f"unit remains in status '{unit.status}'"
            )
            gaps.append(
                {
                    "coverage_id": unit.coverage_id,
                    "component": unit.component,
                    "attack_class": unit.attack_class,
                    "status": unit.status,
                    "reason": detail,
                }
            )
        return gaps

    def to_dict(self) -> dict[str, Any]:
        self.sort_units()
        data: dict[str, Any] = {
            "schema_version": COVERAGE_SCHEMA_VERSION,
            "ledger_id": self.ledger_id,
            "audit_run_id": self.audit_run_id,
            "project": self.project,
            "commit_sha": self.commit_sha,
            "profile": self.profile,
            "audit_status": self.audit_status,
            "execution_mode": self.execution_mode,
            "scope_paths": list(self.scope_paths),
            "units": [u.to_dict() for u in self.units],
            "completeness": self.compute_completeness(),
        }
        if self.orchestration is not None:
            data["orchestration"] = dict(self.orchestration)
        return data

    def save(self, path: Path) -> Path:
        """Atomically persist the coverage ledger JSON to disk."""
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(self.to_dict(), indent=2) + "\n"
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=path.parent,
            prefix=".ledger-",
            suffix=".tmp",
            delete=False,
        ) as handle:
            handle.write(payload)
            temp_path = Path(handle.name)
        temp_path.replace(path)
        return path

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> CoverageLedger:
        return cls(
            ledger_id=str(payload["ledger_id"]),
            audit_run_id=str(payload["audit_run_id"]),
            project=str(payload["project"]),
            commit_sha=str(payload["commit_sha"]),
            profile=str(payload["profile"]),
            audit_status=str(payload["audit_status"]),
            execution_mode=str(payload["execution_mode"]),
            scope_paths=[str(p) for p in payload["scope_paths"]],
            units=[CoverageUnit.from_dict(u) for u in payload["units"]],
            orchestration=(
                None if payload.get("orchestration") is None else dict(payload["orchestration"])
            ),
        )

    @classmethod
    def load(cls, path: Path) -> CoverageLedger:
        raw = json.loads(path.read_text(encoding="utf-8"))
        return cls.from_dict(raw)


def compare_coverage_ledgers(
    prior: CoverageLedger,
    current: CoverageLedger,
) -> dict[str, Any]:
    """Compare two coverage ledgers across runs and compute unit-level deltas."""
    prior_map = {u.coverage_id: u for u in prior.units}
    curr_map = {u.coverage_id: u for u in current.units}
    added = sorted(set(curr_map) - set(prior_map))
    removed = sorted(set(prior_map) - set(curr_map))
    transitions: list[dict[str, str]] = []
    for cid in sorted(set(prior_map) & set(curr_map)):
        if prior_map[cid].status != curr_map[cid].status:
            transitions.append(
                {
                    "coverage_id": cid,
                    "from_status": prior_map[cid].status,
                    "to_status": curr_map[cid].status,
                }
            )
    return {
        "prior_run_id": prior.audit_run_id,
        "current_run_id": current.audit_run_id,
        "prior_commit": prior.commit_sha,
        "current_commit": current.commit_sha,
        "added_units": added,
        "removed_units": removed,
        "status_transitions": transitions,
        "prior_completeness": prior.compute_completeness(),
        "current_completeness": current.compute_completeness(),
    }


class LockedCoverageLedgerStore:
    """Concurrency-safe shared coverage ledger coordinating atomic multi-agent updates."""

    def __init__(self, ledger_path: Path, *, lock_timeout_seconds: float = 10.0) -> None:
        self.ledger_path = ledger_path.resolve()
        self.lock_path = self.ledger_path.with_suffix(".json.lock")
        self.lock_timeout_seconds = lock_timeout_seconds
        self._thread_lock = threading.RLock()

    @contextlib.contextmanager
    def _exclusive_lock(self) -> Iterator[None]:
        self.ledger_path.parent.mkdir(parents=True, exist_ok=True)
        with self._thread_lock:
            deadline = time.monotonic() + self.lock_timeout_seconds
            lock_fd: int | None = None
            while lock_fd is None:
                try:
                    lock_fd = os.open(
                        str(self.lock_path),
                        os.O_CREAT | os.O_EXCL | os.O_WRONLY,
                        0o600,
                    )
                    os.write(lock_fd, f"{os.getpid()}\n".encode("ascii"))
                except FileExistsError:
                    if time.monotonic() >= deadline:
                        raise TimeoutError(
                            f"timed out acquiring coverage ledger lock: {self.lock_path}"
                        ) from None
                    time.sleep(0.01)
            try:
                yield
            finally:
                os.close(lock_fd)
                with contextlib.suppress(FileNotFoundError):
                    self.lock_path.unlink()

    def initialize(self, ledger: CoverageLedger) -> CoverageLedger:
        """Atomically persist initial ledger under exclusive lock."""
        with self._exclusive_lock():
            ledger.save(self.ledger_path)
            return ledger

    def read(self) -> CoverageLedger:
        """Read current ledger snapshot under exclusive lock."""
        with self._exclusive_lock():
            return CoverageLedger.load(self.ledger_path)

    def mutate(self, mutator: Callable[[CoverageLedger], None]) -> CoverageLedger:
        """Apply an atomic read-modify-write mutation to the shared coverage ledger."""
        with self._exclusive_lock():
            ledger = CoverageLedger.load(self.ledger_path)
            mutator(ledger)
            ledger.save(self.ledger_path)
            return ledger

    def claim_unit(self, coverage_id: str, investigator_id: str) -> CoverageUnit:
        """Atomically transition a planned coverage unit to in_progress for investigator_id."""
        claimed: list[CoverageUnit] = []

        def _claim(ledger: CoverageLedger) -> None:
            for unit in ledger.units:
                if unit.coverage_id == coverage_id:
                    if unit.status != "planned":
                        raise ValueError(
                            f"cannot claim unit {coverage_id!r} in status {unit.status!r}"
                        )
                    unit.status = "in_progress"
                    unit.investigator_id = investigator_id
                    claimed.append(CoverageUnit.from_dict(unit.to_dict()))
                    return
            raise KeyError(f"unknown coverage_id: {coverage_id!r}")

        self.mutate(_claim)
        return claimed[0]

    def apply_unit_outcome(self, updated_unit: CoverageUnit) -> CoverageLedger:
        """Atomically merge an investigator's completed/partial/blocked unit outcome."""

        def _apply(ledger: CoverageLedger) -> None:
            for idx, existing in enumerate(ledger.units):
                if existing.coverage_id == updated_unit.coverage_id:
                    merged = CoverageUnit.from_dict(updated_unit.to_dict())
                    merged.finding_ids = sorted(set(existing.finding_ids) | set(merged.finding_ids))
                    merged.candidate_fingerprints = sorted(
                        set(existing.candidate_fingerprints) | set(merged.candidate_fingerprints)
                    )
                    ledger.units[idx] = merged
                    return
            raise KeyError(f"unknown coverage_id: {updated_unit.coverage_id!r}")

        return self.mutate(_apply)

    def archive_and_reassign_unit(self, coverage_id: str, reason: str) -> int:
        """Archive a failed/incomplete wave attempt and reset unit to planned for next wave."""
        next_wave = [1]

        def _reassign(ledger: CoverageLedger) -> None:
            for unit in ledger.units:
                if unit.coverage_id == coverage_id:
                    unit.reassign(reason)
                    next_wave[0] = unit.wave
                    return
            raise KeyError(f"unknown coverage_id: {coverage_id!r}")

        self.mutate(_reassign)
        return next_wave[0]
