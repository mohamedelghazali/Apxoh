"""Change-aware security reassessment across Git commits and prior audit runs."""

from __future__ import annotations

import json
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from gencode_gov.security_audit.coverage import (
    CoverageLedger,
    compare_coverage_ledgers,
)
from gencode_gov.security_audit.dispatcher import AuditRole, SecurityAuditTaskDispatcher
from gencode_gov.security_audit.findings import FindingsCollection, SecurityFinding
from gencode_gov.security_audit.hunting import (
    discover_architecture,
    execute_hunting_waves,
    seed_coverage_ledger,
    write_reconnaissance_artifacts,
)
from gencode_gov.security_audit.reporting import write_audit_reports
from gencode_gov.security_audit.sandbox import SandboxExecutor
from gencode_gov.security_audit.verifier import verify_findings_collection

_DEPENDENCY_FILES = frozenset(
    {
        "pyproject.toml",
        "requirements.txt",
        "package.json",
        "package-lock.json",
        "go.mod",
        "Cargo.toml",
    }
)


@dataclass(frozen=True)
class ReassessmentDelta:
    """Summary of coverage, remediation, regression, and new-finding deltas across commits."""

    prior_commit: str
    head_commit: str
    changed_files: tuple[str, ...]
    dependency_or_config_changed: bool
    new_finding_ids: tuple[str, ...]
    persisting_finding_ids: tuple[str, ...]
    remediated_finding_ids: tuple[str, ...]
    reopened_finding_ids: tuple[str, ...]
    coverage_delta: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "prior_commit": self.prior_commit,
            "head_commit": self.head_commit,
            "changed_files": list(self.changed_files),
            "dependency_or_config_changed": self.dependency_or_config_changed,
            "new_finding_ids": list(self.new_finding_ids),
            "persisting_finding_ids": list(self.persisting_finding_ids),
            "remediated_finding_ids": list(self.remediated_finding_ids),
            "reopened_finding_ids": list(self.reopened_finding_ids),
            "coverage_delta": self.coverage_delta,
        }


def compute_changed_files(
    project_root: Path,
    base_commit: str,
    head_commit: str,
) -> tuple[str, ...]:
    """Compute repository-relative changed files via git diff between two commits."""
    if base_commit == head_commit:
        return ()
    git_bin = shutil.which("git")
    if git_bin is None:
        raise RuntimeError("git executable required to compute commit diff")
    res = subprocess.run(  # noqa: S603 - fixed git diff command vector
        [git_bin, "diff", "--name-only", base_commit, head_commit],
        cwd=project_root,
        capture_output=True,
        text=True,
        check=True,
        timeout=15,
    )
    paths = [line.strip().replace("\\", "/") for line in res.stdout.splitlines() if line.strip()]
    return tuple(sorted(set(paths)))


def reassess_repository(
    *,
    project_root: Path,
    prior_dir: Path,
    output_dir: Path,
    audit_run_id: str,
    head_commit: str,
    base_commit: str | None = None,
) -> ReassessmentDelta:
    """Re-evaluate impacted coverage, carry unchanged evidence, and track finding states."""
    resolved_proj = project_root.resolve()
    prior_ledger = CoverageLedger.load(prior_dir / "coverage-ledger.json")
    prior_findings = FindingsCollection.load(prior_dir / "findings.json")
    effective_base = base_commit or prior_ledger.commit_sha

    changed_files = compute_changed_files(resolved_proj, effective_base, head_commit)
    changed_set = set(changed_files)
    dep_or_cfg_changed = any(
        Path(p).name in _DEPENDENCY_FILES
        or p.startswith((".github/workflows/", "system/policies/", ".gencode-gov/"))
        for p in changed_files
    )

    inventory = discover_architecture(resolved_proj, head_commit)
    new_ledger = seed_coverage_ledger(
        inventory,
        audit_run_id=audit_run_id,
        profile=prior_ledger.profile,
        execution_mode=prior_ledger.execution_mode,
        scope_paths=prior_ledger.scope_paths,
    )

    prior_units_by_id = {u.coverage_id: u for u in prior_ledger.units}
    prior_records_by_id = {r.finding_id: r for r in prior_findings.records}
    carried_unchanged_records: dict[str, SecurityFinding] = {}

    for unit in new_ledger.units:
        prev_unit = prior_units_by_id.get(unit.coverage_id)
        if prev_unit is None:
            unit.prior_status = "new"
            continue

        unit_touched = dep_or_cfg_changed or any(p in changed_set for p in unit.starting_paths)
        if unit_touched:
            unit.prior_status = (
                "prior_examined_changed_source"
                if prev_unit.status == "examined"
                else "prior_partially_examined"
            )
            unit.status = "planned"
        elif prev_unit.status == "examined":
            has_unresolved_prior = any(
                prior_records_by_id[fid].verification_status
                in {"needs_validation", "blocked", "not_verified"}
                for fid in prev_unit.finding_ids
                if fid in prior_records_by_id
            )
            if has_unresolved_prior:
                unit.prior_status = "prior_needs_validation"
                unit.status = "planned"
            else:
                unit.prior_status = "prior_examined_same_source"
                unit.status = "examined"
                unit.investigator_id = prev_unit.investigator_id
                unit.reviewed_paths = list(prev_unit.reviewed_paths)
                unit.checks = list(prev_unit.checks)
                unit.finding_ids = list(prev_unit.finding_ids)
                unit.candidate_fingerprints = list(prev_unit.candidate_fingerprints)
                unit.limitations = []
                for fid in prev_unit.finding_ids:
                    if fid in prior_records_by_id:
                        carried_rec = SecurityFinding.from_dict(prior_records_by_id[fid].to_dict())
                        carried_rec.commit_sha = head_commit
                        carried_rec.last_seen_commit = head_commit
                        carried_rec.last_seen_run = audit_run_id
                        carried_unchanged_records[carried_rec.fingerprint] = carried_rec
        else:
            unit.prior_status = "prior_not_examined"

    dispatcher = SecurityAuditTaskDispatcher(
        audit_dir=output_dir,
        execution_mode=new_ledger.execution_mode,
    )
    write_reconnaissance_artifacts(output_dir, inventory, new_ledger)
    sandbox = SandboxExecutor(output_dir)

    fresh_candidates = execute_hunting_waves(
        project_root=resolved_proj,
        ledger=new_ledger,
        dispatcher=dispatcher,
    )
    verified_fresh = verify_findings_collection(
        fresh_candidates,
        project_root=resolved_proj,
        verifier_id="independent-verifier-01",
        record_verifier_id="record-verifier-01",
        sandbox=sandbox,
    )

    # Reconcile prior findings against fresh run results (remediation & regression detection)
    dispatcher.assign(
        agent_id="remediation-verifier-01",
        role=AuditRole.REMEDIATION_VERIFIER,
        wave=1,
        targets=("prior-findings-reconciliation",),
    )
    fresh_by_fp = {r.fingerprint: r for r in verified_fresh.records}
    merged_by_fp: dict[str, SecurityFinding] = dict(carried_unchanged_records)

    new_ids: list[str] = []
    persisting_ids: list[str] = []
    remediated_ids: list[str] = []
    reopened_ids: list[str] = []

    prior_by_fp = {r.fingerprint: r for r in prior_findings.records}

    for fp, fresh_rec in fresh_by_fp.items():
        prior_rec = prior_by_fp.get(fp)
        if prior_rec is None:
            merged_by_fp[fp] = fresh_rec
            if fresh_rec.verification_status != "rejected":
                new_ids.append(fresh_rec.finding_id)
        else:
            fresh_rec.first_seen_run = prior_rec.first_seen_run
            fresh_rec.first_seen_commit = prior_rec.first_seen_commit
            fresh_rec.state_history = [*prior_rec.state_history, *fresh_rec.state_history[-1:]]
            if (
                prior_rec.lifecycle_state == "remediated"
                and fresh_rec.verification_status == "confirmed"
            ):
                reopened = SecurityFinding.from_dict(prior_rec.to_dict())
                reopened.transition_to(
                    "reopened",
                    run_id=audit_run_id,
                    commit_sha=head_commit,
                    actor="remediation-verifier-01",
                    reason="Previously remediated vulnerability reappeared in changed source.",
                )
                reopened.verification_status = "confirmed"
                reopened.severity = fresh_rec.severity
                reopened.root_cause = fresh_rec.root_cause
                reopened.remediation = fresh_rec.remediation
                reopened.verification_provenance = fresh_rec.verification_provenance
                merged_by_fp[fp] = reopened
                reopened_ids.append(reopened.finding_id)
            else:
                merged_by_fp[fp] = fresh_rec
                if fresh_rec.verification_status != "rejected":
                    persisting_ids.append(fresh_rec.finding_id)

    for fp, prior_rec in prior_by_fp.items():
        if fp in merged_by_fp:
            continue
        if prior_rec.verification_status in {"confirmed", "needs_validation"} and (
            prior_rec.lifecycle_state != "remediated"
        ):
            resolved_copy = SecurityFinding.from_dict(prior_rec.to_dict())
            resolved_copy.transition_to(
                "remediated",
                run_id=audit_run_id,
                commit_sha=head_commit,
                actor="remediation-verifier-01",
                reason="Impacted source re-examined on head commit; sink no longer present.",
            )
            merged_by_fp[fp] = resolved_copy
            remediated_ids.append(resolved_copy.finding_id)

    for _fp, carried in carried_unchanged_records.items():
        if carried.verification_status != "rejected" and carried.finding_id not in persisting_ids:
            persisting_ids.append(carried.finding_id)

    final_findings = FindingsCollection(
        audit_run_id=audit_run_id,
        commit_sha=head_commit,
        records=list(merged_by_fp.values()),
    )
    final_findings.save(output_dir / "findings.json")
    new_ledger.save(output_dir / "coverage-ledger.json")
    write_audit_reports(
        audit_dir=output_dir,
        ledger=new_ledger,
        findings=final_findings,
        sandbox_caps=sandbox.capabilities,
        fmt="all",
    )

    cov_delta = compare_coverage_ledgers(prior_ledger, new_ledger)
    delta = ReassessmentDelta(
        prior_commit=effective_base,
        head_commit=head_commit,
        changed_files=changed_files,
        dependency_or_config_changed=dep_or_cfg_changed,
        new_finding_ids=tuple(sorted(new_ids)),
        persisting_finding_ids=tuple(sorted(persisting_ids)),
        remediated_finding_ids=tuple(sorted(remediated_ids)),
        reopened_finding_ids=tuple(sorted(reopened_ids)),
        coverage_delta=cov_delta,
    )
    (output_dir / "reassessment-delta.json").write_text(
        json.dumps(delta.to_dict(), indent=2) + "\n", encoding="utf-8"
    )
    md_lines = [
        f"# Security Reassessment Report ({effective_base[:12]} -> {head_commit[:12]})",
        "",
        f"- **Changed Files**: `{len(changed_files)}`",
        f"- **Dependency / Config Touched**: `{dep_or_cfg_changed}`",
        f"- **New Findings**: `{len(delta.new_finding_ids)}`",
        f"- **Persisting Findings**: `{len(delta.persisting_finding_ids)}`",
        f"- **Verified Remediated**: `{len(delta.remediated_finding_ids)}`",
        f"- **Reopened Regressions**: `{len(delta.reopened_finding_ids)}`",
        "",
    ]
    (output_dir / "REASSESSMENT-REPORT.md").write_text("\n".join(md_lines), encoding="utf-8")
    return delta
