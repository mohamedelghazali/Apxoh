"""Unit tests for OS SandboxExecutor and descriptor-pinned O_NOFOLLOW promotion."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

from arkhon.security_audit.sandbox import (
    SandboxCapabilities,
    SandboxExecutor,
    SandboxLimits,
    probe_sandbox_capabilities,
    promote_agent_artifacts,
    validate_agent_id,
    validate_relative_artifact_path,
)


def test_agent_id_and_artifact_path_validation() -> None:
    assert validate_agent_id("hunter-01") is True
    assert validate_agent_id("UpperCase") is False
    assert validate_agent_id("con") is False
    assert validate_agent_id("lpt1.txt") is False

    assert validate_relative_artifact_path("sub/out.json") == ("sub", "out.json")
    assert validate_relative_artifact_path("") is None
    assert validate_relative_artifact_path("/abs/path") is None
    assert validate_relative_artifact_path("../escape") is None
    assert validate_relative_artifact_path("C:/win") is None
    assert validate_relative_artifact_path("a\\b") is None
    assert validate_relative_artifact_path("aux/file.txt") is None
    assert validate_relative_artifact_path("bad\x00name") is None


def test_sandbox_capability_probing_and_isolated_execution(tmp_path: Path) -> None:
    caps_no_probe = probe_sandbox_capabilities(which_fn=lambda _: None, run_probe=False)
    assert caps_no_probe.network_isolated_backend == "unavailable"
    assert caps_no_probe.can_enforce_full_sandbox is False

    caps_bwrap = SandboxCapabilities(True, True, True, True, "/usr/bin/bwrap", False)
    assert caps_bwrap.network_isolated_backend == "bwrap"
    assert caps_bwrap.can_enforce_full_sandbox is True

    # Probe with failing fake binary path falls back cleanly
    caps_bad_bin = probe_sandbox_capabilities(
        which_fn=lambda name: "/bin/false" if name in {"bwrap", "unshare"} else None,
        run_probe=True,
    )
    assert caps_bad_bin.bwrap_path is None
    assert caps_bad_bin.unshare_net_available is False

    src_root = tmp_path / "src_repo"
    src_root.mkdir()
    (src_root / "app.py").write_text("x = 1\n", encoding="utf-8")

    # Fail-closed when network isolation is unavailable
    blocked_exec = SandboxExecutor(tmp_path / "audit_blocked", capabilities=caps_no_probe)
    with pytest.raises(ValueError, match="unsafe or non-canonical"):
        blocked_exec.prepare_agent_dirs("PRN")
    with pytest.raises(ValueError, match="non-empty command vector"):
        blocked_exec.run_bounded(agent_id="hunter-01", argv=[], source_root=src_root)
    with pytest.raises(ValueError, match="not in sandbox allowlist"):
        blocked_exec.build_allowlisted_env(tmp_path, {"SECRET_API_TOKEN": "nope"})

    blk = blocked_exec.run_bounded(
        agent_id="hunter-01",
        argv=[sys.executable, "-c", "print('hi')"],
        source_root=src_root,
    )
    assert blk.status == "BLOCKED"
    assert blk.returncode is None

    # Allow explicit opt-out of network requirement (rlimit-only fallback) & test timeout/tamper
    rlimit_res = blocked_exec.run_bounded(
        agent_id="hunter-01",
        argv=[
            sys.executable,
            "-c",
            "import os; assert 'SECRET' not in os.environ; print(os.environ['ARKHON_SANDBOX'])",
        ],
        source_root=src_root,
        extra_env={"PYTHONPATH": str(src_root)},
        require_network_isolation=False,
    )
    assert rlimit_res.status == "PASS"
    assert rlimit_res.stdout.strip() == "1"

    # Timeout handling
    fast_timeout = SandboxExecutor(
        tmp_path / "audit_timeout",
        capabilities=caps_no_probe,
        limits=SandboxLimits(wall_timeout_seconds=0.1),
    )
    to_res = fast_timeout.run_bounded(
        agent_id="hunter-01",
        argv=[sys.executable, "-c", "import time; time.sleep(2)"],
        source_root=src_root,
        require_network_isolation=False,
    )
    assert to_res.status == "BLOCKED"
    assert "timeout" in (to_res.blocker_reason or "")

    # Missing executable handling
    os_err = blocked_exec.run_bounded(
        agent_id="hunter-01",
        argv=["/nonexistent/binary/arkhon_nope"],
        source_root=src_root,
        require_network_isolation=False,
    )
    assert os_err.status == "BLOCKED"

    # Source tree tamper detection fails closed to BLOCKED
    tamper_res = blocked_exec.run_bounded(
        agent_id="hunter-01",
        argv=[
            sys.executable,
            "-c",
            f"from pathlib import Path; Path({str(src_root / 'app.py')!r}).write_text('x = 2\\n')",
        ],
        source_root=src_root,
        require_network_isolation=False,
    )
    assert tamper_res.status == "BLOCKED"
    assert "modified" in (tamper_res.blocker_reason or "")

    # Real Linux unshare -r --net verification when available on host
    live_exec = SandboxExecutor(tmp_path / "audit_live")
    if live_exec.capabilities.unshare_net_available:
        net_res = live_exec.run_bounded(
            agent_id="hunter-net",
            argv=[
                sys.executable,
                "-c",
                (
                    "import socket\n"
                    "s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)\n"
                    "try:\n"
                    "    s.connect(('192.0.2.1', 53))\n"
                    "    raise SystemExit(1)\n"
                    "except OSError:\n"
                    "    print('NET_ISOLATED')\n"
                ),
            ],
            source_root=src_root,
            allow_loopback=True,
        )
        assert net_res.status == "PASS"
        assert "NET_ISOLATED" in net_res.stdout


def test_descriptor_pinned_artifact_promotion_rejects_symlinks_hardlinks_fifos_and_caps(
    tmp_path: Path,
) -> None:
    exec_sb = SandboxExecutor(tmp_path / "promo")
    scratch, artifacts = exec_sb.prepare_agent_dirs("hunter-01")

    (scratch / "nested").mkdir()
    good = scratch / "nested" / "result.json"
    good.write_text('{"ok": true}\n', encoding="utf-8")

    symlink_file = scratch / "sym.json"
    symlink_file.symlink_to(good)

    hardlink_target = scratch / "hard_src.txt"
    hardlink_target.write_text("shared", encoding="utf-8")
    hardlink_alias = scratch / "hard_alias.txt"
    os.link(hardlink_target, hardlink_alias)

    fifo_path = scratch / "pipe.fifo"
    os.mkfifo(fifo_path)

    oversized = scratch / "huge.bin"
    oversized.write_bytes(b"x" * 200)

    second_ok = scratch / "second.txt"
    second_ok.write_bytes(b"y" * 80)

    res = promote_agent_artifacts(
        scratch_dir=scratch,
        artifacts_dir=artifacts,
        allowlisted_files=(
            "nested/result.json",
            "../traversal.txt",
            "missing_dir/file.txt",
            "sym.json",
            "hard_alias.txt",
            "pipe.fifo",
            "huge.bin",
            "second.txt",
        ),
        max_file_bytes=100,
        max_cumulative_bytes=85,
    )
    assert res.promoted == ("nested/result.json",)
    assert (artifacts / "nested" / "result.json").read_text(encoding="utf-8") == '{"ok": true}\n'
    rejected_names = {name for name, _ in res.rejected}
    assert {
        "../traversal.txt",
        "missing_dir/file.txt",
        "sym.json",
        "hard_alias.txt",
        "pipe.fifo",
        "huge.bin",
        "second.txt",
    } == rejected_names
