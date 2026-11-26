"""Security reconnaissance, deterministic coverage seeding, and AST/structural hunting."""

from __future__ import annotations

import ast
import json
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from arkhon.orchestrator.task_dispatcher import AuditRole, SecurityAuditTaskDispatcher
from arkhon.security_audit.coverage import (
    CoverageCheck,
    CoverageLedger,
    CoverageUnit,
    build_canonical_coverage_id,
)
from arkhon.security_audit.findings import (
    DiscoveryProvenance,
    FindingsCollection,
    LocationRef,
    SecurityFinding,
    TraceStep,
    compute_finding_fingerprint,
    finding_id_from_fingerprint,
)
from arkhon.security_audit.taxonomy import DEFAULT_TAXONOMY, AttackClassRegistry

_IGNORED_DIRS = frozenset(
    {
        ".git",
        ".venv",
        "venv",
        "node_modules",
        "__pycache__",
        ".mypy_cache",
        ".ruff_cache",
        ".pytest_cache",
        "build",
        "dist",
        ".arkhon",
    }
)

_SOURCE_SUFFIXES = frozenset(
    {
        ".py",
        ".js",
        ".ts",
        ".tsx",
        ".jsx",
        ".go",
        ".rs",
        ".java",
        ".cs",
        ".rb",
        ".yaml",
        ".yml",
    }
)


def _utc_now() -> str:
    return datetime.now(UTC).isoformat()


@dataclass(frozen=True)
class DiscoveredSurface:
    """Single source-backed entry point or subsystem boundary discovered in Phase 1."""

    component: str
    entry_point: str
    trust_boundary: str
    interface: str
    paths: tuple[str, ...]
    applicable_classes: tuple[str, ...]


@dataclass(frozen=True)
class ArchitectureInventory:
    """Phase 1 reconnaissance inventory written to architecture.json and architecture.md."""

    project: str
    commit_sha: str
    source_files: tuple[str, ...]
    surfaces: tuple[DiscoveredSurface, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "project": self.project,
            "commit_sha": self.commit_sha,
            "source_file_count": len(self.source_files),
            "source_files": list(self.source_files),
            "surfaces": [
                {
                    "component": s.component,
                    "entry_point": s.entry_point,
                    "trust_boundary": s.trust_boundary,
                    "interface": s.interface,
                    "paths": list(s.paths),
                    "applicable_classes": list(s.applicable_classes),
                }
                for s in self.surfaces
            ],
        }

    def render_markdown(self) -> str:
        lines = [
            f"# Security Architecture Inventory — {self.project}",
            "",
            f"- **Commit SHA**: `{self.commit_sha}`",
            f"- **Inventoried Files**: `{len(self.source_files)}`",
            f"- **Mapped Surfaces**: `{len(self.surfaces)}`",
            "",
            "## Entry Surfaces and Trust Boundaries",
            "",
            "| Component | Entry Point | Trust Boundary | Interface | Applicable Classes |",
            "| :--- | :--- | :--- | :--- | :--- |",
        ]
        for surf in self.surfaces:
            classes_str = ", ".join(surf.applicable_classes)
            lines.append(
                f"| `{surf.component}` | `{surf.entry_point}` | `{surf.trust_boundary}` "
                f"| `{surf.interface}` | {classes_str} |"
            )
        return "\n".join(lines) + "\n"


def _iter_source_files(project_root: Path) -> list[Path]:
    collected: list[Path] = []
    for path in sorted(project_root.rglob("*")):
        if path.is_symlink() or not path.is_file():
            continue
        rel_parts = path.relative_to(project_root).parts
        if any(part in _IGNORED_DIRS or part.endswith(".egg-info") for part in rel_parts):
            continue
        if rel_parts[0] in {"tests", "docs"}:
            continue
        if path.suffix in _SOURCE_SUFFIXES or path.name == "Dockerfile":
            collected.append(path)
    return collected


def _classify_component_classes(rel_path: str, text: str) -> tuple[str, str, str, tuple[str, ...]]:
    """Map a source file to (entry_point, trust_boundary, interface, attack_classes)."""
    classes: list[str] = ["injection-input-handling", "secrets-credential-handling"]
    entry = "module-interface"
    boundary = "internal-caller-to-module"
    interface = "library"

    if rel_path.startswith(".github/workflows/"):
        return (
            "ci-workflow",
            "untrusted-repo-event-to-ci-runner",
            "ci-pipeline",
            ("supply-chain-release", "secrets-credential-handling"),
        )
    if rel_path.endswith("Dockerfile") or "terraform" in rel_path:
        return (
            "deployment-spec",
            "workload-to-cloud-runtime",
            "infrastructure",
            ("cloud-deployment-security", "configuration-infrastructure"),
        )
    if any(tok in text for tok in ("FastAPI", "Flask", "@app.route", "@router.", "HttpResponse")):
        entry = "http-route-handler"
        boundary = "external-unauthenticated-to-http"
        interface = "http-api"
        classes.extend(
            ["web-protocol-security", "authn-authz-boundaries", "api-security"]
        )
    elif "ArgumentParser" in text or "subparsers" in text:
        entry = "cli-entrypoint"
        boundary = "cli-operator-to-engine"
        interface = "cli"
        classes.append("configuration-infrastructure")

    if any(tok in text for tok in ("prompt", "mcp", "tool_call", "agent")):
        classes.append("ai-llm-security")
    if any(tok in text for tok in ("SELECT ", "INSERT ", "tenant_id", "sqlite3")):
        classes.append("data-tenant-isolation")
    if any(tok in text for tok in ("hashlib.", "hmac.", "AES", "bcrypt", "argon2")):
        classes.append("cryptographic-implementation")
    if any(tok in text for tok in ("innerHTML", "postMessage", "localStorage")):
        classes.append("client-side-security")
    if any(tok in text for tok in ("AF_UNIX", "O_NOFOLLOW", "/tmp/")):
        classes.append("local-ipc-trust")
    if any(tok in text for tok in ("logger.", "logging.", "traceback")):
        classes.append("data-lifecycle-privacy")
    if any(tok in text for tok in ("zipfile", "tarfile", "ElementTree", "re.compile")):
        classes.append("resource-exhaustion-availability")
    if any(tok in text for tok in ("verify=False", "debug=True", "CERT_NONE")):
        classes.append("configuration-infrastructure")

    deduped = tuple(dict.fromkeys(classes))
    return entry, boundary, interface, deduped


def discover_architecture(project_root: Path, commit_sha: str) -> ArchitectureInventory:
    """Perform deterministic Phase 1 source reconnaissance."""
    resolved = project_root.resolve()
    files = _iter_source_files(resolved)
    rel_files = tuple(str(p.relative_to(resolved)).replace("\\", "/") for p in files)

    grouped: dict[tuple[str, str, str, str], tuple[list[str], set[str]]] = {}
    for file_path in files:
        rel = str(file_path.relative_to(resolved)).replace("\\", "/")
        parts = rel.split("/")
        component = "/".join(parts[:3]) if parts[0] == "src" and len(parts) >= 3 else parts[0]
        text = file_path.read_text(encoding="utf-8", errors="replace")
        entry, boundary, iface, classes = _classify_component_classes(rel, text)
        key = (component, entry, boundary, iface)
        paths_list, class_set = grouped.setdefault(key, ([], set()))
        paths_list.append(rel)
        class_set.update(classes)

    surfaces = tuple(
        DiscoveredSurface(
            component=comp,
            entry_point=entry,
            trust_boundary=boundary,
            interface=iface,
            paths=tuple(sorted(paths_list)),
            applicable_classes=tuple(sorted(class_set)),
        )
        for (comp, entry, boundary, iface), (paths_list, class_set) in sorted(grouped.items())
    )
    return ArchitectureInventory(
        project=resolved.name,
        commit_sha=commit_sha,
        source_files=rel_files,
        surfaces=surfaces,
    )


def seed_coverage_ledger(
    inventory: ArchitectureInventory,
    *,
    audit_run_id: str,
    profile: str = "standard",
    execution_mode: str = "single_process_deterministic",
    scope_paths: list[str] | None = None,
    taxonomy: AttackClassRegistry = DEFAULT_TAXONOMY,
) -> CoverageLedger:
    """Create initial deterministic CoverageLedger in 'initiated' state with planned units."""
    clean_scopes = [s.strip("/") for s in (scope_paths or []) if s.strip("/")]
    units: list[CoverageUnit] = []
    lifecycle = "runtime" if profile == "deep" else None

    for surf in inventory.surfaces:
        component_name = (
            "profile/quick/all-in-scope-subsystems" if profile == "quick" else surf.component
        )
        in_scope = not clean_scopes or any(
            any(p == sc or p.startswith(f"{sc}/") for sc in clean_scopes) for p in surf.paths
        )
        for cls_id in surf.applicable_classes:
            taxonomy.require(cls_id)
            cid = build_canonical_coverage_id(
                entry_point=surf.entry_point,
                trust_boundary=surf.trust_boundary,
                component=component_name,
                attack_class=cls_id,
                interface=surf.interface,
                lifecycle=lifecycle,
            )
            if any(u.coverage_id == cid for u in units):
                existing = next(u for u in units if u.coverage_id == cid)
                merged_paths = sorted(set(existing.starting_paths) | set(surf.paths))
                existing.starting_paths = merged_paths
                continue

            if in_scope:
                units.append(
                    CoverageUnit(
                        coverage_id=cid,
                        component=component_name,
                        attack_class=cls_id,
                        trust_boundary=surf.trust_boundary,
                        entry_point=surf.entry_point,
                        interface=surf.interface,
                        starting_paths=list(surf.paths),
                        status="planned",
                        prior_status="new",
                        lifecycle=lifecycle,
                    )
                )
            else:
                units.append(
                    CoverageUnit(
                        coverage_id=cid,
                        component=component_name,
                        attack_class=cls_id,
                        trust_boundary=surf.trust_boundary,
                        entry_point=surf.entry_point,
                        interface=surf.interface,
                        starting_paths=list(surf.paths),
                        status="not_examined",
                        prior_status="new",
                        limitations=["Excluded from scoped audit run (--scope filter)."],
                        lifecycle=lifecycle,
                    )
                )

    ledger = CoverageLedger(
        ledger_id=f"LEDGER-{audit_run_id.removeprefix('AUDIT-')}",
        audit_run_id=audit_run_id,
        project=inventory.project,
        commit_sha=inventory.commit_sha,
        profile=profile,
        audit_status="initiated",
        execution_mode=execution_mode,
        scope_paths=clean_scopes,
        units=units,
    )
    ledger.sort_units()
    return ledger


@dataclass(frozen=True)
class _RawHit:
    line: int
    symbol: str
    invariant_key: str
    title: str
    claimed_cause: str
    impact: str
    needs_external_context: bool = False


def _scan_python_ast(source: str, attack_class: str) -> list[_RawHit]:
    """Perform defensive AST analysis for unsafe sinks matching attack_class."""
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []

    hits: list[_RawHit] = []
    func_stack: list[str] = ["<module>"]

    class _Visitor(ast.NodeVisitor):
        def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
            func_stack.append(node.name)
            self.generic_visit(node)
            func_stack.pop()

        def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
            func_stack.append(node.name)
            self.generic_visit(node)
            func_stack.pop()

        def visit_Call(self, node: ast.Call) -> None:
            scope_name = func_stack[-1]
            call_name = _dotted_name(node.func)
            if attack_class == "injection-input-handling":
                if call_name in {"eval", "exec", "pickle.loads"}:
                    hits.append(
                        _RawHit(
                            line=node.lineno,
                            symbol=scope_name,
                            invariant_key=f"unsafe-call-{call_name}",
                            title=f"Unsafe dynamic execution or deserialization ({call_name})",
                            claimed_cause=f"Direct invocation of {call_name} on runtime input.",
                            impact="Arbitrary code execution within target process boundary.",
                        )
                    )
                elif call_name == "yaml.load" and not _has_kwarg(node, "Loader"):
                    hits.append(
                        _RawHit(
                            line=node.lineno,
                            symbol=scope_name,
                            invariant_key="yaml-unsafe-load",
                            title="Unsafe YAML deserialization without SafeLoader",
                            claimed_cause="yaml.load called without explicit SafeLoader.",
                            impact="Arbitrary object instantiation from untrusted YAML input.",
                        )
                    )
                elif call_name.startswith("subprocess.") and _kwarg_true(node, "shell"):
                    hits.append(
                        _RawHit(
                            line=node.lineno,
                            symbol=scope_name,
                            invariant_key="subprocess-shell-true",
                            title="Subprocess invoked with shell=True",
                            claimed_cause="Shell interpretation enabled on subprocess call.",
                            impact="Command injection across shell boundary.",
                        )
                    )
                elif call_name.endswith(".execute") and node.args and isinstance(
                    node.args[0], (ast.JoinedStr, ast.BinOp)
                ):
                    hits.append(
                        _RawHit(
                            line=node.lineno,
                            symbol=scope_name,
                            invariant_key="dynamic-sql-query",
                            title="Dynamically formatted SQL query passed to execute()",
                            claimed_cause="String interpolation or concatenation in SQL statement.",
                            impact="Unauthorized SQL query across database boundary.",
                        )
                    )
            elif attack_class == "cryptographic-implementation" and call_name in {
                "hashlib.md5",
                "hashlib.sha1",
            } and not _kwarg_false(node, "usedforsecurity"):
                hits.append(
                    _RawHit(
                        line=node.lineno,
                        symbol=scope_name,
                        invariant_key=f"weak-digest-{call_name}",
                        title=f"Weak cryptographic digest ({call_name}) without security opt-out",
                        claimed_cause=f"{call_name} invoked without usedforsecurity=False.",
                        impact="Collision or fast brute-force weakness if used for credentials.",
                    )
                )
            elif attack_class == "configuration-infrastructure" and (
                _kwarg_false(node, "verify")
                and call_name.startswith(("requests.", "httpx."))
            ):
                hits.append(
                    _RawHit(
                        line=node.lineno,
                        symbol=scope_name,
                        invariant_key="tls-verify-disabled",
                        title="Outbound HTTP request disables TLS certificate verification",
                        claimed_cause=f"{call_name} sets verify=False.",
                        impact="Man-in-the-middle interception of outbound transport traffic.",
                    )
                )
            self.generic_visit(node)

    _Visitor().visit(tree)
    return hits


def _dotted_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        prefix = _dotted_name(node.value)
        return f"{prefix}.{node.attr}" if prefix else node.attr
    return ""


def _has_kwarg(node: ast.Call, name: str) -> bool:
    return any(kw.arg == name for kw in node.keywords)


def _kwarg_true(node: ast.Call, name: str) -> bool:
    return any(
        kw.arg == name and isinstance(kw.value, ast.Constant) and kw.value.value is True
        for kw in node.keywords
    )


def _kwarg_false(node: ast.Call, name: str) -> bool:
    return any(
        kw.arg == name and isinstance(kw.value, ast.Constant) and kw.value.value is False
        for kw in node.keywords
    )


_WORKFLOW_INTERP_RE = re.compile(r"\$\{\{\s*github\.event\.(?:pull_request\.title|issue\.body)")
_HARDCODED_CRED_RE = re.compile(
    r"""(?i)\b(db_password|admin_password|private_signing_seed)\s*=\s*['"][^'"]{8,}['"]"""
)


def _scan_structural_text(rel_path: str, source: str, attack_class: str) -> list[_RawHit]:
    hits: list[_RawHit] = []
    for idx, line in enumerate(source.splitlines(), 1):
        if attack_class == "supply-chain-release" and rel_path.startswith(".github/workflows/"):
            if _WORKFLOW_INTERP_RE.search(line):
                hits.append(
                    _RawHit(
                        line=idx,
                        symbol="workflow-step",
                        invariant_key="ci-untrusted-event-interp",
                        title="Untrusted GitHub event field interpolated in workflow",
                        claimed_cause="Direct ${{ github.event.* }} expression in workflow step.",
                        impact="Arbitrary command injection inside CI runner environment.",
                    )
                )
        elif attack_class == "secrets-credential-handling" and _HARDCODED_CRED_RE.search(line):
            hits.append(
                _RawHit(
                    line=idx,
                    symbol="config-assignment",
                    invariant_key="hardcoded-credential-assignment",
                    title="Hardcoded credential literal assigned in source",
                    claimed_cause="Static credential string literal embedded in source code.",
                    impact="Credential exposure to any reader with repository access.",
                )
            )
        elif attack_class == "cloud-deployment-security" and "privileged: true" in line:
            hits.append(
                _RawHit(
                    line=idx,
                    symbol="container-spec",
                    invariant_key="privileged-container-spec",
                    title="Container workload configured with privileged: true",
                    claimed_cause="Privileged container flag present in deployment manifest.",
                    impact="Container escape to underlying node if admission policy permits it.",
                    needs_external_context=True,
                )
            )
    return hits


def _unit_priority_key(unit: CoverageUnit) -> tuple[int, int, str]:
    unauth_rank = 0 if "unauthenticated" in unit.trust_boundary else 1
    reval_rank = 0 if "changed_source" in unit.prior_status else 1
    return (unauth_rank, reval_rank, unit.coverage_id)


def execute_hunting_waves(
    *,
    project_root: Path,
    ledger: CoverageLedger,
    dispatcher: SecurityAuditTaskDispatcher,
    max_units: int | None = None,
    taxonomy: AttackClassRegistry = DEFAULT_TAXONOMY,
) -> FindingsCollection:
    """Execute deterministic coverage-led hunting across planned units."""
    resolved = project_root.resolve()
    planned = sorted(
        [u for u in ledger.units if u.status == "planned"],
        key=_unit_priority_key,
    )
    candidates: list[SecurityFinding] = []

    for index, unit in enumerate(planned):
        if max_units is not None and index >= max_units:
            unit.status = "not_examined"
            unit.limitations = ["Deferred due to explicit max_units budget cap."]
            continue

        hunter_id = f"hunter-w{unit.wave}-{index + 1:03d}"
        dispatcher.assign(
            agent_id=hunter_id,
            role=AuditRole.HUNTER,
            wave=unit.wave,
            targets=(unit.coverage_id,),
        )
        unit.status = "in_progress"
        unit.investigator_id = hunter_id

        cls_def = taxonomy.require(unit.attack_class)
        reviewed: list[str] = []
        unit_findings: list[str] = []
        unit_fps: list[str] = []

        for rel_path in unit.starting_paths:
            full_path = resolved / rel_path
            if not full_path.is_file() or full_path.is_symlink():
                continue
            reviewed.append(rel_path)
            text = full_path.read_text(encoding="utf-8", errors="replace")
            raw_hits = (
                _scan_python_ast(text, unit.attack_class)
                if rel_path.endswith(".py")
                else []
            )
            raw_hits.extend(_scan_structural_text(rel_path, text, unit.attack_class))

            for hit in raw_hits:
                fp = compute_finding_fingerprint(
                    component=unit.component,
                    attack_class=unit.attack_class,
                    primary_file=rel_path,
                    symbol=hit.symbol,
                    invariant_key=hit.invariant_key,
                )
                fid = finding_id_from_fingerprint(fp)
                dispatcher.register_discovery(fp, hunter_id)
                blockers = (
                    [
                        "Cluster admission controller policy is outside repository source."
                    ]
                    if hit.needs_external_context
                    else []
                )
                finding = SecurityFinding(
                    finding_id=fid,
                    fingerprint=fp,
                    title=hit.title,
                    description=f"{hit.claimed_cause} ({rel_path}:{hit.line})",
                    attack_class=unit.attack_class,
                    component=unit.component,
                    affected_locations=[
                        LocationRef(file=rel_path, line=hit.line, symbol=hit.symbol)
                    ],
                    trace=[
                        TraceStep(
                            kind="sink",
                            file=rel_path,
                            line=hit.line,
                            scope=hit.symbol,
                            description=hit.claimed_cause,
                        )
                    ],
                    trust_boundary=unit.trust_boundary,
                    entry_point=unit.entry_point,
                    affected_principal_or_resource=f"{unit.component} runtime state",
                    preconditions=[
                        f"Caller reaches {unit.entry_point} across {unit.trust_boundary}."
                    ],
                    scenario_summary=hit.claimed_cause,
                    reproduction_steps=[
                        f"Inspect {rel_path} line {hit.line} in scope {hit.symbol}."
                    ],
                    security_impact=hit.impact,
                    evidence_refs=[f"{rel_path}:{hit.line}"],
                    discovery_provenance=DiscoveryProvenance(
                        agent_id=hunter_id,
                        role=AuditRole.HUNTER.value,
                        run_id=ledger.audit_run_id,
                        timestamp=_utc_now(),
                        method="static_ast" if rel_path.endswith(".py") else "structural_source",
                    ),
                    verification_provenance=None,
                    verification_status="not_verified",
                    lifecycle_state="candidate",
                    confidence_score="medium",
                    confidence_reason="Static AST/structural sink candidate awaiting verification.",
                    uncertainty_notes=list(blockers),
                    severity=None,
                    root_cause=None,
                    claimed_root_cause=hit.claimed_cause,
                    remediation=None,
                    unresolved_blockers=blockers,
                    validation_plan=(
                        {
                            "owner_deployment_check": (
                                "Verify cluster admission policy in deployment environment."
                            )
                        }
                        if blockers
                        else None
                    ),
                    rejection_reason=None,
                    related_rules=list(cls_def.related_rules),
                    related_requirements=[],
                    commit_sha=ledger.commit_sha,
                    first_seen_run=ledger.audit_run_id,
                    last_seen_run=ledger.audit_run_id,
                    first_seen_commit=ledger.commit_sha,
                    last_seen_commit=ledger.commit_sha,
                    state_history=[
                        {
                            "state": "candidate",
                            "run_id": ledger.audit_run_id,
                            "commit_sha": ledger.commit_sha,
                            "actor": hunter_id,
                            "reason": "Discovered during Phase 2 coverage-led hunting.",
                        }
                    ],
                )
                candidates.append(finding)
                if fid not in unit_findings:
                    unit_findings.append(fid)
                if fp not in unit_fps:
                    unit_fps.append(fp)

        if not reviewed:
            unit.status = "not_applicable"
            unit.investigator_id = None
            unit.limitations = ["No regular source files remained present for unit."]
        else:
            unit.reviewed_paths = sorted(set(reviewed))
            unit.checks = [
                CoverageCheck(
                    investigator_id=hunter_id,
                    method="source",
                    reviewed_paths=tuple(unit.reviewed_paths),
                    invariant=cls_def.defensive_invariants[0],
                    result=(
                        f"Examined {len(unit.reviewed_paths)} file(s); "
                        f"{len(unit_findings)} candidate(s) recorded."
                    ),
                    evidence_refs=tuple(unit.reviewed_paths),
                    artifact_path=None,
                    timestamp=_utc_now(),
                )
            ]
            unit.finding_ids = sorted(unit_findings)
            unit.candidate_fingerprints = sorted(unit_fps)
            unit.limitations = []
            unit.status = "examined"

    critic_report = run_coverage_critic(project_root=resolved, ledger=ledger, dispatcher=dispatcher)
    comp = ledger.compute_completeness()
    if comp["blocked"] > 0:
        ledger.audit_status = "blocked"
    elif comp["is_complete"] and not critic_report["unmapped_files"]:
        ledger.audit_status = "completed"
    else:
        ledger.audit_status = "partially_completed"

    collection = FindingsCollection(
        audit_run_id=ledger.audit_run_id,
        commit_sha=ledger.commit_sha,
        records=candidates,
    )
    collection.deduplicate_and_sort()
    return collection


def run_coverage_critic(
    *,
    project_root: Path,
    ledger: CoverageLedger,
    dispatcher: SecurityAuditTaskDispatcher,
) -> dict[str, Any]:
    """Post-wave Coverage Analyst check detecting unmapped source files or incomplete units."""
    critic_id = "coverage-critic-01"
    dispatcher.assign(
        agent_id=critic_id,
        role=AuditRole.COVERAGE_ANALYST,
        wave=1,
        targets=("coverage-ledger",),
    )
    covered_files: set[str] = set()
    for unit in ledger.units:
        covered_files.update(unit.reviewed_paths)
        if unit.status in {"not_examined", "not_applicable"}:
            covered_files.update(unit.starting_paths)

    all_files = {
        str(p.relative_to(project_root.resolve())).replace("\\", "/")
        for p in _iter_source_files(project_root.resolve())
    }
    unmapped = sorted(all_files - covered_files)
    gaps = ledger.detect_gaps()
    return {
        "critic_id": critic_id,
        "unmapped_files": unmapped,
        "gap_units": gaps,
        "clean": not unmapped and not gaps,
    }


def write_reconnaissance_artifacts(
    audit_dir: Path,
    inventory: ArchitectureInventory,
    ledger: CoverageLedger,
) -> tuple[Path, Path, Path]:
    """Write architecture.json, architecture.md, and initial coverage-ledger.json."""
    audit_dir.mkdir(parents=True, exist_ok=True)
    arch_json = audit_dir / "architecture.json"
    arch_md = audit_dir / "architecture.md"
    ledger_json = audit_dir / "coverage-ledger.json"
    arch_json.write_text(json.dumps(inventory.to_dict(), indent=2) + "\n", encoding="utf-8")
    arch_md.write_text(inventory.render_markdown(), encoding="utf-8")
    ledger.save(ledger_json)
    return arch_json, arch_md, ledger_json
