"""Backward-compatible re-export of GENCODE-GOV enforcement policies."""

from __future__ import annotations

from gencode_gov.policies.loader import (
    POLICY_CATEGORIES,
    Policy,
    PolicyLoadResult,
    PolicyRegistry,
    _load_policy_file,
    load_policies,
)

__all__ = [
    "POLICY_CATEGORIES",
    "Policy",
    "PolicyLoadResult",
    "PolicyRegistry",
    "_load_policy_file",
    "load_policies",
]
