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
from arkhon.evidence.supply_chain import (
    verify_cyclonedx_sbom,
    verify_supply_chain_attestation_report,
)

logger = get_logger("reporting.json")

SECTION_MAP = {
    "charter": "charter",
    "requirements": "requirements",
    "architecture": "architecture",
    "code-quality": "code_quality",
    "testing": "testing",
    "software-security": "security",
    "supply-chain": "supply_chain",
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
    "supply-chain": 168,
}
_ALLOWED_STATUSES = {"PASS", "FAIL", "BLOCKED", "NOT_APPLICABLE", "ACCEPTED_RISK"}


def _record_timestamp(record: Any) -> datetime:
    value = record.data.get("executed_at")
    if not isinstance(value, str):
        raise EvidenceError(f"evidence {record.evidence_id} has invalid executed_at")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise EvidenceError(f"evidence {record.evidence_id} has invalid executed_at") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise EvidenceError(f"evidence {record.evidence_id} executed_at must include a timezone")
    return parsed.astimezone(UTC)


@dataclass
class JsonReporter:
    """Writes a JSON report aggregating all evidence."""

    def build(self, project_root: Path, expected_commit_sha: str | None = None) -> dict[str, Any]:
        store = EvidenceStore(project_root)
        all_records = list(store.iter_records())
        if not all_records:
            raise EvidenceError(f"no evidence found under {store.root}")
        for record in all_records:
            record_commit = record.data.get("commit_sha")
            if not isinstance(record_commit, str) or not re.fullmatch(
                r"[0-9a-f]{40}", record_commit
            ):
                raise EvidenceError(f"evidence {record.evidence_id} has invalid commit_sha")

        if expected_commit_sha is not None:
            if not re.fullmatch(r"[0-9a-f]{40}", expected_commit_sha):
                raise EvidenceError("expected commit_sha is invalid")
            commit_sha = expected_commit_sha
        else:
            latest_record = max(all_records, key=_record_timestamp)
            commit_sha = latest_record.data["commit_sha"]
        records = [record for record in all_records if record.data["commit_sha"] == commit_sha]
        if not records:
            raise EvidenceError(f"no evidence found for commit {commit_sha}")

        # Records were selected by the exact commit SHA above; validate their status
        # and integrity before trusting them in an assessment.
        for record in records:
            status = record.data.get("status")
            if not isinstance(status, str) or status not in _ALLOWED_STATUSES:
                raise EvidenceError(f"evidence {record.evidence_id} has invalid status: {status!r}")
            try:
                verify_bundle(
                    record.path,
                    evidence_root=project_root,
                    expected_commit_sha=commit_sha,
                )
                if record.path.parent.name == "supply-chain" and status == "PASS":
                    evidence_artifacts = record.data.get("artifacts")
                    if not isinstance(evidence_artifacts, list):
                        raise EvidenceError("supply-chain evidence artifacts must be an array")
                    sbom_paths = [
                        project_root / item["path"]
                        for item in evidence_artifacts
                        if isinstance(item, dict)
                        and isinstance(item.get("path"), str)
                        and item["path"].endswith(".cdx.json")
                    ]
                    attestation_paths = [
                        project_root / item["path"]
                        for item in evidence_artifacts
                        if isinstance(item, dict)
                        and isinstance(item.get("path"), str)
                        and item["path"].endswith(".attestation.json")
                    ]
                    if len(sbom_paths) != 1 or len(attestation_paths) != 1:
                        raise EvidenceError(
                            "PASS supply-chain evidence requires exactly one SBOM "
                            "and attestation report"
                        )
                    verify_cyclonedx_sbom(sbom_paths[0], expected_commit_sha=commit_sha)
                    verify_supply_chain_attestation_report(
                        attestation_paths[0],
                        evidence_root=project_root,
                        expected_commit_sha=commit_sha,
                        evidence_artifacts=evidence_artifacts,
                    )
                executed_at = _record_timestamp(record)
                verify_freshness(
                    executed_at.isoformat(),
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

    def write(
        self,
        project_root: Path,
        output_dir: Path,
        expected_commit_sha: str | None = None,
    ) -> Path:
        report = self.build(project_root, expected_commit_sha=expected_commit_sha)
        output_dir.mkdir(parents=True, exist_ok=True)
        target = output_dir / "report.json"
        target.write_text(json.dumps(report, indent=2), encoding="utf-8")
        return target
