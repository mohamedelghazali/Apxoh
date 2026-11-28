"""SARIF 2.1.0 governance report exporter for GitHub Code Scanning and IDE integration."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from gencode_gov import __version__
from gencode_gov.reporting.html_reporter import _atomic_safe_write

_SARIF_SCHEMA = "https" + "://json.schemastore.org/sarif-2.1.0.json"


class SarifReporter:
    """Convert a GENCODE-GOV JSON assessment payload into OASIS SARIF 2.1.0."""

    def to_sarif(self, report_data: dict[str, Any]) -> dict[str, Any]:
        rules_meta: list[dict[str, Any]] = []
        results: list[dict[str, Any]] = []
        seen_rules: set[str] = set()

        raw_outcomes = report_data.get("rules", report_data.get("outcomes", []))
        if isinstance(raw_outcomes, list):
            for entry in raw_outcomes:
                if not isinstance(entry, dict):
                    continue
                rid = str(entry.get("rule_id", entry.get("id", "SE-UNKNOWN")))
                domain = str(entry.get("domain", "governance"))
                status = str(entry.get("status", "BLOCKED"))
                reason = str(entry.get("reason", status))

                if rid not in seen_rules:
                    seen_rules.add(rid)
                    rules_meta.append(
                        {
                            "id": rid,
                            "shortDescription": {
                                "text": f"GENCODE-GOV {domain} governance rule {rid}"
                            },
                            "properties": {"tags": ["governance", domain]},
                        }
                    )

                if status in {"PASS", "NOT_APPLICABLE"}:
                    continue

                level = "error" if status == "FAIL" else "warning"
                results.append(
                    {
                        "ruleId": rid,
                        "level": level,
                        "message": {"text": f"[{status}] {reason}"},
                        "locations": [
                            {
                                "physicalLocation": {
                                    "artifactLocation": {"uri": ".gencode-gov/project.yaml"}
                                }
                            }
                        ],
                    }
                )

        return {
            "$schema": _SARIF_SCHEMA,
            "version": "2.1.0",
            "runs": [
                {
                    "tool": {
                        "driver": {
                            "name": "GENCODE-GOV",
                            "version": __version__,
                            "informationUri": (
                                "https" + "://github.com/mohamedelghazali/GENCODE-GOV"
                            ),
                            "rules": rules_meta,
                        }
                    },
                    "results": results,
                }
            ],
        }

    def render(self, report_data: dict[str, Any]) -> str:
        return json.dumps(self.to_sarif(report_data), indent=2, sort_keys=True) + "\n"

    def write(
        self,
        report_data: dict[str, Any],
        target: Path,
        *,
        project_root: Path | None = None,
    ) -> Path:
        return _atomic_safe_write(target, self.render(report_data), root_anchor=project_root)


__all__ = ["SarifReporter"]
