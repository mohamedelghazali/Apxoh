"""Longitudinal architectural, complexity, dependency, and exception drift ledger."""

from __future__ import annotations

import ast
import json
import os
import tempfile
import tomllib
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from gencode_gov.core.errors import GovernanceError
from gencode_gov.policies.exceptions import load_exceptions
from gencode_gov.verification.architecture_verifier import verify_architecture_contracts
from gencode_gov.verification.code_and_test_integrity import compute_cyclomatic_complexity


@dataclass(frozen=True)
class DriftSnapshot:
    """Point-in-time structural engineering telemetry for a commit."""

    recorded_at: str
    commit_sha: str
    python_files: int
    max_cyclomatic_complexity: int
    mean_cyclomatic_complexity: float
    internal_import_edges: int
    declared_dependencies: int
    active_exceptions: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "recorded_at": self.recorded_at,
            "commit_sha": self.commit_sha,
            "python_files": self.python_files,
            "max_cyclomatic_complexity": self.max_cyclomatic_complexity,
            "mean_cyclomatic_complexity": round(self.mean_cyclomatic_complexity, 2),
            "internal_import_edges": self.internal_import_edges,
            "declared_dependencies": self.declared_dependencies,
            "active_exceptions": self.active_exceptions,
        }


def compute_drift_snapshot(project_root: Path, commit_sha: str) -> DriftSnapshot:
    """Measure complexity, coupling, dependency count, and active exceptions."""
    root = project_root.resolve()
    src_root = root / "src" if (root / "src").is_dir() else root
    py_files = 0
    complexities: list[int] = []
    for pf in sorted(src_root.rglob("*.py")):
        if pf.is_symlink() or ".venv" in pf.parts or "__pycache__" in pf.parts:  # pragma: no cover
            continue
        py_files += 1
        try:
            tree = ast.parse(pf.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, SyntaxError):  # pragma: no cover
            continue
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                complexities.append(compute_cyclomatic_complexity(node))

    max_cc = max(complexities, default=0)
    mean_cc = (sum(complexities) / len(complexities)) if complexities else 0.0

    arch = verify_architecture_contracts(root)
    dep_count = 0
    pyproj = root / "pyproject.toml"
    if pyproj.is_file() and not pyproj.is_symlink():
        try:
            pdata = tomllib.loads(pyproj.read_text(encoding="utf-8"))
            deps = pdata.get("project", {}).get("dependencies", [])
            if isinstance(deps, list):
                dep_count = len(deps)
        except (OSError, tomllib.TOMLDecodeError):  # pragma: no cover
            dep_count = 0

    active_exc = 0
    exc_reg = root / "system" / "policies" / "exceptions" / "registry.yaml"
    if exc_reg.is_file() and not exc_reg.is_symlink():
        try:
            reg = load_exceptions(exc_reg)
            active_exc = sum(1 for item in reg.exceptions if item.is_active())
        except Exception:  # noqa: BLE001  # pragma: no cover
            active_exc = 0

    return DriftSnapshot(
        recorded_at=datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        commit_sha=commit_sha,
        python_files=py_files,
        max_cyclomatic_complexity=max_cc,
        mean_cyclomatic_complexity=round(mean_cc, 2),
        internal_import_edges=arch.edge_count,
        declared_dependencies=dep_count,
        active_exceptions=active_exc,
    )


def record_and_evaluate_drift(
    project_root: Path,
    commit_sha: str,
    *,
    persist: bool = True,
) -> tuple[DriftSnapshot, DriftSnapshot | None, list[str]]:
    """Compare current snapshot against prior ledger entry and optionally append."""
    root = project_root.resolve()
    state_dir = root / ".gencode-gov" / "state"
    if state_dir.exists() and state_dir.is_symlink():
        raise GovernanceError("refusing symlinked .gencode-gov/state directory")
    ledger_path = state_dir / "drift-ledger.jsonl"
    if ledger_path.exists() and ledger_path.is_symlink():
        raise GovernanceError("refusing symlinked drift-ledger.jsonl")

    prior: DriftSnapshot | None = None
    existing_lines: list[str] = []
    if ledger_path.is_file():
        existing_lines = [
            ln for ln in ledger_path.read_text(encoding="utf-8").splitlines() if ln.strip()
        ]
        if existing_lines:
            last = json.loads(existing_lines[-1])
            prior = DriftSnapshot(
                recorded_at=str(last["recorded_at"]),
                commit_sha=str(last["commit_sha"]),
                python_files=int(last["python_files"]),
                max_cyclomatic_complexity=int(last["max_cyclomatic_complexity"]),
                mean_cyclomatic_complexity=float(last["mean_cyclomatic_complexity"]),
                internal_import_edges=int(last["internal_import_edges"]),
                declared_dependencies=int(last["declared_dependencies"]),
                active_exceptions=int(last["active_exceptions"]),
            )

    current = compute_drift_snapshot(root, commit_sha)
    warnings: list[str] = []
    if prior is not None:
        if current.max_cyclomatic_complexity > prior.max_cyclomatic_complexity + 10:
            warnings.append(
                f"max cyclomatic complexity jumped from {prior.max_cyclomatic_complexity} "
                f"to {current.max_cyclomatic_complexity}"
            )
        if current.declared_dependencies > prior.declared_dependencies + 5:
            warnings.append(
                f"runtime dependency count jumped from {prior.declared_dependencies} "
                f"to {current.declared_dependencies}"
            )
        if current.active_exceptions > prior.active_exceptions:
            warnings.append(
                f"active governance exceptions increased from {prior.active_exceptions} "
                f"to {current.active_exceptions}"
            )

    if persist:
        state_dir.mkdir(parents=True, exist_ok=True)
        state_dir.resolve().relative_to(root)
        serialized = json.dumps(current.to_dict(), sort_keys=True)
        updated = [*existing_lines, serialized]
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=state_dir,
            prefix=".drift-",
            suffix=".tmp",
            delete=False,
        ) as handle:
            handle.write("\n".join(updated) + "\n")
            handle.flush()
            os.fsync(handle.fileno())
            tmp = Path(handle.name)
        tmp.replace(ledger_path)

    return current, prior, warnings
