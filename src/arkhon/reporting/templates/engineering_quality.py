"""Dependency-free rendering for standard engineering quality documents."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from arkhon.core.logging import get_logger

logger = get_logger("reporting.templates")
TEMPLATES = {
    "00-ENGINEERING-CHARTER": "# Engineering Charter\n\nCommit: `{commit_sha}`\n\nCharter version: 1.0\n",
    "01-REQUIREMENTS-AUDIT": "# Requirements Audit\n\nStatus: {status_requirements}\n\nEvidence: {evidence_requirements} artifact(s).\n",
    "02-ARCHITECTURE-REVIEW": "# Architecture Review\n\nStatus: {status_architecture}\n\nEvidence: {evidence_architecture} artifact(s).\n",
    "03-CODE-QUALITY-REPORT": "# Code Quality Report\n\nStatus: {status_code_quality}\n\nEvidence: {evidence_code_quality} artifact(s).\n",
    "04-TEST-COVERAGE-REPORT": "# Test Coverage Report\n\nStatus: {status_testing}\n\nEvidence: {evidence_testing} artifact(s).\n",
    "05-SECURITY-AUDIT": "# Security Audit (delegated to TSAR)\n\nStatus: {status_security}\n\nEvidence: {evidence_security} artifact(s).\n",
    "06-PERFORMANCE-REPORT": "# Performance Report\n\nStatus: {status_performance}\n\nEvidence: {evidence_performance} artifact(s).\n",
    "07-RELIABILITY-REPORT": "# Reliability Report\n\nStatus: {status_reliability}\n\nEvidence: {evidence_reliability} artifact(s).\n",
    "08-SCALABILITY-ASSESSMENT": "# Scalability Assessment\n\nStatus: {status_scalability}\n\nEvidence: {evidence_scalability} artifact(s).\n",
    "09-DEPENDENCY-SBOM-AUDIT": "# Dependency & SBOM Audit\n\nStatus: {status_dependencies}\n\nEvidence: {evidence_dependencies} artifact(s).\n",
    "10-DEPLOYMENT-VALIDATION": "# Deployment Validation\n\nStatus: {status_deployment}\n\nEvidence: {evidence_deployment} artifact(s).\n",
    "11-DISASTER-RECOVERY": "# Disaster Recovery\n\nStatus: {status_disaster_recovery}\n\nEvidence: {evidence_disaster_recovery} artifact(s).\n",
    "12-PRR-REPORT": "# Production Readiness Review\n\nStatus: {status_prr}\n\nEvidence: {evidence_prr} artifact(s).\n",
    "13-COMPLIANCE-ASSESSMENT": "# Compliance Assessment\n\nStatus: {status_compliance}\n\nEvidence: {evidence_compliance} artifact(s).\n",
    "14-RISK-REGISTER": "# Risk Register\n\nStatus: {status_risk_register}\n\nEvidence: {evidence_risk_register} artifact(s).\n",
    "FINAL-ENGINEERING-ACCEPTANCE": "# Final Engineering Acceptance\n\nDecision: **{final_decision}**\n\nCommit: `{commit_sha}`\n\nReport: `{report_id}`\n",
}


def _context_from_report(report: dict[str, Any]) -> dict[str, str]:
    sections = report.get("sections", {})
    ctx = {
        "commit_sha": report.get("commit_sha", ""),
        "report_id": report.get("report_id", ""),
        "final_decision": report.get("final_decision", "PENDING_EVIDENCE"),
    }
    for name, section in sections.items():
        ctx[f"status_{name}"] = section.get("status", "NOT_APPLICABLE")
        ctx[f"evidence_{name}"] = str(len(section.get("evidence_ids", [])))
    for key in (
        "requirements",
        "architecture",
        "code_quality",
        "testing",
        "security",
        "performance",
        "reliability",
        "scalability",
        "dependencies",
        "deployment",
        "disaster_recovery",
        "prr",
        "compliance",
        "risk_register",
    ):
        ctx.setdefault(f"status_{key}", "NOT_APPLICABLE")
        ctx.setdefault(f"evidence_{key}", "0")
    return ctx


@dataclass
class EngineeringQualityRenderer:
    """Renders the 16 engineering quality documents from a report."""

    def render_all(self, report: dict[str, Any]) -> dict[str, str]:
        ctx = _context_from_report(report)
        rendered = {}
        for name, template in TEMPLATES.items():
            try:
                rendered[name] = template.format(**ctx)
            except KeyError as exc:
                logger.warning("template %s missing key %s", name, exc)
                rendered[name] = template
        return rendered

    def write_all(self, report: dict[str, Any], output_dir: Path) -> list[Path]:
        output_dir.mkdir(parents=True, exist_ok=True)
        written = []
        for name, content in self.render_all(report).items():
            target = output_dir / f"{name}.md"
            target.write_text(content, encoding="utf-8")
            written.append(target)
        return written
