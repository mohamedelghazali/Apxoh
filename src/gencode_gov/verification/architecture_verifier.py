"""Executable architectural fitness functions: layer boundaries and cycle-free module DAGs."""

from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from gencode_gov.core.constants import STATUS_BLOCKED, STATUS_FAIL, STATUS_PASS


@dataclass(frozen=True)
class ArchitectureReport:
    """Result of evaluating module dependency cycles and layer import contracts."""

    status: str
    reason: str
    modules_scanned: int
    edge_count: int
    cycles: tuple[tuple[str, ...], ...]
    layer_violations: tuple[str, ...]


def _extract_submodules(
    source: str,
    package_name: str,
    current_top: str,
    *,
    top_level_only: bool = False,
) -> set[str]:
    try:
        tree = ast.parse(source)
    except SyntaxError:  # pragma: no cover
        return set()
    targets: set[str] = set()
    prefix = f"{package_name}."
    nodes: list[ast.AST] = list(tree.body) if top_level_only else list(ast.walk(tree))
    for node in nodes:
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.startswith(prefix):
                    sub = alias.name[len(prefix) :].split(".", 1)[0]
                    if sub and sub != current_top:
                        targets.add(sub)
        elif isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            if node.level == 0 and mod.startswith(prefix):
                sub = mod[len(prefix) :].split(".", 1)[0]
                if sub and sub != current_top:
                    targets.add(sub)
    return targets


def _find_strongly_connected_cycles(graph: dict[str, set[str]]) -> list[tuple[str, ...]]:
    index = 0
    indices: dict[str, int] = {}
    lowlink: dict[str, int] = {}
    stack: list[str] = []
    on_stack: set[str] = set()
    cycles: list[tuple[str, ...]] = []

    def strongconnect(node: str) -> None:
        nonlocal index
        indices[node] = index
        lowlink[node] = index
        index += 1
        stack.append(node)
        on_stack.add(node)

        for nxt in sorted(graph.get(node, ())):
            if nxt not in indices:
                strongconnect(nxt)
                lowlink[node] = min(lowlink[node], lowlink[nxt])
            elif nxt in on_stack:
                lowlink[node] = min(lowlink[node], indices[nxt])

        if lowlink[node] == indices[node]:
            scc: list[str] = []
            while True:
                w = stack.pop()
                on_stack.remove(w)
                scc.append(w)
                if w == node:
                    break
            if len(scc) > 1:
                cycles.append(tuple(sorted(scc)))

    for vertex in sorted(graph):
        if vertex not in indices:
            strongconnect(vertex)
    return sorted(cycles)


def verify_architecture_contracts(project_root: Path) -> ArchitectureReport:
    """Verify .gencode-gov/architecture-contracts.yaml or discover src/ acyclic boundaries."""
    root = project_root.resolve()
    contract_path = root / ".gencode-gov" / "architecture-contracts.yaml"
    layers: list[dict[str, Any]] = []
    max_cycles = 0

    if contract_path.is_file() and not contract_path.is_symlink():
        try:
            raw = yaml.safe_load(contract_path.read_text(encoding="utf-8"))
        except (OSError, yaml.YAMLError) as exc:
            return ArchitectureReport(
                STATUS_BLOCKED,
                f"cannot parse architecture-contracts.yaml: {exc}",
                0,
                0,
                (),
                (),
            )
        if not isinstance(raw, dict):
            return ArchitectureReport(
                STATUS_BLOCKED,
                "architecture-contracts.yaml must be a mapping",
                0,
                0,
                (),
                (),
            )
        pkg_root_rel = str(raw.get("package_root", "")).strip()
        pkg_name = str(raw.get("package_name", "")).strip()
        if not pkg_root_rel:
            return ArchitectureReport(
                STATUS_BLOCKED,
                "architecture-contracts.yaml missing package_root",
                0,
                0,
                (),
                (),
            )
        pkg_root = (root / pkg_root_rel).resolve()
        try:
            pkg_root.relative_to(root)
        except ValueError:
            return ArchitectureReport(
                STATUS_BLOCKED,
                "package_root escapes project root",
                0,
                0,
                (),
                (),
            )
        if not pkg_name:
            pkg_name = pkg_root.name
        max_cycles = int(raw.get("max_cycles", 0))
        raw_layers = raw.get("layers", [])
        if isinstance(raw_layers, list):
            layers = [item for item in raw_layers if isinstance(item, dict)]
    else:
        src_dir = root / "src"
        candidates = (
            [d for d in sorted(src_dir.iterdir()) if d.is_dir() and (d / "__init__.py").is_file()]
            if src_dir.is_dir()
            else []
        )
        if not candidates:
            return ArchitectureReport(
                STATUS_BLOCKED,
                "missing .gencode-gov/architecture-contracts.yaml and no src/<pkg> package found",
                0,
                0,
                (),
                (),
            )
        pkg_root = candidates[0]
        pkg_name = pkg_root.name

    if not pkg_root.is_dir():
        return ArchitectureReport(
            STATUS_BLOCKED,
            f"declared package_root does not exist: {pkg_root}",
            0,
            0,
            (),
            (),
        )

    all_graph: dict[str, set[str]] = {}
    top_graph: dict[str, set[str]] = {}
    py_count = 0
    for py_file in sorted(pkg_root.rglob("*.py")):
        if py_file.is_symlink():  # pragma: no cover
            continue
        rel = py_file.relative_to(pkg_root)
        top_mod = rel.stem if len(rel.parts) == 1 else rel.parts[0]
        if top_mod == "__init__":
            continue
        py_count += 1
        all_graph.setdefault(top_mod, set())
        top_graph.setdefault(top_mod, set())
        try:
            src_txt = py_file.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):  # pragma: no cover
            continue
        all_graph[top_mod].update(_extract_submodules(src_txt, pkg_name, top_mod))
        top_graph[top_mod].update(
            _extract_submodules(src_txt, pkg_name, top_mod, top_level_only=True)
        )

    edge_count = sum(len(v) for v in all_graph.values())
    cycles = _find_strongly_connected_cycles(top_graph)
    violations: list[str] = []

    for layer in layers:
        layer_name = str(layer.get("name", "unnamed"))
        mods = [str(m) for m in layer.get("modules", []) if isinstance(m, str)]
        forbidden = {str(f) for f in layer.get("forbidden_imports", []) if isinstance(f, str)}
        for mod in mods:
            bad = sorted(all_graph.get(mod, set()) & forbidden)
            for target in bad:
                violations.append(
                    f"layer '{layer_name}' module '{mod}' imports forbidden '{target}'"
                )

    if violations or len(cycles) > max_cycles:
        reasons: list[str] = list(violations)
        if len(cycles) > max_cycles:
            formatted = [" <-> ".join(c) for c in cycles[:5]]
            reasons.append(
                f"circular package dependencies ({len(cycles)} > {max_cycles}): {formatted}"
            )
        return ArchitectureReport(
            STATUS_FAIL,
            "; ".join(reasons),
            py_count,
            edge_count,
            tuple(cycles),
            tuple(violations),
        )

    return ArchitectureReport(
        STATUS_PASS,
        f"verified {py_count} module files ({edge_count} internal edges, {len(cycles)} cycles, "
        "0 layer violations)",
        py_count,
        edge_count,
        tuple(cycles),
        (),
    )
