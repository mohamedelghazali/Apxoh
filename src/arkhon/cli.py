"""ARKHON (Apxoh) command-line interface."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path
from typing import Any

from arkhon import __version__


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _project_template_root() -> Path:
    """Locate project schemas and profiles in a checkout or installed wheel."""
    repository_root = _repo_root()
    if (repository_root / "schemas" / "project.schema.json").is_file() and (
        repository_root / "projects"
    ).is_dir():
        return repository_root
    return Path(__file__).resolve().parent / "resources" / "project_templates"


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
    from arkhon.projects.loader import list_profiles
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


def _working_tree_clean(project: Path) -> bool:
    git_executable = shutil.which("git")
    if git_executable is None:
        return False
    try:
        result = subprocess.run(  # noqa: S603 - resolved git executable and fixed arguments
            [git_executable, "status", "--porcelain", "--untracked-files=all"],
            cwd=project,
            capture_output=True,
            text=True,
            check=True,
            timeout=10,
        )
    except (OSError, subprocess.SubprocessError):
        return False
    return not result.stdout.strip()


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
    """Execute supported rule methods and fail closed on missing proof."""
    from arkhon.assessment.decision import decide
    from arkhon.assessment.gates import RuleOutcome, evaluate_all_gates
    from arkhon.assessment.scorer import score_from_outcomes
    from arkhon.core.constants import (
        ALL_ENFORCEMENT,
        STATUS_BLOCKED,
        STATUS_FAIL,
        STATUS_NOT_APPLICABLE,
        STATUS_PASS,
    )
    from arkhon.core.errors import ConfigError, EvidenceError, GateError
    from arkhon.evidence.collector import EvidenceCollector
    from arkhon.evidence.store import EvidenceStore
    from arkhon.projects.matcher import match_profile
    from arkhon.rules.loader import load_rules_dir
    from arkhon.verification.methods import resolve_methods
    from arkhon.verification.runners.base import RunnerOutcome, RunnerResult
    from arkhon.verification.runners.mypy_runner import MypyRunner
    from arkhon.verification.runners.tsar_runner import TsarRunner

    project = Path(args.project).resolve()
    if not project.is_dir():
        print(f"[FAIL] not a directory: {project}", file=sys.stderr)
        return 1

    rules_result = load_rules_dir(_repo_root() / "rules")
    if not rules_result.ok:
        print(f"[FAIL] rule load errors: {len(rules_result.errors)}", file=sys.stderr)
        for error in rules_result.errors:
            print(f"  - {error}", file=sys.stderr)
        return 1

    try:
        records = list(EvidenceStore(project).iter_records())
        profile = match_profile(project)
        available_profiles = set(list_profiles(_project_template_root()))
        if profile.profile not in available_profiles:
            raise ConfigError(f"unknown project profile: {profile.profile!r}")
    except EvidenceError as exc:
        print(f"[FAIL] evidence integrity check failed: {exc}", file=sys.stderr)
        return 1
    except (ConfigError, OSError, ValueError) as exc:
        print(f"[FAIL] project applicability could not be determined: {exc}", file=sys.stderr)
        return 1

    commit_sha = _commit_sha(project)
    working_tree_clean = commit_sha is not None and _working_tree_clean(project)
    active_rules = [rule for rule in rules_result.rules if rule.status == "active"]
    assessment_id = f"ASSESS-{uuid.uuid4().hex[:12].upper()}"
    evidence_records_written = 0
    planned: dict[str, tuple[tuple[tuple[str, Any], ...], bool, str | None]] = {}
    required_runners: set[str] = set()
    total_methods = implemented_methods = human_review_rules = malformed_rules = 0

    print(f"Project profile: {profile.profile} ({profile.reason})")
    print("Rule verification execution:")
    for rule in active_rules:
        if not re.fullmatch(r"SE-[A-Z]+(-[A-Z]+)?-\d{3,}", rule.id):
            malformed_rules += 1
            planned[rule.id] = ((), False, "rule identifier does not match the evidence schema")
            print(f"  {rule.id}: BLOCKED (invalid rule identifier)")
            continue
        scope = rule.raw.get("scope", {"project_types": ["all"]})
        project_types = scope.get("project_types") if isinstance(scope, dict) else None
        if (
            not isinstance(project_types, list)
            or not project_types
            or any(not isinstance(item, str) or not item for item in project_types)
        ):
            malformed_rules += 1
            planned[rule.id] = ((), False, "scope.project_types is missing or malformed")
            print(f"  {rule.id}: BLOCKED (invalid project scope)")
            continue

        if (
            commit_sha is not None
            and working_tree_clean
            and profile.explicit
            and profile.profile != "universal"
            and "all" not in project_types
            and profile.profile not in project_types
        ):
            planned[rule.id] = ((), False, None)
            print(f"  {rule.id}: NOT_APPLICABLE (outside declared project scope)")
            continue

        verification = rule.raw.get("verification")
        methods = verification.get("methods") if isinstance(verification, dict) else None
        try:
            resolutions = resolve_methods(methods)
        except ValueError as exc:
            malformed_rules += 1
            planned[rule.id] = ((), False, str(exc))
            print(f"  {rule.id}: BLOCKED ({exc})")
            continue

        total_methods += len(resolutions)
        supported = [
            (method, implementation)
            for method, implementation in resolutions
            if implementation is not None
        ]
        implemented_methods += len(supported)
        required_runners.update(implementation.runner for _, implementation in supported)

        human_review = rule.raw.get("human_review", {})
        if not isinstance(human_review, dict) or not isinstance(
            human_review.get("required", False), bool
        ):
            malformed_rules += 1
            planned[rule.id] = (resolutions, False, "human_review declaration is malformed")
            print(f"  {rule.id}: BLOCKED (human_review declaration is malformed)")
            continue
        review_required = human_review.get("required", False)
        human_review_rules += int(review_required)
        planned[rule.id] = (resolutions, review_required, None)
        print(
            f"  {rule.id}: {len(supported)}/{len(resolutions)} methods implemented; "
            f"human review {'required' if review_required else 'not required'}"
        )

    runner_instances = {
        "mypy": MypyRunner(),
        "tsar": TsarRunner(),
    }
    runner_results: dict[str, RunnerResult] = {}

    if commit_sha is None:
        block_reason = "assessment requires a resolvable Git commit SHA"
    elif not working_tree_clean:
        block_reason = "working tree is dirty or its clean state could not be verified"
    else:
        block_reason = ""
    if block_reason:
        for runner_name in required_runners:
            runner_results[runner_name] = RunnerResult(
                runner=runner_name,
                outcome=RunnerOutcome.BLOCKED,
                reason=block_reason,
            )
    else:
        for runner_name in sorted(required_runners):
            runner = runner_instances.get(runner_name)
            if runner is None:
                runner_results[runner_name] = RunnerResult(
                    runner=runner_name,
                    outcome=RunnerOutcome.BLOCKED,
                    reason="registered runner has no executable implementation",
                )
                continue
            try:
                result = runner.run(project)
            except Exception as exc:
                result = RunnerResult(
                    runner=runner_name,
                    outcome=RunnerOutcome.BLOCKED,
                    reason=f"runner crashed: {type(exc).__name__}: {exc}",
                )
            if not isinstance(result, RunnerResult) or not isinstance(
                result.outcome, RunnerOutcome
            ):
                result = RunnerResult(
                    runner=runner_name,
                    outcome=RunnerOutcome.BLOCKED,
                    reason="runner returned an invalid result",
                )
            elif result.outcome != RunnerOutcome.BLOCKED:
                artifact_error = ""
                if not result.artifacts:
                    artifact_error = "runner returned a verdict without evidence artifacts"
                else:
                    for artifact in result.artifacts:
                        try:
                            resolved = Path(artifact).resolve()
                            resolved.relative_to(project)
                            if not resolved.is_file():
                                artifact_error = f"runner artifact is missing: {artifact}"
                                break
                        except (OSError, RuntimeError, TypeError, ValueError):
                            artifact_error = f"runner artifact is outside project root: {artifact}"
                            break
                if artifact_error:
                    result = RunnerResult(
                        runner=runner_name,
                        outcome=RunnerOutcome.BLOCKED,
                        reason=artifact_error,
                    )
            runner_results[runner_name] = result

        current_commit_sha = _commit_sha(project)
        current_working_tree_clean = _working_tree_clean(project)
        if current_commit_sha != commit_sha or not current_working_tree_clean:
            working_tree_clean = False
            for runner_name in required_runners:
                runner_results[runner_name] = RunnerResult(
                    runner=runner_name,
                    outcome=RunnerOutcome.BLOCKED,
                    reason="project commit or working tree changed during assessment; rerun required",
                )

    def method_status(method_id: str, runner_name: str) -> tuple[str, str]:
        result = runner_results.get(runner_name)
        if result is None or result.outcome == RunnerOutcome.BLOCKED:
            return STATUS_BLOCKED, (
                result.reason if result is not None else "verification method was not executed"
            )
        if method_id == "type-checker-execution":
            if result.outcome in {RunnerOutcome.PASS, RunnerOutcome.FAIL}:
                return STATUS_PASS, "Mypy executed and produced an evidence artifact"
        elif method_id == "zero-type-errors-check":
            if result.outcome == RunnerOutcome.PASS:
                return STATUS_PASS, "Mypy reported zero type errors"
            return STATUS_FAIL, result.reason or "Mypy reported type errors"
        elif method_id == "tsar-audit-invocation":
            if result.outcome == RunnerOutcome.PASS:
                return STATUS_PASS, "TSAR audit and acceptance checks passed"
            return STATUS_FAIL, result.reason or "TSAR reported unresolved security findings"
        elif method_id in {
            "evidence-integrity-check",
            "evidence-commit-match",
            "evidence-freshness-check",
            "timestamp-verification",
        } and result.outcome in {RunnerOutcome.PASS, RunnerOutcome.FAIL}:
            return STATUS_PASS, "TSAR evidence integrity, provenance, and freshness verified"
        return STATUS_BLOCKED, result.reason or "method did not establish its acceptance criteria"

    outcomes_per_domain: dict[str, list[RuleOutcome]] = {}
    complete = commit_sha is not None and working_tree_clean
    print("Rule outcomes:")
    for rule in active_rules:
        resolutions, review_required, planning_error = planned[rule.id]
        if planning_error is not None:
            rule_status = STATUS_BLOCKED
            reasons = [planning_error]
            method_details: list[tuple[str, str, str]] = []
        elif not resolutions and not review_required:
            rule_status = STATUS_NOT_APPLICABLE
            reasons = ["outside declared project scope"]
            method_details = []
        else:
            method_details = []
            for method_id, implementation in resolutions:
                if implementation is None:
                    status = STATUS_BLOCKED
                    reason = (
                        "authorized human approval evidence is not available"
                        if method_id == "human-review"
                        else "no executable implementation is registered"
                    )
                else:
                    status, reason = method_status(method_id, implementation.runner)
                method_details.append((method_id, status, reason))

            if review_required and not any(item[0] == "human-review" for item in method_details):
                method_details.append(
                    (
                        "human-review-approval",
                        STATUS_BLOCKED,
                        "authorized human approval is required",
                    )
                )

            statuses = [item[1] for item in method_details]
            if STATUS_FAIL in statuses:
                rule_status = STATUS_FAIL
            elif STATUS_BLOCKED in statuses or not statuses:
                rule_status = STATUS_BLOCKED
            else:
                rule_status = STATUS_PASS
            reasons = [
                f"{method_id}: {reason}"
                for method_id, status, reason in method_details
                if status != STATUS_PASS
            ]

        if rule.enforcement not in ALL_ENFORCEMENT:
            rule_status = STATUS_BLOCKED
            reasons.append(f"unsupported enforcement level: {rule.enforcement!r}")
            malformed_rules += 1

        if commit_sha is not None and re.fullmatch(r"SE-[A-Z]+(-[A-Z]+)?-\d{3,}", rule.id):
            try:
                summary_dir = (
                    project / ".arkhon" / "reports" / "assessments" / assessment_id
                )
                summary_dir.mkdir(parents=True, exist_ok=True)
                resolved_summary_dir = summary_dir.resolve()
                resolved_summary_dir.relative_to(project)
                summary_path = resolved_summary_dir / f"{rule.id}.json"
                if summary_path.is_symlink():
                    raise EvidenceError("refusing symlinked assessment summary")
                artifact_paths: set[Path] = set()
                for _, implementation in resolutions:
                    if implementation is None:
                        continue
                    runner_result = runner_results.get(implementation.runner)
                    if runner_result is not None and runner_result.outcome in {
                        RunnerOutcome.PASS,
                        RunnerOutcome.FAIL,
                    }:
                        artifact_paths.update(
                            Path(item).resolve() for item in runner_result.artifacts
                        )
                summary = {
                    "assessment_id": assessment_id,
                    "rule_id": rule.id,
                    "domain": rule.domain,
                    "enforcement": rule.enforcement,
                    "status": rule_status,
                    "commit_sha": commit_sha,
                    "project_profile": profile.profile,
                    "working_tree_clean": working_tree_clean,
                    "human_review_required": review_required,
                    "methods": [
                        {"method_id": method_id, "status": status, "reason": reason}
                        for method_id, status, reason in method_details
                    ],
                    "reasons": reasons,
                }
                with summary_path.open("x", encoding="utf-8") as stream:
                    json.dump(summary, stream, indent=2, sort_keys=True)
                    stream.write("\n")
                collector = EvidenceCollector(root=project)
                draft = collector.new_evidence(
                    source="arkhon",
                    source_version=__version__,
                    commit_sha=commit_sha,
                    status=rule_status,
                )
                draft.rule_ids = [rule.id]
                draft.notes = (
                    f"Rule-level assessment {assessment_id}; "
                    "generated by live verification"
                )
                for artifact_path in sorted(artifact_paths):
                    draft.add_artifact(artifact_path)
                draft.add_artifact(summary_path)
                evidence = draft.to_evidence()
                evidence_store = EvidenceStore(project)
                evidence_store.write(rule.domain, evidence)
                evidence_store.read(rule.domain, str(evidence["evidence_id"]))
                evidence_records_written += 1
            except (EvidenceError, OSError, RuntimeError, ValueError) as exc:
                rule_status = STATUS_BLOCKED
                reasons.append(f"rule assessment evidence could not be persisted: {exc}")
                complete = False

        outcome = RuleOutcome(
            rule_id=rule.id,
            enforcement=rule.enforcement,
            status=rule_status,
            reason="; ".join(reasons),
        )
        outcomes_per_domain.setdefault(rule.domain, []).append(outcome)
        complete = complete and rule_status in {STATUS_PASS, STATUS_NOT_APPLICABLE}
        print(f"  {rule.id}: {rule_status}")
        for method_id, status, reason in method_details:
            print(f"    [{status}] {method_id}: {reason}")

    try:
        verdicts = evaluate_all_gates(outcomes_per_domain)
    except GateError as exc:
        print(f"[FAIL] rule outcomes cannot be evaluated safely: {exc}", file=sys.stderr)
        return 1
    print(f"Active rules inspected: {len(active_rules)}")
    print(
        f"Method implementations present: {implemented_methods}/{total_methods}; "
        f"rules requiring human review: {human_review_rules}; "
        f"malformed rule declarations: {malformed_rules}"
    )
    print(f"Evidence records inspected: {len(records)} (integrity-checked)")
    print(f"New rule-level evidence records persisted: {evidence_records_written}")
    print(f"Commit assessed: {commit_sha or 'UNRESOLVED'}")
    print(f"Working tree clean: {'yes' if working_tree_clean else 'no'}")
    print("Gates:")
    for gate, verdict in verdicts.items():
        print(f"  {gate}: {verdict.status}")

    if not complete or any(verdict.status != STATUS_PASS for verdict in verdicts.values()):
        print("[BLOCKED] one or more rules lack complete, commit-bound verification")
        print("[BLOCKED] no score or readiness level has been computed")
        return 1

    score_domain_map = {
        "requirements": "requirements",
        "architecture": "architecture_and_code_quality",
        "code-quality": "architecture_and_code_quality",
        "testing": "testing",
        "software-security": "security",
        "privacy-compliance": "security",
        "performance": "performance",
        "reliability": "reliability",
        "scalability": "scalability",
        "api-integration": "documentation_deployment_maintenance",
        "database": "documentation_deployment_maintenance",
        "devops": "documentation_deployment_maintenance",
        "infrastructure": "documentation_deployment_maintenance",
        "maintenance": "documentation_deployment_maintenance",
        "observability": "documentation_deployment_maintenance",
        "release": "documentation_deployment_maintenance",
    }
    score_outcomes: dict[str, list[str]] = {}
    for domain, rule_outcomes in outcomes_per_domain.items():
        score_domain = score_domain_map.get(domain)
        if score_domain is not None:
            score_outcomes.setdefault(score_domain, []).extend(
                item.status for item in rule_outcomes
            )
    score = score_from_outcomes(score_outcomes)
    decision = decide(score, verdicts)
    print(f"Engineering score: {score.total:.2f}/{score.maximum:.0f}")
    print(f"Readiness level: {score.level}")
    print(f"Decision: {decision.decision} — {decision.reason}")
    return 0 if decision.decision in {"APPROVED", "APPROVED_WITH_CONDITIONS"} else 1


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

    templates_root = _project_template_root()
    available_profiles = list_profiles(templates_root)
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
        schema_path = templates_root / "schemas" / "project.schema.json"
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
