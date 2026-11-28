"""Explicit inventory of rule verification methods backed by real implementations.

A method being registered means an implementation exists; it does not mean a
rule has passed. Rule-level outcomes still require validated, commit-bound
evidence and any required human approval.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType

from gencode_gov.core.constants import ALL_RULE_DOMAINS


@dataclass(frozen=True)
class MethodImplementation:
    """Implementation component that can execute or validate one method."""

    method_id: str
    component: str
    runner: str
    allowed_domains: frozenset[str] = frozenset()


def _dom(
    method_id: str,
    *domains: str,
    component: str = "evaluate_domain_method",
    runner: str = "governance-domain",
) -> tuple[str, MethodImplementation]:
    return (
        method_id,
        MethodImplementation(
            method_id=method_id,
            component=component,
            runner=runner,
            allowed_domains=frozenset(domains),
        ),
    )


_REGISTRY_ITEMS: dict[str, MethodImplementation] = dict(
    [
        # Existing core runners
        _dom("type-checker-execution", "code-quality", component="MypyRunner", runner="mypy"),
        _dom("zero-type-errors-check", "code-quality", component="MypyRunner", runner="mypy"),
        _dom("static-lint-execution", "code-quality", component="RuffRunner", runner="ruff"),
        _dom("zero-lint-errors-check", "code-quality", component="RuffRunner", runner="ruff"),
        _dom("ruff-check", "code-quality", component="RuffRunner", runner="ruff"),
        _dom(
            "polyglot-static-quality-check",
            "code-quality",
            component="PolyglotQualityRunner",
            runner="polyglot-quality",
        ),
        _dom("ast-analysis", "code-quality"),
        _dom("anti-fabrication-ast-check", "code-quality"),
        _dom("exception-handling-safety-check", "code-quality"),
        _dom("complexity-budget-check", "code-quality"),
        # Testing
        _dom(
            "automated-test-suite-execution",
            "testing",
            component="LanguageNeutralTestRunner",
            runner="test-suite",
        ),
        _dom(
            "zero-test-failures-check",
            "testing",
            component="LanguageNeutralTestRunner",
            runner="test-suite",
        ),
        _dom(
            "test-collector-analysis",
            "testing",
            component="LanguageNeutralTestRunner",
            runner="test-suite",
        ),
        _dom(
            "skip-marker-detection",
            "testing",
            component="LanguageNeutralTestRunner",
            runner="test-suite",
        ),
        _dom(
            "negative-security-scenario-traceability",
            "testing",
            component="verify_negative_security_scenarios",
            runner="test-suite",
        ),
        _dom("coverage-analysis", "testing"),
        _dom("ast-test-mapping", "testing"),
        _dom("commit-message-analysis", "testing"),
        _dom("test-diff-analysis", "testing"),
        _dom("critical-workflow-test-coverage-review", "testing"),
        _dom("assertion-adequacy-check", "testing"),
        _dom("regression-tamper-diff-check", "testing"),
        # Human review & attestation methods (applicable to any hybrid governance rule)
        _dom(
            "human-review",
            *ALL_RULE_DOMAINS,
            component="verify_human_attestation",
            runner="human-attestation",
        ),
        _dom(
            "human-security-review",
            *ALL_RULE_DOMAINS,
            component="verify_human_attestation",
            runner="human-attestation",
        ),
        _dom(
            "human-approval",
            *ALL_RULE_DOMAINS,
            component="verify_human_attestation",
            runner="human-attestation",
        ),
        # Architecture
        _dom("adr-presence-check", "architecture"),
        _dom("adr-structure-validation", "architecture"),
        _dom("architecture-layer-boundary-check", "architecture"),
        _dom("module-cycle-detection", "architecture"),
        # Requirements
        _dom("schema-validation", "requirements"),
        _dom("requirements-audit", "requirements"),
        _dom("acceptance-criteria-validation", "requirements"),
        _dom("requirements-conflict-analysis", "requirements"),
        _dom("requirements-traceability-analysis", "requirements"),
        _dom("test-traceability-analysis", "requirements"),
        # API & Integration
        _dom("api-contract-analysis", "api-integration"),
        _dom("endpoint-version-inventory", "api-integration"),
        _dom("frozen-api-contract-check", "api-integration"),
        _dom("schema-compatibility-diff-check", "api-integration"),
        # Database
        _dom("migration-file-detection", "database"),
        _dom("schema-and-data-compatibility-review", "database"),
        _dom("production-like-migration-test", "database"),
        _dom("prechange-backup-verification", "database", "reliability"),
        _dom("rollback-or-forward-recovery-drill", "database"),
        _dom("database-role-review", "database"),
        _dom("network-exposure-review", "database"),
        _dom("credential-separation-review", "database"),
        _dom("unauthorized-modification-controls-review", "database"),
        _dom("row-ownership-negative-tests", "database"),
        _dom("cross-tenant-isolation-tests", "database"),
        _dom("destructive-ddl-migration-scan", "database"),
        _dom("concurrent-index-and-lock-check", "database"),
        # DevOps
        _dom("workflow-file-presence", "devops"),
        _dom("branch-protection-check", "devops"),
        _dom("github-actions-sha-pinning-scan", "devops"),
        _dom("dependency-lockfile-determinism-check", "devops"),
        # Infrastructure
        _dom("iac-file-detection", "infrastructure"),
        _dom("change-review-record", "infrastructure"),
        # Maintenance & Release
        _dom("changelog-format-validation", "maintenance"),
        _dom("version-consistency-check", "maintenance"),
        _dom("release-notes-presence", "release"),
        _dom("release-notes-structure-validation", "release"),
        # Observability
        _dom(
            "observability-behavior-test-verification",
            "observability",
            component="verify_observability_and_crash_dump_controls",
            runner="test-suite",
        ),
        _dom("endpoint-detection", "observability"),
        _dom("endpoint-schema-validation", "observability"),
        _dom("public-health-disclosure-test", "observability"),
        _dom("detailed-health-access-control-test", "observability"),
        _dom("monitoring-signal-inventory", "observability"),
        _dom("dashboard-access-control-tests", "observability"),
        _dom("health-response-disclosure-review", "observability"),
        _dom("alert-delivery-test", "observability"),
        _dom("operator-audit-review", "observability"),
        _dom("error-handler-boundary-review", "observability"),
        _dom("crash-dump-governance-review", "observability"),
        # Performance & Scalability
        _dom("load-test-execution", "performance", "scalability"),
        _dom("target-comparison", "performance", "scalability"),
        _dom("latency-telemetry-instrumentation-review", "performance"),
        _dom("baseline-regression-comparison", "performance"),
        _dom("degradation-alert-rule-validation", "performance"),
        _dom("alert-routing-and-runbook-check", "performance"),
        # Privacy & Compliance
        _dom("data-inventory-presence", "privacy-compliance"),
        _dom("dpia-presence", "privacy-compliance"),
        # Reliability
        _dom("slo-document-presence", "reliability"),
        _dom("monitoring-config-check", "reliability"),
        _dom("restore-execution", "reliability"),
        _dom("data-integrity-check", "reliability"),
        _dom("rto-rpo-verification", "reliability"),
        _dom("change-risk-classification", "reliability"),
        _dom("restore-drill", "reliability"),
        _dom("application-rollback-test", "reliability"),
        _dom("database-compatibility-test", "reliability"),
        _dom("outbound-timeout-enforcement-scan", "reliability"),
        _dom("unbounded-retry-loop-scan", "reliability"),
        # Software Security & Supply Chain
        _dom(
            "security-audit-artifact-verification",
            "software-security",
            component="evaluate_security_audit_method",
            runner="security-audit",
        ),
        _dom("tsar-audit-invocation", "software-security", component="TsarRunner", runner="tsar"),
        _dom(
            "evidence-integrity-check",
            "software-security",
            component="verify_tsar_evidence",
            runner="tsar",
        ),
        _dom(
            "evidence-commit-match",
            "software-security",
            component="verify_tsar_evidence",
            runner="tsar",
        ),
        _dom(
            "evidence-freshness-check",
            "software-security",
            component="verify_tsar_evidence",
            runner="tsar",
        ),
        _dom(
            "timestamp-verification",
            "software-security",
            component="verify_tsar_evidence",
            runner="tsar",
        ),
        _dom("sbom-component-inventory-check", "software-security"),
        _dom("sbom-license-and-cve-policy-check", "software-security"),
        *(
            _dom(sec_m, "software-security")
            for sec_m in (
                "authentication-flow-inventory",
                "password-storage-review",
                "session-lifecycle-tests",
                "negative-authentication-tests",
                "authorization-matrix-review",
                "route-policy-inventory",
                "object-ownership-tests",
                "cross-tenant-negative-tests",
                "input-boundary-inventory",
                "server-validation-review",
                "api-schema-and-bounds-review",
                "sql-query-review",
                "injection-negative-tests",
                "fuzz-or-property-tests",
                "tls-configuration-review",
                "certificate-validation-tests",
                "http-redirect-check",
                "cors-policy-tests",
                "security-header-tests",
                "csrf-negative-tests",
                "cookie-attribute-review",
                "secret-scanner",
                "repository-config-review",
                "env-file-audit",
                "secret-manager-policy-review",
                "log-and-evidence-redaction-review",
                "auth-endpoint-inventory",
                "rate-limit-tests",
                "account-enumeration-tests",
                "reset-token-lifecycle-tests",
                "abuse-monitoring-review",
                "security-event-coverage-review",
                "log-redaction-tests",
                "log-access-control-review",
                "alert-rule-review",
                "incident-playbook-review",
                "lockfile-inventory",
                "software-composition-analysis",
                "unused-dependency-analysis",
                "vulnerability-triage",
                "provenance-review",
                "production-config-review",
                "exposed-resource-scan",
                "admin-route-access-tests",
                "debug-mode-negative-tests",
                "cloud-storage-permission-review",
                "working-tree-secret-scan",
                "git-history-secret-scan",
                "branch-and-tag-coverage-review",
                "credential-revocation-confirmation",
                "incident-review",
            )
        ),
    ]
)

METHOD_REGISTRY: Mapping[str, MethodImplementation] = MappingProxyType(_REGISTRY_ITEMS)


def resolve_method(method_id: str) -> MethodImplementation | None:
    """Return the registered implementation, or None when unsupported."""
    if not isinstance(method_id, str) or not method_id:
        raise ValueError("method_id must be a non-empty string")
    return METHOD_REGISTRY.get(method_id)


def resolve_methods(method_ids: object) -> tuple[tuple[str, MethodImplementation | None], ...]:
    """Resolve a rule's declared method list without silently dropping entries."""
    if not isinstance(method_ids, list):
        raise ValueError("verification.methods must be a list")
    if any(not isinstance(method_id, str) or not method_id for method_id in method_ids):
        raise ValueError("verification.methods must contain non-empty strings")
    if len(set(method_ids)) != len(method_ids):
        raise ValueError("verification.methods must not contain duplicates")
    return tuple((method_id, resolve_method(method_id)) for method_id in method_ids)
