"""Structural and semantic validation for GENCODE-GOV rules."""

from __future__ import annotations

import json
from pathlib import Path

from gencode_gov.core.constants import (
    ALL_ENFORCEMENT,
    ALL_RULE_DOMAINS,
    ALL_RULE_STATUSES,
    ALL_SEVERITIES,
    DOMAIN_RULE_PREFIX,
    ENFORCEMENT_ADVISORY,
    SEVERITY_CRITICAL,
)
from gencode_gov.core.errors import RuleValidationError
from gencode_gov.rules.loader import Rule


def validate_against_schema(rule: Rule, schema_path: Path) -> list[RuleValidationError]:
    """Validate against Draft 2020-12; missing validator dependency is a hard error."""
    try:
        import jsonschema
    except ImportError:
        return [
            RuleValidationError(
                "jsonschema is required for schema validation; install the project dependencies"
            )
        ]
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
        errors.append(
            RuleValidationError(f"{rule.id} [{rule.path.name}]: {location}: {err.message}")
        )
    return errors


def _validate_unique_string_list(
    value: object,
    field_name: str,
    rule_id: str,
    *,
    require_non_empty: bool,
) -> list[RuleValidationError]:
    """Validate a list of unique non-empty strings without hashing untyped elements."""
    if not isinstance(value, list):
        return [RuleValidationError(f"{rule_id}: '{field_name}' must be a non-empty list")]
    if require_non_empty and not value:
        return [RuleValidationError(f"{rule_id}: '{field_name}' must be a non-empty list")]
    errors: list[RuleValidationError] = []
    seen: set[str] = set()
    for index, entry in enumerate(value):
        if not isinstance(entry, str) or not entry.strip():
            errors.append(
                RuleValidationError(
                    f"{rule_id}: '{field_name}[{index}]' must be a non-empty string"
                )
            )
            continue
        if entry in seen:
            errors.append(
                RuleValidationError(f"{rule_id}: '{field_name}' must not repeat entry '{entry}'")
            )
        else:
            seen.add(entry)
    return errors


def validate_semantics(rule: Rule) -> list[RuleValidationError]:
    """Validate invariants that JSON Schema cannot express, safely handling malformed YAML."""
    errors: list[RuleValidationError] = []
    if not isinstance(rule.raw, dict):
        return [RuleValidationError(f"{rule.id}: rule document must be a mapping")]

    raw_meta = rule.raw.get("metadata")
    if not isinstance(raw_meta, dict):
        errors.append(RuleValidationError(f"{rule.id}: 'metadata' must be a mapping"))
        meta: dict[str, object] = {}
    else:
        meta = raw_meta

    domain = meta.get("domain")
    if not isinstance(domain, str) or domain not in ALL_RULE_DOMAINS:
        errors.append(RuleValidationError(f"{rule.id}: unknown domain '{domain}'"))
    enforcement = meta.get("enforcement")
    if not isinstance(enforcement, str) or enforcement not in ALL_ENFORCEMENT:
        errors.append(RuleValidationError(f"{rule.id}: invalid enforcement '{enforcement}'"))
    severity = meta.get("severity")
    if not isinstance(severity, str) or severity not in ALL_SEVERITIES:
        errors.append(RuleValidationError(f"{rule.id}: invalid severity '{severity}'"))
    if severity == SEVERITY_CRITICAL and enforcement == ENFORCEMENT_ADVISORY:
        errors.append(
            RuleValidationError(
                f"{rule.id}: critical-severity rule cannot use 'advisory' enforcement"
            )
        )
    status = meta.get("status")
    if not isinstance(status, str) or status not in ALL_RULE_STATUSES:
        errors.append(RuleValidationError(f"{rule.id}: invalid status '{status}'"))

    expected = DOMAIN_RULE_PREFIX.get(domain) if isinstance(domain, str) else None
    raw_id = rule.raw.get("id")
    identifier = raw_id if isinstance(raw_id, str) else rule.id
    if expected is not None and not identifier.startswith(f"{expected}-"):
        errors.append(
            RuleValidationError(
                f"{identifier}: rule id must start with '{expected}'- for domain '{domain}'"
            )
        )
    if identifier != rule.id:
        errors.append(
            RuleValidationError(f"{rule.id}: Rule.id does not match the document id '{identifier}'")
        )

    scope = rule.raw.get("scope")
    if scope is not None:
        if not isinstance(scope, dict):
            errors.append(RuleValidationError(f"{rule.id}: 'scope' must be a mapping"))
        else:
            for key in ("project_types", "lifecycle_stages", "languages"):
                if key in scope:
                    errors.extend(
                        _validate_unique_string_list(
                            scope.get(key),
                            f"scope.{key}",
                            rule.id,
                            require_non_empty=key == "project_types",
                        )
                    )

    verification = rule.raw.get("verification")
    if not isinstance(verification, dict):
        errors.append(RuleValidationError(f"{rule.id}: 'verification' must be a mapping"))
    else:
        errors.extend(
            _validate_unique_string_list(
                verification.get("methods"),
                "verification.methods",
                rule.id,
                require_non_empty=True,
            )
        )
        delegate_to = verification.get("delegate_to")
        if verification.get("mode") == "delegated" and (
            not isinstance(delegate_to, str) or not delegate_to.strip()
        ):
            errors.append(
                RuleValidationError(f"{rule.id}: delegated verification requires 'delegate_to'")
            )

    failure = rule.raw.get("failure")
    if failure is not None:
        if not isinstance(failure, dict):
            errors.append(RuleValidationError(f"{rule.id}: 'failure' must be a mapping"))
        elif "actions" in failure:
            errors.extend(
                _validate_unique_string_list(
                    failure.get("actions"),
                    "failure.actions",
                    rule.id,
                    require_non_empty=False,
                )
            )

    human_review = rule.raw.get("human_review")
    if human_review is not None:
        if not isinstance(human_review, dict):
            errors.append(RuleValidationError(f"{rule.id}: 'human_review' must be a mapping"))
        elif human_review.get("required") is True:
            approver = human_review.get("approver_role")
            if not isinstance(approver, str) or not approver.strip():
                errors.append(
                    RuleValidationError(
                        f"{rule.id}: 'human_review.approver_role' is required "
                        "when human_review is true"
                    )
                )

    acceptance = rule.raw.get("acceptance")
    if not isinstance(acceptance, dict) or not acceptance:
        errors.append(RuleValidationError(f"{rule.id}: 'acceptance' must be a non-empty mapping"))
    return errors


def validate_rule(rule: Rule, schema_path: Path | None = None) -> list[RuleValidationError]:
    """Run structural validation when a schema path is supplied, then semantics."""
    errors: list[RuleValidationError] = []
    if schema_path is not None:
        errors.extend(validate_against_schema(rule, schema_path))
    errors.extend(validate_semantics(rule))
    return errors
