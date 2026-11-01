"""Protocol constants and manifest-derived identifiers."""
from __future__ import annotations

from arkhon.config import get_manifest

STATUS_PASS = "PASS"
STATUS_FAIL = "FAIL"
STATUS_BLOCKED = "BLOCKED"
STATUS_NOT_APPLICABLE = "NOT_APPLICABLE"
STATUS_ACCEPTED_RISK = "ACCEPTED_RISK"
ALL_STATUSES = (
    STATUS_PASS, STATUS_FAIL, STATUS_BLOCKED, STATUS_NOT_APPLICABLE, STATUS_ACCEPTED_RISK,
)

ENFORCEMENT_ADVISORY = "advisory"
ENFORCEMENT_REQUIRED = "required"
ENFORCEMENT_BLOCKING = "blocking"
ENFORCEMENT_CRITICAL = "critical"
ALL_ENFORCEMENT = (
    ENFORCEMENT_ADVISORY, ENFORCEMENT_REQUIRED, ENFORCEMENT_BLOCKING, ENFORCEMENT_CRITICAL,
)

SEVERITY_CRITICAL = "critical"
SEVERITY_HIGH = "high"
SEVERITY_MEDIUM = "medium"
SEVERITY_LOW = "low"
ALL_SEVERITIES = (SEVERITY_CRITICAL, SEVERITY_HIGH, SEVERITY_MEDIUM, SEVERITY_LOW)

RULE_STATUS_PROPOSED = "proposed"
RULE_STATUS_ACTIVE = "active"
RULE_STATUS_DEPRECATED = "deprecated"
RULE_STATUS_ARCHIVED = "archived"
ALL_RULE_STATUSES = (
    RULE_STATUS_PROPOSED, RULE_STATUS_ACTIVE, RULE_STATUS_DEPRECATED, RULE_STATUS_ARCHIVED,
)

VERIFICATION_LEVELS = ("installed", "discoverable", "activated", "configured", "verified")

ALL_RULE_DOMAINS = (
    "requirements", "architecture", "code-quality", "software-security", "testing",
    "performance", "reliability", "database", "api-integration", "devops",
    "observability", "privacy-compliance", "scalability", "infrastructure",
    "maintenance", "release",
)

# SE-REL is intentionally shared here; semantic validation uses the domain as well.
DOMAIN_RULE_PREFIX = {
    "requirements": "SE-REQ", "architecture": "SE-ARC", "code-quality": "SE-CQ",
    "software-security": "SE-SEC", "testing": "SE-TST", "performance": "SE-PRF",
    "reliability": "SE-REL", "database": "SE-DB", "api-integration": "SE-API",
    "devops": "SE-DEV", "observability": "SE-OBS", "privacy-compliance": "SE-PRI",
    "scalability": "SE-SCL", "infrastructure": "SE-INF", "maintenance": "SE-MNT",
    "release": "SE-REL",
}


def model_ids() -> list[str]:
    return [item["id"] for item in get_manifest().integrations["integrations"]["models"]]


def platform_ids() -> list[str]:
    return [item["id"] for item in get_manifest().integrations["integrations"]["platforms"]]


def language_ids() -> list[str]:
    return [item["id"] for item in get_manifest().languages["supported"]]


def product_ids() -> list[str]:
    return [item["id"] for item in get_manifest().products["products"]]
