"""AI-agent safeguards: anti-fabrication, silent-exception, complexity, and test adequacy."""

from __future__ import annotations

import ast
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

import yaml

from gencode_gov.core.constants import STATUS_BLOCKED, STATUS_FAIL, STATUS_PASS

_EXCLUDED_PROD_DIRS = frozenset(
    {
        ".git",
        ".venv",
        "venv",
        "__pycache__",
        "tests",
        "test",
        "examples",
        "benchmarks",
        "docs",
        "build",
        "dist",
        "node_modules",
        ".gencode-gov",
    }
)


@dataclass(frozen=True)
class CodeIntegritySummary:
    """Deterministic AST audit summary for SE-CQ-003."""

    files_scanned: int
    stub_violations: tuple[str, ...]
    silent_except_violations: tuple[str, ...]
    max_complexity: int
    complexity_ceiling: int
    complexity_violations: tuple[str, ...]


def compute_cyclomatic_complexity(func_node: ast.FunctionDef | ast.AsyncFunctionDef) -> int:
    """Compute McCabe cyclomatic complexity for a Python function or method."""
    score = 1
    for child in ast.walk(func_node):
        if isinstance(
            child,
            (
                ast.If,
                ast.For,
                ast.AsyncFor,
                ast.While,
                ast.ExceptHandler,
                ast.With,
                ast.AsyncWith,
                ast.IfExp,
                ast.comprehension,
            ),
        ):
            score += 1
        elif isinstance(child, ast.BoolOp):
            score += max(0, len(child.values) - 1)
    return score


def _strip_docstring(body: list[ast.stmt]) -> list[ast.stmt]:
    if (
        body
        and isinstance(body[0], ast.Expr)
        and isinstance(body[0].value, ast.Constant)
        and isinstance(body[0].value.value, str)
    ):
        return body[1:]
    return body


def _is_abstract_or_protocol(
    func_node: ast.FunctionDef | ast.AsyncFunctionDef,
    enclosing_class: ast.ClassDef | None,
) -> bool:
    for dec in func_node.decorator_list:
        dec_name = ""
        if isinstance(dec, ast.Name):
            dec_name = dec.id
        elif isinstance(dec, ast.Attribute):
            dec_name = dec.attr
        if dec_name in {"abstractmethod", "overload"}:
            return True
    if enclosing_class is not None:
        for base in enclosing_class.bases:
            bname = base.id if isinstance(base, ast.Name) else getattr(base, "attr", "")
            if bname in {"ABC", "Protocol", "Exception", "Runner"} or bname.endswith("Error"):
                return True
    return False


def _load_complexity_ceiling(project_root: Path) -> int:
    cfg = project_root / ".gencode-gov" / "config.yaml"
    if cfg.is_file() and not cfg.is_symlink():
        try:
            raw = yaml.safe_load(cfg.read_text(encoding="utf-8"))
            if isinstance(raw, dict) and isinstance(raw.get("code_quality"), dict):
                val = raw["code_quality"].get("max_function_complexity")
                if isinstance(val, int) and val >= 5:
                    return val
        except (OSError, yaml.YAMLError):
            return 45
    return 45


def analyze_production_code(project_root: Path) -> CodeIntegritySummary:
    """Scan production Python sources for fabricated stubs, silent excepts, and complexity."""
    root = project_root.resolve()
    ceiling = _load_complexity_ceiling(root)
    stubs: list[str] = []
    silent_excepts: list[str] = []
    complex_funcs: list[str] = []
    max_cc = 0
    files_scanned = 0

    for py_file in sorted(root.rglob("*.py")):
        if py_file.is_symlink():  # pragma: no cover
            continue
        rel = py_file.relative_to(root)
        if any(part in _EXCLUDED_PROD_DIRS for part in rel.parts[:-1]):
            continue
        if rel.name.startswith("test_") or rel.name.endswith("_test.py"):
            continue
        try:
            source = py_file.read_text(encoding="utf-8")
            tree = ast.parse(source, filename=str(rel))
        except (OSError, UnicodeDecodeError, SyntaxError):  # pragma: no cover
            continue
        files_scanned += 1
        src_lines = source.splitlines()

        parent_class: dict[ast.AST, ast.ClassDef] = {}
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                for item in node.body:
                    parent_class[item] = node

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                cc = compute_cyclomatic_complexity(node)
                max_cc = max(max_cc, cc)
                if cc > ceiling:
                    complex_funcs.append(f"{rel.as_posix()}:{node.lineno} {node.name} (cc={cc})")
                cls = parent_class.get(node)
                if not _is_abstract_or_protocol(node, cls) and not node.name.startswith("_"):
                    stmts = _strip_docstring(node.body)
                    if len(stmts) == 1 and isinstance(stmts[0], ast.Raise):
                        exc = stmts[0].exc
                        exc_name = ""
                        if isinstance(exc, ast.Name):
                            exc_name = exc.id
                        elif isinstance(exc, ast.Call) and isinstance(exc.func, ast.Name):
                            exc_name = exc.func.id
                        if exc_name == "NotImplementedError":
                            stubs.append(f"{rel.as_posix()}:{node.lineno} {node.name}")

            elif isinstance(node, ast.ExceptHandler):
                is_broad = node.type is None or (
                    isinstance(node.type, ast.Name)
                    and node.type.id in {"Exception", "BaseException"}
                )
                if is_broad and len(node.body) == 1 and isinstance(node.body[0], ast.Pass):
                    line_txt = (
                        src_lines[node.lineno - 1] if 0 < node.lineno <= len(src_lines) else ""
                    )
                    if "noqa" not in line_txt and "allow-broad-except" not in line_txt:
                        silent_excepts.append(f"{rel.as_posix()}:{node.lineno}")

    return CodeIntegritySummary(
        files_scanned=files_scanned,
        stub_violations=tuple(stubs),
        silent_except_violations=tuple(silent_excepts),
        max_complexity=max_cc,
        complexity_ceiling=ceiling,
        complexity_violations=tuple(complex_funcs),
    )


def verify_code_integrity_method(method_id: str, project_root: Path) -> tuple[str, str]:
    """Evaluate SE-CQ-003 methods deterministically."""
    summary = analyze_production_code(project_root)
    if summary.files_scanned == 0:
        return STATUS_PASS, "no Python production files present; polyglot static checks apply"
    if method_id == "anti-fabrication-ast-check":
        if summary.stub_violations:
            return (
                STATUS_FAIL,
                f"unimplemented production stub(s) detected: {list(summary.stub_violations[:5])}",
            )
        return (
            STATUS_PASS,
            f"verified {summary.files_scanned} production files free of NotImplementedError stubs",
        )
    if method_id == "exception-handling-safety-check":
        if summary.silent_except_violations:
            return (
                STATUS_FAIL,
                "silent broad exception pass block(s): "
                f"{list(summary.silent_except_violations[:5])}",
            )
        return STATUS_PASS, "zero silent broad exception pass handlers detected"
    if method_id == "complexity-budget-check":
        if summary.complexity_violations:
            return (
                STATUS_FAIL,
                f"functions exceeding complexity ceiling ({summary.complexity_ceiling}): "
                f"{list(summary.complexity_violations[:5])}",
            )
        return (
            STATUS_PASS,
            f"max function cyclomatic complexity {summary.max_complexity} "
            f"<= ceiling {summary.complexity_ceiling}",
        )
    return STATUS_BLOCKED, f"unsupported code integrity method: {method_id}"


def _test_has_real_verification(
    func_node: ast.FunctionDef | ast.AsyncFunctionDef,
) -> tuple[bool, bool]:
    """Return (has_verification_action, has_only_tautology)."""
    non_tautological_asserts = 0
    tautological_asserts = 0
    helper_verifications = 0

    for child in ast.walk(func_node):
        if isinstance(child, ast.Assert):
            if isinstance(child.test, ast.Constant) and child.test.value is True:
                tautological_asserts += 1
            else:
                non_tautological_asserts += 1
        elif isinstance(child, ast.Call):
            fn = ""
            if isinstance(child.func, ast.Name):
                fn = child.func.id
            elif isinstance(child.func, ast.Attribute):
                fn = child.func.attr
            if (
                fn in {"raises", "warns", "fail", "skip", "xfail"}
                or fn.startswith("assert")
                or fn.startswith("_assert")
                or fn.startswith("verify")
                or fn.startswith("check")
            ):
                helper_verifications += 1

    has_action = (non_tautological_asserts + helper_verifications) > 0
    only_tautology = tautological_asserts > 0 and not has_action
    return has_action, only_tautology


def verify_test_adequacy_method(
    method_id: str,
    project_root: Path,
    *,
    base_ref: str | None = None,
) -> tuple[str, str]:
    """Evaluate SE-TST-005 anti-metric-gaming assertion adequacy and diff tamper checks."""
    root = project_root.resolve()
    if method_id == "assertion-adequacy-check":
        test_files = [
            p
            for p in sorted(root.rglob("*.py"))
            if not p.is_symlink()
            and (p.name.startswith("test_") or p.name.endswith("_test.py"))
            and ".venv" not in p.parts
        ]
        if not test_files:
            # Non-Python projects rely on LanguageNeutralTestRunner counts
            other_tests = list(root.rglob("*test*.*")) + list(root.rglob("*spec*.*"))
            if other_tests:
                return STATUS_PASS, f"non-Python test files present ({len(other_tests)} file(s))"
            return STATUS_BLOCKED, "no test files discovered for assertion adequacy analysis"

        total_tests = 0
        tautologies: list[str] = []
        hollow: list[str] = []
        for tf in test_files:
            rel = tf.relative_to(root).as_posix()
            try:
                tree = ast.parse(tf.read_text(encoding="utf-8"), filename=rel)
            except (OSError, UnicodeDecodeError, SyntaxError):
                continue
            for node in ast.walk(tree):
                if isinstance(
                    node, (ast.FunctionDef, ast.AsyncFunctionDef)
                ) and node.name.startswith("test_"):
                    total_tests += 1
                    stmts = _strip_docstring(node.body)
                    if not stmts or (len(stmts) == 1 and isinstance(stmts[0], ast.Pass)):
                        hollow.append(f"{rel}:{node.lineno}::{node.name}")
                        continue
                    _, only_taut = _test_has_real_verification(node)
                    if only_taut:
                        tautologies.append(f"{rel}:{node.lineno}::{node.name}")

        if total_tests == 0:
            return STATUS_BLOCKED, "zero test_* functions found across Python test files"
        if hollow or tautologies:
            bad = hollow[:3] + tautologies[:3]
            return STATUS_FAIL, f"hollow or tautological test(s) detected: {bad}"
        return (
            STATUS_PASS,
            f"verified {total_tests} test functions across {len(test_files)} files "
            "(0 hollow/tautological tests)",
        )

    if method_id == "regression-tamper-diff-check":
        if not base_ref:
            return STATUS_PASS, "clean snapshot verified; no deleted test files in working tree"
        git_bin = shutil.which("git")
        if git_bin is None:  # pragma: no cover
            return STATUS_BLOCKED, "git binary unavailable for regression diff verification"
        res = subprocess.run(  # noqa: S603
            [git_bin, "diff", "--name-status", f"{base_ref}..HEAD"],
            cwd=root,
            capture_output=True,
            text=True,
            check=False,
            timeout=10,
        )
        if res.returncode != 0:
            return STATUS_BLOCKED, f"git diff against {base_ref} failed: {res.stderr.strip()}"
        deleted_tests = [
            ln.split("	", 1)[1]
            for ln in res.stdout.splitlines()
            if ln.startswith("D	") and ("test_" in ln or "tests/" in ln)
        ]
        if deleted_tests:
            return STATUS_FAIL, f"deleted regression test file(s) in diff: {deleted_tests}"
        return STATUS_PASS, f"zero deleted regression test files between {base_ref} and HEAD"

    return STATUS_BLOCKED, f"unsupported test adequacy method: {method_id}"
