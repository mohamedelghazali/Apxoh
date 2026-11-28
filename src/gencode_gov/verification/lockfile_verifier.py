"""Deterministic lockfile integrity, hash completeness, and manifest-drift verification."""

from __future__ import annotations

import hashlib
import json
import re
import tomllib
from pathlib import Path
from typing import Any

from gencode_gov.core.constants import STATUS_FAIL, STATUS_PASS

PYTHON_HASH_LOCKFILES = ("requirements.lock", "requirements-dev.lock")
ECOSYSTEM_LOCKFILES = (
    "uv.lock",
    "poetry.lock",
    "Cargo.lock",
    "package-lock.json",
    "pnpm-lock.yaml",
    "go.sum",
)

_CANON_RE = re.compile(r"[-_.]+")
_PINNED_SPEC_RE = re.compile(
    r"^([A-Za-z0-9](?:[A-Za-z0-9._-]*[A-Za-z0-9])?)==([A-Za-z0-9][A-Za-z0-9._!+-]*)$"
)
_DECLARED_SPEC_RE = re.compile(
    r"^([A-Za-z0-9](?:[A-Za-z0-9._-]*[A-Za-z0-9])?)(?:\[[^\]]*\])?\s*(.*)$"
)
_OP_SPEC_RE = re.compile(r"^(==|!=|<=|>=|~=|===|<|>)\s*([A-Za-z0-9][A-Za-z0-9._!+-]*)$")
_SHA256_HASH_RE = re.compile(r"^--hash=sha256:[0-9a-f]{64}$")
_HEX64_RE = re.compile(r"^[0-9a-f]{64}$")
_FORBIDDEN_DIRECTIVES = (
    "--index-url",
    "--extra-index-url",
    "--trusted-host",
    "--find-links",
    "--no-binary",
    "--pre",
    "--editable",
    "--requirement",
    "--constraint",
)
_FORBIDDEN_SHORT_FLAGS = ("-i", "-f", "-e", "-r", "-c")
_FORBIDDEN_URL_TOKENS = (
    "git+",
    "hg+",
    "svn+",
    "bzr+",
    "ht" + "tp://",
    "ht" + "tps://",
    "file:",
)

MANIFEST_SEAL_PREFIX = "# gencode-gov-manifest-sha256:"
BODY_SEAL_PREFIX = "# gencode-gov-lock-body-sha256:"


def canonicalize_pkg_name(name: str) -> str:
    """Normalize a Python distribution name per PEP 503."""
    return _CANON_RE.sub("-", name.strip()).lower()


def _string_list(mapping: dict[str, Any], key: str) -> list[str]:
    raw = mapping.get(key, [])
    if not isinstance(raw, list):
        return []
    return [str(item).strip() for item in raw if str(item).strip()]


def compute_pyproject_lock_digest(
    pyproject_data: dict[str, Any],
    *,
    include_dev: bool = False,
) -> str:
    """Compute a canonical SHA-256 digest of dependency declarations in pyproject.toml."""
    project = pyproject_data.get("project", {})
    proj_map = project if isinstance(project, dict) else {}

    payload: dict[str, Any] = {
        "dependencies": _string_list(proj_map, "dependencies"),
        "requires-python": str(proj_map.get("requires-python", "")).strip(),
    }
    if include_dev:
        build_sys = pyproject_data.get("build-system", {})
        bs_map = build_sys if isinstance(build_sys, dict) else {}
        opt = proj_map.get("optional-dependencies", {})
        opt_map = opt if isinstance(opt, dict) else {}

        payload["build-system.build-backend"] = str(bs_map.get("build-backend", "")).strip()
        payload["build-system.requires"] = _string_list(bs_map, "requires")
        payload["optional-dependencies.dev"] = _string_list(opt_map, "dev")

    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def compute_lock_body_digest(lock_text: str) -> str:
    """Compute SHA-256 over normalized lockfile contents excluding the body-seal line itself."""
    normalized = lock_text.replace("\r\n", "\n").replace("\r", "\n")
    kept = [line for line in normalized.split("\n") if not line.startswith(BODY_SEAL_PREFIX)]
    return hashlib.sha256("\n".join(kept).encode("utf-8")).hexdigest()


def _version_key(version: str) -> tuple[tuple[int, int | str], ...]:
    parts = re.split(r"([0-9]+)", version.strip())
    key: list[tuple[int, int | str]] = []
    for token in parts:
        if not token or token == ".":
            continue
        if token.isdigit():
            key.append((1, int(token)))
        else:
            key.append((0, token.lower()))
    return tuple(key)


def _match_single_clause(locked_version: str, op: str, target: str) -> bool:
    if op in {"==", "==="}:
        return locked_version == target
    if op == "!=":
        return locked_version != target
    lkey, tkey = _version_key(locked_version), _version_key(target)
    comparisons = {
        ">=": lkey >= tkey,
        "<=": lkey <= tkey,
        ">": lkey > tkey,
        "<": lkey < tkey,
    }
    if op in comparisons:
        return comparisons[op]
    prefix_parts = target.split(".")[:-1]
    prefix = ".".join(prefix_parts) + "." if prefix_parts else target
    return lkey >= tkey and (locked_version == target or locked_version.startswith(prefix))


def _satisfies_specifier(locked_version: str, spec_expr: str) -> bool:
    if not spec_expr.strip():
        return True
    for clause in spec_expr.split(","):
        item = clause.strip()
        if not item:
            continue
        match = _OP_SPEC_RE.match(item)
        if match is None:
            return False
        if not _match_single_clause(locked_version, match.group(1), match.group(2)):
            return False
    return True


def _extract_seals_and_entries(
    raw_text: str,
    lock_name: str,
) -> tuple[str | None, str | None, list[str], str | None]:
    manifest_seal: str | None = None
    body_seal: str | None = None
    entries: list[str] = []
    current_parts: list[str] = []

    for raw_line in raw_text.replace("\r\n", "\n").splitlines():
        stripped = raw_line.strip()
        if stripped.startswith(MANIFEST_SEAL_PREFIX):
            val = stripped[len(MANIFEST_SEAL_PREFIX) :].strip()
            if not _HEX64_RE.fullmatch(val):
                return None, None, [], f"{lock_name} has malformed manifest seal header"
            manifest_seal = val
            continue
        if stripped.startswith(BODY_SEAL_PREFIX):
            val = stripped[len(BODY_SEAL_PREFIX) :].strip()
            if not _HEX64_RE.fullmatch(val):
                return None, None, [], f"{lock_name} has malformed body seal header"
            body_seal = val
            continue
        if not stripped or stripped.startswith("#"):
            if current_parts:
                entries.append(" ".join(current_parts))
                current_parts = []
            continue

        code_part = raw_line.split(" #", 1)[0].rstrip()
        is_cont = code_part.endswith("\\")
        seg = (code_part[:-1] if is_cont else code_part).strip()
        if seg:
            current_parts.append(seg)
        if not is_cont and current_parts:
            entries.append(" ".join(current_parts))
            current_parts = []

    if current_parts:
        entries.append(" ".join(current_parts))
    return manifest_seal, body_seal, entries, None


def _is_forbidden_token(tok: str) -> str | None:
    if tok in _FORBIDDEN_SHORT_FLAGS or any(tok.startswith(d) for d in _FORBIDDEN_DIRECTIVES):
        return f"contains forbidden pip directive: {tok}"
    if "@" in tok or any(tok.lower().startswith(u) for u in _FORBIDDEN_URL_TOKENS):
        return f"contains unpinned URL or VCS requirement: {tok}"
    return None


def _parse_and_check_entry(
    entry: str,
    lock_name: str,
    pinned: dict[str, str],
) -> str | None:
    tokens = entry.split()
    for tok in tokens:
        violation = _is_forbidden_token(tok)
        if violation is not None:
            return f"{lock_name} {violation}"

    hash_tokens = [tok for tok in tokens if tok.startswith("--hash")]
    other_flags = [tok for tok in tokens if tok.startswith("-") and not tok.startswith("--hash")]
    if other_flags:
        return f"{lock_name} contains unsupported option flag: {other_flags[0]}"
    if not hash_tokens:
        return f"{lock_name} requirement missing --hash=sha256 digest: {tokens[0]}"
    for htok in hash_tokens:
        if not _SHA256_HASH_RE.fullmatch(htok):
            return f"{lock_name} contains invalid or weak hash token: {htok}"

    non_hash_text = " ".join(tok for tok in tokens if not tok.startswith("--hash"))
    spec_part = non_hash_text.split(";", 1)[0].strip()
    match = _PINNED_SPEC_RE.fullmatch(spec_part)
    if match is None:
        return f"{lock_name} requirement is not exact == pinned: {spec_part}"

    pkg_name = canonicalize_pkg_name(match.group(1))
    pkg_ver = match.group(2)
    existing = pinned.get(pkg_name)
    if existing is not None and existing != pkg_ver:
        return f"{lock_name} defines conflicting versions for {pkg_name}: {existing} vs {pkg_ver}"
    pinned[pkg_name] = pkg_ver
    return None


def _collect_declared_specs(pyproject_data: dict[str, Any], *, is_dev: bool) -> list[str]:
    project = pyproject_data.get("project", {})
    proj_map = project if isinstance(project, dict) else {}
    declared = _string_list(proj_map, "dependencies")
    if is_dev:
        opt = proj_map.get("optional-dependencies", {})
        opt_map = opt if isinstance(opt, dict) else {}
        declared.extend(_string_list(opt_map, "dev"))
        build_sys = pyproject_data.get("build-system", {})
        bs_map = build_sys if isinstance(build_sys, dict) else {}
        declared.extend(_string_list(bs_map, "requires"))
    return declared


def _check_declared_dependencies(
    pyproject_data: dict[str, Any],
    pinned: dict[str, str],
    lock_name: str,
    *,
    is_dev: bool,
) -> str | None:
    for raw_req in _collect_declared_specs(pyproject_data, is_dev=is_dev):
        req_head = raw_req.split(";", 1)[0].strip()
        match = _DECLARED_SPEC_RE.fullmatch(req_head)
        if match is None:
            return f"pyproject.toml contains unparseable dependency declaration: {raw_req}"
        pkg_name = canonicalize_pkg_name(match.group(1))
        spec_expr = match.group(2).strip()
        locked_ver = pinned.get(pkg_name)
        if locked_ver is None:
            return f"declaration drift: {pkg_name} from pyproject.toml missing in {lock_name}"
        if not _satisfies_specifier(locked_ver, spec_expr):
            return (
                f"declaration drift: {pkg_name}=={locked_ver} in {lock_name} "
                f"violates pyproject.toml specifier '{raw_req}'"
            )
    return None


def validate_python_lockfile(
    lock_path: Path,
    *,
    pyproject_data: dict[str, Any] | None = None,
    is_dev: bool = False,
) -> tuple[bool, str, dict[str, str]]:
    """Validate pins, SHA-256 hashes, seal integrity, and pyproject.toml alignment."""
    if lock_path.is_symlink() or not lock_path.is_file():
        return False, f"missing or symlinked lockfile: {lock_path.name}", {}
    try:
        raw_text = lock_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        return False, f"cannot read {lock_path.name}: {exc}", {}

    manifest_seal, body_seal, entries, hdr_err = _extract_seals_and_entries(
        raw_text, lock_path.name
    )
    if hdr_err is not None:
        return False, hdr_err, {}
    if not entries:
        return False, f"{lock_path.name} contains zero pinned requirements", {}

    if body_seal is not None and compute_lock_body_digest(raw_text) != body_seal:
        return (
            False,
            f"manual tampering or corruption detected in {lock_path.name} (body digest mismatch)",
            {},
        )

    pinned: dict[str, str] = {}
    for entry in entries:
        err = _parse_and_check_entry(entry, lock_path.name, pinned)
        if err is not None:
            return False, err, {}

    if pyproject_data is not None:
        if manifest_seal is not None:
            expected_manifest = compute_pyproject_lock_digest(pyproject_data, include_dev=is_dev)
            if manifest_seal != expected_manifest:
                return (
                    False,
                    f"declaration drift between pyproject.toml and {lock_path.name} "
                    "(manifest digest mismatch)",
                    {},
                )
        drift_err = _check_declared_dependencies(
            pyproject_data,
            pinned,
            lock_path.name,
            is_dev=is_dev,
        )
        if drift_err is not None:
            return False, drift_err, {}

    return True, f"{lock_path.name} ({len(pinned)} hash-pinned packages)", pinned


def _safe_root_file(root: Path, rel_name: str) -> Path | None:
    candidate = root / rel_name
    if candidate.is_symlink() or not candidate.is_file():
        return None
    try:
        candidate.resolve().relative_to(root.resolve())
    except ValueError:  # pragma: no cover
        return None
    return candidate


def _check_cross_lockfile_parity(pinned_by_lock: dict[str, dict[str, str]]) -> str | None:
    if "requirements.lock" not in pinned_by_lock or "requirements-dev.lock" not in pinned_by_lock:
        return None
    rt_pins = pinned_by_lock["requirements.lock"]
    dev_pins = pinned_by_lock["requirements-dev.lock"]
    for pkg, rt_ver in sorted(rt_pins.items()):
        dev_ver = dev_pins.get(pkg)
        if dev_ver != rt_ver:
            return (
                f"cross-lockfile drift for {pkg}: requirements.lock={rt_ver} "
                f"vs requirements-dev.lock={dev_ver}"
            )
    return None


def verify_dependency_lockfiles(project_root: Path) -> tuple[str, str]:
    """Verify repository dependency lockfiles for determinism, hashes, and drift."""
    root = project_root.resolve()
    pyproject_data: dict[str, Any] | None = None
    pyproj_path = _safe_root_file(root, "pyproject.toml")
    if pyproj_path is not None:
        try:
            loaded = tomllib.loads(pyproj_path.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                pyproject_data = loaded
        except (OSError, UnicodeDecodeError, tomllib.TOMLDecodeError) as exc:
            return STATUS_FAIL, f"invalid pyproject.toml: {exc}"

    py_locks = [name for name in PYTHON_HASH_LOCKFILES if _safe_root_file(root, name) is not None]
    eco_locks = [name for name in ECOSYSTEM_LOCKFILES if _safe_root_file(root, name) is not None]

    if not py_locks and not eco_locks:
        return STATUS_FAIL, "no deterministic dependency lockfile found in repository root"

    has_alt_py_lock = bool({"uv.lock", "poetry.lock"} & set(eco_locks))
    if pyproject_data is not None and not py_locks and not has_alt_py_lock:
        proj = pyproject_data.get("project", {})
        if isinstance(proj, dict) and proj.get("dependencies"):
            return (
                STATUS_FAIL,
                "pyproject.toml declares Python dependencies but no Python lockfile is present",
            )

    verified_summaries: list[str] = []
    pinned_by_lock: dict[str, dict[str, str]] = {}

    for lock_name in py_locks:
        ok, detail, pinned = validate_python_lockfile(
            root / lock_name,
            pyproject_data=pyproject_data,
            is_dev=(lock_name == "requirements-dev.lock"),
        )
        if not ok:
            return STATUS_FAIL, detail
        verified_summaries.append(detail)
        pinned_by_lock[lock_name] = pinned

    parity_err = _check_cross_lockfile_parity(pinned_by_lock)
    if parity_err is not None:
        return STATUS_FAIL, parity_err

    for eco_name in eco_locks:
        content = (root / eco_name).read_text(encoding="utf-8", errors="ignore").strip()
        if not content:
            return STATUS_FAIL, f"empty dependency lockfile: {eco_name}"
        verified_summaries.append(eco_name)

    summary_str = ", ".join(verified_summaries)
    return STATUS_PASS, f"verified deterministic dependency lockfile(s): {summary_str}"
