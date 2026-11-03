"""JSON report generator."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from arkhon.core.errors import EvidenceError
from arkhon.core.logging import get_logger
from arkhon.evidence.integrity import verify_bundle, verify_freshness
from arkhon.evidence.store import EvidenceStore

logger = get_logger("reporting.json")

SECTION_MAP = {
    "charter": "charter",
    "requirements": "requirements",
    "architecture": "architecture",
    "code-quality": "code_quality",
    "testing": "testing",
    "software-security": "security",
    "performance": "performance",
    "reliability": "reliability",
    "observability": "reliability",
    "scalability": "scalability",
    "database": "dependencies",
    "api-integration": "dependencies",
    "infrastructure": "deployment",
    "devops": "deployment",
    "disaster-recovery": "disaster_recovery",
    "prr": "prr",
    "compliance": "compliance",
    "privacy-compliance": "compliance",
    "risk-register": "risk_register",
    "release": "final_acceptance",
    "maintenance": "final_acceptance",
}
FRESHNESS_HOURS = {
    "software-security": 168,
    "security": 168,
    "database": 168,
    "dependencies": 168,
    "testing": 720,
}
_ALLOWED_STATUSES = {"PASS", "FAIL", "BLOCKED", "NOT_APPLICABLE", "ACCEPTED_RISK"}


@dataclass
class JsonReporter:
    """Writes a JSON report aggregating all evidence."""

    def build(self, project_root: Path) -> dict[str, Any]:
        store = EvidenceStore(project_root)
        records = list(store.iter_records())
        if not records:
            raise EvidenceError(f"no evidence found under {store.root}")
        commit_sha = records[0].data.get("commit_sha", "")
        if not isinstance(commit_sha, str) or not re.fullmatch(r"[0-9a-f]{40}", commit_sha):
            raise EvidenceError("evidence missing valid commit_sha")

        # Validate every record before trusting its status in an assessment.
        for record in records:
            record_commit = record.data.get("commit_sha")
            if not isinstance(record_commit, str) or not re.fullmatch(
                r"[0-9a-f]{40}", record_commit
            ):
                raise EvidenceError(f"evidence {record.evidence_id} has invalid commit_sha")
            if record_commit != commit_sha:
                raise EvidenceError(
                    f"evidence commit mismatch: {record.evidence_id} is for {record_commit}, "
                    f"report is for {commit_sha}"
                )
            status = record.data.get("status")
            if status not in _ALLOWED_STATUSES:
                raise EvidenceError(f"evidence {record.evidence_id} has invalid status: {status!r}")
            try:
                verify_bundle(
                    record.path,
                    evidence_root=project_root,
                    expected_commit_sha=commit_sha,
                )
                verify_freshness(
                    record.data.get("executed_at"),
                    max_age_hours=FRESHNESS_HOURS.get(record.path.parent.name, 720),
                )
            except EvidenceError as exc:
                raise EvidenceError(
                    f"evidence verification failed for {record.evidence_id}: {exc}"
                ) from exc

        # Unassessed sections start as NOT_APPLICABLE while records are folded;
        # after aggregation, sections with no record become BLOCKED, never PASS.
        sections: dict[str, dict[str, Any]] = {
            name: {"status": "NOT_APPLICABLE", "content": "", "evidence_ids": []}
            for name in set(SECTION_MAP.values())
        }
        for record in records:
            section_name = SECTION_MAP.get(record.path.parent.name)
            if not section_name:
                continue
            status = record.data["status"]
            if status == "ACCEPTED_RISK":
                status = "BLOCKED"
            section = sections[section_name]
            section["evidence_ids"] = [*section["evidence_ids"], record.evidence_id]
            if status == "FAIL":
                section["status"] = "FAIL"
            elif status == "BLOCKED" and section["status"] != "FAIL":
                section["status"] = "BLOCKED"
            elif status == "PASS" and section["status"] not in {"FAIL", "BLOCKED"}:
                section["status"] = "PASS"

        for section in sections.values():
            if not section["evidence_ids"]:
                section["status"] = "BLOCKED"

        statuses = {section["status"] for section in sections.values()}
        if "FAIL" in statuses:
            final = "REJECTED"
        elif "BLOCKED" in statuses:
            final = "PENDING_EVIDENCE"
        else:
            final = "APPROVED"
        now = datetime.now(UTC)
        report = {
            "report_id": f"REP-{now.strftime('%Y%m%d%H%M%S')}",
            "project": project_root.name,
            "commit_sha": commit_sha,
            "generated_at": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "apxoh_version": "0.1.0.dev1",
            "sections": sections,
            "final_decision": final,
        }
        logger.debug("built report with %d evidence records", len(records))
        return report

    def write(self, project_root: Path, output_dir: Path) -> Path:
        report = self.build(project_root)
        output_dir.mkdir(parents=True, exist_ok=True)
        target = output_dir / "report.json"
        target.write_text(json.dumps(report, indent=2), encoding="utf-8")
        return target
