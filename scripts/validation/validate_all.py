#!/usr/bin/env python3
"""Validate the Apxoh manifest, JSON Schemas, and rule documents.

Exit codes: 0 success, 1 validation errors, 2 repository/dependency failure.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from arkhon.config import find_repo_root, load_manifest
from arkhon.core.errors import ArkhonError
from arkhon.rules.loader import load_rules_dir
from arkhon.rules.validator import validate_rule


def validate_manifest(root: Path) -> list[str]:
    try:
        manifest = load_manifest(root)
        _ = (manifest.name, manifest.identifier, manifest.version)
    except ArkhonError as exc:
        return [f"manifest: {exc}"]
    return []


def validate_json_schema_file(path: Path) -> list[str]:
    try:
        with path.open("r", encoding="utf-8") as handle:
            schema = json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        return [f"{path.name}: not valid JSON: {exc}"]
    try:
        import jsonschema
    except ImportError:
        return [f"{path.name}: jsonschema dependency is missing; install arkhon[dev]"]
    try:
        jsonschema.Draft202012Validator.check_schema(schema)
    except jsonschema.SchemaError as exc:
        return [f"{path.name}: invalid JSON Schema: {exc.message}"]
    return []


def validate_rules(root: Path) -> list[str]:
    rules_dir = root / "rules"
    if not rules_dir.is_dir():
        return [f"rules directory missing: {rules_dir}"]
    result = load_rules_dir(rules_dir)
    errors = [f"rule load: {error}" for error in result.errors]
    if result.warnings:
        errors.extend(f"rule warning: {warning}" for warning in result.warnings)
    schema_path = root / "schemas" / "rule.schema.json"
    if not schema_path.is_file():
        errors.append(f"rule schema missing: {schema_path}")
    for rule in result.rules:
        errors.extend(f"rule validate: {error}" for error in validate_rule(rule, schema_path))
    return errors


def main(argv: list[str] | None = None) -> int:
    del argv
    try:
        root = find_repo_root()
    except ArkhonError as exc:
        print(f"[FAIL] {exc}", file=sys.stderr)
        return 2

    print(f"[INFO] Validating Apxoh at {root}")
    errors: list[str] = []
    print("[INFO] Manifest...")
    errors.extend(validate_manifest(root))
    print("[INFO] Schemas...")
    schemas_dir = root / "schemas"
    if not schemas_dir.is_dir():
        errors.append(f"schemas directory missing: {schemas_dir}")
    else:
        for schema_file in sorted(schemas_dir.glob("*.json")):
            errors.extend(validate_json_schema_file(schema_file))
    print("[INFO] Rules...")
    errors.extend(validate_rules(root))

    if errors:
        print(f"\n[FAIL] {len(errors)} error(s):", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        return 1
    print("[OK] All validations passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
