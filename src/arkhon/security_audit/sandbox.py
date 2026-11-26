"""Enforceable OS sandbox and descriptor-pinned artifact promotion for security audits."""

from __future__ import annotations

import hashlib
import os
import re
import resource
import shutil
import stat
import subprocess
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

AGENT_ID_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{0,63}$")
WINDOWS_RESERVED_NAMES = frozenset(
    {
        "con",
        "prn",
        "aux",
        "nul",
        *(f"com{i}" for i in range(1, 10)),
        *(f"lpt{i}" for i in range(1, 10)),
    }
)

SAFE_ENV_ALLOWLIST = frozenset({"PATH", "LANG", "LC_ALL", "PYTHONPATH", "PYTHONHASHSEED"})


def validate_agent_id(agent_id: str) -> bool:
    """Validate canonical lowercase agent identifier and reject reserved device names."""
    if not AGENT_ID_RE.fullmatch(agent_id):
        return False
    stem = agent_id.split(".", 1)[0]
    return stem not in WINDOWS_RESERVED_NAMES


def validate_relative_artifact_path(rel_path: str) -> tuple[str, ...] | None:
    """Validate declared scratch-relative path and return path segments or None."""
    if not rel_path or rel_path != rel_path.strip() or "\\" in rel_path:
        return None
    if rel_path.startswith(("/", "~")) or re.match(r"^[A-Za-z]:", rel_path):
        return None
    parts = tuple(rel_path.split("/"))
    for part in parts:
        if not part or part in {".", ".."} or part.endswith((" ", ".")):
            return None
        if part.split(".", 1)[0].lower() in WINDOWS_RESERVED_NAMES:
            return None
        if any(ord(ch) < 32 for ch in part):
            return None
    return parts


@dataclass(frozen=True)
class SandboxCapabilities:
    """Detected host OS isolation primitives."""

    posix: bool
    has_o_nofollow: bool
    has_dir_fd: bool
    has_rlimits: bool
    bwrap_path: str | None
    unshare_net_available: bool

    @property
    def network_isolated_backend(self) -> str:
        if self.bwrap_path is not None:
            return "bwrap"
        if self.unshare_net_available:
            return "unshare-user-net"
        return "unavailable"

    @property
    def can_enforce_full_sandbox(self) -> bool:
        return (
            self.posix
            and self.has_o_nofollow
            and self.has_dir_fd
            and self.has_rlimits
            and self.network_isolated_backend != "unavailable"
        )


def probe_sandbox_capabilities(
    *,
    which_fn: Callable[[str], str | None] = shutil.which,
    run_probe: bool = True,
) -> SandboxCapabilities:
    """Probe actual host OS capabilities without fabricating unavailable isolation."""
    is_posix = os.name == "posix"
    has_nofollow = hasattr(os, "O_NOFOLLOW")
    has_dir_fd = os.open in os.supports_dir_fd
    has_rlimits = hasattr(resource, "setrlimit")
    bwrap = which_fn("bwrap")
    if bwrap is not None and run_probe:
        try:
            probe_bwrap = subprocess.run(  # noqa: S603 - fixed binary probe
                [bwrap, "--unshare-net", "--ro-bind", "/", "/", "/bin/true"],
                capture_output=True,
                text=True,
                timeout=3,
                check=False,
            )
            if probe_bwrap.returncode != 0:
                bwrap = None
        except (OSError, subprocess.SubprocessError):
            bwrap = None

    unshare_ok = False
    unshare_bin = which_fn("unshare")
    true_bin = which_fn("true") or "/bin/true"
    if is_posix and unshare_bin is not None and run_probe:
        try:
            probe_res = subprocess.run(  # noqa: S603 - fixed capability probe
                [unshare_bin, "-r", "--net", true_bin],
                capture_output=True,
                text=True,
                timeout=3,
                check=False,
            )
            unshare_ok = probe_res.returncode == 0
        except (OSError, subprocess.SubprocessError):
            unshare_ok = False

    return SandboxCapabilities(
        posix=is_posix,
        has_o_nofollow=has_nofollow,
        has_dir_fd=has_dir_fd,
        has_rlimits=has_rlimits,
        bwrap_path=bwrap,
        unshare_net_available=unshare_ok,
    )


@dataclass(frozen=True)
class SandboxLimits:
    """Explicit low resource and byte caps enforced for bounded local checks."""

    cpu_seconds: int = 10
    wall_timeout_seconds: float = 10.0
    memory_bytes: int = 512 * 1024 * 1024
    max_file_bytes: int = 2 * 1024 * 1024
    max_cumulative_artifact_bytes: int = 8 * 1024 * 1024
    max_processes: int = 32
    max_open_files: int = 128


@dataclass(frozen=True)
class SandboxResult:
    """Outcome of a sandboxed local verification command."""

    status: str
    backend: str
    returncode: int | None
    stdout: str
    stderr: str
    scratch_dir: Path
    blocker_reason: str | None = None


@dataclass(frozen=True)
class PromotionResult:
    """Outcome of descriptor-pinned parent-side scratch artifact promotion."""

    promoted: tuple[str, ...]
    rejected: tuple[tuple[str, str], ...]
    total_bytes: int


def _snapshot_tree_digests(root: Path) -> dict[str, str]:
    digests: dict[str, str] = {}
    for file_path in sorted(root.rglob("*")):
        if file_path.is_file() and not file_path.is_symlink():
            rel = str(file_path.relative_to(root))
            if rel.startswith(".git/"):
                continue
            digests[rel] = hashlib.sha256(file_path.read_bytes()).hexdigest()
    return digests


def _build_preexec_limiter(limits: SandboxLimits) -> Callable[[], None]:
    def _apply() -> None:
        pairs = (
            (resource.RLIMIT_CPU, (limits.cpu_seconds, limits.cpu_seconds)),
            (resource.RLIMIT_FSIZE, (limits.max_file_bytes, limits.max_file_bytes)),
            (resource.RLIMIT_NOFILE, (limits.max_open_files, limits.max_open_files)),
        )
        for res_key, bounds in pairs:
            try:
                resource.setrlimit(res_key, bounds)
            except (OSError, ValueError):
                continue
        for optional_key, bound_val in (
            (resource.RLIMIT_AS, limits.memory_bytes),
            (resource.RLIMIT_NPROC, limits.max_processes),
        ):
            try:
                soft, hard = resource.getrlimit(optional_key)
                capped = bound_val if hard == resource.RLIM_INFINITY else min(bound_val, hard)
                _ = soft
                resource.setrlimit(optional_key, (capped, hard))
            except (OSError, ValueError):
                continue

    return _apply


class SandboxExecutor:
    """Executes bounded local checks inside an OS-isolated workspace or fails closed."""

    def __init__(
        self,
        audit_dir: Path,
        *,
        capabilities: SandboxCapabilities | None = None,
        limits: SandboxLimits | None = None,
    ) -> None:
        self.audit_dir = audit_dir.resolve()
        self.capabilities = capabilities or probe_sandbox_capabilities()
        self.limits = limits or SandboxLimits()

    def prepare_agent_dirs(self, agent_id: str) -> tuple[Path, Path]:
        """Create isolated scratch/ and parent-owned artifacts/ directories for agent_id."""
        if not validate_agent_id(agent_id):
            raise ValueError(f"unsafe or non-canonical agent_id: {agent_id!r}")
        agent_root = self.audit_dir / "agents" / agent_id
        scratch_dir = agent_root / "scratch"
        artifacts_dir = agent_root / "artifacts"
        scratch_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
        artifacts_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
        for sub in ("home", "tmp", "cache"):
            (scratch_dir / sub).mkdir(parents=True, exist_ok=True, mode=0o700)
        return scratch_dir, artifacts_dir

    def build_allowlisted_env(
        self,
        scratch_dir: Path,
        extra_env: dict[str, str] | None = None,
    ) -> dict[str, str]:
        """Construct an empty environment populated strictly from safe allowlisted keys."""
        clean_env: dict[str, str] = {
            "PATH": "/usr/local/bin:/usr/bin:/bin",
            "HOME": str(scratch_dir / "home"),
            "TMPDIR": str(scratch_dir / "tmp"),
            "XDG_CACHE_HOME": str(scratch_dir / "cache"),
            "LANG": "C.UTF-8",
            "LC_ALL": "C.UTF-8",
            "PYTHONHASHSEED": "0",
            "ARKHON_SANDBOX": "1",
        }
        if extra_env:
            for key, val in extra_env.items():
                if key not in SAFE_ENV_ALLOWLIST:
                    raise ValueError(f"environment variable not in sandbox allowlist: {key!r}")
                clean_env[key] = val
        return clean_env

    def run_bounded(
        self,
        *,
        agent_id: str,
        argv: list[str],
        source_root: Path,
        extra_env: dict[str, str] | None = None,
        allow_loopback: bool = False,
        require_network_isolation: bool = True,
    ) -> SandboxResult:
        """Execute argv under OS isolation; fail closed as BLOCKED if unavailable."""
        scratch_dir, _ = self.prepare_agent_dirs(agent_id)
        if not argv or any(not arg for arg in argv):
            raise ValueError("argv must be a non-empty command vector")
        resolved_source = source_root.resolve()
        if require_network_isolation and not self.capabilities.can_enforce_full_sandbox:
            return SandboxResult(
                status="BLOCKED",
                backend=self.capabilities.network_isolated_backend,
                returncode=None,
                stdout="",
                stderr="",
                scratch_dir=scratch_dir,
                blocker_reason=(
                    "OS network-isolated sandbox unavailable; refusing to execute target code"
                ),
            )

        clean_env = self.build_allowlisted_env(scratch_dir, extra_env)
        backend = self.capabilities.network_isolated_backend
        cmd: list[str]
        if self.capabilities.bwrap_path is not None:
            cmd = [
                self.capabilities.bwrap_path,
                "--unshare-all",
                "--die-with-parent",
                "--ro-bind",
                "/",
                "/",
                "--ro-bind",
                str(resolved_source),
                str(resolved_source),
                "--bind",
                str(scratch_dir),
                str(scratch_dir),
                "--dev",
                "/dev",
                "--proc",
                "/proc",
                "--chdir",
                str(scratch_dir),
                "--",
                *argv,
            ]
        elif self.capabilities.unshare_net_available:
            unshare_bin = shutil.which("unshare") or "/usr/bin/unshare"
            if allow_loopback and shutil.which("ip"):
                ip_bin = shutil.which("ip") or "/sbin/ip"
                sh_bin = shutil.which("sh") or "/bin/sh"
                cmd = [
                    unshare_bin,
                    "-r",
                    "--net",
                    sh_bin,
                    "-c",
                    f'{ip_bin} link set lo up >/dev/null 2>&1 || true; exec "$@"',
                    "arkhon-sandbox",
                    *argv,
                ]
            else:
                cmd = [unshare_bin, "-r", "--net", *argv]
        else:
            backend = "rlimit-only"
            cmd = list(argv)

        before_digests = _snapshot_tree_digests(resolved_source)
        try:
            proc = subprocess.run(  # noqa: S603 - fixed sandbox wrapper and allowlisted env
                cmd,
                cwd=scratch_dir,
                env=clean_env,
                capture_output=True,
                text=True,
                timeout=self.limits.wall_timeout_seconds,
                check=False,
                preexec_fn=(
                    _build_preexec_limiter(self.limits) if self.capabilities.posix else None
                ),
            )
        except subprocess.TimeoutExpired:
            return SandboxResult(
                status="BLOCKED",
                backend=backend,
                returncode=None,
                stdout="",
                stderr="",
                scratch_dir=scratch_dir,
                blocker_reason="sandboxed check exceeded wall-clock timeout",
            )
        except OSError as exc:
            return SandboxResult(
                status="BLOCKED",
                backend=backend,
                returncode=None,
                stdout="",
                stderr=str(exc),
                scratch_dir=scratch_dir,
                blocker_reason=f"sandbox process launch failed: {exc}",
            )

        after_digests = _snapshot_tree_digests(resolved_source)
        if before_digests != after_digests:
            return SandboxResult(
                status="BLOCKED",
                backend=backend,
                returncode=proc.returncode,
                stdout=proc.stdout,
                stderr=proc.stderr,
                scratch_dir=scratch_dir,
                blocker_reason="target source tree was modified during sandboxed check",
            )

        return SandboxResult(
            status="PASS" if proc.returncode == 0 else "FAIL",
            backend=backend,
            returncode=proc.returncode,
            stdout=proc.stdout[:65536],
            stderr=proc.stderr[:65536],
            scratch_dir=scratch_dir,
            blocker_reason=None,
        )


def _walk_parent_dirs_nofollow(root_fd: int, segments: tuple[str, ...], create: bool) -> int:
    """Walk parent directory segments via dir_fd + O_NOFOLLOW; caller closes returned fd."""
    current_fd = os.dup(root_fd)
    flags = os.O_RDONLY | os.O_NOFOLLOW | getattr(os, "O_DIRECTORY", 0)
    try:
        for seg in segments:
            if create:
                try:
                    os.mkdir(seg, 0o700, dir_fd=current_fd)
                except FileExistsError:
                    pass
            next_fd = os.open(seg, flags, dir_fd=current_fd)
            st = os.fstat(next_fd)
            if not stat.S_ISDIR(st.st_mode):
                os.close(next_fd)
                raise OSError(f"path segment is not a directory: {seg}")
            os.close(current_fd)
            current_fd = next_fd
        return current_fd
    except Exception:
        os.close(current_fd)
        raise


def promote_agent_artifacts(
    *,
    scratch_dir: Path,
    artifacts_dir: Path,
    allowlisted_files: tuple[str, ...],
    max_file_bytes: int = 2 * 1024 * 1024,
    max_cumulative_bytes: int = 8 * 1024 * 1024,
) -> PromotionResult:
    """Promote allowlisted regular files from scratch/ to artifacts/ using dir_fd + O_NOFOLLOW."""
    promoted: list[str] = []
    rejected: list[tuple[str, str]] = []
    cumulative_bytes = 0

    dir_flags = os.O_RDONLY | os.O_NOFOLLOW | getattr(os, "O_DIRECTORY", 0)
    scratch_root_fd = os.open(str(scratch_dir), dir_flags)
    artifacts_root_fd = os.open(str(artifacts_dir), dir_flags)
    try:
        for rel_path in allowlisted_files:
            segments = validate_relative_artifact_path(rel_path)
            if segments is None:
                rejected.append((rel_path, "unsafe or non-relative artifact path"))
                continue
            parent_segs, leaf_name = segments[:-1], segments[-1]
            try:
                src_parent_fd = _walk_parent_dirs_nofollow(
                    scratch_root_fd, parent_segs, create=False
                )
            except OSError as exc:
                rejected.append((rel_path, f"invalid scratch parent directory: {exc}"))
                continue

            try:
                read_flags = os.O_RDONLY | os.O_NOFOLLOW | getattr(os, "O_NONBLOCK", 0)
                src_fd = os.open(leaf_name, read_flags, dir_fd=src_parent_fd)
            except OSError as exc:
                os.close(src_parent_fd)
                rejected.append((rel_path, f"cannot open scratch file no-follow: {exc}"))
                continue
            os.close(src_parent_fd)

            try:
                st_before = os.fstat(src_fd)
                if not stat.S_ISREG(st_before.st_mode):
                    rejected.append((rel_path, "scratch entry is not a regular file"))
                    continue
                if st_before.st_nlink != 1:
                    rejected.append((rel_path, "hard-linked scratch file rejected"))
                    continue
                if st_before.st_size > max_file_bytes:
                    rejected.append((rel_path, "file exceeds per-file byte limit"))
                    continue
                if cumulative_bytes + st_before.st_size > max_cumulative_bytes:
                    rejected.append((rel_path, "cumulative artifact byte limit exceeded"))
                    continue

                chunks: list[bytes] = []
                bytes_read = 0
                while bytes_read < st_before.st_size + 1:
                    chunk = os.read(src_fd, 65536)
                    if not chunk:
                        break
                    bytes_read += len(chunk)
                    if bytes_read > max_file_bytes:
                        break
                    chunks.append(chunk)

                st_after = os.fstat(src_fd)
                identity_unchanged = (
                    stat.S_ISREG(st_after.st_mode)
                    and st_after.st_nlink == 1
                    and st_after.st_dev == st_before.st_dev
                    and st_after.st_ino == st_before.st_ino
                    and st_after.st_size == st_before.st_size
                    and bytes_read == st_before.st_size
                )
                if not identity_unchanged:
                    rejected.append((rel_path, "scratch file mutated during promotion"))
                    continue
                data = b"".join(chunks)

                dst_parent_fd = _walk_parent_dirs_nofollow(
                    artifacts_root_fd, parent_segs, create=True
                )
                try:
                    write_flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW
                    dst_fd = os.open(leaf_name, write_flags, 0o600, dir_fd=dst_parent_fd)
                    try:
                        dst_stat = os.fstat(dst_fd)
                        if not stat.S_ISREG(dst_stat.st_mode) or dst_stat.st_nlink != 1:
                            rejected.append((rel_path, "destination verification failed"))
                            continue
                        view = memoryview(data)
                        written = 0
                        while written < len(data):
                            written += os.write(dst_fd, view[written:])
                    finally:
                        os.close(dst_fd)
                finally:
                    os.close(dst_parent_fd)

                cumulative_bytes += len(data)
                promoted.append(rel_path)
            except OSError as exc:
                rejected.append((rel_path, f"artifact promotion error: {exc}"))
            finally:
                os.close(src_fd)
    finally:
        os.close(scratch_root_fd)
        os.close(artifacts_root_fd)

    return PromotionResult(
        promoted=tuple(promoted),
        rejected=tuple(rejected),
        total_bytes=cumulative_bytes,
    )
