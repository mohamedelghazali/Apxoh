"""Bridge connecting Security Audit runs to GENCODE-GOV EvidenceStore, Runner, and Gates."""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

from arkhon import __version__
from arkhon.core.constants import STATUS_BLOCKED, STATUS_FAIL, STATUS_NOT_APPLICABLE, STATUS_PASS
from arkhon.evidence.collector import EvidenceCollector
from arkhon.evidence.store import EvidenceStore
from arkhon.security_audit.coverage import CoverageLedger
from arkhon.security_audit.findings import FindingsCollection
from arkhon.security_audit.reporting import compute_governance_gate_status
from arkhon.security_audit.validators import validate_audit_directory
from arkhon.verification.runners.base import Runner, RunnerOutcome, RunnerResult


def record_security_audit_evidence(
    *,
    project_root: Path,
    audit_dir: Path,
    commit_sha: str,
) -> tuple[str, Path, str]:
    """Validate audit_dir, copy immutable artifacts into .arkhon/evidence, and write record."""
    resolved_project = project_root.resolve()
    validation = validate_audit_directory(audit_dir)
    if not validation.ok:
        raise ValueError(
            f"cannot record invalid security audit bundle: {'; '.join(validation.errors[:5])}"
        )

    ledger = CoverageLedger.load(audit_dir / "coverage-ledger.json")
    findings = FindingsCollection.load(audit_dir / "findings.json")
    gate_status = compute_governance_gate_status(ledger, findings)

    collector = EvidenceCollector(root=resolved_project)
    comp = ledger.compute_completeness()
    draft = collector.new_evidence(
        source="arkhon",
        source_version=__version__,
        commit_sha=commit_sha,
        status=gate_status,
    )
    evidence_id = draft.evidence_id
    artifact_stage = (
        resolved_project / ".arkhon" / "evidence" / "software-security" / "artifacts" / evidence_id
    )
    artifact_stage.mkdir(parents=True, exist_ok=True)

    for filename in ("coverage-ledger.json", "findings.json", "security-audit-report.json"):
        src = audit_dir / filename
        if src.is_file() and not src.is_symlink():
            dst = artifact_stage / filename
            shutil.copyfile(src, dst)
            draft.add_artifact(dst)

    draft.summary = {
        "examined_units": int(comp["examined"]),
        "total_units": int(comp["total_units"]),
        "confirmed_findings": sum(
            1
            for r in findings.records
            if r.verification_status == "confirmed" and r.lifecycle_state != "remediated"
        ),
        "needs_validation": sum(
            1
            for r in findings.records
            if r.verification_status == "needs_validation" and r.lifecycle_state != "remediated"
        ),
    }
    draft.rule_ids = sorted(derive_rule_outcomes_from_audit(ledger, findings).keys())
    draft.notes = f"security-audit run {ledger.audit_run_id} ({ledger.audit_status})"
    store = EvidenceStore(resolved_project)
    written_path = store.write("software-security", draft.to_evidence())
    return evidence_id, written_path, gate_status


def derive_rule_outcomes_from_audit(
    ledger: CoverageLedger,
    findings: FindingsCollection,
) -> dict[str, tuple[str, str]]:
    """Map verified security audit results onto related SE-* rule statuses."""
    gate_status = compute_governance_gate_status(ledger, findings)
    by_rule: dict[str, list[str]] = {}
    blocked_by_rule: dict[str, list[str]] = {}

    for rec in findings.records:
        if rec.lifecycle_state == "remediated":
            continue
        for rule_id in rec.related_rules:
            if rec.verification_status == "confirmed":
                by_rule.setdefault(rule_id, []).append(rec.finding_id)
            elif rec.verification_status in {"needs_validation", "blocked", "not_verified"}:
                blocked_by_rule.setdefault(rule_id, []).append(rec.finding_id)

    outcomes: dict[str, tuple[str, str]] = {}
    all_rules = sorted(set(by_rule) | set(blocked_by_rule))
    for rule_id in all_rules:
        if rule_id in by_rule:
            fids = ", ".join(by_rule[rule_id])
            outcomes[rule_id] = (STATUS_FAIL, f"Confirmed security finding(s): {fids}")
        else:
            fids = ", ".join(blocked_by_rule[rule_id])
            outcomes[rule_id] = (
                STATUS_BLOCKED,
                f"Unresolved security validation lead(s): {fids}",
            )

    if not outcomes and gate_status in {STATUS_PASS, STATUS_BLOCKED, STATUS_NOT_APPLICABLE}:
        outcomes["SE-SEC-003"] = (
            gate_status,
            f"Security audit status={ledger.audit_status} gate={gate_status}",
        )
    return outcomes


class SecurityAuditRunner(Runner):
    """Deterministic GENCODE-GOV VerificationEngine runner executing a full security audit."""

    name = "security-audit"

    def run(self, project_root: Path, artifact_dir: Path | None = None) -> RunnerResult:
        from arkhon.cli import _commit_sha
        from arkhon.security_audit.dispatcher import SecurityAuditTaskDispatcher
        from arkhon.security_audit.hunting import (
            discover_architecture,
            execute_hunting_waves,
            seed_coverage_ledger,
            write_reconnaissance_artifacts,
        )
        from arkhon.security_audit.reporting import write_audit_reports
        from arkhon.security_audit.sandbox import SandboxExecutor
        from arkhon.security_audit.verifier import verify_findings_collection

        resolved = project_root.resolve()
        commit_sha = _commit_sha(resolved)
        if commit_sha is None:
            return RunnerResult(
                runner=self.name,
                outcome=RunnerOutcome.BLOCKED,
                reason="project does not have a resolvable Git HEAD commit SHA",
                artifacts=[],
            )
        out_dir = (
            artifact_dir.resolve()
            if artifact_dir is not None
            else resolved / ".arkhon" / "security-audit" / "latest"
        )
        run_id = f"AUDIT-{commit_sha[:12]}"
        inventory = discover_architecture(resolved, commit_sha)
        ledger = seed_coverage_ledger(inventory, audit_run_id=run_id)
        write_reconnaissance_artifacts(out_dir, inventory, ledger)
        dispatcher = SecurityAuditTaskDispatcher(audit_dir=out_dir)
        sandbox = SandboxExecutor(out_dir)
        raw_findings = execute_hunting_waves(
            project_root=resolved,
            ledger=ledger,
            dispatcher=dispatcher,
        )
        verified = verify_findings_collection(
            raw_findings,
            project_root=resolved,
            sandbox=sandbox,
        )
        verified.save(out_dir / "findings.json")
        ledger.save(out_dir / "coverage-ledger.json")
        reports = write_audit_reports(
            audit_dir=out_dir,
            ledger=ledger,
            findings=verified,
            sandbox_caps=sandbox.capabilities,
            fmt="all",
        )
        val = validate_audit_directory(out_dir)
        if not val.ok:
            return RunnerResult(
                runner=self.name,
                outcome=RunnerOutcome.BLOCKED,
                reason=f"artifact validation failed: {'; '.join(val.errors[:3])}",
                artifacts=[],
            )
        gate_verdict = compute_governance_gate_status(ledger, verified)
        outcome_map = {
            STATUS_PASS: RunnerOutcome.PASS,
            STATUS_NOT_APPLICABLE: RunnerOutcome.PASS,
            STATUS_FAIL: RunnerOutcome.FAIL,
            STATUS_BLOCKED: RunnerOutcome.BLOCKED,
        }
        attached: list[Path] = [
            out_dir / "coverage-ledger.json",
            out_dir / "findings.json",
            reports["json"],
        ]
        return RunnerResult(
            runner=self.name,
            outcome=outcome_map[gate_verdict],
            reason=f"security audit completed with gate verdict {gate_verdict}",
            artifacts=attached,
        )


def evaluate_security_audit_method(result: RunnerResult) -> tuple[str, str]:
    """Evaluate security-audit-artifact-verification method from RunnerResult."""
    if result.outcome == RunnerOutcome.BLOCKED:
        return STATUS_BLOCKED, result.reason or "security-audit runner was blocked"
    report_paths = [
        Path(p) for p in result.artifacts if Path(p).name == "security-audit-report.json"
    ]
    if len(report_paths) != 1 or not report_paths[0].is_file():
        return STATUS_BLOCKED, "security-audit runner did not attach security-audit-report.json"
    audit_dir = report_paths[0].parent
    val = validate_audit_directory(audit_dir)
    if not val.ok:
        return STATUS_BLOCKED, f"invalid security-audit artifacts: {'; '.join(val.errors[:2])}"
    if result.outcome == RunnerOutcome.PASS:
        return STATUS_PASS, "Verified security-audit coverage ledger, findings, and report"
    return STATUS_FAIL, result.reason or "Confirmed high/critical security audit findings"


def summarize_audit_status(audit_dir: Path) -> dict[str, Any]:
    """Load and summarize an existing audit directory for CLI status/coverage commands."""
    val = validate_audit_directory(audit_dir)
    if not val.ok:
        return {"valid": False, "errors": list(val.errors)}
    ledger = CoverageLedger.load(audit_dir / "coverage-ledger.json")
    findings = FindingsCollection.load(audit_dir / "findings.json")
    return {
        "valid": True,
        "audit_run_id": ledger.audit_run_id,
        "project": ledger.project,
        "commit_sha": ledger.commit_sha,
        "profile": ledger.profile,
        "audit_status": ledger.audit_status,
        "execution_mode": ledger.execution_mode,
        "completeness": ledger.compute_completeness(),
        "gaps": ledger.detect_gaps(),
        "governance_gate_status": compute_governance_gate_status(ledger, findings),
        "finding_counts": {
            "confirmed": sum(
                1
                for r in findings.records
                if r.verification_status == "confirmed" and r.lifecycle_state != "remediated"
            ),
            "needs_validation": sum(
                1
                for r in findings.records
                if r.verification_status == "needs_validation"
                and r.lifecycle_state != "remediated"
            ),
            "blocked": sum(
                1
                for r in findings.records
                if r.verification_status == "blocked" and r.lifecycle_state != "remediated"
            ),
            "rejected": sum(1 for r in findings.records if r.verification_status == "rejected"),
            "remediated": sum(1 for r in findings.records if r.lifecycle_state == "remediated"),
        },
    }
