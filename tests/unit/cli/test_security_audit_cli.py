"""CLI tests verifying legacy audit compatibility and security audit subcommand routing."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from gencode_gov.cli import main

_GIT = shutil.which("git") or "/usr/bin/git"


def _init_clean_git_repo(root: Path) -> Path:
    proj = root / "clean_app"
    (proj / "src" / "clean_app").mkdir(parents=True)
    (proj / "src" / "clean_app" / "math_ops.py").write_text(
        "def add(a: int, b: int) -> int:\n    return a + b\n",
        encoding="utf-8",
    )
    subprocess.run([_GIT, "init"], cwd=proj, check=True, capture_output=True)  # noqa: S603
    subprocess.run(  # noqa: S603
        [_GIT, "config", "user.email", "ci@example.com"], cwd=proj, check=True
    )
    subprocess.run([_GIT, "config", "user.name", "CI"], cwd=proj, check=True)  # noqa: S603
    subprocess.run([_GIT, "add", "."], cwd=proj, check=True)  # noqa: S603
    subprocess.run(  # noqa: S603
        [_GIT, "commit", "-m", "initial clean commit"],
        cwd=proj,
        check=True,
        capture_output=True,
    )
    return proj


def test_cli_audit_subcommands_and_legacy_audit_backward_compatibility(
    tmp_path: Path,
) -> None:
    proj = _init_clean_git_repo(tmp_path)
    out_dir = tmp_path / "audit_out"

    # New security audit subcommands via gencode_gov.cli.main
    assert main(["audit", "plan", str(proj), "--output-dir", str(out_dir / "plan"), "--json"]) == 0
    assert main(["audit", "run", str(proj), "--output-dir", str(out_dir), "--json"]) == 0
    assert main(["audit", "validate", "--audit-dir", str(out_dir), "--json"]) == 0
    assert main(["audit", "coverage", "--audit-dir", str(out_dir), "--json"]) == 0

    # New opt-in domain in gencode-gov verify
    assert main(["verify", str(proj), "--domain", "security-audit"]) == 0

    # Legacy gencode-gov audit invocation (both positional and --project flag) remains intact
    assert main(["audit", str(proj), "--domain", "unknown-legacy-domain"]) == 1
    assert main(["audit", "--project", str(proj), "--domain", "unknown-legacy-domain"]) == 1
