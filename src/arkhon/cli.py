"""ARKHON (Apxoh) command-line interface."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

from arkhon import __version__


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def cmd_version(args: argparse.Namespace) -> int:
    if getattr(args, "json", False):
        payload = {"name": "Apxoh", "identifier": "arkhon", "version": __version__}
        print(json.dumps(payload, indent=2))
    else:
        print(f"Apxoh {__version__} (ARKHON)")
    return 0


def cmd_doctor(_args: argparse.Namespace) -> int:
    failures: list[str] = []
    warnings: list[str] = []
    root = _repo_root()
    for required in ("VERSION", "manifest/index.yaml", "README.md", "AGENTS.md"):
        if not (root / required).exists():
            failures.append(f"missing required file: {required}")
    try:
        from arkhon.config import load_manifest

        _ = load_manifest(root).version
    except Exception as exc:
        failures.append(f"manifest load failed: {exc}")
    try:
        from arkhon.integrations.tsar.adapter import TsarAdapter

        if not TsarAdapter().health_check():
            warnings.append(
                "TSAR is not available; security verification remains BLOCKED until configured"
            )
    except Exception as exc:
        warnings.append(f"optional TSAR integration check failed: {exc}")
    if failures:
        print("Apxoh doctor — FAILED")
        for failure in failures:
            print(f"  [FAIL] {failure}")
        for warning in warnings:
            print(f"  [WARN] {warning}")
        return 1
    print("Apxoh doctor — OK")
    print(f"  Python:  {sys.version.split()[0]}")
    print(f"  Version: {__version__}")
    print(f"  Root:    {root}")
    for warning in warnings:
        print(f"  [WARN] {warning}")
    return 0


def cmd_validate(_args: argparse.Namespace) -> int:
    import sys as _sys

    repo_root = Path(__file__).resolve().parents[2]
    if str(repo_root) not in _sys.path:
        _sys.path.insert(0, str(repo_root))

    try:
        from scripts.validation.validate_all import main as validate_main
    except ImportError:
        print(
            "[FAIL] scripts.validation.validate_all not available. "
            "Run from a repository checkout.",
            file=sys.stderr,
        )
        return 1

    return int(validate_main())


def cmd_inspect(args: argparse.Namespace) -> int:
    from arkhon.config import get_manifest
    from arkhon.language_support.detector import detect_languages
    from arkhon.projects.matcher import match_profile

    project = Path(args.project).resolve()
    if not project.is_dir():
        print(f"[FAIL] not a directory: {project}", file=sys.stderr)
        return 1

    manifest = get_manifest()
    languages = detect_languages(project)
    profile = match_profile(project)
    detected_ids = [lang.definition.id for lang in languages.detected]
    report: dict[str, Any] = {
        "project": str(project),
        "profile": {
            "name": profile.profile,
            "reason": profile.reason,
            "explicit": profile.explicit,
        },
        "languages": {
            "detected": detected_ids,
            "unknown": languages.unknown,
        },
        "system": {
            "name": manifest.name,
            "version": manifest.version,
        },
    }

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(f"Project: {project}")
        print(f"Profile: {profile.profile} ({profile.reason})")
        print("Languages detected:")
        for lang_id in detected_ids:
            print(f"  - {lang_id}")
        if languages.unknown:
            print("Unknown language files:")
            for ext in languages.unknown:
                print(f"  - {ext}")
    return 0


def _commit_sha(project: Path) -> str | None:
    git_executable = shutil.which("git")
    if git_executable is None:
        print("[FAIL] git executable not found on PATH", file=sys.stderr)
        return None
    try:
        # The executable and argument vector are fixed; shell execution is disabled.
        result = subprocess.run(  # noqa: S603 - resolved git executable and fixed arguments
            [git_executable, "rev-parse", "HEAD"],
            cwd=project,
            capture_output=True,
            text=True,
            check=True,
            timeout=10,
        )
        return result.stdout.strip()
    except (OSError, subprocess.SubprocessError) as exc:
        print(f"[FAIL] cannot resolve commit SHA: {exc}", file=sys.stderr)
        return None


def cmd_audit(args: argparse.Namespace) -> int:
    from arkhon.rules.loader import load_rules_dir

    rules_result = load_rules_dir(_repo_root() / "rules")
    if not rules_result.ok:
        print(f"[FAIL] rule load errors: {len(rules_result.errors)}", file=sys.stderr)
        for error in rules_result.errors:
            print(f"  - {error}", file=sys.stderr)
        return 1
    # Keep audit and verify on the same runner map so a domain can never be
    # reported as PASS by an unrelated verification tool.
    return cmd_verify(args)


def cmd_assess(args: argparse.Namespace) -> int:
    from arkhon.assessment.gates import RuleOutcome, evaluate_all_gates
    from arkhon.assessment.scorer import WEIGHTS, score_from_ratios
    from arkhon.evidence.store import EvidenceStore

    project = Path(args.project).resolve()
    if not project.is_dir():
        print(f"[FAIL] not a directory: {project}", file=sys.stderr)
        return 1
    store = EvidenceStore(project)
    ratios = {key: 0.0 for key in WEIGHTS}
    outcomes_per_domain: dict[str, list[RuleOutcome]] = {}
    for record in store.iter_records():
        domain = record.path.parent.name
        if domain in ratios and record.status == "PASS":
            ratios[domain] = min(1.0, ratios[domain] + 0.25)
    score = score_from_ratios(ratios)
    verdicts = evaluate_all_gates(outcomes_per_domain)
    print(f"Score: {score.total:.1f} / {score.maximum}")
    print(f"Level: {score.level}")
    print("Gates:")
    for gate, verdict in verdicts.items():
        print(f"  {gate}: {verdict.status}")
    if not outcomes_per_domain:
        print("[BLOCKED] rule-level assessment outcomes are not available")
    return 1




def cmd_status(args: argparse.Namespace) -> int:
    """Summarize project configuration and persisted verification evidence."""
    from arkhon.core.errors import EvidenceError
    from arkhon.evidence.store import EvidenceStore
    from arkhon.language_support.detector import detect_languages
    from arkhon.projects.matcher import match_profile

    project = Path(args.project).resolve()
    if not project.is_dir():
        print(f"[FAIL] not a directory: {project}", file=sys.stderr)
        return 1
    try:
        records = list(EvidenceStore(project).iter_records())
        profile = match_profile(project)
        languages = detect_languages(project)
    except EvidenceError as exc:
        print(f"[FAIL] evidence integrity check failed: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"[FAIL] project status could not be computed: {exc}", file=sys.stderr)
        return 1

    by_domain: dict[str, dict[str, int]] = {}
    totals = {"PASS": 0, "FAIL": 0, "BLOCKED": 0, "other": 0}
    for record in records:
        domain = record.path.parent.name
        status = record.status.upper()
        bucket = by_domain.setdefault(domain, {"PASS": 0, "FAIL": 0, "BLOCKED": 0, "other": 0})
        key = status if status in {"PASS", "FAIL", "BLOCKED"} else "other"
        bucket[key] += 1
        totals[key] += 1

    report = {
        "project": str(project),
        "profile": {
            "name": profile.profile,
            "reason": profile.reason,
            "explicit": profile.explicit,
        },
        "languages": {
            "detected": [item.definition.id for item in languages.detected],
            "unknown": languages.unknown,
        },
        "evidence": {
            "total": len(records),
            "counts": totals,
            "by_domain": by_domain,
        },
    }
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(f"Project: {project}")
        print(f"Profile: {profile.profile} ({profile.reason})")
        print("Languages: " + (", ".join(report["languages"]["detected"]) or "none"))
        print(f"Evidence records: {len(records)}")
        for key, value in totals.items():
            print(f"  {key}: {value}")
        if not records:
            print("  [INFO] no evidence has been recorded yet")
    return 0


def cmd_exceptions_list(args: argparse.Namespace) -> int:
    """List policy exceptions without granting, extending, or revoking them."""
    import yaml

    from arkhon.policies.exceptions import load_exceptions

    registry_path = (
        Path(args.registry).expanduser().resolve()
        if args.registry
        else _repo_root() / "system" / "policies" / "exceptions" / "registry.yaml"
    )
    try:
        registry = load_exceptions(registry_path)
    except (OSError, yaml.YAMLError) as exc:
        print(f"[FAIL] cannot load exception registry: {exc}", file=sys.stderr)
        return 1

    items = []
    for exception in sorted(registry.exceptions, key=lambda item: item.exception_id):
        state = "expired" if exception.is_expired() else exception.status
        items.append(
            {
                "exception_id": exception.exception_id,
                "rule_id": exception.rule_id,
                "owner": exception.owner,
                "approver": exception.approver,
                "expires_at": exception.expires_at,
                "status": state,
                "active": exception.is_active(),
            }
        )
    if args.json:
        print(json.dumps({"registry": str(registry_path), "exceptions": items}, indent=2))
    elif not items:
        print(f"No exceptions registered in {registry_path}")
    else:
        print(f"Exception registry: {registry_path}")
        for item in items:
            marker = "ACTIVE" if item["active"] else str(item["status"]).upper()
            print(
                f"{item['exception_id']} | {item['rule_id']} | {marker} | "
                f"expires {item['expires_at']} | owner {item['owner']}"
            )
    return 0


def cmd_report(args: argparse.Namespace) -> int:
    from arkhon.reporting.json_reporter import JsonReporter
    from arkhon.reporting.markdown_reporter import MarkdownReporter

    project = Path(args.project).resolve()
    if not project.is_dir():
        print(f"[FAIL] not a directory: {project}", file=sys.stderr)
        return 1
    fmt = args.format or "json"
    output = Path(args.output) if args.output else project / ".arkhon" / "reports"
    reporter = (
        JsonReporter() if fmt == "json" else MarkdownReporter() if fmt == "markdown" else None
    )
    if reporter is None:
        print(f"[FAIL] unknown format: {fmt}", file=sys.stderr)
        return 1
    commit_sha = _commit_sha(project)
    if commit_sha is None:
        return 1
    path = reporter.write(project, output, expected_commit_sha=commit_sha)
    print(f"[OK] report written to {path}")
    return 0


def cmd_verify(args: argparse.Namespace) -> int:
    from arkhon.evidence.collector import EvidenceCollector
    from arkhon.evidence.store import EvidenceStore
    from arkhon.verification.engine import VerificationEngine
    from arkhon.verification.runners.base import Runner
    from arkhon.verification.runners.mypy_runner import MypyRunner
    from arkhon.verification.runners.pytest_runner import PytestRunner
    from arkhon.verification.runners.ruff_runner import RuffRunner
    from arkhon.verification.runners.supply_chain_runner import (
        SupplyChainAttestationRunner,
        SyftRunner,
    )
    from arkhon.verification.runners.tsar_runner import TsarRunner

    project = Path(args.project).resolve()
    if not project.is_dir():
        print(f"[FAIL] not a directory: {project}", file=sys.stderr)
        return 1
    domain = args.domain or "all"
    runners_map: dict[str, tuple[Runner, ...]] = {
        "testing": (PytestRunner(),),
        "code-quality": (RuffRunner(), MypyRunner()),
        "software-security": (TsarRunner(),),
        "supply-chain": (SyftRunner(),),
        "release-attestations": (SupplyChainAttestationRunner(),)
    }
    domains: tuple[str, ...]
    if domain == "all":
        # Release supply-chain verification requires release artifacts and is
        # an explicit gate, not a local source-only default.
        domains = ("testing", "code-quality", "software-security", "supply-chain")
    elif domain in runners_map:
        domains = (domain,)
    else:
        print(f"[FAIL] unknown domain: {domain}", file=sys.stderr)
        return 1
    commit_sha = _commit_sha(project)
    if commit_sha is None:
        return 1
    engine = VerificationEngine(
        store=EvidenceStore(project),
        collector=EvidenceCollector(root=project),
    )
    runs = []
    for selected_domain in domains:
        run = engine.run(
            domain=selected_domain,
            commit_sha=commit_sha,
            runners=runners_map[selected_domain],
            project_root=project,
        )
        runs.append(run)
        print(f"Run:      {run.run_id}")
        print(f"Domain:   {run.domain}")
        print(f"Commit:   {run.commit_sha[:12]}")
        print(f"Status:   {run.status}")
        print(f"Evidence: {run.evidence_id}")
        for result in run.results:
            print(f"  [{result.runner}] {result.outcome.value}")
    return 0 if runs and all(run.status == "PASS" for run in runs) else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="arkhon",
        description="Apxoh (ARKHON) — Software Engineering Governance & Assurance System",
    )
    sub = parser.add_subparsers(dest="command")
    version = sub.add_parser("version", help="Print ARKHON version")
    version.add_argument("--json", action="store_true", help="Output as JSON")
    version.set_defaults(func=cmd_version)
    sub.add_parser("doctor", help="Check installation and environment").set_defaults(
        func=cmd_doctor
    )
    sub.add_parser("validate", help="Validate manifest, schemas, and rules").set_defaults(
        func=cmd_validate
    )
    inspect = sub.add_parser("inspect", help="Inspect a project (languages, profile)")
    inspect.add_argument("project", nargs="?", default=".")
    inspect.add_argument("--json", action="store_true")
    inspect.set_defaults(func=cmd_inspect)
    audit = sub.add_parser("audit", help="Run verification for a specific domain")
    audit.add_argument("project", nargs="?", default=".")
    audit.add_argument("--domain", default="testing")
    audit.set_defaults(func=cmd_audit)
    assess = sub.add_parser("assess", help="Compute engineering score and gate status")
    assess.add_argument("project", nargs="?", default=".")
    assess.set_defaults(func=cmd_assess)
    status = sub.add_parser("status", help="Summarize project configuration and evidence")
    status.add_argument("project", nargs="?", default=".")
    status.add_argument("--json", action="store_true")
    status.set_defaults(func=cmd_status)
    exceptions = sub.add_parser("exceptions", help="Inspect governance exceptions")
    exceptions_sub = exceptions.add_subparsers(dest="exceptions_command")
    exceptions_list = exceptions_sub.add_parser("list", help="List registered exceptions")
    exceptions_list.add_argument("--registry")
    exceptions_list.add_argument("--json", action="store_true")
    exceptions_list.set_defaults(func=cmd_exceptions_list)
    report = sub.add_parser("report", help="Generate an engineering-quality report")
    report.add_argument("project", nargs="?", default=".")
    report.add_argument("--format", choices=["json", "markdown"], default="json")
    report.add_argument("--output")
    report.set_defaults(func=cmd_report)
    verify = sub.add_parser("verify", help="Run verification runners on a project")
    verify.add_argument("project", nargs="?", default=".")
    verify.add_argument("--domain", default="all")
    verify.set_defaults(func=cmd_verify)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not hasattr(args, "func"):
        parser.print_help()
        return 1
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
