"""CLI subcommand dispatcher for Apxoh Security Audit operations."""

from __future__ import annotations

import argparse
import json
import sys
import uuid
from pathlib import Path
from typing import Any

from arkhon.core.constants import STATUS_NOT_APPLICABLE, STATUS_PASS
from arkhon.orchestrator.task_dispatcher import SecurityAuditTaskDispatcher
from arkhon.security_audit.coverage import CoverageLedger, compare_coverage_ledgers
from arkhon.security_audit.findings import FindingsCollection
from arkhon.security_audit.governance_bridge import (
    record_security_audit_evidence,
    summarize_audit_status,
)
from arkhon.security_audit.hunting import (
    discover_architecture,
    execute_hunting_waves,
    seed_coverage_ledger,
    write_reconnaissance_artifacts,
)
from arkhon.security_audit.reassessment import reassess_repository
from arkhon.security_audit.reporting import (
    compute_governance_gate_status,
    write_audit_reports,
)
from arkhon.security_audit.sandbox import (
    SandboxCapabilities,
    SandboxExecutor,
    probe_sandbox_capabilities,
)
from arkhon.security_audit.validators import validate_audit_directory
from arkhon.security_audit.verifier import verify_findings_collection

SECURITY_AUDIT_ACTIONS = frozenset(
    {
        "plan",
        "run",
        "status",
        "coverage",
        "verify-findings",
        "validate",
        "report",
        "compare",
        "reassess",
    }
)


def _default_output_dir(project: Path, run_id: str) -> Path:
    return (Path.home() / ".arkhon-security-audits" / project.name / run_id).resolve()


def _resolve_output_dir(args: argparse.Namespace, project: Path, run_id: str) -> Path:
    raw = getattr(args, "output_dir", None)
    return Path(raw).resolve() if raw else _default_output_dir(project, run_id)


def _resolve_sandbox_caps(mode: str) -> SandboxCapabilities:
    if mode == "disabled":
        return SandboxCapabilities(
            posix=True,
            has_o_nofollow=True,
            has_dir_fd=True,
            has_rlimits=True,
            bwrap_path=None,
            unshare_net_available=False,
        )
    return probe_sandbox_capabilities()


def _emit(payload: dict[str, Any], as_json: bool, summary_line: str) -> None:
    if as_json:
        print(json.dumps(payload, indent=2))
    else:
        print(summary_line)


def dispatch_security_audit(
    action: str,
    args: argparse.Namespace,
    *,
    commit_resolver: Any,
) -> int:
    """Execute one security audit CLI subcommand while preserving exit-code discipline."""
    as_json = bool(getattr(args, "json", False))
    raw_project = getattr(args, "project_flag", None) or getattr(args, "audit_target", None) or "."
    project = Path(raw_project).resolve()

    if action in {"plan", "run", "reassess"}:
        if not project.is_dir():
            print(f"[FAIL] not a directory: {project}", file=sys.stderr)
            return 1
        commit_sha = commit_resolver(project)
        if commit_sha is None:
            return 1
    else:
        commit_sha = ""

    run_id = f"AUDIT-{commit_sha[:8]}-{uuid.uuid4().hex[:6]}" if commit_sha else ""

    if action == "plan":
        out_dir = _resolve_output_dir(args, project, run_id)
        inventory = discover_architecture(project, commit_sha)
        ledger = seed_coverage_ledger(
            inventory,
            audit_run_id=run_id,
            profile=getattr(args, "profile", "standard"),
            scope_paths=getattr(args, "scope", None),
        )
        write_reconnaissance_artifacts(out_dir, inventory, ledger)
        FindingsCollection(audit_run_id=run_id, commit_sha=commit_sha, records=[]).save(
            out_dir / "findings.json"
        )
        payload = {
            "action": "plan",
            "audit_run_id": run_id,
            "audit_dir": str(out_dir),
            "audit_status": ledger.audit_status,
            "completeness": ledger.compute_completeness(),
        }
        _emit(payload, as_json, f"[OK] security audit plan written to {out_dir}")
        return 0

    if action == "run":
        out_dir = _resolve_output_dir(args, project, run_id)
        sandbox_mode = getattr(args, "sandbox_mode", "auto")
        caps = _resolve_sandbox_caps(sandbox_mode)
        if sandbox_mode == "required" and not caps.can_enforce_full_sandbox:
            print(
                "[BLOCKED] OS network-isolated sandbox required (--sandbox-mode=required) "
                "but unavailable on this host",
                file=sys.stderr,
            )
            return 1

        inventory = discover_architecture(project, commit_sha)
        ledger = seed_coverage_ledger(
            inventory,
            audit_run_id=run_id,
            profile=getattr(args, "profile", "standard"),
            scope_paths=getattr(args, "scope", None),
        )
        write_reconnaissance_artifacts(out_dir, inventory, ledger)
        dispatcher = SecurityAuditTaskDispatcher(audit_dir=out_dir)
        sandbox = SandboxExecutor(out_dir, capabilities=caps)
        candidates = execute_hunting_waves(
            project_root=project,
            ledger=ledger,
            dispatcher=dispatcher,
            max_units=getattr(args, "max_units", None),
        )
        verified = verify_findings_collection(
            candidates,
            project_root=project,
            verifier_id=getattr(args, "verifier_id", "independent-verifier-01"),
            sandbox=sandbox,
        )
        verified.save(out_dir / "findings.json")
        ledger.save(out_dir / "coverage-ledger.json")
        write_audit_reports(
            audit_dir=out_dir,
            ledger=ledger,
            findings=verified,
            sandbox_caps=caps,
            fmt=getattr(args, "report_format", "all"),
        )
        val = validate_audit_directory(out_dir)
        if not val.ok:
            print(f"[FAIL] audit validation errors: {'; '.join(val.errors)}", file=sys.stderr)
            return 1

        evid_id: str | None = None
        if getattr(args, "record_evidence", False):
            evid_id, _, _ = record_security_audit_evidence(
                project_root=project,
                audit_dir=out_dir,
                commit_sha=commit_sha,
            )

        gate = compute_governance_gate_status(ledger, verified)
        payload = {
            "action": "run",
            "audit_run_id": run_id,
            "audit_dir": str(out_dir),
            "audit_status": ledger.audit_status,
            "governance_gate_status": gate,
            "evidence_id": evid_id,
            "completeness": ledger.compute_completeness(),
        }
        _emit(
            payload,
            as_json,
            f"[{gate}] security audit {run_id} written to {out_dir}",
        )
        return 0 if gate in {STATUS_PASS, STATUS_NOT_APPLICABLE} else 1

    if action in {"status", "coverage", "validate", "verify-findings", "report"}:
        raw_audit_dir = getattr(args, "audit_dir", None)
        if not raw_audit_dir:
            print(f"[FAIL] --audit-dir is required for 'arkhon audit {action}'", file=sys.stderr)
            return 1
        audit_dir = Path(raw_audit_dir).resolve()

        if action == "validate":
            val = validate_audit_directory(audit_dir)
            payload = {"valid": val.ok, "errors": list(val.errors)}
            _emit(
                payload,
                as_json,
                "[OK] audit artifacts valid"
                if val.ok
                else f"[FAIL] {len(val.errors)} error(s): {'; '.join(val.errors[:3])}",
            )
            return 0 if val.ok else 1

        if action in {"status", "coverage"}:
            summary = summarize_audit_status(audit_dir)
            if not summary["valid"]:
                print(
                    f"[FAIL] invalid audit directory: {'; '.join(summary['errors'])}",
                    file=sys.stderr,
                )
                return 1
            _emit(
                summary,
                as_json,
                f"[OK] {summary['audit_run_id']} status={summary['audit_status']} "
                f"examined={summary['completeness']['examined']}/"
                f"{summary['completeness']['total_units']}",
            )
            return 0

        if action == "verify-findings":
            if not project.is_dir():
                print(f"[FAIL] not a directory: {project}", file=sys.stderr)
                return 1
            findings = FindingsCollection.load(audit_dir / "findings.json")
            ledger = CoverageLedger.load(audit_dir / "coverage-ledger.json")
            sandbox = SandboxExecutor(audit_dir)
            verified = verify_findings_collection(
                findings,
                project_root=project,
                verifier_id=getattr(args, "verifier_id", "independent-verifier-01"),
                sandbox=sandbox,
            )
            verified.save(audit_dir / "findings.json")
            write_audit_reports(
                audit_dir=audit_dir,
                ledger=ledger,
                findings=verified,
                sandbox_caps=sandbox.capabilities,
            )
            val = validate_audit_directory(audit_dir)
            if not val.ok:
                print(f"[FAIL] post-verify validation failed: {val.errors}", file=sys.stderr)
                return 1
            _emit(
                {"action": "verify-findings", "audit_dir": str(audit_dir), "valid": True},
                as_json,
                f"[OK] verified findings in {audit_dir}",
            )
            return 0

        # action == "report"
        ledger = CoverageLedger.load(audit_dir / "coverage-ledger.json")
        findings = FindingsCollection.load(audit_dir / "findings.json")
        caps = probe_sandbox_capabilities()
        written = write_audit_reports(
            audit_dir=audit_dir,
            ledger=ledger,
            findings=findings,
            sandbox_caps=caps,
            fmt=getattr(args, "report_format", "all"),
        )
        _emit(
            {"action": "report", "files": {k: str(v) for k, v in written.items()}},
            as_json,
            f"[OK] security audit report(s) written to {audit_dir}",
        )
        return 0

    if action == "compare":
        prior_raw = getattr(args, "prior_dir", None)
        curr_raw = getattr(args, "current_dir", None)
        if not prior_raw or not curr_raw:
            print("[FAIL] --prior-dir and --current-dir are required", file=sys.stderr)
            return 1
        p_ledger = CoverageLedger.load(Path(prior_raw).resolve() / "coverage-ledger.json")
        c_ledger = CoverageLedger.load(Path(curr_raw).resolve() / "coverage-ledger.json")
        delta_cov = compare_coverage_ledgers(p_ledger, c_ledger)
        _emit(
            delta_cov,
            as_json,
            f"[OK] compared {p_ledger.audit_run_id} -> {c_ledger.audit_run_id}",
        )
        return 0

    # action == "reassess"
    prior_raw = getattr(args, "prior_dir", None)
    if not prior_raw:
        print("[FAIL] --prior-dir is required for 'arkhon audit reassess'", file=sys.stderr)
        return 1
    out_dir = _resolve_output_dir(args, project, run_id)
    head_sha = getattr(args, "head_commit", None) or commit_sha
    delta = reassess_repository(
        project_root=project,
        prior_dir=Path(prior_raw).resolve(),
        output_dir=out_dir,
        audit_run_id=run_id,
        head_commit=head_sha,
        base_commit=getattr(args, "base_commit", None),
    )
    if getattr(args, "record_evidence", False):
        record_security_audit_evidence(
            project_root=project,
            audit_dir=out_dir,
            commit_sha=head_sha,
        )
    _emit(
        delta.to_dict(),
        as_json,
        f"[OK] reassessment written to {out_dir} "
        f"(remediated={len(delta.remediated_finding_ids)}, "
        f"reopened={len(delta.reopened_finding_ids)})",
    )
    return 0
