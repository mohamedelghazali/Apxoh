"""Standalone out-of-process worker entrypoint for independent security audit sessions."""

from __future__ import annotations

import dataclasses
import json
import os
import sys
from pathlib import Path
from typing import Any

from gencode_gov.security_audit.coverage import CoverageLedger, CoverageUnit
from gencode_gov.security_audit.findings import (
    SecurityFinding,
    VerificationProvenance,
)
from gencode_gov.security_audit.hunting import (
    _iter_source_files,
    discover_architecture,
    hunt_coverage_unit,
    seed_coverage_ledger,
)
from gencode_gov.security_audit.runtime import AgentTaskSpec
from gencode_gov.security_audit.verifier import IndependentFindingVerifier


def execute_worker_envelope(envelope: dict[str, Any]) -> dict[str, Any]:
    """Execute a single isolated session action and return structured JSON output."""
    session_id = str(envelope["session_id"])
    runtime_id = str(envelope["runtime_id"])
    task = AgentTaskSpec.from_dict(envelope["task"])
    project_root = Path(task.project_root).resolve()
    my_pid = os.getpid()

    if task.action == "reconnaissance":
        profile = str(task.payload.get("profile", "standard"))
        raw_scope = task.payload.get("scope_paths")
        scope_paths = [str(x) for x in raw_scope] if isinstance(raw_scope, list) else None
        inventory = discover_architecture(project_root, task.commit_sha)
        ledger = seed_coverage_ledger(
            inventory,
            audit_run_id=task.audit_run_id,
            profile=profile,
            scope_paths=scope_paths,
        )
        ledger.execution_mode = "multi_agent_independent_sessions"
        return {
            "action": "reconnaissance",
            "session_id": session_id,
            "worker_pid": my_pid,
            "inventory": inventory.to_dict(),
            "architecture_markdown": inventory.render_markdown(),
            "ledger": ledger.to_dict(),
        }

    if task.action == "hunt_unit":
        unit = CoverageUnit.from_dict(task.payload["unit"])
        updated_unit, candidates = hunt_coverage_unit(
            project_root=project_root,
            unit=unit,
            hunter_id=task.agent_id,
            audit_run_id=task.audit_run_id,
            commit_sha=task.commit_sha,
            session_id=session_id,
            runtime_id=runtime_id,
            pid=my_pid,
        )
        return {
            "action": "hunt_unit",
            "session_id": session_id,
            "worker_pid": my_pid,
            "unit": updated_unit.to_dict(),
            "candidates": [cand.to_dict() for cand in candidates],
        }

    if task.action == "coverage_critic":
        ledger = CoverageLedger.from_dict(task.payload["ledger"])
        covered_files: set[str] = set()
        reassignable_ids: list[str] = []
        for u in ledger.units:
            covered_files.update(u.reviewed_paths)
            if u.status in {"not_examined", "not_applicable"}:
                covered_files.update(u.starting_paths)
            if u.status == "partially_examined":
                reassignable_ids.append(u.coverage_id)
        all_files = {
            str(p.relative_to(project_root)).replace("\\", "/")
            for p in _iter_source_files(project_root)
        }
        unmapped = sorted(all_files - covered_files)
        gaps = ledger.detect_gaps()
        return {
            "action": "coverage_critic",
            "session_id": session_id,
            "worker_pid": my_pid,
            "unmapped_files": unmapped,
            "gap_units": gaps,
            "reassignable_unit_ids": sorted(reassignable_ids),
            "clean": not unmapped and not gaps,
        }

    if task.action == "verify_candidate":
        candidate = SecurityFinding.from_dict(task.payload["candidate"])
        if candidate.discovery_provenance.agent_id == task.agent_id:
            raise ValueError(
                f"separation-of-duties violation: {task.agent_id!r} discovered candidate"
            )
        if (
            candidate.discovery_provenance.session_id is not None
            and candidate.discovery_provenance.session_id == session_id
        ):
            raise ValueError(f"session isolation violation: {session_id!r} discovered candidate")
        verifier = IndependentFindingVerifier(project_root, verifier_id=task.agent_id)
        verified = verifier.verify_candidate(
            candidate,
            run_id=task.audit_run_id,
            commit_sha=task.commit_sha,
        )
        if verified.verification_provenance is not None:
            verified.verification_provenance = dataclasses.replace(
                verified.verification_provenance,
                session_id=session_id,
                runtime_id=runtime_id,
                pid=my_pid,
            )
        return {
            "action": "verify_candidate",
            "session_id": session_id,
            "worker_pid": my_pid,
            "finding": verified.to_dict(),
        }

    if task.action == "verify_record":
        finding = SecurityFinding.from_dict(task.payload["finding"])
        prior_status = finding.verification_status
        disc_sess = finding.discovery_provenance.session_id
        ver_sess = (
            finding.verification_provenance.session_id
            if finding.verification_provenance is not None
            else None
        )
        if session_id in {disc_sess, ver_sess}:
            raise ValueError("Phase 5 record verifier session must be independent")
        verifier = IndependentFindingVerifier(project_root, verifier_id="record-stage-guard")
        checked = verifier.verify_record_integrity(
            finding,
            record_verifier_id=task.agent_id,
            run_id=task.audit_run_id,
            commit_sha=task.commit_sha,
        )
        if checked.verification_provenance is not None:
            orig_vp: VerificationProvenance = checked.verification_provenance
            checked.verification_provenance = dataclasses.replace(
                orig_vp,
                session_id=ver_sess or session_id,
                runtime_id=orig_vp.runtime_id or runtime_id,
                pid=orig_vp.pid or my_pid,
                record_verifier_id=task.agent_id,
                record_verifier_session_id=session_id,
            )
        return {
            "action": "verify_record",
            "session_id": session_id,
            "worker_pid": my_pid,
            "materially_changed": checked.verification_status != prior_status,
            "finding": checked.to_dict(),
        }

    raise ValueError(f"unsupported worker task action: {task.action!r}")


def run_worker_task_file(task_file: Path) -> int:
    """Load task envelope JSON, execute worker session, and write scratch output atomically."""
    envelope = json.loads(task_file.read_text(encoding="utf-8"))
    output_path = Path(str(envelope["output_path"]))
    result = execute_worker_envelope(envelope)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return 0


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    if len(args) != 1:
        print(
            "usage: python -m gencode_gov.security_audit.worker_entry <task.json>", file=sys.stderr
        )
        return 2
    try:
        return run_worker_task_file(Path(args[0]))
    except Exception as exc:
        print(f"[WORKER_ERROR] {exc}", file=sys.stderr)
        return 1
