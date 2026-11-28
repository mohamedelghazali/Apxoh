"""Deterministic lockfile compiler, drift verifier, installer, and security auditor.

Compiles `requirements.lock` (runtime) and `requirements-dev.lock` (development,
testing, tooling, and build closure) exclusively from `pyproject.toml` using PyPA
`pip-tools` (`pip-compile --generate-hashes`), preserving PEP 508 Python-version and
platform environment markers across Python 3.11-3.13 and Linux/macOS/Windows.
"""

from __future__ import annotations

import argparse
import difflib
import importlib.metadata
import os
import re
import subprocess
import sys
import tempfile
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "src"))

from gencode_gov.verification.lockfile_verifier import (  # noqa: E402
    BODY_SEAL_PREFIX,
    MANIFEST_SEAL_PREFIX,
    canonicalize_pkg_name,
    compute_lock_body_digest,
    compute_pyproject_lock_digest,
    validate_python_lockfile,
    verify_dependency_lockfiles,
)

SUPPORTED_PYTHONS = ("3.11", "3.12", "3.13")
SUPPORTED_PLATFORMS = (
    ("linux", "posix", "Linux"),
    ("darwin", "posix", "Darwin"),
    ("win32", "nt", "Windows"),
)
ALL_ENV_KEYS = frozenset(
    (sys_plat, py) for py in SUPPORTED_PYTHONS for sys_plat, _, _ in SUPPORTED_PLATFORMS
)
_STANZA_HEAD_RE = re.compile(
    r"^([A-Za-z0-9](?:[A-Za-z0-9._-]*[A-Za-z0-9])?)==([A-Za-z0-9][A-Za-z0-9._!+-]*)"
)


@dataclass(frozen=True)
class LockedPackage:
    """Canonical representation of a single hash-pinned package stanza."""

    name: str
    version: str
    hashes: tuple[str, ...]
    marker: str | None
    via: tuple[str, ...]

    def render(self) -> str:
        spec = f"{self.name}=={self.version}"
        if self.marker:
            spec = f"{spec} ; {self.marker}"
        lines = [f"{spec} \\"]
        for idx, digest in enumerate(self.hashes):
            suffix = " \\" if idx < len(self.hashes) - 1 else ""
            lines.append(f"    {digest}{suffix}")
        if len(self.via) == 1:
            lines.append(f"    # via {self.via[0]}")
        elif len(self.via) > 1:
            lines.append("    # via")
            lines.extend(f"    #   {src}" for src in self.via)
        return "\n".join(lines)


def _load_pyproject(root: Path) -> dict[str, Any]:
    return tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))


def _verify_compiler_version(pyproject_data: dict[str, Any]) -> str:
    dev_reqs = pyproject_data.get("project", {}).get("optional-dependencies", {}).get("dev", [])
    expected = next(
        (
            str(i).split("==", 1)[1].strip()
            for i in dev_reqs
            if str(i).strip().startswith("pip-tools==")
        ),
        None,
    )
    if not expected:
        raise RuntimeError("pyproject.toml must declare pip-tools==<version> in [dev]")
    try:
        installed = importlib.metadata.version("pip-tools")
    except importlib.metadata.PackageNotFoundError as exc:
        raise RuntimeError(f"pip-tools=={expected} is not installed in {sys.executable}") from exc
    if installed != expected:
        raise RuntimeError(f"Compiler mismatch: expected pip-tools=={expected}, found {installed}")
    return installed


def _parse_pip_compile_stanzas(raw_output: str) -> dict[str, tuple[str, tuple[str, ...]]]:
    parsed: dict[str, tuple[str, tuple[str, ...]]] = {}
    current_parts: list[str] = []

    def flush(parts: list[str]) -> None:
        if not parts:
            return
        tokens = " ".join(parts).split()
        hashes = tuple(sorted({tok for tok in tokens if tok.startswith("--hash=sha256:")}))
        non_hash = " ".join(tok for tok in tokens if not tok.startswith("--hash"))
        match = _STANZA_HEAD_RE.match(non_hash.split(";", 1)[0].strip())
        if match and hashes:
            parsed[canonicalize_pkg_name(match.group(1))] = (match.group(2), hashes)

    for raw_line in raw_output.replace("\r\n", "\n").splitlines():
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("#"):
            flush(current_parts)
            current_parts = []
            continue
        code = raw_line.split(" #", 1)[0].rstrip()
        is_cont = code.endswith("\\")
        seg = (code[:-1] if is_cont else code).strip()
        if seg:
            current_parts.append(seg)
        if not is_cont:
            flush(current_parts)
            current_parts = []
    flush(current_parts)
    return parsed


def _synthesize_marker(active: set[tuple[str, str]]) -> str | None:
    if not active or active >= ALL_ENV_KEYS:
        return None
    plats, pys = {p for p, _ in active}, {v for _, v in active}
    if active == {(p, v) for p in plats for v in pys}:
        clauses: list[str] = []
        if len(plats) == 1:
            clauses.append(f'sys_platform == "{next(iter(plats))}"')
        elif len(plats) == 2:
            missing_plat = next(iter({"linux", "darwin", "win32"} - plats))
            clauses.append(f'sys_platform != "{missing_plat}"')
        py_map = {
            frozenset({"3.11", "3.12"}): 'python_version < "3.13"',
            frozenset({"3.11"}): 'python_version < "3.12"',
            frozenset({"3.12", "3.13"}): 'python_version >= "3.12"',
            frozenset({"3.13"}): 'python_version >= "3.13"',
        }
        if frozenset(pys) in py_map:
            clauses.append(py_map[frozenset(pys)])
        elif len(pys) < len(SUPPORTED_PYTHONS):
            clauses.append("(" + " or ".join(f'python_version == "{v}"' for v in sorted(pys)) + ")")
        return " and ".join(clauses) if clauses else None
    return " or ".join(
        f'(sys_platform == "{p}" and python_version == "{v}")' for p, v in sorted(active)
    )


def _discover_metadata_graph(
    pyproject_data: dict[str, Any],
    *,
    is_dev: bool,
) -> tuple[dict[str, set[tuple[str, str]]], dict[str, set[str]], dict[str, str]]:
    from packaging.requirements import Requirement

    dist_requires = {
        canonicalize_pkg_name(d.metadata["Name"]): list(d.requires or [])
        for d in importlib.metadata.distributions()
        if d.metadata.get("Name")
    }
    active_by_extra: dict[tuple[str, str], set[tuple[str, str]]] = {}
    via_map: dict[str, set[str]] = {}
    fallback_specs: dict[str, str] = {}

    def eval_req(
        raw_req: str,
        parent_envs: set[tuple[str, str]],
        source_label: str,
        parent_extra: str = "",
    ) -> bool:
        req = Requirement(raw_req)
        child = canonicalize_pkg_name(req.name)
        matched: set[tuple[str, str]] = set()
        for sys_plat, os_name, plat_sys in SUPPORTED_PLATFORMS:
            for py_ver in SUPPORTED_PYTHONS:
                if (sys_plat, py_ver) not in parent_envs:
                    continue
                env = {
                    "extra": parent_extra,
                    "implementation_name": "cpython",
                    "implementation_version": f"{py_ver}.0",
                    "os_name": os_name,
                    "platform_machine": "x86_64",
                    "platform_python_implementation": "CPython",
                    "platform_release": "",
                    "platform_system": plat_sys,
                    "platform_version": "",
                    "python_full_version": f"{py_ver}.0",
                    "python_version": py_ver,
                    "sys_platform": sys_plat,
                }
                if req.marker is None or req.marker.evaluate(env):
                    matched.add((sys_plat, py_ver))
        if not matched:
            return False
        via_map.setdefault(child, set()).add(source_label)
        spec_str = f"{child}{req.specifier}" if str(req.specifier) else child
        fallback_specs.setdefault(child, spec_str)
        updated = False
        for ext in {"", *(e.lower() for e in req.extras)}:
            prev = active_by_extra.setdefault((child, ext), set())
            before = len(prev)
            prev.update(matched)
            updated = updated or (len(prev) > before)
        return updated

    proj = pyproject_data.get("project", {})
    for dep in proj.get("dependencies", []):
        eval_req(str(dep), set(ALL_ENV_KEYS), "pyproject.toml ([project.dependencies])")
    if is_dev:
        dev_label = "pyproject.toml ([project.optional-dependencies.dev])"
        for dep in proj.get("optional-dependencies", {}).get("dev", []):
            eval_req(str(dep), set(ALL_ENV_KEYS), dev_label)
        bs_label = "pyproject.toml ([build-system.requires])"
        for dep in pyproject_data.get("build-system", {}).get("requires", []):
            eval_req(str(dep), set(ALL_ENV_KEYS), bs_label)

    changed = True
    while changed:
        changed = False
        for (pkg, ext), envs in list(active_by_extra.items()):
            if pkg in {"pip", "distribute"}:
                continue
            for req_line in dist_requires.get(pkg, ()):
                if eval_req(req_line, envs, pkg, parent_extra=ext):
                    changed = True

    active_envs: dict[str, set[tuple[str, str]]] = {}
    for (pkg, _ext), envs in active_by_extra.items():
        if pkg not in {"pip", "distribute"}:
            active_envs.setdefault(pkg, set()).update(envs)
    return active_envs, via_map, fallback_specs


def _run_pip_compile(args: list[str], *, cwd: Path) -> None:
    env = {**os.environ, "CUSTOM_COMPILE_COMMAND": "make lock"}
    cmd = [
        sys.executable,
        "-m",
        "piptools",
        "compile",
        "--generate-hashes",
        "--strip-extras",
        "--newline=lf",
        "--no-header",
        "--no-emit-index-url",
        "--no-emit-trusted-host",
        "--no-emit-find-links",
        "--no-emit-options",
        *args,
    ]
    subprocess.run(cmd, cwd=cwd, env=env, check=True, timeout=300)  # noqa: S603


def _seed_without_markers(seed_source: Path, dest: Path) -> None:
    if not seed_source.is_file():
        return
    cleaned = [
        f"{line.split(' ; ', 1)[0]} \\"
        if (" ; " in line and line.endswith("\\"))
        else line
        for line in seed_source.read_text(encoding="utf-8").splitlines()
        if not line.startswith((MANIFEST_SEAL_PREFIX, BODY_SEAL_PREFIX))
    ]
    dest.write_text("\n".join(cleaned) + "\n", encoding="utf-8")


def build_lockfile_content(
    root: Path,
    *,
    is_dev: bool,
    upgrade: bool = False,
    runtime_constraint: Path | None = None,
) -> str:
    """Compile and canonicalize a hash-pinned lockfile in memory without mutating root."""
    pyproject_data = _load_pyproject(root)
    compiler_ver = _verify_compiler_version(pyproject_data)
    target_name = "requirements-dev.lock" if is_dev else "requirements.lock"
    existing_lock = root / target_name
    unsafe_flags = ["--no-allow-unsafe", "--unsafe-package=pip", "--unsafe-package=distribute"]

    with tempfile.TemporaryDirectory(prefix="gencode-gov-lock-") as tmp_str:
        tmpdir = Path(tmp_str)
        tmp_out = tmpdir / target_name
        if not upgrade and existing_lock.is_file():
            _seed_without_markers(existing_lock, tmp_out)

        compile_args = ["--upgrade"] if upgrade else []
        if is_dev:
            compile_args.extend(["--extra=dev", "--all-build-deps", *unsafe_flags])
            if runtime_constraint is not None and runtime_constraint.is_file():
                tmp_c = tmpdir / "runtime-constraint.txt"
                _seed_without_markers(runtime_constraint, tmp_c)
                compile_args.extend(["-c", str(tmp_c)])
        compile_args.extend(["--output-file", str(tmp_out), str(root / "pyproject.toml")])
        _run_pip_compile(compile_args, cwd=root)

        stanzas = _parse_pip_compile_stanzas(tmp_out.read_text(encoding="utf-8"))
        active_envs, via_map, fallback_specs = _discover_metadata_graph(
            pyproject_data, is_dev=is_dev
        )

        for missing_pkg in sorted(set(active_envs) - set(stanzas)):
            aux_in, aux_out = tmpdir / f"aux-{missing_pkg}.in", tmpdir / f"aux-{missing_pkg}.txt"
            if not upgrade and existing_lock.is_file():
                _seed_without_markers(existing_lock, aux_out)
            aux_in.write_text(fallback_specs[missing_pkg] + "\n", encoding="utf-8")
            aux_args = (["--upgrade"] if upgrade else []) + [
                *unsafe_flags,
                "--output-file",
                str(aux_out),
                str(aux_in),
            ]
            _run_pip_compile(aux_args, cwd=root)
            for sub_pkg, payload in _parse_pip_compile_stanzas(
                aux_out.read_text(encoding="utf-8")
            ).items():
                if sub_pkg not in stanzas:
                    stanzas[sub_pkg] = payload
                    active_envs.setdefault(sub_pkg, set(active_envs[missing_pkg]))
                    if sub_pkg != missing_pkg:
                        via_map.setdefault(sub_pkg, set()).add(missing_pkg)

    locked_items = [
        LockedPackage(
            name=pkg,
            version=stanzas[pkg][0],
            hashes=stanzas[pkg][1],
            marker=_synthesize_marker(active_envs.get(pkg, set(ALL_ENV_KEYS))),
            via=tuple(sorted(via_map.get(pkg, ()))),
        )
        for pkg in sorted(stanzas)
    ]
    manifest_digest = compute_pyproject_lock_digest(pyproject_data, include_dev=is_dev)
    scope_desc = (
        "development, testing, tooling, and build closure"
        if is_dev
        else "production/runtime dependency closure"
    )
    header_lines = [
        f"# Deterministic {scope_desc} for GENCODE-GOV ({target_name}).",
        f"# Generated from pyproject.toml via pip-tools=={compiler_ver} (--generate-hashes).",
        "# Do not edit manually; regenerate via: make lock",
        f"{MANIFEST_SEAL_PREFIX} {manifest_digest}",
    ]
    body_str = "\n\n".join(item.render() for item in locked_items) + "\n"
    unsealed = "\n".join(header_lines) + "\n\n" + body_str
    body_digest = compute_lock_body_digest(unsealed)
    final_text = "\n".join([*header_lines, f"{BODY_SEAL_PREFIX} {body_digest}"]) + "\n\n" + body_str

    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", suffix=f"-{target_name}", delete=False
    ) as handle:
        handle.write(final_text)
        tmp_verify = Path(handle.name)
    try:
        ok, msg, _ = validate_python_lockfile(
            tmp_verify, pyproject_data=pyproject_data, is_dev=is_dev
        )
        if not ok:
            raise RuntimeError(f"Generated {target_name} failed self-validation: {msg}")
    finally:
        tmp_verify.unlink(missing_ok=True)
    return final_text


def cmd_verify(root: Path) -> int:
    status, reason = verify_dependency_lockfiles(root)
    stream = sys.stdout if status == "PASS" else sys.stderr
    print(f"[{'OK' if status == 'PASS' else 'FAIL'}] {reason}", file=stream)
    return 0 if status == "PASS" else 1


def cmd_compile(root: Path, *, target: str, upgrade: bool) -> int:
    rt_path, dev_path = root / "requirements.lock", root / "requirements-dev.lock"
    if target in {"all", "runtime"}:
        rt_path.write_text(
            build_lockfile_content(root, is_dev=False, upgrade=upgrade),
            encoding="utf-8",
            newline="\n",
        )
        print("[OK] Wrote requirements.lock")
    if target in {"all", "dev"}:
        dev_path.write_text(
            build_lockfile_content(
                root,
                is_dev=True,
                upgrade=upgrade,
                runtime_constraint=rt_path if rt_path.is_file() else None,
            ),
            encoding="utf-8",
            newline="\n",
        )
        print("[OK] Wrote requirements-dev.lock")
    return cmd_verify(root)


def cmd_check_drift(root: Path, *, target: str) -> int:
    if cmd_verify(root) != 0:
        return 1
    rt_path, dev_path = root / "requirements.lock", root / "requirements-dev.lock"
    with tempfile.TemporaryDirectory(prefix="gencode-gov-drift-") as tmp_str:
        tmp_rt = Path(tmp_str) / "requirements.lock"
        if target in {"all", "runtime"}:
            expected_rt = build_lockfile_content(root, is_dev=False, upgrade=False)
            actual_rt = rt_path.read_text(encoding="utf-8").replace("\r\n", "\n")
            if actual_rt != expected_rt:
                diff = "".join(
                    difflib.unified_diff(
                        actual_rt.splitlines(keepends=True),
                        expected_rt.splitlines(keepends=True),
                        fromfile="committed/requirements.lock",
                        tofile="recompiled/requirements.lock",
                    )
                )
                print("[FAIL] Drift detected in requirements.lock:\n" + diff, file=sys.stderr)
                return 1
            tmp_rt.write_text(expected_rt, encoding="utf-8")
        elif rt_path.is_file():
            tmp_rt.write_text(rt_path.read_text(encoding="utf-8"), encoding="utf-8")

        if target in {"all", "dev"}:
            expected_dev = build_lockfile_content(
                root,
                is_dev=True,
                upgrade=False,
                runtime_constraint=tmp_rt if tmp_rt.is_file() else None,
            )
            actual_dev = dev_path.read_text(encoding="utf-8").replace("\r\n", "\n")
            if actual_dev != expected_dev:
                diff = "".join(
                    difflib.unified_diff(
                        actual_dev.splitlines(keepends=True),
                        expected_dev.splitlines(keepends=True),
                        fromfile="committed/requirements-dev.lock",
                        tofile="recompiled/requirements-dev.lock",
                    )
                )
                print("[FAIL] Drift detected in requirements-dev.lock:\n" + diff, file=sys.stderr)
                return 1
    print("[OK] Committed lockfiles are 100% reproducible and free of drift.")
    return 0


def cmd_install_build_deps(root: Path) -> int:
    pyproject_data = _load_pyproject(root)
    dev_lock = root / "requirements-dev.lock"
    ok, msg, _ = validate_python_lockfile(dev_lock, pyproject_data=pyproject_data, is_dev=True)
    if not ok:
        print(f"[FAIL] Cannot install build dependencies: {msg}", file=sys.stderr)
        return 1
    build_pkgs = {
        canonicalize_pkg_name(str(i).split("==", 1)[0].split(">=", 1)[0])
        for i in pyproject_data.get("build-system", {}).get("requires", [])
    }
    stanzas = _parse_pip_compile_stanzas(dev_lock.read_text(encoding="utf-8"))
    missing = sorted(build_pkgs - set(stanzas))
    if missing:
        print(f"[FAIL] Missing build package(s): {missing}", file=sys.stderr)
        return 1
    blocks = [
        LockedPackage(pkg, stanzas[pkg][0], stanzas[pkg][1], None, ()).render()
        for pkg in sorted(build_pkgs)
    ]
    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", suffix="-build.lock", delete=False
    ) as handle:
        handle.write("\n\n".join(blocks) + "\n")
        tmp_build = Path(handle.name)
    try:
        cmd = [
            sys.executable,
            "-m",
            "pip",
            "install",
            "--require-hashes",
            "--no-deps",
            "-r",
            str(tmp_build),
        ]
        subprocess.run(cmd, cwd=root, check=True, timeout=300)  # noqa: S603
    finally:
        tmp_build.unlink(missing_ok=True)
    return 0


def cmd_install(root: Path, *, target: str) -> int:
    if cmd_verify(root) != 0:
        return 1
    if target == "runtime":
        if cmd_install_build_deps(root) != 0:
            return 1
        lock_file = root / "requirements.lock"
    else:
        lock_file = root / "requirements-dev.lock"
    pip_lock_cmd = [
        sys.executable,
        "-m",
        "pip",
        "install",
        "--require-hashes",
        "--no-deps",
        "-r",
        str(lock_file),
    ]
    for cmd in (
        pip_lock_cmd,
        [sys.executable, "-m", "pip", "install", "--no-build-isolation", "--no-deps", "-e", "."],
        [sys.executable, "-m", "pip", "check"],
    ):
        subprocess.run(cmd, cwd=root, check=True, timeout=600)  # noqa: S603
    return 0


def cmd_audit(root: Path) -> int:
    if cmd_verify(root) != 0:
        return 1
    base_flags = ["--require-hashes", "--disable-pip", "--strict", "--desc"]
    with tempfile.TemporaryDirectory(prefix="gencode-gov-audit-") as tmp_str:
        tmpdir = Path(tmp_str)
        for lock_name in ("requirements.lock", "requirements-dev.lock"):
            lock_path = root / lock_name
            if not lock_path.is_file():
                continue
            raw_txt = lock_path.read_text(encoding="utf-8")
            cmd = [sys.executable, "-m", "pip_audit", "--requirement", str(lock_path), *base_flags]
            subprocess.run(cmd, cwd=root, check=True, timeout=300)  # noqa: S603
            if " ; " in raw_txt:
                uni_path = tmpdir / f"universal-{lock_name}"
                _seed_without_markers(lock_path, uni_path)
                uni_cmd = [
                    sys.executable,
                    "-m",
                    "pip_audit",
                    "--requirement",
                    str(uni_path),
                    *base_flags,
                ]
                subprocess.run(uni_cmd, cwd=root, check=True, timeout=300)  # noqa: S603
    subprocess.run(  # noqa: S603
        [sys.executable, "-m", "pip_audit", "--strict", "--desc"],
        cwd=root,
        check=True,
        timeout=300,
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Deterministic hash-pinned dependency lockfile manager for GENCODE-GOV."
    )
    parser.add_argument("--root", type=Path, default=REPO_ROOT, help="Repository root path")
    sub = parser.add_subparsers(dest="command", required=True)
    p_comp = sub.add_parser("compile", help="Compile deterministic root lockfiles")
    p_comp.add_argument("--target", choices=("all", "runtime", "dev"), default="all")
    p_comp.add_argument("--upgrade", action="store_true", help="Upgrade transitive pins")
    sub.add_parser("verify", help="Verify lockfile integrity, hashes, seals, and manifest parity")
    p_drift = sub.add_parser("check-drift", help="Verify lockfile reproducibility without writing")
    p_drift.add_argument("--target", choices=("all", "runtime", "dev"), default="all")
    sub.add_parser("install-build-deps", help="Install hash-verified build-system dependencies")
    p_inst = sub.add_parser("install", help="Perform clean hash-verified environment installation")
    p_inst.add_argument("--target", choices=("runtime", "dev"), default="dev")
    sub.add_parser("audit", help="Audit committed lockfiles and active environment with pip-audit")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = args.root.resolve()
    dispatch = {
        "compile": lambda: cmd_compile(root, target=args.target, upgrade=bool(args.upgrade)),
        "verify": lambda: cmd_verify(root),
        "check-drift": lambda: cmd_check_drift(root, target=args.target),
        "install-build-deps": lambda: cmd_install_build_deps(root),
        "install": lambda: cmd_install(root, target=args.target),
        "audit": lambda: cmd_audit(root),
    }
    return dispatch[args.command]()


if __name__ == "__main__":
    raise SystemExit(main())
