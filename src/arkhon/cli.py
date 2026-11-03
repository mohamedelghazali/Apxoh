"""ARKHON (Apxoh) command-line interface."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import tempfile
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
    from arkhon.core.errors import ConfigError, EvidenceError
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
    except (ConfigError, OSError, ValueError) as exc:
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

    detected_language_ids = [item.definition.id for item in languages.detected]
    report = {
        "project": str(project),
        "profile": {
            "name": profile.profile,
            "reason": profile.reason,
            "explicit": profile.explicit,
        },
        "languages": {
            "detected": detected_language_ids,
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
        print("Languages: " + (", ".join(detected_language_ids) or "none"))
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
    except (OSError, yaml.YAMLError, TypeError, AttributeError, ValueError) as exc:
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



def _agent_pack_source() -> Path:
    return Path(__file__).resolve().parent / "resources" / "agent_pack"


def cmd_install(args: argparse.Namespace) -> int:
    """Stage the general governance pack without changing agent-specific settings."""
    scope = args.scope
    if scope == "project":
        base = Path(args.project).expanduser().resolve()
        if not base.is_dir():
            print(f"[FAIL] not a directory: {base}", file=sys.stderr)
            return 1
    else:
        base = Path.home().resolve()

    parent = base / ".arkhon"
    if parent.is_symlink():
        print(f"[FAIL] refusing symlinked install directory: {parent}", file=sys.stderr)
        return 1

    staging: Path | None = None
    backup: Path | None = None
    try:
        parent.mkdir(parents=True, exist_ok=True)
        resolved_parent = parent.resolve()
        resolved_parent.relative_to(base)
        target = resolved_parent / "agent-pack"
        if target.is_symlink():
            raise ValueError(f"refusing symlinked agent pack: {target}")
        if target.exists() and not args.force:
            print(
                f"[FAIL] agent pack already exists: {target} (use --force)",
                file=sys.stderr,
            )
            return 1

        source = _agent_pack_source()
        if not source.is_dir():
            raise OSError(f"packaged agent resources not found: {source}")
        files = sorted(
            item.relative_to(source).as_posix()
            for item in source.rglob("*")
            if item.is_file()
        )
        if not files:
            raise OSError(f"agent resource pack is empty: {source}")

        staging = Path(tempfile.mkdtemp(prefix=".agent-pack-staging-", dir=resolved_parent))
        shutil.copytree(source, staging, dirs_exist_ok=True)
        manifest = {
            "format_version": 1,
            "arkhon_version": __version__,
            "scope": scope,
            "activation": "manual",
            "files": files,
        }
        (staging / "manifest.json").write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

        if target.exists():
            backup = Path(tempfile.mkdtemp(prefix=".agent-pack-backup-", dir=resolved_parent))
            backup.rmdir()
            target.rename(backup)
        try:
            staging.rename(target)
            staging = None
        except OSError:
            if backup is not None and backup.exists() and not target.exists():
                backup.rename(target)
                backup = None
            raise
        if backup is not None:
            shutil.rmtree(backup, ignore_errors=True)
            backup = None
    except (OSError, ValueError) as exc:
        print(f"[FAIL] agent pack installation failed: {exc}", file=sys.stderr)
        return 1
    finally:
        if staging is not None and staging.exists():
            shutil.rmtree(staging, ignore_errors=True)
        if backup is not None and backup.exists():
            if not target.exists():
                backup.rename(target)
            else:
                shutil.rmtree(backup, ignore_errors=True)

    print(f"[OK] governance pack staged: {target}")
    print("  Agent-specific settings were not changed; activation must be verified per product.")
    return 0


def cmd_project_init(args: argparse.Namespace) -> int:
    """Create a schema-validated project declaration without overwriting by default."""
    import jsonschema
    import yaml

    from arkhon.language_support.detector import detect_languages
    from arkhon.projects.loader import list_profiles

    project = Path(args.project).expanduser().resolve()
    if not project.is_dir():
        print(f"[FAIL] not a directory: {project}", file=sys.stderr)
        return 1

    metadata_dir = project / ".arkhon"
    if metadata_dir.is_symlink():
        print("[FAIL] refusing symlinked .arkhon directory", file=sys.stderr)
        return 1
    target = metadata_dir / "project.yaml"
    if target.is_symlink():
        print("[FAIL] refusing symlinked project declaration", file=sys.stderr)
        return 1
    if target.exists() and not args.force:
        print(
            f"[FAIL] project declaration already exists: {target} (use --force)",
            file=sys.stderr,
        )
        return 1

    available_profiles = list_profiles(_repo_root())
    if args.profile not in available_profiles:
        available = ", ".join(available_profiles)
        print(
            f"[FAIL] unknown profile {args.profile!r}; available: {available}",
            file=sys.stderr,
        )
        return 1

    name = (args.name or project.name).strip()
    if not name:
        print("[FAIL] project name cannot be empty", file=sys.stderr)
        return 1
    identifier = args.identifier or re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    if len(identifier) < 2:
        identifier = f"{identifier or 'project'}-project"
    if not re.fullmatch(r"[a-z][a-z0-9-]{1,62}", identifier):
        print(
            "[FAIL] identifier must match ^[a-z][a-z0-9-]{1,62}$",
            file=sys.stderr,
        )
        return 1

    try:
        detection = detect_languages(project)
        detected = [item.definition.id for item in detection.detected]
        declaration = {
            "project": {
                "name": name,
                "identifier": identifier,
                "type": args.project_type,
                "profile": args.profile,
                "risk_level": args.risk_level,
                "description": args.description or "",
            },
            "languages": {
                "primary": detected[0] if detected else "unknown",
                "secondary": detected[1:],
            },
            "lifecycle": {
                "current_stage": "development",
                "current_milestone": 2,
                "release_channel": "pre-release",
            },
            "gates": {
                "requirements_gate": "required",
                "testing_gate": "required",
                "security_gate": "required",
                "release_gate": "required",
            },
        }
        schema_path = _repo_root() / "schemas" / "project.schema.json"
        if not schema_path.is_file():
            raise OSError(f"project schema not found: {schema_path}")
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        jsonschema.validate(instance=declaration, schema=schema)
        metadata_dir.mkdir(parents=True, exist_ok=True)
        metadata_dir.resolve().relative_to(project)
        payload = yaml.safe_dump(declaration, sort_keys=False, allow_unicode=True)
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=metadata_dir,
            prefix=".project-",
            suffix=".tmp",
            delete=False,
        ) as stream:
            stream.write(payload)
            temporary = Path(stream.name)
        temporary.replace(target)
    except (OSError, ValueError, jsonschema.ValidationError) as exc:
        print(f"[FAIL] project initialization failed: {exc}", file=sys.stderr)
        return 1

    print(f"[OK] project declaration created: {target}")
    print(f"  Profile: {args.profile}")
    print(f"  Languages: {', '.join(detected) if detected else 'unknown'}")
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
    install = sub.add_parser("install", help="Stage the agent governance pack")
    install.add_argument("--scope", choices=["project", "global"], default="project")
    install.add_argument("--project", default=".")
    install.add_argument("--force", action="store_true")
    install.set_defaults(func=cmd_install)
    project = sub.add_parser("project", help="Initialize and manage project configuration")
    project_sub = project.add_subparsers(dest="project_command")
    project_init = project_sub.add_parser("init", help="Create .arkhon/project.yaml")
    project_init.add_argument("project", nargs="?", default=".")
    project_init.add_argument("--name")
    project_init.add_argument("--identifier")
    project_init.add_argument(
        "--type",
        dest="project_type",
        choices=["library", "library-and-cli", "application", "service", "platform", "tool"],
        default="library",
    )
    project_init.add_argument("--profile", default="universal")
    project_init.add_argument(
        "--risk-level",
        choices=["low", "medium", "high", "critical"],
        default="medium",
    )
    project_init.add_argument("--description", default="")
    project_init.add_argument("--force", action="store_true")
    project_init.set_defaults(func=cmd_project_init)
    status = sub.add_parser("status", help="Summarize project configuration and evidence")
    status.add_argument("project", nargs="?", default=".")
    status.add_argument("--json", action="store_true")
    status.set_defaults(func=cmd_status)
    exceptions = sub.add_parser("exceptions", help="Inspect governance exceptions")
    exceptions_sub = exceptions.add_subparsers(dest="exceptions_command")
    exceptions_sub.required = True
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
