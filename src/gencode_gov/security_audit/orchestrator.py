"""Dependency-aware multi-agent security audit orchestrator with checkpoint resumption."""

from __future__ import annotations

import concurrent.futures
import dataclasses
import json
import os
import tempfile
import threading
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from gencode_gov.security_audit.coverage import (
    CoverageCheck,
    CoverageLedger,
    CoverageUnit,
    LockedCoverageLedgerStore,
)
from gencode_gov.security_audit.dispatcher import AuditRole, SecurityAuditTaskDispatcher
from gencode_gov.security_audit.findings import FindingsCollection, SecurityFinding
from gencode_gov.security_audit.hunting import _unit_priority_key
from gencode_gov.security_audit.reporting import (
    compute_governance_gate_status,
    write_audit_reports,
)
from gencode_gov.security_audit.runtime import (
    AgentRuntimeAdapter,
    AgentSessionResult,
    AgentTaskSpec,
)
from gencode_gov.security_audit.sandbox import SandboxCapabilities, probe_sandbox_capabilities
from gencode_gov.security_audit.validators import validate_audit_directory

CHECKPOINT_FILENAME = "orchestration-state.json"


def _utc_now() -> str:
    return datetime.now(UTC).isoformat()


def _save_json_atomic(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(payload, indent=2) + "\n"
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        dir=path.parent,
        prefix=".orch-",
        suffix=".tmp",
        delete=False,
    ) as handle:
        handle.write(text)
        tmp = Path(handle.name)
    tmp.replace(path)


@dataclass(frozen=True)
class OrchestrationConfig:
    """Configuration governing bounded parallel multi-agent audit execution."""

    profile: str = "standard"
    scope_paths: list[str] | None = None
    max_workers: int = 4
    task_timeout_seconds: float = 30.0
    max_retries: int = 1
    max_units: int | None = None
    report_format: str = "all"

    def __post_init__(self) -> None:
        if self.max_workers < 1:
            raise ValueError("max_workers must be >= 1")
        if self.task_timeout_seconds <= 0:
            raise ValueError("task_timeout_seconds must be > 0")
        if self.max_retries < 0:
            raise ValueError("max_retries must be >= 0")


@dataclass(frozen=True)
class MultiAgentRunOutcome:
    """Result returned by MultiAgentAuditOrchestrator.run()."""

    audit_run_id: str
    audit_dir: Path
    status: str
    execution_mode: str
    governance_gate_status: str
    session_count: int
    distinct_session_ids: int
    distinct_pids: int
    resumed: bool
    blocker_reason: str | None = None


class MultiAgentAuditOrchestrator:
    """Coordinates genuine independent discovery, critic, and verification agent sessions."""

    def __init__(
        self,
        *,
        project_root: Path,
        audit_dir: Path,
        audit_run_id: str,
        commit_sha: str,
        runtime: AgentRuntimeAdapter,
        config: OrchestrationConfig | None = None,
        sandbox_caps: SandboxCapabilities | None = None,
    ) -> None:
        self.project_root = project_root.resolve()
        self.audit_dir = audit_dir.resolve()
        self.audit_run_id = audit_run_id
        self.commit_sha = commit_sha
        self.runtime = runtime
        self.config = config or OrchestrationConfig()
        self.sandbox_caps = sandbox_caps or probe_sandbox_capabilities()
        self.checkpoint_path = self.audit_dir / CHECKPOINT_FILENAME
        self._state_lock = threading.RLock()

    def _load_or_init_checkpoint(self, *, resume: bool) -> dict[str, Any]:
        if resume and self.checkpoint_path.is_file():
            loaded = json.loads(self.checkpoint_path.read_text(encoding="utf-8"))
            if loaded.get("commit_sha") != self.commit_sha:
                raise ValueError("cannot resume checkpoint bound to a different Git commit SHA")
            self.audit_run_id = str(loaded["audit_run_id"])
            loaded["resumed"] = True
            loaded["interrupted"] = False
            return dict(loaded)
        return {
            "audit_run_id": self.audit_run_id,
            "commit_sha": self.commit_sha,
            "runtime_id": self.runtime.runtime_id,
            "stage": "init",
            "interrupted": False,
            "resumed": False,
            "retried_tasks": 0,
            "timed_out_tasks": 0,
            "cancelled_tasks": 0,
            "sessions": [],
            "completed_hunt_units": [],
            "discoverer_tasks": {},
            "candidates_by_fp": {},
            "verified_by_fp": {},
            "verifier_tasks": {},
            "record_verified_fps": [],
        }

    def _persist_checkpoint(self, state: dict[str, Any]) -> None:
        with self._state_lock:
            _save_json_atomic(self.checkpoint_path, state)

    def _record_session(
        self,
        state: dict[str, Any],
        dispatcher: SecurityAuditTaskDispatcher,
        res: AgentSessionResult,
        role: AuditRole,
        wave: int,
    ) -> None:
        with self._state_lock:
            state["sessions"].append(res.to_session_record(wave))
            if res.status == "timed_out":
                state["timed_out_tasks"] = int(state["timed_out_tasks"]) + 1
            elif res.status == "cancelled":
                state["cancelled_tasks"] = int(state["cancelled_tasks"]) + 1
            if res.isolated_process and res.pid != os.getpid():
                dispatcher.register_external_session(
                    session_id=res.session_id,
                    agent_id=res.agent_id,
                    role=role,
                    runtime_id=res.runtime_id,
                    pid=res.pid,
                    wave=wave,
                    status=res.status,
                )
            self._persist_checkpoint(state)

    def _execute_with_retries(
        self,
        *,
        base_agent_prefix: str,
        task_id: str,
        action: str,
        role: AuditRole,
        wave: int,
        output_filename: str,
        payload: dict[str, Any],
        depends_on: tuple[str, ...],
        targets: tuple[str, ...],
        dispatcher: SecurityAuditTaskDispatcher,
        state: dict[str, Any],
        cancel_event: threading.Event | None,
    ) -> AgentSessionResult:
        def _attempt_once(attempt_num: int) -> AgentSessionResult:
            agent_id = (
                base_agent_prefix if attempt_num == 1 else f"{base_agent_prefix}-r{attempt_num - 1}"
            )
            cur_wave = wave + attempt_num - 1
            with self._state_lock:
                dispatcher.assign(
                    agent_id=agent_id,
                    role=role,
                    wave=cur_wave,
                    targets=targets,
                )
            spec = AgentTaskSpec(
                task_id=task_id,
                action=action,
                audit_run_id=self.audit_run_id,
                commit_sha=self.commit_sha,
                role=role.value,
                agent_id=agent_id,
                wave=cur_wave,
                attempt=attempt_num,
                project_root=str(self.project_root),
                output_filename=output_filename,
                payload=payload,
                timeout_seconds=self.config.task_timeout_seconds,
                depends_on=depends_on,
            )
            result = self.runtime.execute_session(
                spec, audit_dir=self.audit_dir, cancel_event=cancel_event
            )
            self._record_session(state, dispatcher, result, role, cur_wave)
            return result

        res = _attempt_once(1)
        for retry_idx in range(1, self.config.max_retries + 1):
            if res.status in {"completed", "cancelled", "blocked"}:
                break
            with self._state_lock:
                state["retried_tasks"] = int(state["retried_tasks"]) + 1
                self._persist_checkpoint(state)
            res = _attempt_once(retry_idx + 1)
        return res

    def _build_orchestration_dict(
        self,
        state: dict[str, Any],
        *,
        independent_verified: bool,
    ) -> dict[str, Any]:
        sessions: list[dict[str, Any]] = list(state["sessions"])
        completed_isolated = [
            s for s in sessions if s["status"] == "completed" and int(s["pid"]) != os.getpid()
        ]
        distinct_sess = len({s["session_id"] for s in completed_isolated})
        distinct_pids = len({int(s["pid"]) for s in completed_isolated})
        return {
            "runtime_id": self.runtime.runtime_id,
            "independent_sessions_verified": independent_verified and distinct_sess >= 2,
            "max_workers": self.config.max_workers,
            "session_count": len(sessions),
            "distinct_session_ids": distinct_sess,
            "distinct_pids": distinct_pids,
            "retried_tasks": int(state["retried_tasks"]),
            "timed_out_tasks": int(state["timed_out_tasks"]),
            "cancelled_tasks": int(state["cancelled_tasks"]),
            "resumed": bool(state["resumed"]),
            "sessions": sessions,
        }

    def run(
        self,
        *,
        resume: bool = False,
        cancel_event: threading.Event | None = None,
    ) -> MultiAgentRunOutcome:
        """Execute or resume a multi-agent security audit across isolated sessions."""
        self.audit_dir.mkdir(parents=True, exist_ok=True)
        probe = self.runtime.probe()
        if not probe.available:
            return MultiAgentRunOutcome(
                audit_run_id=self.audit_run_id,
                audit_dir=self.audit_dir,
                status="blocked",
                execution_mode="single_process_deterministic",
                governance_gate_status="BLOCKED",
                session_count=0,
                distinct_session_ids=0,
                distinct_pids=0,
                resumed=False,
                blocker_reason=probe.reason,
            )

        state = self._load_or_init_checkpoint(resume=resume)
        dispatcher = SecurityAuditTaskDispatcher(
            audit_dir=self.audit_dir,
            execution_mode="multi_agent_independent_sessions",
        )
        ledger_store = LockedCoverageLedgerStore(self.audit_dir / "coverage-ledger.json")

        # Stage 1: Independent Reconnaissance Session
        if state["stage"] == "init" or not ledger_store.ledger_path.is_file():
            recon_res = self._execute_with_retries(
                base_agent_prefix="recon-01",
                task_id="task-recon-01",
                action="reconnaissance",
                role=AuditRole.RECONNAISSANCE,
                wave=1,
                output_filename="recon.json",
                payload={
                    "profile": self.config.profile,
                    "scope_paths": self.config.scope_paths,
                },
                depends_on=(),
                targets=("repository-recon",),
                dispatcher=dispatcher,
                state=state,
                cancel_event=cancel_event,
            )
            if recon_res.status != "completed" or recon_res.output_data is None:
                state["interrupted"] = recon_res.status == "cancelled"
                self._persist_checkpoint(state)
                return MultiAgentRunOutcome(
                    audit_run_id=self.audit_run_id,
                    audit_dir=self.audit_dir,
                    status="interrupted" if recon_res.status == "cancelled" else "blocked",
                    execution_mode="single_process_deterministic",
                    governance_gate_status="BLOCKED",
                    session_count=len(state["sessions"]),
                    distinct_session_ids=0,
                    distinct_pids=0,
                    resumed=bool(state["resumed"]),
                    blocker_reason=recon_res.error or "reconnaissance session failed",
                )
            (self.audit_dir / "architecture.json").write_text(
                json.dumps(recon_res.output_data["inventory"], indent=2) + "\n",
                encoding="utf-8",
            )
            (self.audit_dir / "architecture.md").write_text(
                str(recon_res.output_data["architecture_markdown"]),
                encoding="utf-8",
            )
            seeded_ledger = CoverageLedger.from_dict(recon_res.output_data["ledger"])
            ledger_store.initialize(seeded_ledger)
            state["stage"] = "hunting"
            self._persist_checkpoint(state)

        # Stage 2: Bounded Parallel Wave 1 Hunting Sessions
        self._execute_hunting_wave(
            wave_num=1,
            depends_on=("task-recon-01",),
            ledger_store=ledger_store,
            dispatcher=dispatcher,
            state=state,
            cancel_event=cancel_event,
        )
        if cancel_event is not None and cancel_event.is_set():
            return self._finalize_interrupted(ledger_store, state)

        # Stage 3: Independent Coverage Critic & Wave 2 Gap Reassignment
        current_ledger = ledger_store.read()
        critic_res = self._execute_with_retries(
            base_agent_prefix="coverage-critic-01",
            task_id="task-critic-01",
            action="coverage_critic",
            role=AuditRole.COVERAGE_ANALYST,
            wave=1,
            output_filename="critic.json",
            payload={"ledger": current_ledger.to_dict()},
            depends_on=("task-recon-01",),
            targets=("coverage-ledger",),
            dispatcher=dispatcher,
            state=state,
            cancel_event=cancel_event,
        )
        if critic_res.status == "completed" and critic_res.output_data is not None:
            for cid in critic_res.output_data.get("reassignable_unit_ids", []):
                ledger_store.archive_and_reassign_unit(
                    str(cid), "Coverage critic scheduled Wave 2 gap follow-up."
                )
            if critic_res.output_data.get("reassignable_unit_ids"):
                self._execute_hunting_wave(
                    wave_num=2,
                    depends_on=("task-critic-01",),
                    ledger_store=ledger_store,
                    dispatcher=dispatcher,
                    state=state,
                    cancel_event=cancel_event,
                )
        if cancel_event is not None and cancel_event.is_set():
            return self._finalize_interrupted(ledger_store, state)

        # Stage 4: Bounded Parallel Independent Candidate Verifiers
        state["stage"] = "verifying_candidates"
        self._persist_checkpoint(state)
        self._execute_candidate_verifiers(
            dispatcher=dispatcher,
            state=state,
            cancel_event=cancel_event,
        )
        if cancel_event is not None and cancel_event.is_set():
            return self._finalize_interrupted(ledger_store, state)

        # Stage 5: Bounded Parallel Phase 5 Independent Record Verifiers
        state["stage"] = "verifying_records"
        self._persist_checkpoint(state)
        self._execute_record_verifiers(
            dispatcher=dispatcher,
            state=state,
            cancel_event=cancel_event,
        )
        if cancel_event is not None and cancel_event.is_set():
            return self._finalize_interrupted(ledger_store, state)

        return self._finalize_completed(ledger_store, state)

    def _execute_hunting_wave(
        self,
        *,
        wave_num: int,
        depends_on: tuple[str, ...],
        ledger_store: LockedCoverageLedgerStore,
        dispatcher: SecurityAuditTaskDispatcher,
        state: dict[str, Any],
        cancel_event: threading.Event | None,
    ) -> None:
        snapshot = ledger_store.read()
        planned = sorted(
            [u for u in snapshot.units if u.status == "planned"],
            key=_unit_priority_key,
        )
        if not planned:
            return

        active_units: list[tuple[int, CoverageUnit]] = []
        deferred_ids: list[str] = []
        completed_already = set(state["completed_hunt_units"])

        for idx, unit in enumerate(planned):
            if unit.coverage_id in completed_already and wave_num == 1:
                continue
            if wave_num == 1 and self.config.max_units is not None and idx >= self.config.max_units:
                deferred_ids.append(unit.coverage_id)
                continue
            active_units.append((idx + 1, unit))

        if deferred_ids:

            def _mark_deferred(led: CoverageLedger) -> None:
                for u in led.units:
                    if u.coverage_id in deferred_ids:
                        u.status = "not_examined"
                        u.investigator_id = None
                        u.limitations = ["Deferred due to explicit max_units budget cap."]

            ledger_store.mutate(_mark_deferred)

        def _hunt_worker(item: tuple[int, CoverageUnit]) -> None:
            seq_idx, target_unit = item
            if cancel_event is not None and cancel_event.is_set():
                return
            for attempt in range(1, self.config.max_retries + 2):
                cur_wave = wave_num + attempt - 1
                hunter_id = f"hunter-w{cur_wave}-{seq_idx:03d}"
                task_id = f"task-hunt-w{cur_wave}-{seq_idx:03d}"
                with self._state_lock:
                    dispatcher.assign(
                        agent_id=hunter_id,
                        role=AuditRole.HUNTER,
                        wave=cur_wave,
                        targets=(target_unit.coverage_id,),
                    )
                claimed = ledger_store.claim_unit(target_unit.coverage_id, hunter_id)
                spec = AgentTaskSpec(
                    task_id=task_id,
                    action="hunt_unit",
                    audit_run_id=self.audit_run_id,
                    commit_sha=self.commit_sha,
                    role=AuditRole.HUNTER.value,
                    agent_id=hunter_id,
                    wave=cur_wave,
                    attempt=attempt,
                    project_root=str(self.project_root),
                    output_filename="hunt-result.json",
                    payload={"unit": claimed.to_dict()},
                    timeout_seconds=self.config.task_timeout_seconds,
                    depends_on=depends_on,
                )
                res = self.runtime.execute_session(
                    spec, audit_dir=self.audit_dir, cancel_event=cancel_event
                )
                self._record_session(state, dispatcher, res, AuditRole.HUNTER, cur_wave)

                if res.status == "cancelled":

                    def _revert_cancelled(
                        led: CoverageLedger, cid: str = claimed.coverage_id
                    ) -> None:
                        for u in led.units:
                            if u.coverage_id == cid and u.status == "in_progress":
                                u.status = "planned"
                                u.investigator_id = None

                    ledger_store.mutate(_revert_cancelled)
                    return

                if res.status == "completed" and res.output_data is not None:
                    done_unit = CoverageUnit.from_dict(res.output_data["unit"])
                    raw_cands = [
                        SecurityFinding.from_dict(c) for c in res.output_data["candidates"]
                    ]
                    ledger_store.apply_unit_outcome(done_unit)
                    with self._state_lock:
                        if done_unit.coverage_id not in state["completed_hunt_units"]:
                            state["completed_hunt_units"].append(done_unit.coverage_id)
                        for cand in raw_cands:
                            dispatcher.register_discovery(
                                cand.fingerprint,
                                hunter_id,
                                session_id=res.session_id,
                            )
                            state["discoverer_tasks"][cand.fingerprint] = task_id
                            state["candidates_by_fp"].setdefault(cand.fingerprint, cand.to_dict())
                        self._persist_checkpoint(state)
                    return

                # Session failed, timed out, or blocked: record honest unit blocker
                err_msg = res.error or f"hunter session ended with status {res.status}"
                failed_unit = CoverageUnit.from_dict(claimed.to_dict())
                failed_unit.reviewed_paths = list(claimed.starting_paths)
                failed_unit.checks = [
                    CoverageCheck(
                        investigator_id=hunter_id,
                        method="source",
                        reviewed_paths=tuple(claimed.starting_paths),
                        invariant="Complete isolated hunter session execution.",
                        result=f"Session {res.status}: {err_msg}",
                        evidence_refs=tuple(claimed.starting_paths),
                        artifact_path=None,
                        timestamp=_utc_now(),
                        session_id=res.session_id,
                        runtime_id=res.runtime_id,
                    )
                ]
                failed_unit.limitations = [err_msg]
                failed_unit.status = (
                    "partially_examined"
                    if attempt <= self.config.max_retries and res.status != "blocked"
                    else "blocked"
                )
                ledger_store.apply_unit_outcome(failed_unit)
                if attempt <= self.config.max_retries and res.status != "blocked":
                    with self._state_lock:
                        state["retried_tasks"] = int(state["retried_tasks"]) + 1
                        self._persist_checkpoint(state)
                    ledger_store.archive_and_reassign_unit(
                        claimed.coverage_id,
                        f"Retrying after hunter session {res.status}: {err_msg}",
                    )
                else:
                    return

        with concurrent.futures.ThreadPoolExecutor(max_workers=self.config.max_workers) as pool:
            futures = [pool.submit(_hunt_worker, item) for item in active_units]
            for fut in futures:
                fut.result()

    def _execute_candidate_verifiers(
        self,
        *,
        dispatcher: SecurityAuditTaskDispatcher,
        state: dict[str, Any],
        cancel_event: threading.Event | None,
    ) -> None:
        pending_fps = sorted(
            fp for fp in state["candidates_by_fp"] if fp not in state["verified_by_fp"]
        )
        if not pending_fps:
            return

        def _verify_worker(item: tuple[int, str]) -> None:
            idx, fp = item
            if cancel_event is not None and cancel_event.is_set():
                return
            cand_dict = state["candidates_by_fp"][fp]
            dep_task = str(state["discoverer_tasks"].get(fp, "task-recon-01"))
            v_prefix = f"verifier-{idx:03d}"
            v_task_id = f"task-verify-{idx:03d}"
            res = self._execute_with_retries(
                base_agent_prefix=v_prefix,
                task_id=v_task_id,
                action="verify_candidate",
                role=AuditRole.INDEPENDENT_VERIFIER,
                wave=1,
                output_filename="verify-result.json",
                payload={"candidate": cand_dict},
                depends_on=(dep_task,),
                targets=(fp,),
                dispatcher=dispatcher,
                state=state,
                cancel_event=cancel_event,
            )
            if res.status == "cancelled":
                return
            if res.status == "completed" and res.output_data is not None:
                verified = SecurityFinding.from_dict(res.output_data["finding"])
                dispatcher.assert_independent_verifier(
                    fp,
                    res.agent_id,
                    verifier_session_id=res.session_id,
                )
                with self._state_lock:
                    state["verified_by_fp"][fp] = verified.to_dict()
                    state["verifier_tasks"][fp] = v_task_id
                    self._persist_checkpoint(state)
                return

            blocked_rec = SecurityFinding.from_dict(cand_dict)
            reason = res.error or f"verifier session {res.status}"
            blocked_rec.verification_status = "blocked"
            blocked_rec.unresolved_blockers = [f"Independent verifier failed: {reason}"]
            blocked_rec.validation_plan = {
                "local_check": "Re-run independent verifier session under healthy runtime."
            }
            blocked_rec.transition_to(
                "blocked",
                run_id=self.audit_run_id,
                commit_sha=self.commit_sha,
                actor=res.agent_id,
                reason=reason,
            )
            with self._state_lock:
                state["verified_by_fp"][fp] = blocked_rec.to_dict()
                state["verifier_tasks"][fp] = v_task_id
                self._persist_checkpoint(state)

        with concurrent.futures.ThreadPoolExecutor(max_workers=self.config.max_workers) as pool:
            futs = [pool.submit(_verify_worker, (i + 1, fp)) for i, fp in enumerate(pending_fps)]
            for fut in futs:
                fut.result()

    def _execute_record_verifiers(
        self,
        *,
        dispatcher: SecurityAuditTaskDispatcher,
        state: dict[str, Any],
        cancel_event: threading.Event | None,
    ) -> None:
        already_done = set(state["record_verified_fps"])
        eligible_fps = sorted(
            fp
            for fp, rec_d in state["verified_by_fp"].items()
            if fp not in already_done
            and rec_d["verification_status"] in {"confirmed", "needs_validation"}
        )
        if not eligible_fps:
            return

        def _record_worker(item: tuple[int, str]) -> None:
            idx, fp = item
            if cancel_event is not None and cancel_event.is_set():
                return
            rec_dict = state["verified_by_fp"][fp]
            dep_task = str(state["verifier_tasks"].get(fp, "task-recon-01"))
            rv_prefix = f"record-verifier-{idx:03d}"
            res = self._execute_with_retries(
                base_agent_prefix=rv_prefix,
                task_id=f"task-rec-verify-{idx:03d}",
                action="verify_record",
                role=AuditRole.INDEPENDENT_VERIFIER,
                wave=1,
                output_filename="record-verify.json",
                payload={"finding": rec_dict},
                depends_on=(dep_task,),
                targets=(fp,),
                dispatcher=dispatcher,
                state=state,
                cancel_event=cancel_event,
            )
            if res.status == "cancelled":
                return
            if res.status == "completed" and res.output_data is not None:
                checked_dict = res.output_data["finding"]
                if res.output_data.get("materially_changed"):
                    re_res = self._execute_with_retries(
                        base_agent_prefix=f"record-reverify-{idx:03d}",
                        task_id=f"task-rec-reverify-{idx:03d}",
                        action="verify_record",
                        role=AuditRole.INDEPENDENT_VERIFIER,
                        wave=2,
                        output_filename="record-reverify.json",
                        payload={"finding": checked_dict},
                        depends_on=(f"task-rec-verify-{idx:03d}",),
                        targets=(fp,),
                        dispatcher=dispatcher,
                        state=state,
                        cancel_event=cancel_event,
                    )
                    if re_res.status == "completed" and re_res.output_data is not None:
                        checked_dict = re_res.output_data["finding"]
                with self._state_lock:
                    state["verified_by_fp"][fp] = checked_dict
                    state["record_verified_fps"].append(fp)
                    self._persist_checkpoint(state)

        with concurrent.futures.ThreadPoolExecutor(max_workers=self.config.max_workers) as pool:
            futs = [pool.submit(_record_worker, (i + 1, fp)) for i, fp in enumerate(eligible_fps)]
            for fut in futs:
                fut.result()

    def _collect_current_findings(self, state: dict[str, Any]) -> FindingsCollection:
        records: list[SecurityFinding] = []
        for fp in sorted(state["candidates_by_fp"]):
            raw = state["verified_by_fp"].get(fp, state["candidates_by_fp"][fp])
            records.append(SecurityFinding.from_dict(raw))
        coll = FindingsCollection(
            audit_run_id=self.audit_run_id,
            commit_sha=self.commit_sha,
            records=records,
        )
        coll.deduplicate_and_sort()
        return coll

    def _finalize_interrupted(
        self,
        ledger_store: LockedCoverageLedgerStore,
        state: dict[str, Any],
    ) -> MultiAgentRunOutcome:
        state["interrupted"] = True
        self._persist_checkpoint(state)
        orch_meta = self._build_orchestration_dict(state, independent_verified=True)
        mode = (
            "multi_agent_independent_sessions"
            if orch_meta["independent_sessions_verified"]
            else "single_process_deterministic"
        )

        def _mark_partial(led: CoverageLedger) -> None:
            for u in led.units:
                if u.status == "in_progress":
                    u.status = "planned"
                    u.investigator_id = None
            led.execution_mode = mode
            led.audit_status = "partially_completed"
            led.orchestration = orch_meta if mode == "multi_agent_independent_sessions" else None

        final_ledger = ledger_store.mutate(_mark_partial)
        findings = self._collect_current_findings(state)
        if mode == "single_process_deterministic":
            for rec in findings.records:
                rec.discovery_provenance = dataclasses.replace(
                    rec.discovery_provenance, session_id=None
                )
        findings.save(self.audit_dir / "findings.json")
        write_audit_reports(
            audit_dir=self.audit_dir,
            ledger=final_ledger,
            findings=findings,
            sandbox_caps=self.sandbox_caps,
            fmt=self.config.report_format,
        )
        gate = compute_governance_gate_status(final_ledger, findings)
        return MultiAgentRunOutcome(
            audit_run_id=self.audit_run_id,
            audit_dir=self.audit_dir,
            status="interrupted",
            execution_mode=mode,
            governance_gate_status=gate,
            session_count=int(orch_meta["session_count"]),
            distinct_session_ids=int(orch_meta["distinct_session_ids"]),
            distinct_pids=int(orch_meta["distinct_pids"]),
            resumed=bool(state["resumed"]),
            blocker_reason=(
                "audit interrupted before completion; resumable via gencode-gov audit resume"
            ),
        )

    def _finalize_completed(
        self,
        ledger_store: LockedCoverageLedgerStore,
        state: dict[str, Any],
    ) -> MultiAgentRunOutcome:
        findings = self._collect_current_findings(state)
        orch_meta = self._build_orchestration_dict(state, independent_verified=True)
        verified_multi = bool(orch_meta["independent_sessions_verified"])
        mode = (
            "multi_agent_independent_sessions" if verified_multi else "single_process_deterministic"
        )

        def _finalize_ledger(led: CoverageLedger) -> None:
            comp = led.compute_completeness()
            has_blocked_finding = any(r.verification_status == "blocked" for r in findings.records)
            if comp["blocked"] > 0 or has_blocked_finding:
                led.audit_status = "blocked"
            elif comp["is_complete"]:
                led.audit_status = "completed"
            else:
                led.audit_status = "partially_completed"
            led.execution_mode = mode
            led.orchestration = orch_meta if verified_multi else None

        final_ledger = ledger_store.mutate(_finalize_ledger)
        findings.save(self.audit_dir / "findings.json")
        write_audit_reports(
            audit_dir=self.audit_dir,
            ledger=final_ledger,
            findings=findings,
            sandbox_caps=self.sandbox_caps,
            fmt=self.config.report_format,
        )
        val = validate_audit_directory(self.audit_dir)
        if not val.ok:
            return MultiAgentRunOutcome(
                audit_run_id=self.audit_run_id,
                audit_dir=self.audit_dir,
                status="blocked",
                execution_mode=mode,
                governance_gate_status="BLOCKED",
                session_count=int(orch_meta["session_count"]),
                distinct_session_ids=int(orch_meta["distinct_session_ids"]),
                distinct_pids=int(orch_meta["distinct_pids"]),
                resumed=bool(state["resumed"]),
                blocker_reason=f"post-orchestration validation failed: {'; '.join(val.errors[:3])}",
            )

        state["stage"] = "completed"
        state["interrupted"] = False
        self._persist_checkpoint(state)
        gate = compute_governance_gate_status(final_ledger, findings)
        return MultiAgentRunOutcome(
            audit_run_id=self.audit_run_id,
            audit_dir=self.audit_dir,
            status=final_ledger.audit_status,
            execution_mode=mode,
            governance_gate_status=gate,
            session_count=int(orch_meta["session_count"]),
            distinct_session_ids=int(orch_meta["distinct_session_ids"]),
            distinct_pids=int(orch_meta["distinct_pids"]),
            resumed=bool(state["resumed"]),
            blocker_reason=None,
        )
