"""Modular CLI handlers for attest, diff-check, drift, polyglot inspect, and HTML/SARIF reports."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

from gencode_gov.assessment.drift import record_and_evaluate_drift
from gencode_gov.core.constants import STATUS_PASS
from gencode_gov.core.errors import ConfigError, EvidenceError, GovernanceError
from gencode_gov.evidence.attestation import create_human_attestation
from gencode_gov.language_support.detector import detect_languages
from gencode_gov.language_support.language_profile_loader import load_language_profile
from gencode_gov.language_support.tool_resolver import ToolStatus, resolve_tools
from gencode_gov.reporting.html_reporter import HtmlReporter
from gencode_gov.reporting.sarif_reporter import SarifReporter
from gencode_gov.verification.diff_governance import evaluate_diff_governance


def register_extended_subcommands(
    subparsers: Any,
    commit_resolver: Callable[[Path], str | None],
) -> None:
    """Register attest, diff-check, and drift subcommands on the main CLI parser."""
    attest_p = subparsers.add_parser(
        "attest",
        help="Record a commit-bound human engineering review attestation for hybrid rules",
    )
    attest_p.add_argument("project", nargs="?", default=".")
    attest_p.add_argument("--rule", dest="rules", action="append", required=True)
    attest_p.add_argument("--reviewer", required=True)
    attest_p.add_argument("--role", dest="approver_role", required=True)
    attest_p.add_argument("--rationale", required=True)
    attest_p.add_argument("--artifact", dest="artifacts", action="append", default=None)
    attest_p.add_argument("--expires-days", type=int, default=30)
    attest_p.add_argument("--commit", default=None)
    attest_p.add_argument("--json", action="store_true")
    attest_p.set_defaults(func=lambda args: cmd_attest(args, commit_resolver=commit_resolver))

    diff_p = subparsers.add_parser(
        "diff-check",
        help="Verify frozen APIs, JSON schema compatibility, protected files, and test deletions",
    )
    diff_p.add_argument("project", nargs="?", default=".")
    diff_p.add_argument("--base", dest="base_ref", default=None)
    diff_p.add_argument("--head", dest="head_ref", default="HEAD")
    diff_p.add_argument("--max-files", type=int, default=500)
    diff_p.add_argument("--allow-protected", action="store_true")
    diff_p.add_argument("--json", action="store_true")
    diff_p.set_defaults(func=cmd_diff_check)

    drift_p = subparsers.add_parser(
        "drift",
        help="Compute and record longitudinal structural and exception drift",
    )
    drift_p.add_argument("project", nargs="?", default=".")
    drift_p.add_argument("--no-persist", action="store_true")
    drift_p.add_argument("--json", action="store_true")
    drift_p.set_defaults(func=lambda args: cmd_drift(args, commit_resolver=commit_resolver))


def cmd_attest(
    args: argparse.Namespace,
    *,
    commit_resolver: Callable[[Path], str | None],
) -> int:
    project = Path(args.project).resolve()
    commit_sha = args.commit or commit_resolver(project)
    if commit_sha is None:
        print("[FAIL] could not resolve 40-char Git HEAD commit SHA", file=sys.stderr)
        return 1
    try:
        att = create_human_attestation(
            project,
            rule_ids=list(args.rules),
            reviewer=args.reviewer,
            approver_role=args.approver_role,
            commit_sha=commit_sha,
            rationale=args.rationale,
            artifact_paths=list(args.artifacts or []),
            expires_days=int(args.expires_days),
        )
    except EvidenceError as exc:
        print(f"[FAIL] {exc}", file=sys.stderr)
        return 1

    payload = {
        "attestation_id": att.attestation_id,
        "rule_ids": list(att.rule_ids),
        "reviewer": att.reviewer,
        "approver_role": att.approver_role,
        "commit_sha": att.commit_sha,
        "expires_at": att.expires_at,
        "path": str(att.path.relative_to(project)),
    }
    if getattr(args, "json", False):
        print(json.dumps(payload, indent=2))
    else:
        print(f"[OK] Recorded attestation {att.attestation_id} -> {payload['path']}")
    return 0


def cmd_diff_check(args: argparse.Namespace) -> int:
    project = Path(args.project).resolve()
    rep = evaluate_diff_governance(
        project,
        base_ref=args.base_ref,
        head_ref=args.head_ref,
        max_files=int(args.max_files),
        allow_protected=bool(args.allow_protected),
    )
    if getattr(args, "json", False):
        print(json.dumps(rep.to_dict(), indent=2))
    else:
        print(f"[{rep.status}] files_changed={rep.files_changed}")
        for rsn in rep.reasons:
            print(f"  - {rsn}")
    return 0 if rep.status == STATUS_PASS else 1


def cmd_drift(
    args: argparse.Namespace,
    *,
    commit_resolver: Callable[[Path], str | None],
) -> int:
    project = Path(args.project).resolve()
    sha = commit_resolver(project) or ("0" * 40)
    try:
        current, prior, warnings = record_and_evaluate_drift(
            project,
            sha,
            persist=not bool(args.no_persist),
        )
    except GovernanceError as exc:
        print(f"[FAIL] {exc}", file=sys.stderr)
        return 1

    out = {
        "current": current.to_dict(),
        "prior": prior.to_dict() if prior else None,
        "warnings": warnings,
    }
    if getattr(args, "json", False):
        print(json.dumps(out, indent=2))
    else:
        print(
            f"[OK] commit={sha[:12]} files={current.python_files} "
            f"max_cc={current.max_cyclomatic_complexity} edges={current.internal_import_edges} "
            f"deps={current.declared_dependencies}"
        )
        for w in warnings:
            print(f"  [WARN] {w}")
    return 0


def build_tools_matrix(project: Path, repo_root: Path) -> list[dict[str, Any]]:
    """Build language profile & resolved tool matrix for gencode-gov inspect --tools."""
    default_tools: dict[str, list[str]] = {
        "python": ["ruff", "mypy", "pytest"],
        "typescript": ["eslint", "tsc", "jest"],
        "javascript": ["eslint", "jest"],
        "go": ["go", "golangci-lint"],
        "rust": ["cargo", "clippy-driver"],
        "ruby": ["rubocop", "rspec"],
        "java": ["checkstyle"],
        "csharp": ["dotnet"],
        "cpp": ["cmake", "clang-tidy"],
    }
    detection = detect_languages(project)
    detected_ids = [item.definition.id for item in detection.detected] or ["python"]
    has_reg = (repo_root / "languages" / "registry.yaml").is_file()
    rows: list[dict[str, Any]] = []
    for lang in detected_ids:
        prof_loaded = False
        if has_reg:
            try:
                _ = load_language_profile(lang, repo_root)
                prof_loaded = True
            except ConfigError:  # pragma: no cover
                prof_loaded = False
        res = resolve_tools(lang, list(default_tools.get(lang, [])))
        resolved = [
            {
                "tool": tc.name,
                "available": tc.status == ToolStatus.AVAILABLE,
                "path": tc.path or None,
            }
            for tc in res.tools
        ]
        rows.append({"language": lang, "profile_loaded": prof_loaded, "tools": resolved})
    return rows


def render_extended_report_format(
    fmt: str,
    report_payload: dict[str, Any],
    output_path: Path | None,
    project_root: Path,
) -> int | None:
    """Handle --format html and --format sarif in cmd_report."""
    if fmt == "html":
        reporter = HtmlReporter()
        if output_path is not None:
            reporter.write(report_payload, output_path, project_root=project_root)
        else:
            print(reporter.render(report_payload), end="")
        return 0
    if fmt == "sarif":
        s_reporter = SarifReporter()
        if output_path is not None:
            s_reporter.write(report_payload, output_path, project_root=project_root)
        else:
            print(s_reporter.render(report_payload), end="")
        return 0
    return None
