# GENCODE-GOV Engineering Governance Rule Catalog

GENCODE-GOV enforces **47 active `SE-*` rules** across **16 software engineering domains** (`44` universal/domain rules under `rules/` plus `3` language-specific Python rules under `languages/python/rules/`).

## Rule Domains & Prefixes

| Domain | Prefix | Core Rules |
| --- | --- | --- |
| `architecture` | `SE-ARC-*` | `SE-ARC-001` (ADRs), `SE-ARC-002` (Executable Layering & Cycle-Free DAG) |
| `api-integration` | `SE-API-*` | `SE-API-001` (Versioned Schemas/Contracts), `SE-API-002` (Frozen APIs & Schema Diff) |
| `code-quality` | `SE-CQ-*` | `SE-CQ-001` (Python Lint/AST), `SE-CQ-002` (Static Lint & Types), `SE-CQ-003` (AI Anti-Fabrication, Exception Safety & Complexity) |
| `database` | `SE-DB-*` | `SE-DB-001` (Reversible Migrations), `SE-DB-002` (Least Privilege & Isolation), `SE-DB-003` (Zero-Downtime Expand-Contract DDL) |
| `devops` | `SE-DEV-*` | `SE-DEV-001` (CI Gates), `SE-DEV-002` (40-Char Action SHA Pinning & Deterministic Lockfiles) |
| `infrastructure` | `SE-INF-*` | `SE-INF-001` (IaC Review & Drift Governance) |
| `maintenance` | `SE-MNT-*` | `SE-MNT-001` (Keep-a-Changelog & Version Parity) |
| `observability` | `SE-OBS-*` | `SE-OBS-001`..`003` (Health Endpoints, Telemetry, Redacted Structured Logging & Crash Dump Governance) |
| `performance` | `SE-PRF-*` | `SE-PRF-001` (Load Benchmarks), `SE-PRF-002` (P50/P95/P99 Latency Regression & Alerting) |
| `privacy-compliance` | `SE-PRI-*` | `SE-PRI-001` (Data Inventory & DPIA) |
| `release` | `SE-REL-003` | `SE-REL-003` (Structured Release Notes) |
| `reliability` | `SE-REL-*` | `SE-REL-001` (SLOs), `SE-REL-002` (Verified Restore), `SE-REL-004` (Rollback Readiness), `SE-REL-005` (Outbound Timeouts & Bounded Retries) |
| `requirements` | `SE-REQ-*` | `SE-REQ-001`..`003` (Structured Specs, Conflict Analysis & Test Traceability) |
| `scalability` | `SE-SCL-*` | `SE-SCL-001` (Horizontal/Load Targets) |
| `software-security` | `SE-SEC-*` | `SE-SEC-001`..`011` (AuthN/Z, Injection, TLS/CORS/CSRF, Secrets, Abuse, Audit Logs, SCA, Hardening, Secret Remediation, SBOM Gate) + `SE-SEC-GOV-001`/`002` |
| `testing` | `SE-TST-*` | `SE-TST-001`..`005` (Coverage, Regression, Polyglot Execution, Negative Security Scenarios, Anti-Tampering & Assertion Adequacy) |

## Validation Contract

Every rule file is validated by `gencode-gov validate` against:
1. [`../schemas/rule.schema.json`](../schemas/rule.schema.json) (`additionalProperties: false` Draft 2020-12 JSON Schema).
2. Semantic invariants in [`../src/gencode_gov/rules/validator.py`](../src/gencode_gov/rules/validator.py) (`validate_semantics`).
3. 100% registration and domain authorization in [`../src/gencode_gov/verification/methods.py`](../src/gencode_gov/verification/methods.py) (`METHOD_REGISTRY`).
