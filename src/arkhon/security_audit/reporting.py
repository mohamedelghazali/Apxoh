"""Target-neutral machine-readable and Markdown security audit reporting (Phase 6)."""

from __future__ import annotations

import json
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from arkhon.security_audit.coverage import CoverageLedger
from arkhon.security_audit.findings import FindingsCollection, SecurityFinding
from arkhon.security_audit.sandbox import SandboxCapabilities

REPORT_SCHEMA_VERSION = "1.0.0"


def compute_governance_gate_status(
    ledger: CoverageLedger,
    findings: FindingsCollection,
) -> str:
    """Derive fail-closed GENCODE-GOV gate status; NEVER convert unverified/partial into PASS."""
    for rec in findings.records:
        if (
            rec.verification_status == "confirmed"
            and rec.lifecycle_state != "remediated"
            and rec.severity is not None
            and rec.severity.overall_severity in {"critical", "high"}
        ):
            return "FAIL"

    comp = ledger.compute_completeness()
    if comp["total_units"] == 0 or (
        comp["examined"] == 0 and comp["not_applicable"] == comp["total_units"]
    ):
        return "NOT_APPLICABLE"

    has_unresolved = any(
        rec.verification_status in {"needs_validation", "blocked", "not_verified"}
        and rec.lifecycle_state != "remediated"
        for rec in findings.records
    )
    if ledger.audit_status != "completed" or not comp["is_complete"] or has_unresolved:
        return "BLOCKED"
    return "PASS"


def build_security_audit_report(
    *,
    ledger: CoverageLedger,
    findings: FindingsCollection,
    sandbox_caps: SandboxCapabilities,
    hardening_notes: list[str] | None = None,
) -> dict[str, Any]:
    """Construct schema-compliant machine-readable security audit report."""
    comp = ledger.compute_completeness()
    confirmed_out: list[dict[str, Any]] = []
    needs_val_out: list[dict[str, Any]] = []
    blocked_items: list[str] = []
    not_verified_items: list[str] = []
    rejected_count = 0
    remediated_count = 0
    reopened_count = 0

    for rec in findings.records:
        if rec.lifecycle_state == "remediated":
            remediated_count += 1
            continue
        if rec.lifecycle_state == "reopened":
            reopened_count += 1

        loc = rec.affected_locations[0]
        loc_str = f"{loc.file}:{loc.line}"
        if rec.verification_status == "confirmed" and rec.severity and rec.remediation:
            confirmed_out.append(
                {
                    "finding_id": rec.finding_id,
                    "fingerprint": rec.fingerprint,
                    "title": rec.title,
                    "severity": rec.severity.overall_severity,
                    "component": rec.component,
                    "attack_class": rec.attack_class,
                    "trust_boundary": rec.trust_boundary,
                    "primary_location": loc_str,
                    "remediation_strategy": rec.remediation.strategy,
                    "related_rules": list(rec.related_rules),
                }
            )
        elif rec.verification_status == "needs_validation":
            needs_val_out.append(
                {
                    "finding_id": rec.finding_id,
                    "fingerprint": rec.fingerprint,
                    "title": rec.title,
                    "component": rec.component,
                    "attack_class": rec.attack_class,
                    "primary_location": loc_str,
                    "unresolved_blockers": list(rec.unresolved_blockers),
                    "validation_plan": dict(rec.validation_plan or {}),
                }
            )
        elif rec.verification_status == "blocked":
            reason = "; ".join(rec.unresolved_blockers) or "sandbox or verification blocked"
            blocked_items.append(f"{rec.finding_id} ({loc_str}): {reason}")
        elif rec.verification_status == "not_verified":
            not_verified_items.append(f"{rec.finding_id} ({loc_str}): candidate not yet verified")
        elif rec.verification_status == "rejected":
            rejected_count += 1

    limitations: list[str] = []
    if ledger.execution_mode == "single_process_deterministic":
        limitations.append(
            "Executed in single_process_deterministic role isolation rather than separate "
            "external multi-agent processes."
        )
    if not sandbox_caps.can_enforce_full_sandbox:
        limitations.append(
            "Host OS network-namespace sandbox unavailable; dynamic checks fail closed to BLOCKED."
        )
    for gap in ledger.detect_gaps():
        limitations.append(f"Coverage gap [{gap['status']}] {gap['coverage_id']}: {gap['reason']}")

    run_suffix = ledger.audit_run_id.removeprefix("AUDIT-")
    orch_summary: dict[str, Any] | None = None
    if ledger.orchestration is not None:
        orch_summary = {
            k: v
            for k, v in ledger.orchestration.items()
            if k != "sessions"
        }
    report_payload: dict[str, Any] = {
        "schema_version": REPORT_SCHEMA_VERSION,
        "report_id": f"SEC-REP-{run_suffix}",
        "audit_run_id": ledger.audit_run_id,
        "project": ledger.project,
        "commit_sha": ledger.commit_sha,
        "generated_at": datetime.now(UTC).isoformat(),
        "profile": ledger.profile,
        "audit_status": ledger.audit_status,
        "execution_mode": ledger.execution_mode,
        "sandbox_summary": {
            "network_isolated": sandbox_caps.can_enforce_full_sandbox,
            "backend": sandbox_caps.network_isolated_backend,
            "details": (
                f"OS sandbox backend: {sandbox_caps.network_isolated_backend} "
                f"(O_NOFOLLOW={sandbox_caps.has_o_nofollow}, rlimits={sandbox_caps.has_rlimits})"
            ),
        },
        "coverage_summary": comp,
        "confirmed_findings": confirmed_out,
        "needs_validation_leads": needs_val_out,
        "blocked_items": blocked_items,
        "not_verified_items": not_verified_items,
        "rejected_count": rejected_count,
        "remediated_count": remediated_count,
        "reopened_count": reopened_count,
        "hardening_notes": list(hardening_notes or []),
        "limitations": limitations,
        "governance_gate_status": compute_governance_gate_status(ledger, findings),
    }
    if orch_summary is not None:
        report_payload["orchestration_summary"] = orch_summary
    return report_payload


def render_markdown_audit_report(report: dict[str, Any]) -> str:
    """Render target-neutral executive and technical Markdown report."""
    comp = report["coverage_summary"]
    lines = [
        f"# Security Audit Report — {report['project']}",
        "",
        "## 1. Run Scope, Execution Posture, and Governance Gate",
        "",
        f"- **Report ID**: `{report['report_id']}`",
        f"- **Audit Run ID**: `{report['audit_run_id']}`",
        f"- **Commit SHA**: `{report['commit_sha']}`",
        f"- **Profile**: `{report['profile']}`",
        f"- **Audit Status**: `{report['audit_status']}`",
        f"- **Execution Mode**: `{report['execution_mode']}`",
        *(
            [
                f"- **Multi-Agent Runtime**: "
                f"`{report['orchestration_summary']['runtime_id']}` "
                f"(sessions={report['orchestration_summary']['session_count']}, "
                f"distinct_pids={report['orchestration_summary']['distinct_pids']})"
            ]
            if report.get("orchestration_summary")
            else []
        ),
        f"- **Sandbox Posture**: `{report['sandbox_summary']['details']}`",
        f"- **Governance Gate Verdict**: `{report['governance_gate_status']}`",
        "",
        "## 2. Executive Posture Summary",
        "",
        f"- **Confirmed Findings**: `{len(report['confirmed_findings'])}`",
        f"- **Needs Validation (No Severity Assigned)**: `{len(report['needs_validation_leads'])}`",
        f"- **Blocked Items**: `{len(report['blocked_items'])}`",
        f"- **Unverified Candidates**: `{len(report['not_verified_items'])}`",
        f"- **Disproved / Rejected Hypotheses**: `{report['rejected_count']}`",
        f"- **Remediated Findings**: `{report['remediated_count']}`",
        "",
        "## 3. Confirmed Security Findings",
        "",
    ]
    if report["confirmed_findings"]:
        lines.extend(
            [
                "| ID | Severity | Title | Component | Location | Rules |",
                "| :--- | :--- | :--- | :--- | :--- | :--- |",
            ]
        )
        for item in report["confirmed_findings"]:
            rules_str = ", ".join(item["related_rules"])
            lines.append(
                f"| `{item['finding_id']}` | **{item['severity'].upper()}** | {item['title']} "
                f"| `{item['component']}` | `{item['primary_location']}` | {rules_str} |"
            )
    else:
        lines.append("No confirmed findings recorded in this run.")

    lines.extend(["", "## 4. Leads Requiring Owner or Local Validation (Unscored)", ""])
    if report["needs_validation_leads"]:
        lines.extend(
            [
                "| ID | Title | Location | Unresolved Blocker |",
                "| :--- | :--- | :--- | :--- |",
            ]
        )
        for lead in report["needs_validation_leads"]:
            blocker_text = "; ".join(lead["unresolved_blockers"])
            lines.append(
                f"| `{lead['finding_id']}` | {lead['title']} "
                f"| `{lead['primary_location']}` | {blocker_text} |"
            )
    else:
        lines.append("No unresolved validation leads.")

    lines.extend(
        [
            "",
            "## 5. Coverage Summary",
            "",
            "| Metric | Count |",
            "| :--- | ---: |",
            f"| Total Units | {comp['total_units']} |",
            f"| Examined | {comp['examined']} |",
            f"| Partially Examined | {comp['partially_examined']} |",
            f"| Planned (Unexamined) | {comp['planned']} |",
            f"| Not Examined (Scoped/Deferred) | {comp['not_examined']} |",
            f"| Blocked | {comp['blocked']} |",
            f"| Not Applicable | {comp['not_applicable']} |",
            f"| Complete Coverage | `{comp['is_complete']}` |",
            "",
            "## 6. Limitations and Residual Scope",
            "",
        ]
    )
    if report["limitations"]:
        for lim in report["limitations"]:
            lines.append(f"- {lim}")
    else:
        lines.append("- All seeded in-scope coverage units were examined without blockers.")
    return "\n".join(lines) + "\n"


def render_findings_detail_markdown(findings: FindingsCollection) -> str:
    """Render technical source-trace and remediation details for confirmed findings."""
    confirmed: list[SecurityFinding] = [
        r
        for r in findings.records
        if r.verification_status == "confirmed" and r.lifecycle_state != "remediated"
    ]
    lines = ["# Confirmed Security Findings — Technical Detail", ""]
    if not confirmed:
        lines.append("No active confirmed findings.")
        return "\n".join(lines) + "\n"

    for rec in confirmed:
        sev = rec.severity.overall_severity.upper() if rec.severity else "UNKNOWN"
        lines.extend(
            [
                f"## {rec.finding_id} — {rec.title} ({sev})",
                "",
                f"- **Fingerprint**: `{rec.fingerprint}`",
                f"- **Attack Class**: `{rec.attack_class}`",
                f"- **Trust Boundary**: `{rec.trust_boundary}`",
                f"- **Root Cause**: {rec.root_cause}",
                f"- **Security Impact**: {rec.security_impact}",
                f"- **Remediation**: {rec.remediation.strategy if rec.remediation else ''}",
                "",
            ]
        )
    return "\n".join(lines)


def render_needs_validation_markdown(findings: FindingsCollection) -> str:
    """Render target-neutral validation plans for unresolved leads (zero live probes)."""
    leads = [
        r
        for r in findings.records
        if r.verification_status in {"needs_validation", "blocked"}
        and r.lifecycle_state != "remediated"
    ]
    lines = ["# Security Leads Needing Validation", ""]
    if not leads:
        lines.append("No leads currently awaiting validation.")
        return "\n".join(lines) + "\n"

    for rec in leads:
        lines.extend(
            [
                f"## {rec.finding_id} — {rec.title}",
                "",
                f"- **Fingerprint**: `{rec.fingerprint}`",
                f"- **Claimed Hypothesis**: {rec.claimed_root_cause}",
                f"- **Blockers**: {'; '.join(rec.unresolved_blockers)}",
                f"- **Safe Validation Plan**: `{json.dumps(rec.validation_plan or {})}`",
                "",
            ]
        )
    return "\n".join(lines)


def _atomic_write(path: Path, content: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        dir=path.parent,
        prefix=f".{path.stem}-",
        suffix=".tmp",
        delete=False,
    ) as handle:
        handle.write(content)
        tmp = Path(handle.name)
    tmp.replace(path)
    return path


def write_audit_reports(
    *,
    audit_dir: Path,
    ledger: CoverageLedger,
    findings: FindingsCollection,
    sandbox_caps: SandboxCapabilities,
    fmt: str = "all",
) -> dict[str, Path]:
    """Write machine-readable JSON and/or target-neutral Markdown reports."""
    report_dict = build_security_audit_report(
        ledger=ledger,
        findings=findings,
        sandbox_caps=sandbox_caps,
    )
    written: dict[str, Path] = {}
    if fmt in {"all", "json"}:
        json_path = audit_dir / "security-audit-report.json"
        _atomic_write(json_path, json.dumps(report_dict, indent=2) + "\n")
        written["json"] = json_path
    if fmt in {"all", "markdown"}:
        md_path = audit_dir / "SECURITY-AUDIT-REPORT.md"
        detail_path = audit_dir / "FINDINGS-DETAIL.md"
        nv_path = audit_dir / "NEEDS-VALIDATION.md"
        _atomic_write(md_path, render_markdown_audit_report(report_dict))
        _atomic_write(detail_path, render_findings_detail_markdown(findings))
        _atomic_write(nv_path, render_needs_validation_markdown(findings))
        written["markdown"] = md_path
        written["findings_detail"] = detail_path
        written["needs_validation"] = nv_path
    return written
