"""Structural and semantic validation for Apxoh rules."""
from __future__ import annotations

import json
from pathlib import Path

from arkhon.core.constants import (
    ALL_ENFORCEMENT, ALL_RULE_DOMAINS, ALL_RULE_STATUSES, ALL_SEVERITIES,
    DOMAIN_RULE_PREFIX,
)
from arkhon.core.errors import RuleValidationError
from arkhon.rules.loader import Rule


def validate_against_schema(rule: Rule, schema_path: Path) -> list[RuleValidationError]:
    """Validate against Draft 2020-12; missing validator dependency is a hard error."""
    try:
        import jsonschema
    except ImportError:
        return [RuleValidationError(
            "jsonschema is required for schema validation; install the project dependencies"
        )]
    if not schema_path.is_file():
        return [RuleValidationError(f"rule schema not found: {schema_path}")]
    try:
        with schema_path.open("r", encoding="utf-8") as fh:
            schema = json.load(fh)
        validator = jsonschema.Draft202012Validator(schema)
        validator.check_schema(schema)
    except (OSError, json.JSONDecodeError, jsonschema.SchemaError) as exc:
        return [RuleValidationError(f"cannot load valid rule schema {schema_path}: {exc}")]
    errors: list[RuleValidationError] = []
    for err in validator.iter_errors(rule.raw):
        location = ".".join(str(part) for part in err.absolute_path) or "<root>"
        errors.append(RuleValidationError(
            f"{rule.id} [{rule.path.name}]: {location}: {err.message}"
        ))
    return errors


def validate_semantics(rule: Rule) -> list[RuleValidationError]:
    """Validate invariants that JSON Schema cannot express."""
    errors: list[RuleValidationError] = []
    meta = rule.metadata
    domain = meta.get("domain")
    if domain not in ALL_RULE_DOMAINS:
        errors.append(RuleValidationError(f"{rule.id}: unknown domain '{domain}'"))
    enforcement = meta.get("enforcement")
    if enforcement not in ALL_ENFORCEMENT:
        errors.append(RuleValidationError(f"{rule.id}: invalid enforcement '{enforcement}'"))
    severity = meta.get("severity")
    if severity not in ALL_SEVERITIES:
        errors.append(RuleValidationError(f"{rule.id}: invalid severity '{severity}'"))
    status = meta.get("status")
    if status not in ALL_RULE_STATUSES:
        errors.append(RuleValidationError(f"{rule.id}: invalid status '{status}'"))

    if isinstance(domain, str) and domain in DOMAIN_RULE_PREFIX:
        expected = DOMAIN_RULE_PREFIX[domain]
        if not rule.id.startswith(expected + "-"):
            errors.append(RuleValidationError(
                f"{rule.id}: rule id must start with '{expected}-' for domain '{domain}'"
            ))

    verification = rule.raw.get("verification")
    if not isinstance(verification, dict):
        errors.append(RuleValidationError(f"{rule.id}: 'verification' must be a mapping"))
    else:
        methods = verification.get("methods")
        if not isinstance(methods, list) or not methods:
            errors.append(RuleValidationError(
                f"{rule.id}: 'verification.methods' must be a non-empty list"
            ))
        if verification.get("mode") == "delegated" and not verification.get("delegate_to"):
            errors.append(RuleValidationError(
                f"{rule.id}: delegated verification requires 'delegate_to'"
            ))

    acceptance = rule.raw.get("acceptance")
    if not isinstance(acceptance, dict) or not acceptance:
        errors.append(RuleValidationError(
            f"{rule.id}: 'acceptance' must be a non-empty mapping"
        ))
    return errors


def validate_rule(
    rule: Rule, schema_path: Path | None = None
) -> list[RuleValidationError]:
    """Run structural validation when a schema path is supplied, then semantics."""
    errors: list[RuleValidationError] = []
    if schema_path is not None:
        errors.extend(validate_against_schema(rule, schema_path))
    errors.extend(validate_semantics(rule))
    return errors
