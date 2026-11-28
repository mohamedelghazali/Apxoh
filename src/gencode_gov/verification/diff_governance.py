"""Change-set (base..head) governance, frozen API compatibility, and schema breaking-diff checks."""

from __future__ import annotations

import ast
import json
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from gencode_gov.core.constants import STATUS_BLOCKED, STATUS_FAIL, STATUS_PASS


@dataclass(frozen=True)
class DiffGovernanceReport:
    """Structured outcome for gencode-gov diff-check and SE-API-002."""

    status: str
    base_ref: str | None
    head_ref: str
    files_changed: int
    protected_touched: tuple[str, ...]
    deleted_tests: tuple[str, ...]
    frozen_api_failures: tuple[str, ...]
    schema_breaking_changes: tuple[str, ...]
    reasons: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "base_ref": self.base_ref,
            "head_ref": self.head_ref,
            "files_changed": self.files_changed,
            "protected_touched": list(self.protected_touched),
            "deleted_tests": list(self.deleted_tests),
            "frozen_api_failures": list(self.frozen_api_failures),
            "schema_breaking_changes": list(self.schema_breaking_changes),
            "reasons": list(self.reasons),
        }


def _symbol_defined_in_python(py_file: Path, symbol: str) -> bool:
    try:
        tree = ast.parse(py_file.read_text(encoding="utf-8"), filename=str(py_file))
    except (OSError, UnicodeDecodeError, SyntaxError):  # pragma: no cover
        return False
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            if node.name == symbol:
                return True
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == symbol:
                    return True
        elif isinstance(node, ast.ImportFrom):
            for alias in node.names:
                bound = alias.asname or alias.name
                if bound == symbol:
                    return True
    return False


def verify_frozen_apis(project_root: Path) -> tuple[str, str, tuple[str, ...]]:
    """Verify frozen_apis entrypoints declared in compatibility.yaml."""
    root = project_root.resolve()
    compat_candidates = [
        root / "manifest" / "compatibility.yaml",
        root / ".gencode-gov" / "compatibility.yaml",
    ]
    compat_file = next((p for p in compat_candidates if p.is_file() and not p.is_symlink()), None)
    if compat_file is None:
        return STATUS_PASS, "no frozen_apis contract declared; skipping frozen API check", ()

    try:
        raw = yaml.safe_load(compat_file.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        return STATUS_BLOCKED, f"cannot parse {compat_file.name}: {exc}", ()
    if not isinstance(raw, dict):
        return STATUS_BLOCKED, f"{compat_file.name} must be a YAML mapping", ()

    frozen = raw.get("frozen_apis", [])
    if not isinstance(frozen, list):
        return STATUS_BLOCKED, "frozen_apis must be a list", ()
    if not frozen:
        return STATUS_PASS, "0 frozen_apis declared", ()

    failures: list[str] = []
    for entry in frozen:
        if not isinstance(entry, str) or "::" not in entry:
            failures.append(f"malformed frozen_apis entry: {entry!r}")
            continue
        mod_spec, sym = entry.split("::", 1)
        candidates = [root / mod_spec]
        if mod_spec.endswith(".py"):
            candidates.append(root / mod_spec[:-3] / "__init__.py")
        else:
            normalized = mod_spec
            if normalized.startswith("src/"):
                pkg_part = normalized[4:].replace(".", "/")
                candidates.append(root / "src" / f"{pkg_part}.py")
                candidates.append(root / "src" / pkg_part / "__init__.py")
            candidates.append(root / f"{mod_spec}.py")
        found_path = next((c for c in candidates if c.is_file() and not c.is_symlink()), None)
        if found_path is None:
            failures.append(f"missing frozen API module for {entry!r}")
            continue
        try:
            found_path.resolve().relative_to(root)
        except ValueError:  # pragma: no cover
            failures.append(f"frozen API path escapes root: {entry!r}")
            continue
        if not _symbol_defined_in_python(found_path, sym):
            failures.append(f"missing frozen symbol {sym!r} in {found_path.relative_to(root)}")

    if failures:
        return STATUS_FAIL, f"frozen API contract broken: {failures}", tuple(failures)
    return STATUS_PASS, f"verified {len(frozen)} frozen_apis entrypoint(s)", ()


def _compare_json_schemas(
    old_schema: dict[str, Any],
    new_schema: dict[str, Any],
    name: str,
) -> list[str]:
    issues: list[str] = []
    old_props = old_schema.get("properties", {})
    new_props = new_schema.get("properties", {})
    if isinstance(old_props, dict) and isinstance(new_props, dict):
        removed = sorted(set(old_props) - set(new_props))
        if removed:
            issues.append(f"{name}: removed schema properties {removed}")
        for prop_name in sorted(set(old_props) & set(new_props)):
            old_p = old_props[prop_name]
            new_p = new_props[prop_name]
            if (
                isinstance(old_p, dict)
                and isinstance(new_p, dict)
                and isinstance(old_p.get("enum"), list)
                and isinstance(new_p.get("enum"), list)
            ):
                dropped_enum = sorted(set(old_p["enum"]) - set(new_p["enum"]))
                if dropped_enum:
                    issues.append(f"{name}.{prop_name}: removed enum values {dropped_enum}")
    return issues


def evaluate_diff_governance(
    project_root: Path,
    *,
    base_ref: str | None = None,
    head_ref: str = "HEAD",
    max_files: int = 500,
    allow_protected: bool = False,
) -> DiffGovernanceReport:
    """Evaluate compatibility, protected files, and test integrity across a diff."""
    root = project_root.resolve()
    frozen_status, frozen_reason, frozen_failures = verify_frozen_apis(root)
    reasons: list[str] = []
    if frozen_status != STATUS_PASS:
        reasons.append(frozen_reason)

    if not base_ref:
        status = frozen_status
        return DiffGovernanceReport(
            status=status,
            base_ref=None,
            head_ref=head_ref,
            files_changed=0,
            protected_touched=(),
            deleted_tests=(),
            frozen_api_failures=frozen_failures,
            schema_breaking_changes=(),
            reasons=tuple(reasons),
        )

    git_bin = shutil.which("git")
    if git_bin is None:  # pragma: no cover
        return DiffGovernanceReport(
            status=STATUS_BLOCKED,
            base_ref=base_ref,
            head_ref=head_ref,
            files_changed=0,
            protected_touched=(),
            deleted_tests=(),
            frozen_api_failures=frozen_failures,
            schema_breaking_changes=(),
            reasons=("git executable not found on PATH",),
        )

    diff_res = subprocess.run(  # noqa: S603
        [git_bin, "diff", "--name-status", f"{base_ref}..{head_ref}"],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
        timeout=15,
    )
    if diff_res.returncode != 0:
        return DiffGovernanceReport(
            status=STATUS_BLOCKED,
            base_ref=base_ref,
            head_ref=head_ref,
            files_changed=0,
            protected_touched=(),
            deleted_tests=(),
            frozen_api_failures=frozen_failures,
            schema_breaking_changes=(),
            reasons=(f"cannot compute git diff {base_ref}..{head_ref}: {diff_res.stderr.strip()}",),
        )

    read_only_prefixes: list[str] = []
    proj_yaml = root / ".gencode-gov" / "project.yaml"
    if proj_yaml.is_file() and not proj_yaml.is_symlink():
        try:
            pdata = yaml.safe_load(proj_yaml.read_text(encoding="utf-8"))
            if isinstance(pdata, dict) and isinstance(pdata.get("governance_files"), dict):
                ro = pdata["governance_files"].get("read_only", [])
                if isinstance(ro, list):
                    read_only_prefixes = [str(x) for x in ro if isinstance(x, str)]
        except (OSError, yaml.YAMLError):  # pragma: no cover
            read_only_prefixes = []

    changed_paths: list[tuple[str, str]] = []
    for ln in diff_res.stdout.splitlines():
        parts = ln.split("	")
        if len(parts) >= 2:
            changed_paths.append((parts[0], parts[-1]))

    protected_touched: list[str] = []
    deleted_tests: list[str] = []
    schema_breaks: list[str] = []

    for mode, rel_path in changed_paths:
        if any(
            rel_path == pref.rstrip("/") or rel_path.startswith(pref.rstrip("/") + "/")
            for pref in read_only_prefixes
        ):
            protected_touched.append(rel_path)
        is_test_path = "tests/" in rel_path or Path(rel_path).name.startswith("test_")
        if mode.startswith("D") and is_test_path:
            deleted_tests.append(rel_path)
        if rel_path.startswith("schemas/") and rel_path.endswith(".json"):
            if mode.startswith("D"):
                schema_breaks.append(f"deleted schema file: {rel_path}")
            elif mode.startswith("M"):
                old_show = subprocess.run(  # noqa: S603
                    [git_bin, "show", f"{base_ref}:{rel_path}"],
                    cwd=root,
                    capture_output=True,
                    text=True,
                    check=False,
                    timeout=10,
                )
                new_fp = root / rel_path
                if old_show.returncode == 0 and new_fp.is_file():
                    try:
                        old_j = json.loads(old_show.stdout)
                        new_j = json.loads(new_fp.read_text(encoding="utf-8"))
                        if isinstance(old_j, dict) and isinstance(new_j, dict):
                            schema_breaks.extend(_compare_json_schemas(old_j, new_j, rel_path))
                    except (OSError, json.JSONDecodeError):
                        schema_breaks.append(f"unparseable JSON schema change: {rel_path}")

    if len(changed_paths) > max_files:
        reasons.append(
            f"diff blast radius ({len(changed_paths)} files) exceeds max_files={max_files}"
        )
    if protected_touched and not allow_protected:
        reasons.append(
            f"protected governance files modified without --allow-protected: {protected_touched}"
        )
    if deleted_tests:
        reasons.append(f"regression test files deleted: {deleted_tests}")
    if schema_breaks:
        reasons.append(f"breaking schema changes: {schema_breaks}")

    if frozen_status == STATUS_BLOCKED:
        final_status = STATUS_BLOCKED
    elif reasons:
        final_status = STATUS_FAIL
    else:
        final_status = STATUS_PASS

    return DiffGovernanceReport(
        status=final_status,
        base_ref=base_ref,
        head_ref=head_ref,
        files_changed=len(changed_paths),
        protected_touched=tuple(sorted(set(protected_touched))),
        deleted_tests=tuple(sorted(set(deleted_tests))),
        frozen_api_failures=frozen_failures,
        schema_breaking_changes=tuple(schema_breaks),
        reasons=tuple(reasons),
    )
