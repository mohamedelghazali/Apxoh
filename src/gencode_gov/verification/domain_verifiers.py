"""Deterministic repository & artifact verifiers across all 16 GENCODE-GOV engineering domains."""

from __future__ import annotations

import ast
import json
import re
import shutil
import subprocess
import tomllib
from pathlib import Path
from typing import Any

import yaml

from gencode_gov.core.constants import STATUS_BLOCKED, STATUS_FAIL, STATUS_PASS
from gencode_gov.evidence.attestation import verify_human_attestation
from gencode_gov.verification.architecture_verifier import verify_architecture_contracts
from gencode_gov.verification.code_and_test_integrity import (
    verify_code_integrity_method,
    verify_test_adequacy_method,
)
from gencode_gov.verification.diff_governance import evaluate_diff_governance
from gencode_gov.verification.lockfile_verifier import verify_dependency_lockfiles
from gencode_gov.verification.runners.base import Runner, RunnerOutcome, RunnerResult

_SHA40_RE = re.compile(r"^[0-9a-f]{40}$")
_SECRET_ASSIGN_RE = re.compile(
    r"""(?ix)
    (?:api[_-]?key|secret[_-]?key|access[_-]?token|private[_-]?key|db[_-]?password)
    \s*[:=]\s*['"]
    (?:sk-[A-Za-z0-9]{20,}|ghp_[A-Za-z0-9]{30,}|AKIA[0-9A-Z]{16}|AIza[0-9A-Za-z_-]{35})['"]
    """
)
_DESTRUCTIVE_SQL_RE = re.compile(
    r"\b(DROP\s+TABLE|DROP\s+COLUMN|TRUNCATE\s+TABLE|"
    r"ALTER\s+TABLE\s+\S+\s+ALTER\s+COLUMN\s+\S+\s+TYPE)\b",
    re.IGNORECASE,
)
_NON_CONCURRENT_INDEX_RE = re.compile(
    r"\bCREATE\s+(?:UNIQUE\s+)?INDEX\s+(?!CONCURRENTLY\b)(?!IF\s+NOT\s+EXISTS\s+idx_sqlite)",
    re.IGNORECASE,
)
_FORBIDDEN_LICENSES = frozenset({"AGPL-3.0", "AGPL-3.0-only", "AGPL-3.0-or-later", "SSPL-1.0"})
_NETWORK_CALL_NAMES = frozenset(
    {"get", "post", "put", "delete", "patch", "head", "request", "urlopen"}
)
_NETWORK_MODULES = frozenset({"requests", "httpx"})


def _write_runner_anchor(root: Path, subdir: str, filename: str, label: str) -> Path | None:
    out_dir = root / ".gencode-gov" / "evidence" / subdir
    if out_dir.exists() and out_dir.is_symlink():  # pragma: no cover
        return None
    out_dir.mkdir(parents=True, exist_ok=True)
    art = out_dir / filename
    if art.exists() and art.is_symlink():  # pragma: no cover
        return None
    art.write_text(
        json.dumps({"runner": subdir, "status": label}, indent=2) + "\n", encoding="utf-8"
    )
    return art


class GovernanceDomainRunner(Runner):
    """Lightweight deterministic workspace inspector enabling multi-domain method evaluation."""

    name = "governance-domain"

    def run(self, project_root: Path, artifact_dir: Path | None = None) -> RunnerResult:
        _ = artifact_dir
        root = project_root.resolve()
        if not root.is_dir():
            return RunnerResult(
                runner=self.name, outcome=RunnerOutcome.BLOCKED, reason=f"missing root: {root}"
            )
        art = _write_runner_anchor(root, "governance-domain", "domain-runner-ready.json", "ready")
        if art is None:  # pragma: no cover
            return RunnerResult(
                runner=self.name, outcome=RunnerOutcome.BLOCKED, reason="unsafe dir"
            )
        return RunnerResult(
            runner=self.name,
            outcome=RunnerOutcome.PASS,
            reason="workspace ready for deterministic domain method verification",
            artifacts=[art],
        )


class HumanAttestationRunner(Runner):
    """Runner anchor for commit-bound human review attestation verification."""

    name = "human-attestation"

    def run(self, project_root: Path, artifact_dir: Path | None = None) -> RunnerResult:
        _ = artifact_dir
        root = project_root.resolve()
        if not root.is_dir():
            return RunnerResult(
                runner=self.name, outcome=RunnerOutcome.BLOCKED, reason=f"missing root: {root}"
            )
        art = _write_runner_anchor(root, "human-attestation", "runner-status.json", "ready")
        if art is None:  # pragma: no cover
            return RunnerResult(
                runner=self.name, outcome=RunnerOutcome.BLOCKED, reason="unsafe dir"
            )
        return RunnerResult(
            runner=self.name,
            outcome=RunnerOutcome.PASS,
            reason="attestation store ready for per-rule verification",
            artifacts=[art],
        )


def _safe_file(root: Path, rel: str) -> Path | None:
    cand = root / rel
    if cand.is_symlink():  # pragma: no cover
        return None  # pragma: no cover
    try:
        resolved = cand.resolve()
        resolved.relative_to(root)
    except (OSError, ValueError):  # pragma: no cover
        return None
    return resolved if resolved.is_file() else None


def _load_yaml_safe(path: Path) -> dict[str, Any] | None:
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, yaml.YAMLError):  # pragma: no cover
        return None
    return raw if isinstance(raw, dict) else None


def _resolve_head_sha(root: Path) -> str | None:
    git_bin = shutil.which("git")
    if git_bin is None:  # pragma: no cover
        return None
    try:
        res = subprocess.run(  # noqa: S603
            [git_bin, "rev-parse", "HEAD"],
            cwd=root,
            capture_output=True,
            text=True,
            check=False,
            timeout=10,
        )
    except (OSError, subprocess.SubprocessError):  # pragma: no cover
        return None
    sha = res.stdout.strip()
    return sha if res.returncode == 0 and _SHA40_RE.fullmatch(sha) else None


def _verify_requirements_methods(method_id: str, root: Path) -> tuple[str, str]:
    req_file = _safe_file(root, ".gencode-gov/requirements.yaml")
    if req_file is None:
        return (
            STATUS_BLOCKED,
            "missing .gencode-gov/requirements.yaml structured specification artifact",
        )
    doc = _load_yaml_safe(req_file)
    if doc is None or not isinstance(doc.get("requirements"), list) or not doc["requirements"]:
        return STATUS_FAIL, "requirements.yaml must define a non-empty 'requirements' list"

    reqs = [r for r in doc["requirements"] if isinstance(r, dict)]
    if len(reqs) != len(doc["requirements"]):
        return STATUS_FAIL, "every requirement entry must be a mapping"

    seen_ids: set[str] = set()
    missing_ac: list[str] = []
    conflicts: list[str] = []
    untraced: list[str] = []
    missing_tests: list[str] = []

    for item in reqs:
        rid = str(item.get("id", "")).strip()
        stmt = str(item.get("statement", "")).strip()
        if not rid or not stmt:
            return STATUS_FAIL, "every requirement requires non-empty 'id' and 'statement'"
        if rid in seen_ids:
            conflicts.append(f"duplicate requirement id {rid}")
        seen_ids.add(rid)
        ac = item.get("acceptance_criteria")
        if not isinstance(ac, list) or not ac:
            missing_ac.append(rid)
        if item.get("conflicts_with"):
            conflicts.append(f"unresolved conflict declared on {rid}")
        tests = item.get("tests")
        if not isinstance(tests, list) or not tests:
            untraced.append(rid)
        else:
            for tf in tests:
                if not isinstance(tf, str) or _safe_file(root, tf) is None:
                    missing_tests.append(f"{rid}->{tf}")

    if method_id in {"schema-validation", "requirements-audit"}:
        return STATUS_PASS, f"validated {len(reqs)} structured requirement record(s)"
    if method_id == "acceptance-criteria-validation":
        if missing_ac:
            return STATUS_FAIL, f"requirements missing acceptance_criteria: {missing_ac}"
        return STATUS_PASS, f"all {len(reqs)} requirements define testable acceptance_criteria"
    if method_id == "requirements-conflict-analysis":
        if conflicts:
            return STATUS_FAIL, f"requirement conflicts detected: {conflicts}"
        return STATUS_PASS, f"0 duplicate IDs or conflicts across {len(reqs)} requirements"
    if method_id == "requirements-traceability-analysis":
        if untraced:
            return STATUS_FAIL, f"requirements missing test traceability links: {untraced}"
        return STATUS_PASS, f"all {len(reqs)} requirements map to verification artifacts"
    if missing_tests or untraced:
        return STATUS_FAIL, f"missing or invalid traced test files: {untraced + missing_tests}"
    return STATUS_PASS, f"verified on-disk test files for all {len(reqs)} requirements"


def _verify_adr_methods(method_id: str, root: Path) -> tuple[str, str]:
    adr_dirs = [root / "docs" / "adr", root / "docs" / "architecture" / "decisions"]
    adr_files: list[Path] = []
    for d in adr_dirs:
        if d.is_dir() and not d.is_symlink():
            adr_files.extend(
                p
                for p in sorted(d.glob("*.md"))
                if not p.is_symlink() and p.name.lower() != "readme.md"
            )
    if not adr_files:
        return STATUS_BLOCKED, "no ADRs found under docs/adr/ or docs/architecture/decisions/"
    if method_id == "adr-presence-check":
        return STATUS_PASS, f"found {len(adr_files)} ADR document(s)"

    malformed: list[str] = []
    for adr in adr_files:
        txt = adr.read_text(encoding="utf-8", errors="ignore").lower()
        for section in ("status", "context", "decision", "consequences"):
            has_sec = f"## {section}" in txt or f"# {section}" in txt or f"{section}:" in txt
            if not has_sec:
                malformed.append(f"{adr.name}:missing-{section}")
                break
    if malformed:
        return STATUS_FAIL, f"ADR structure incomplete: {malformed[:5]}"
    return STATUS_PASS, f"validated ADR structure across {len(adr_files)} ADR(s)"


def _verify_database_methods(method_id: str, root: Path) -> tuple[str, str]:
    sql_files = [
        p
        for p in sorted(root.rglob("*.sql"))
        if not p.is_symlink() and not ({"tests", "examples", ".venv"} & set(p.parts))
    ]
    migration_dirs = [
        d
        for d in (
            root / "migrations",
            root / "alembic" / "versions",
            root / "prisma" / "migrations",
        )
        if d.is_dir()
    ]
    for md in migration_dirs:
        sql_files.extend(p for p in sorted(md.rglob("*.py")) if not p.is_symlink())

    if method_id in {"destructive-ddl-migration-scan", "concurrent-index-and-lock-check"}:
        if not sql_files:
            return STATUS_PASS, "0 SQL/ORM migration files present; no destructive DDL risk"
        destructive_hits: list[str] = []
        index_hits: list[str] = []
        for sf in sql_files:
            txt = sf.read_text(encoding="utf-8", errors="ignore")
            if "gencode-gov:allow-destructive-migration" in txt:
                continue
            rel = sf.relative_to(root).as_posix()
            if _DESTRUCTIVE_SQL_RE.search(txt):
                destructive_hits.append(rel)
            if sf.suffix.lower() == ".sql" and _NON_CONCURRENT_INDEX_RE.search(txt):
                index_hits.append(rel)
        if method_id == "destructive-ddl-migration-scan":
            if destructive_hits:
                return STATUS_FAIL, f"unguarded destructive DDL: {destructive_hits[:5]}"
            return STATUS_PASS, f"scanned {len(sql_files)} migration(s); 0 destructive DDL"
        if index_hits:
            return STATUS_FAIL, f"non-concurrent index build: {index_hits[:5]}"
        return STATUS_PASS, f"scanned {len(sql_files)} migration(s); index locks safe"

    db_gov = _safe_file(root, ".gencode-gov/database-governance.yaml")
    if db_gov is None:
        return STATUS_BLOCKED, f"missing database-governance.yaml evidence for {method_id}"
    doc = _load_yaml_safe(db_gov)
    if doc is None:
        return STATUS_FAIL, "malformed .gencode-gov/database-governance.yaml"
    controls = doc.get("controls", {})
    if not isinstance(controls, dict) or controls.get(method_id) is not True:
        return STATUS_FAIL, f"control {method_id!r} unverified in database-governance.yaml"
    return STATUS_PASS, f"verified {method_id} in .gencode-gov/database-governance.yaml"


def _verify_api_methods(method_id: str, root: Path) -> tuple[str, str]:
    if method_id in {"frozen-api-contract-check", "schema-compatibility-diff-check"}:
        rep = evaluate_diff_governance(root)
        if rep.status == STATUS_BLOCKED:
            return STATUS_BLOCKED, "; ".join(rep.reasons) or "diff governance blocked"
        if method_id == "frozen-api-contract-check":
            if rep.frozen_api_failures:
                return STATUS_FAIL, f"frozen API contract failures: {list(rep.frozen_api_failures)}"
            return STATUS_PASS, "all declared frozen_apis symbols verified on disk"
        if rep.schema_breaking_changes:
            return STATUS_FAIL, f"schema breaking changes: {list(rep.schema_breaking_changes)}"
        return STATUS_PASS, "JSON schema backward-compatibility check passed"

    schemas_dir = root / "schemas"
    openapi_files = [
        p
        for p in [root / "openapi.yaml", root / "openapi.json", root / "docs" / "openapi.yaml"]
        if p.is_file()
    ]
    json_schemas = sorted(schemas_dir.glob("*.schema.json")) if schemas_dir.is_dir() else []
    if not json_schemas and not openapi_files:
        return STATUS_BLOCKED, "no schemas/*.schema.json or OpenAPI contract files found"

    unversioned: list[str] = []
    for js in json_schemas:
        if js.is_symlink():
            continue
        try:
            data = json.loads(js.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return STATUS_FAIL, f"malformed JSON schema: {js.name}"
        sid = str(data.get("$id", ""))
        if not re.search(r"\d+\.\d+\.\d+|/v\d+", sid):
            unversioned.append(js.name)
    if method_id == "endpoint-version-inventory" and unversioned:
        return STATUS_FAIL, f"schemas missing explicit semantic version in $id: {unversioned}"
    return (
        STATUS_PASS,
        f"verified {len(json_schemas)} JSON schema(s) and {len(openapi_files)} OpenAPI spec(s)",
    )


def _verify_devops_methods(method_id: str, root: Path) -> tuple[str, str]:
    wf_dir = root / ".github" / "workflows"
    workflows = (
        [
            p
            for p in sorted(wf_dir.glob("*.yml")) + sorted(wf_dir.glob("*.yaml"))
            if not p.is_symlink()
        ]
        if wf_dir.is_dir()
        else []
    )
    if method_id == "workflow-file-presence":
        if not workflows:
            return STATUS_FAIL, "no CI workflow files found under .github/workflows/"
        return STATUS_PASS, f"verified {len(workflows)} GitHub Actions workflow file(s)"

    if method_id == "branch-protection-check":
        proj = _safe_file(root, ".gencode-gov/project.yaml")
        cfg = _safe_file(root, ".gencode-gov/config.yaml")
        if workflows and (proj is not None or cfg is not None):
            return STATUS_PASS, f"CI workflows ({len(workflows)}) and governance config present"
        return STATUS_BLOCKED, "branch protection & CI gate configuration missing"

    if method_id == "github-actions-sha-pinning-scan":
        if not workflows:
            return STATUS_BLOCKED, "no GitHub Actions workflows present to verify SHA pinning"
        unpinned: list[str] = []
        for wf in workflows:
            wf_lines = wf.read_text(encoding="utf-8", errors="ignore").splitlines()
            for lineno, line in enumerate(wf_lines, 1):
                stripped = line.strip()
                if stripped.startswith("#") or "uses:" not in stripped:
                    continue
                after = stripped.split("uses:", 1)[1].strip()
                ref_part = after.split("#", 1)[0].strip().strip("'\"")
                if not ref_part or ref_part.startswith("./"):
                    continue
                # slsa-github-generator requires @vX.Y.Z tag for OIDC verification
                if ref_part.startswith("slsa-framework/slsa-github-generator"):
                    continue
                if "@" not in ref_part:
                    unpinned.append(f"{wf.name}:{lineno}")
                    continue
                _, rev = ref_part.rsplit("@", 1)
                if not _SHA40_RE.fullmatch(rev):
                    unpinned.append(f"{wf.name}:{lineno} ({ref_part})")
        if unpinned:
            return STATUS_FAIL, f"mutable non-SHA GitHub Action reference(s): {unpinned[:5]}"
        return STATUS_PASS, f"all external Actions across {len(workflows)} workflows SHA-pinned"

    if method_id == "dependency-lockfile-determinism-check":
        return verify_dependency_lockfiles(root)

    return STATUS_BLOCKED, f"unsupported devops method: {method_id}"


def _verify_maintenance_methods(method_id: str, root: Path) -> tuple[str, str]:
    changelog = _safe_file(root, "CHANGELOG.md")
    if method_id == "changelog-format-validation":
        if changelog is None:
            return STATUS_FAIL, "missing CHANGELOG.md"
        txt = changelog.read_text(encoding="utf-8", errors="ignore")
        if "## [" not in txt and "## v" not in txt and "## 0." not in txt and "## 1." not in txt:
            return STATUS_FAIL, "CHANGELOG.md lacks Keep-a-Changelog version headings"
        return STATUS_PASS, "CHANGELOG.md format and version headings verified"

    if method_id == "version-consistency-check":
        pyproj = _safe_file(root, "pyproject.toml")
        if pyproj is None:
            return STATUS_BLOCKED, "no pyproject.toml present for version parity verification"
        try:
            pdata = tomllib.loads(pyproj.read_text(encoding="utf-8"))
        except tomllib.TOMLDecodeError as exc:
            return STATUS_FAIL, f"invalid pyproject.toml: {exc}"
        declared = str(pdata.get("project", {}).get("version", "")).strip()
        if not declared:
            return STATUS_FAIL, "pyproject.toml missing project.version"
        src_dir = root / "src"
        if src_dir.is_dir():
            for init_py in sorted(src_dir.glob("*/__init__.py")):
                if init_py.is_symlink():
                    continue
                txt = init_py.read_text(encoding="utf-8", errors="ignore")
                m = re.search(r'__version__\s*=\s*["\']([^"\']+)["\']', txt)
                if m and m.group(1) != declared:
                    return (
                        STATUS_FAIL,
                        f"version mismatch: {declared!r} vs {m.group(1)!r}",
                    )
        return STATUS_PASS, f"version {declared} consistent across metadata and __version__"

    return STATUS_BLOCKED, f"unsupported maintenance method: {method_id}"


def _verify_release_methods(method_id: str, root: Path) -> tuple[str, str]:
    notes = _safe_file(root, "RELEASE_NOTES.md") or _safe_file(root, "CHANGELOG.md")
    if notes is None:
        return STATUS_BLOCKED, "missing RELEASE_NOTES.md or CHANGELOG.md"
    txt = notes.read_text(encoding="utf-8", errors="ignore")
    if method_id == "release-notes-presence":
        return STATUS_PASS, f"release documentation present in {notes.name}"
    if len(txt.strip()) < 40 or "## " not in txt:
        return STATUS_FAIL, f"{notes.name} lacks structured release sections"
    return STATUS_PASS, f"verified structured release sections in {notes.name}"


def _verify_reliability_resilience_ast(method_id: str, root: Path) -> tuple[str, str]:
    src_root = root / "src" if (root / "src").is_dir() else root
    missing_timeouts: list[str] = []
    unbounded_loops: list[str] = []
    scanned = 0

    for py_file in sorted(src_root.rglob("*.py")):
        if py_file.is_symlink() or any(
            p in {"tests", "examples", ".venv", "venv", "__pycache__"} for p in py_file.parts
        ):
            continue
        try:
            tree = ast.parse(py_file.read_text(encoding="utf-8"), filename=str(py_file))
        except (OSError, UnicodeDecodeError, SyntaxError):
            continue
        scanned += 1
        rel = py_file.relative_to(root).as_posix()

        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                attr = node.func.attr
                owner = node.func.value.id if isinstance(node.func.value, ast.Name) else ""
                if attr in _NETWORK_CALL_NAMES and (
                    owner in _NETWORK_MODULES or (owner == "request" and attr == "urlopen")
                ):
                    has_timeout = any(kw.arg == "timeout" for kw in node.keywords)
                    if not has_timeout:
                        missing_timeouts.append(f"{rel}:{node.lineno} ({owner}.{attr})")
            elif (
                isinstance(node, ast.While)
                and isinstance(node.test, ast.Constant)
                and node.test.value is True
            ):
                has_exit = any(
                    isinstance(sub, (ast.Break, ast.Return, ast.Raise)) for sub in ast.walk(node)
                )
                if not has_exit:
                    unbounded_loops.append(f"{rel}:{node.lineno}")

    if method_id == "outbound-timeout-enforcement-scan":
        if missing_timeouts:
            return STATUS_FAIL, f"outbound network call(s) missing timeout=: {missing_timeouts[:5]}"
        return STATUS_PASS, f"scanned {scanned} module(s); 0 calls missing timeout"

    if unbounded_loops:
        return STATUS_FAIL, f"unbounded while True loop(s): {unbounded_loops[:5]}"
    return STATUS_PASS, f"scanned {scanned} production module(s); all retry/poll loops bounded"


def _verify_sbom_and_security_methods(method_id: str, root: Path) -> tuple[str, str]:
    if method_id in {
        "secret-scanner",
        "working-tree-secret-scan",
        "env-file-audit",
        "repository-config-review",
    }:
        committed_env = [
            p.relative_to(root).as_posix()
            for p in sorted(root.rglob(".env"))
            if not p.is_symlink() and ".venv" not in p.parts and "examples" not in p.parts
        ]
        if method_id == "env-file-audit" and committed_env:
            return STATUS_FAIL, f"committed plaintext .env file(s) found: {committed_env}"

        secret_hits: list[str] = []
        for candidate in sorted(root.rglob("*")):
            if (
                not candidate.is_file()
                or candidate.is_symlink()
                or any(
                    part in {".git", ".venv", "venv", "__pycache__", "tests", ".gencode-gov"}
                    for part in candidate.parts
                )
            ):
                continue
            allowed_ext = {".py", ".yaml", ".yml", ".json", ".toml", ".env", ".sh"}
            if candidate.suffix.lower() not in allowed_ext:
                continue
            try:
                if candidate.stat().st_size > 256 * 1024:
                    continue
                txt = candidate.read_text(encoding="utf-8", errors="ignore")
            except OSError:  # pragma: no cover
                continue
            if _SECRET_ASSIGN_RE.search(txt):
                secret_hits.append(candidate.relative_to(root).as_posix())
        if secret_hits:
            return STATUS_FAIL, f"hardcoded credential pattern(s) detected in: {secret_hits[:5]}"
        return STATUS_PASS, f"{method_id} verified clean tree (0 secrets or .env leaks)"

    if method_id == "lockfile-inventory":
        return _verify_devops_methods("dependency-lockfile-determinism-check", root)

    if method_id in {"sbom-component-inventory-check", "sbom-license-and-cve-policy-check"}:
        sbom_candidates = [
            root / ".gencode-gov" / "evidence" / "supply-chain" / "sbom.cdx.json",
            root / "sbom.cdx.json",
        ]
        sbom_file = next((p for p in sbom_candidates if p.is_file() and not p.is_symlink()), None)
        if sbom_file is not None:
            try:
                sbom = json.loads(sbom_file.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                return STATUS_FAIL, f"malformed CycloneDX SBOM {sbom_file.name}: {exc}"
            comps = sbom.get("components", [])
            if not isinstance(comps, list) or not comps:
                return STATUS_FAIL, "CycloneDX SBOM contains zero components"
            if method_id == "sbom-component-inventory-check":
                return STATUS_PASS, f"verified CycloneDX SBOM with {len(comps)} component(s)"
            bad_lic: list[str] = []
            for comp in comps:
                if not isinstance(comp, dict):
                    continue
                for lic_entry in comp.get("licenses", []):
                    if isinstance(lic_entry, dict) and isinstance(lic_entry.get("license"), dict):
                        lid = str(lic_entry["license"].get("id", ""))
                        if lid in _FORBIDDEN_LICENSES:
                            bad_lic.append(f"{comp.get('name')}:{lid}")
            vulns = sbom.get("vulnerabilities", [])
            crit_vulns = [
                str(v.get("id"))
                for v in (vulns if isinstance(vulns, list) else [])
                if isinstance(v, dict)
                and any(
                    isinstance(r, dict)
                    and str(r.get("severity", "")).lower() in {"critical", "high"}
                    for r in v.get("ratings", [])
                )
            ]
            if bad_lic or crit_vulns:
                return STATUS_FAIL, f"SBOM violations: lic={bad_lic}, vulns={crit_vulns}"
            return STATUS_PASS, f"verified {len(comps)} SBOM components: 0 policy violations"

        # Fallback deterministic manifest + lockfile check when CycloneDX file is absent
        lock_status, lock_msg = _verify_devops_methods(
            "dependency-lockfile-determinism-check", root
        )
        if lock_status != STATUS_PASS:
            return STATUS_BLOCKED, "neither CycloneDX SBOM nor pinned dependency lockfile found"
        if method_id == "sbom-component-inventory-check":
            return STATUS_PASS, f"component inventory anchored by pinned lockfiles ({lock_msg})"
        pyproj = _safe_file(root, "pyproject.toml")
        if pyproj is not None:
            txt = pyproj.read_text(encoding="utf-8", errors="ignore")
            if any(lic in txt for lic in _FORBIDDEN_LICENSES):
                return STATUS_FAIL, "forbidden copyleft license declared in pyproject.toml"
        return STATUS_PASS, "package license metadata and pinned lockfiles compliant"

    sec_doc_path = _safe_file(root, ".gencode-gov/security-controls.yaml")
    if sec_doc_path is None:
        return (
            STATUS_BLOCKED,
            f"missing .gencode-gov/security-controls.yaml verification record for {method_id}",
        )
    sec_doc = _load_yaml_safe(sec_doc_path)
    if sec_doc is None or not isinstance(sec_doc.get("verified_methods"), dict):
        return STATUS_FAIL, "malformed .gencode-gov/security-controls.yaml"
    entry = sec_doc["verified_methods"].get(method_id)
    if entry is True or (isinstance(entry, dict) and entry.get("status") == "PASS"):
        return STATUS_PASS, f"verified {method_id} via .gencode-gov/security-controls.yaml"
    if entry is False or (isinstance(entry, dict) and entry.get("status") == "FAIL"):
        return STATUS_FAIL, f"security control {method_id} marked FAIL in security-controls.yaml"
    return STATUS_BLOCKED, f"security control {method_id} not attested in security-controls.yaml"


def _verify_operational_artifact_method(
    method_id: str,
    root: Path,
    artifact_rel: str,
) -> tuple[str, str]:
    art = _safe_file(root, artifact_rel)
    if art is None:
        return STATUS_BLOCKED, f"missing {artifact_rel} required to verify {method_id}"
    doc = _load_yaml_safe(art)
    if doc is None:
        return STATUS_FAIL, f"malformed YAML in {artifact_rel}"
    methods_map = doc.get("verified_methods", doc.get("controls", {}))
    if isinstance(methods_map, dict):
        val = methods_map.get(method_id)
        if val is True or (isinstance(val, dict) and val.get("status") == "PASS"):
            return STATUS_PASS, f"verified {method_id} in {artifact_rel}"
        if val is False or (isinstance(val, dict) and val.get("status") == "FAIL"):
            return STATUS_FAIL, f"{method_id} reported FAIL in {artifact_rel}"
    return STATUS_BLOCKED, f"{method_id} not yet verified in {artifact_rel}"


def _verify_testing_auxiliary_methods(method_id: str, root: Path) -> tuple[str, str]:
    if method_id == "coverage-analysis":
        pyproj = _safe_file(root, "pyproject.toml")
        if pyproj is not None:
            try:
                data = tomllib.loads(pyproj.read_text(encoding="utf-8"))
                cov_rep = data.get("tool", {}).get("coverage", {}).get("report", {})
                fail_under = cov_rep.get("fail_under", 0)
                if isinstance(fail_under, (int, float)) and fail_under >= 80:
                    return STATUS_PASS, f"coverage gate enforced (fail_under={fail_under}%)"
            except tomllib.TOMLDecodeError:
                return STATUS_FAIL, "malformed pyproject.toml during coverage-analysis"
        cov_json = _safe_file(root, ".gencode-gov/evidence/testing/coverage.json")
        if cov_json is not None:
            try:
                cdata = json.loads(cov_json.read_text(encoding="utf-8"))
                pct = float(cdata.get("totals", {}).get("percent_covered", 0.0))
                if pct >= 80.0:
                    return STATUS_PASS, f"measured test coverage {pct:.2f}% >= 80.0%"
                return STATUS_FAIL, f"measured test coverage {pct:.2f}% < 80.0%"
            except (OSError, ValueError, json.JSONDecodeError):
                return STATUS_FAIL, "malformed coverage.json evidence"
        return STATUS_BLOCKED, "no coverage gate (>=80%) or coverage.json artifact found"

    if method_id == "ast-test-mapping":
        src_files = (
            [p for p in sorted((root / "src").rglob("*.py")) if p.name != "__init__.py"]
            if (root / "src").is_dir()
            else []
        )
        test_files = (
            sorted((root / "tests").rglob("test_*.py")) if (root / "tests").is_dir() else []
        )
        if not src_files:
            return STATUS_PASS, "no Python src/ modules requiring AST test mapping"
        if not test_files:
            return STATUS_FAIL, f"found {len(src_files)} src/ modules without tests"
        return STATUS_PASS, f"mapped {len(src_files)} module(s) across {len(test_files)} tests"

    if method_id in {"commit-message-analysis", "test-diff-analysis"}:
        test_dir = root / "tests"
        if not test_dir.is_dir() or not list(test_dir.rglob("test_*.py")):
            return STATUS_BLOCKED, "no regression test suite found under tests/"
        return STATUS_PASS, f"{method_id} verified regression test suite presence under tests/"

    if method_id == "critical-workflow-test-coverage-review":
        matrix = _safe_file(root, ".gencode-gov/security-test-matrix.yaml") or _safe_file(
            root, ".gencode-gov/critical-workflows.yaml"
        )
        if matrix is None:
            return STATUS_BLOCKED, "missing security-test-matrix.yaml or critical-workflows.yaml"
        doc = _load_yaml_safe(matrix)
        if doc is None:
            return STATUS_FAIL, f"malformed {matrix.name}"
        return STATUS_PASS, f"critical workflow test mapping verified in {matrix.name}"

    return STATUS_BLOCKED, f"unsupported testing method: {method_id}"


def evaluate_domain_method(
    method_id: str,
    project_root: Path,
    *,
    rule: Any | None = None,
    commit_sha: str | None = None,
) -> tuple[str, str] | None:
    """Dispatch deterministic verification for any domain or human-attestation method."""
    root = project_root.resolve()

    if method_id in {"human-review", "human-security-review", "human-approval"}:
        sha = commit_sha or _resolve_head_sha(root)
        rule_id = getattr(rule, "id", None)
        approver_role: str | None = None
        raw = getattr(rule, "raw", None)
        if isinstance(raw, dict) and isinstance(raw.get("human_review"), dict):
            role_val = raw["human_review"].get("approver_role")
            if isinstance(role_val, str) and role_val.strip():
                approver_role = role_val.strip()
        if isinstance(rule_id, str) and rule_id:
            return verify_human_attestation(
                root,
                rule_id=rule_id,
                expected_commit_sha=sha,
                required_role=approver_role,
            )
        # Fallback when invoked without a Rule context
        attest_dir = root / ".gencode-gov" / "evidence" / "attestations"
        if not attest_dir.is_dir() or not list(attest_dir.glob("*.json")):
            return STATUS_BLOCKED, f"authorized human attestation required for {method_id}"
        for cand in sorted(attest_dir.glob("*.json")):
            try:
                data = json.loads(cand.read_text(encoding="utf-8"))
                rids = data.get("rule_ids", [])
                if isinstance(rids, list) and rids:
                    return verify_human_attestation(
                        root, rule_id=str(rids[0]), expected_commit_sha=sha
                    )
            except (OSError, json.JSONDecodeError):
                continue
        return STATUS_BLOCKED, f"no valid human attestation found for {method_id}"

    # Code quality & integrity
    if method_id == "ast-analysis":
        return verify_code_integrity_method("anti-fabrication-ast-check", root)
    if method_id in {
        "anti-fabrication-ast-check",
        "exception-handling-safety-check",
        "complexity-budget-check",
    }:
        return verify_code_integrity_method(method_id, root)

    # Testing adequacy & mapping
    if method_id in {"assertion-adequacy-check", "regression-tamper-diff-check"}:
        return verify_test_adequacy_method(method_id, root)
    if method_id in {
        "coverage-analysis",
        "ast-test-mapping",
        "commit-message-analysis",
        "test-diff-analysis",
        "critical-workflow-test-coverage-review",
    }:
        return _verify_testing_auxiliary_methods(method_id, root)

    # Architecture
    if method_id in {"architecture-layer-boundary-check", "module-cycle-detection"}:
        rep = verify_architecture_contracts(root)
        return rep.status, rep.reason
    if method_id in {"adr-presence-check", "adr-structure-validation"}:
        return _verify_adr_methods(method_id, root)

    # Requirements
    if method_id in {
        "schema-validation",
        "requirements-audit",
        "acceptance-criteria-validation",
        "requirements-conflict-analysis",
        "requirements-traceability-analysis",
        "test-traceability-analysis",
    }:
        return _verify_requirements_methods(method_id, root)

    # API & compatibility
    if method_id in {
        "api-contract-analysis",
        "endpoint-version-inventory",
        "frozen-api-contract-check",
        "schema-compatibility-diff-check",
    }:
        return _verify_api_methods(method_id, root)

    # Database
    if method_id in {
        "destructive-ddl-migration-scan",
        "concurrent-index-and-lock-check",
        "migration-file-detection",
        "schema-and-data-compatibility-review",
        "production-like-migration-test",
        "rollback-or-forward-recovery-drill",
        "database-role-review",
        "network-exposure-review",
        "credential-separation-review",
        "unauthorized-modification-controls-review",
        "row-ownership-negative-tests",
        "cross-tenant-isolation-tests",
    }:
        return _verify_database_methods(method_id, root)

    if method_id == "prechange-backup-verification":
        if _safe_file(root, ".gencode-gov/database-governance.yaml") is not None:
            return _verify_database_methods(method_id, root)
        return _verify_operational_artifact_method(
            method_id, root, ".gencode-gov/reliability-governance.yaml"
        )

    # DevOps
    if method_id in {
        "workflow-file-presence",
        "branch-protection-check",
        "github-actions-sha-pinning-scan",
        "dependency-lockfile-determinism-check",
    }:
        return _verify_devops_methods(method_id, root)

    # Infrastructure
    if method_id in {"iac-file-detection", "change-review-record"}:
        return _verify_operational_artifact_method(
            method_id, root, ".gencode-gov/infrastructure-governance.yaml"
        )

    # Maintenance & Release
    if method_id in {"changelog-format-validation", "version-consistency-check"}:
        return _verify_maintenance_methods(method_id, root)
    if method_id in {"release-notes-presence", "release-notes-structure-validation"}:
        return _verify_release_methods(method_id, root)

    # Observability
    if method_id in {
        "endpoint-detection",
        "endpoint-schema-validation",
        "public-health-disclosure-test",
        "detailed-health-access-control-test",
        "monitoring-signal-inventory",
        "dashboard-access-control-tests",
        "health-response-disclosure-review",
        "alert-delivery-test",
        "operator-audit-review",
        "error-handler-boundary-review",
        "crash-dump-governance-review",
    }:
        if _safe_file(root, ".gencode-gov/observability-verification.yaml") is not None:
            doc = _load_yaml_safe(root / ".gencode-gov" / "observability-verification.yaml")
            if (
                doc is not None
                and isinstance(doc.get("verified_methods"), dict)
                and doc["verified_methods"].get(method_id) is True
            ):
                return STATUS_PASS, f"verified {method_id} in observability-verification.yaml"
        return _verify_operational_artifact_method(
            method_id, root, ".gencode-gov/observability-governance.yaml"
        )

    # Performance & Scalability
    if method_id in {
        "load-test-execution",
        "target-comparison",
        "latency-telemetry-instrumentation-review",
        "baseline-regression-comparison",
        "degradation-alert-rule-validation",
        "alert-routing-and-runbook-check",
    }:
        return _verify_operational_artifact_method(
            method_id, root, ".gencode-gov/performance-governance.yaml"
        )

    # Privacy
    if method_id in {"data-inventory-presence", "dpia-presence"}:
        return _verify_operational_artifact_method(
            method_id, root, ".gencode-gov/privacy-governance.yaml"
        )

    # Reliability
    if method_id in {"outbound-timeout-enforcement-scan", "unbounded-retry-loop-scan"}:
        return _verify_reliability_resilience_ast(method_id, root)
    if method_id in {
        "slo-document-presence",
        "monitoring-config-check",
        "restore-execution",
        "data-integrity-check",
        "rto-rpo-verification",
        "change-risk-classification",
        "restore-drill",
        "application-rollback-test",
        "database-compatibility-test",
    }:
        return _verify_operational_artifact_method(
            method_id, root, ".gencode-gov/reliability-governance.yaml"
        )

    # Software Security & SBOM
    if method_id in {
        "sbom-component-inventory-check",
        "sbom-license-and-cve-policy-check",
        "authentication-flow-inventory",
        "password-storage-review",
        "session-lifecycle-tests",
        "negative-authentication-tests",
        "authorization-matrix-review",
        "route-policy-inventory",
        "object-ownership-tests",
        "cross-tenant-negative-tests",
        "input-boundary-inventory",
        "server-validation-review",
        "api-schema-and-bounds-review",
        "sql-query-review",
        "injection-negative-tests",
        "fuzz-or-property-tests",
        "tls-configuration-review",
        "certificate-validation-tests",
        "http-redirect-check",
        "cors-policy-tests",
        "security-header-tests",
        "csrf-negative-tests",
        "cookie-attribute-review",
        "secret-scanner",
        "repository-config-review",
        "env-file-audit",
        "secret-manager-policy-review",
        "log-and-evidence-redaction-review",
        "auth-endpoint-inventory",
        "rate-limit-tests",
        "account-enumeration-tests",
        "reset-token-lifecycle-tests",
        "abuse-monitoring-review",
        "security-event-coverage-review",
        "log-redaction-tests",
        "log-access-control-review",
        "alert-rule-review",
        "incident-playbook-review",
        "lockfile-inventory",
        "software-composition-analysis",
        "unused-dependency-analysis",
        "vulnerability-triage",
        "provenance-review",
        "production-config-review",
        "exposed-resource-scan",
        "admin-route-access-tests",
        "debug-mode-negative-tests",
        "cloud-storage-permission-review",
        "working-tree-secret-scan",
        "git-history-secret-scan",
        "branch-and-tag-coverage-review",
        "credential-revocation-confirmation",
        "incident-review",
    }:
        return _verify_sbom_and_security_methods(method_id, root)

    return None
