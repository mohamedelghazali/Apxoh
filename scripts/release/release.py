#!/usr/bin/env python3
"""Prepare an Apxoh release without tagging or pushing.

Usage:
    python scripts/release/release.py <version>

Updates VERSION, pyproject.toml, src/arkhon/__init__.py, and CHANGELOG.md.
It does not commit, tag, or push.
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
from datetime import date
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
VERSION_FILE = REPO_ROOT / "VERSION"
PYPROJECT = REPO_ROOT / "pyproject.toml"
INIT_FILE = REPO_ROOT / "src" / "arkhon" / "__init__.py"
CHANGELOG = REPO_ROOT / "CHANGELOG.md"
SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+(-[a-z0-9.]+)?$")


def fail(msg: str) -> None:
    print(f"[FAIL] {msg}", file=sys.stderr)
    raise SystemExit(1)


def validate_version(version: str) -> None:
    if not SEMVER_RE.fullmatch(version):
        fail(f"invalid version: {version!r} (expected MAJOR.MINOR.PATCH[-pre])")


def pep440(version: str) -> str:
    return version.replace("-dev.", ".dev").replace("-rc.", "rc")


def update_version_file(version: str) -> None:
    VERSION_FILE.write_text(version + "\n", encoding="utf-8")
    print(f"[OK] VERSION → {version}")


def update_pyproject(version: str) -> None:
    text = PYPROJECT.read_text(encoding="utf-8")
    updated = re.sub(
        r'^version = "[^"]+"', f'version = "{pep440(version)}"', text, count=1, flags=re.MULTILINE
    )
    if updated == text:
        fail("could not update version in pyproject.toml")
    PYPROJECT.write_text(updated, encoding="utf-8")
    print(f"[OK] pyproject.toml → {pep440(version)}")


def update_init(version: str) -> None:
    text = INIT_FILE.read_text(encoding="utf-8")
    updated = re.sub(
        r'^__version__ = "[^"]+"',
        f'__version__ = "{pep440(version)}"',
        text,
        count=1,
        flags=re.MULTILINE,
    )
    if updated == text:
        fail("could not update __version__ in src/arkhon/__init__.py")
    INIT_FILE.write_text(updated, encoding="utf-8")
    print(f"[OK] __init__.py → {pep440(version)}")


def update_changelog(version: str) -> None:
    text = CHANGELOG.read_text(encoding="utf-8")
    today = date.today().isoformat()
    header = f"## [{version}] - {today}"
    if header in text:
        print(f"[SKIP] CHANGELOG already has {version}")
        return
    lines = text.splitlines()
    out = []
    inserted = False
    for line in lines:
        out.append(line)
        if line.startswith("## [Unreleased]") and not inserted:
            out.extend(["", header, "", "### Added", "", "### Changed", "", "### Fixed", "", ""])
            inserted = True
    if not inserted:
        fail("could not find '## [Unreleased]' in CHANGELOG.md")
    CHANGELOG.write_text("\n".join(out) + "\n", encoding="utf-8")
    print(f"[OK] CHANGELOG.md → {version}")


def run_release_check() -> None:
    print("[INFO] running make release-check...")
    make_executable = shutil.which("make")
    if make_executable is None:
        fail("make executable not found on PATH")
    result = subprocess.run(  # noqa: S603 - resolved make executable and fixed arguments
        [make_executable, "release-check"], cwd=REPO_ROOT, check=False
    )
    if result.returncode != 0:
        fail("release-check failed")


def print_next_steps(version: str) -> None:
    print("\nNext steps:")
    print("  1. Review changes: git diff")
    print("  2. Add files:      git add VERSION pyproject.toml src/arkhon/__init__.py CHANGELOG.md")
    print(f'  3. Commit:         git commit -m "release: v{version}"')
    print(f'  4. Tag:            git tag -s v{version} -m "Apxoh v{version}"')
    print(f"  5. Push:           git push origin v{version}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Prepare an Apxoh release")
    parser.add_argument("version", help="Version string, e.g. 0.2.0 or 1.0.0-rc.1")
    parser.add_argument("--skip-check", action="store_true", help="Skip make release-check")
    args = parser.parse_args(argv)
    validate_version(args.version)
    print(f"[INFO] Preparing release {args.version}")
    update_version_file(args.version)
    update_pyproject(args.version)
    update_init(args.version)
    update_changelog(args.version)
    if not args.skip_check:
        run_release_check()
    print_next_steps(args.version)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
