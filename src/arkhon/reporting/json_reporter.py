"""JSON report generator."""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from arkhon.core.errors import EvidenceError
from arkhon.core.logging import get_logger
from arkhon.evidence.store import EvidenceStore

logger = get_logger("reporting.json")

SECTION_MAP = {
    "requirements": "requirements",
    "architecture": "architecture",
    "code-quality": "code_quality",
    "testing": "testing",
    "software-security": "security",
    "performance": "performance",
    "reliability": "reliability",
    "scalability": "scalability",
    "infrastructure": "deployment",
    "database": "dependencies",
    "release": "final_acceptance",
}


@dataclass
class JsonReporter:
    """Writes a JSON report aggregating all evidence."""

    def build(self, project_root: Path) -> dict[str, Any]:
        store = EvidenceStore(project_root)
        records = list(store.iter_records())
        if not records:
            raise EvidenceError(f"no evidence found under {store.root}")
        commit_sha = records[0].data.get("commit_sha", "")
        if not isinstance(commit_sha, str) or len(commit_sha) != 40:
            raise EvidenceError("evidence missing valid commit_sha")

        # Construct each section independently; sharing the evidence_ids list
        # would leak IDs across unrelated domains.
        sections: dict[str, dict[str, Any]] = {
            name: {"status": "NOT_APPLICABLE", "content": "", "evidence_ids": []}
            for name in SECTION_MAP.values()
        }
        for record in records:
            section_name = SECTION_MAP.get(record.path.parent.name)
            if not section_name:
                continue
            status = record.data.get("status", "NOT_APPLICABLE")
            section = sections[section_name]
            section["evidence_ids"] = [*section["evidence_ids"], record.evidence_id]
            if status == "FAIL":
                section["status"] = "FAIL"
            elif status == "BLOCKED" and section["status"] != "FAIL":
                section["status"] = "BLOCKED"
            elif status == "PASS" and section["status"] == "NOT_APPLICABLE":
                section["status"] = "PASS"

        statuses = {section["status"] for section in sections.values()}
        if "FAIL" in statuses:
            final = "REJECTED"
        elif "BLOCKED" in statuses:
            final = "PENDING_EVIDENCE"
        else:
            final = "APPROVED"
        now = datetime.now(timezone.utc)
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
