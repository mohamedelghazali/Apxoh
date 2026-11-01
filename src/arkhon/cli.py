"""Apxoh command-line interface."""
from __future__ import annotations

import argparse
import json
import runpy
import sys

from arkhon import __version__
from arkhon.config import find_repo_root


def cmd_version(args: argparse.Namespace) -> int:
    if getattr(args, "json", False):
        print(json.dumps(
            {"name": "Apxoh", "identifier": "arkhon", "version": __version__}, indent=2
        ))
    else:
        print(f"Apxoh {__version__}")
    return 0


def cmd_doctor(_args: argparse.Namespace) -> int:
    failures: list[str] = []
    try:
        root = find_repo_root()
    except Exception as exc:
        print(f"Apxoh doctor — FAILED\n  [FAIL] {exc}")
        return 1

    if sys.version_info < (3, 11):
        failures.append(
            f"Python 3.11+ required, found {sys.version_info.major}.{sys.version_info.minor}"
        )
    for required in ("VERSION", "manifest/index.yaml", "README.md", "AGENTS.md"):
        if not (root / required).exists():
            failures.append(f"missing required file: {required}")
    try:
        from arkhon.config import load_manifest
        _ = load_manifest(root).version
    except Exception as exc:
        failures.append(f"manifest load failed: {exc}")
    if failures:
        print("Apxoh doctor — FAILED")
        for failure in failures:
            print(f"  [FAIL] {failure}")
        return 1
    print("Apxoh doctor — OK")
    print(f"  Python:  {sys.version.split()[0]}")
    print(f"  Version: {__version__}")
    print(f"  Root:    {root}")
    return 0


def cmd_validate(_args: argparse.Namespace) -> int:
    """Run repository validation; this command requires a source checkout."""
    try:
        root = find_repo_root()
    except Exception as exc:
        print(f"arkhon validate requires a repository checkout: {exc}", file=sys.stderr)
        return 2
    script = root / "scripts" / "validation" / "validate_all.py"
    if not script.is_file():
        print(f"validation script missing: {script}", file=sys.stderr)
        return 2
    namespace = runpy.run_path(str(script), run_name="arkhon_validation")
    return int(namespace["main"]())


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="arkhon",
        description="Apxoh — Software Engineering Governance & Assurance System",
    )
    subparsers = parser.add_subparsers(dest="command")
    version_parser = subparsers.add_parser("version", help="Print Apxoh version")
    version_parser.add_argument("--json", action="store_true", help="Output as JSON")
    version_parser.set_defaults(func=cmd_version)
    subparsers.add_parser("doctor", help="Check installation and environment").set_defaults(
        func=cmd_doctor
    )
    subparsers.add_parser("validate", help="Validate manifest, schemas, and rules").set_defaults(
        func=cmd_validate
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not hasattr(args, "func"):
        parser.print_help()
        return 1
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
