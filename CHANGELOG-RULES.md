# Rule Catalog Changelog

This file records changes to the Apxoh rule catalog. The YAML rule files remain authoritative for each rule's metadata, scope, verification, acceptance criteria, evidence, and failure behavior.

Rule versioning follows docs/VERSIONING.md §3.4. The lifecycle is described in docs/rule-authoring/RULE_LIFECYCLE.md.

---

## [Unreleased]

### Added
- **SE-API-001** — Versioned APIs; high / blocking / deterministic. Public API endpoints must be versioned and preserve compatibility within a major version. Location: rules/api-integration/SE-API-001-versioned-apis.yaml.
- **SE-INF-001** — Infrastructure as Code Reviewed; high / blocking / hybrid. Infrastructure changes must be represented as code and reviewed before application. Location: rules/infrastructure/SE-INF-001-iac-reviewed.yaml.
- **SE-REQ-003** — Requirements Traceability; high / blocking / hybrid. Approved requirements must trace to design and verification artifacts. Location: rules/requirements/SE-REQ-003-requirement-traceability.yaml.

### Planned
- Expand the catalog in line with the rule-engine milestones in ROADMAP.md.
- Add language- and project-specific rules only after their schema, applicability, verification methods, and tests are defined.
- Keep this inventory synchronized with rules/ and languages/*/rules/.

---

## [1.0.0] - 2026-11-01

Initial catalog snapshot: **20 active rules** — 17 global rules under rules/ and 3 Python-specific rules under languages/python/rules/, spanning **14 domains**.

### Added

#### Requirements (2)
- **SE-REQ-001** — Verifiable Requirements; high / blocking / hybrid. Every approved functional requirement needs measurable acceptance criteria. Location: languages/python/rules/SE-REQ-001-verifiable-requirements.yaml.
- **SE-REQ-002** — No Conflicting Requirements; high / blocking / hybrid. Approved requirements must not contain unresolved contradictions. Location: rules/requirements/SE-REQ-002-no-conflicting-requirements.yaml.

#### Architecture (1)
- **SE-ARC-001** — Architecture Decision Records Required; high / blocking / hybrid. Significant architectural decisions require a documented ADR. Location: rules/architecture/SE-ARC-001-adr-required.yaml.

#### Code Quality (2)
- **SE-CQ-001** — Clean Code: No Dead Code or Placeholder Functions; medium / required / deterministic. Python production code must not contain unused imports, unreachable code, or placeholder functions. Location: languages/python/rules/SE-CQ-001-clean-code.yaml.
- **SE-CQ-002** — Type Safety Enforced; high / blocking / deterministic. Applicable statically typed languages must use strict type checking. Location: rules/code-quality/SE-CQ-002-type-safety.yaml.

#### Database (1)
- **SE-DB-001** — Database Migration Reviewed and Reversible; critical / blocking / hybrid. Migrations require review, a rollback plan, and production-like testing. Location: rules/database/SE-DB-001-migration-review.yaml.

#### DevOps (1)
- **SE-DEV-001** — CI Runs on Every Pull Request; high / blocking / deterministic. Pull requests must trigger CI, and the check must be required before merge. Location: rules/devops/SE-DEV-001-ci-on-every-pr.yaml.

#### Maintenance (1)
- **SE-MNT-001** — CHANGELOG Updated for Every Release; medium / required / deterministic. Release metadata and categorized changelog entries must be consistent. Location: rules/maintenance/SE-MNT-001-changelog-updated.yaml.

#### Observability (1)
- **SE-OBS-001** — Health Endpoint Required for Every Service; high / blocking / deterministic. Applicable services must expose a machine-readable health endpoint. Location: rules/observability/SE-OBS-001-health-endpoint.yaml.

#### Performance (1)
- **SE-PRF-001** — P95 Latency Target Defined and Measured; high / blocking / deterministic. User-facing endpoints require documented and measured latency targets. Location: rules/performance/SE-PRF-001-p95-target.yaml.

#### Privacy & Compliance (1)
- **SE-PRI-001** — Personal Data Inventory Required; high / blocking / hybrid. Projects processing personal data require an inventory and, when applicable, a DPIA. Location: rules/privacy-compliance/SE-PRI-001-data-inventory.yaml.

#### Release (1)
- **SE-REL-003** — Release Notes Published; medium / required / deterministic. Release notes must include the commit SHA, summary, changelog link, and known changes. Location: rules/release/SE-REL-003-release-notes.yaml.

#### Reliability (2)
- **SE-REL-001** — SLO Defined for Every Service; high / blocking / hybrid. Applicable services require a documented SLO, error budget, and monitoring. Location: rules/reliability/SE-REL-001-slo-defined.yaml.
- **SE-REL-002** — Backup Restore Verified; critical / critical / deterministic. A backup must be restored and its data integrity checked before it is accepted as evidence. Location: rules/reliability/SE-REL-002-backup-restore-verified.yaml.

#### Scalability (1)
- **SE-SCL-001** — Load Test Evidence Required for Scale Claims; high / blocking / deterministic. Scalability claims require documented load-test conditions and results. Location: rules/scalability/SE-SCL-001-load-test-evidence.yaml.

#### Software Security (2)
- **SE-SEC-GOV-001** — TSAR Security Audit Required Before Release; critical / critical / delegated. Required security gates depend on valid TSAR evidence for the exact release commit. Location: rules/software-security/SE-SEC-GOV-001-tsar-audit-required.yaml.
- **SE-SEC-GOV-002** — TSAR Evidence Must Be Fresh; high / blocking / delegated. Delegated TSAR evidence must satisfy the configured freshness window. Location: rules/software-security/SE-SEC-GOV-002-tsar-evidence-fresh.yaml.

#### Testing (3)
- **SE-TST-001** — Unit Tests Required for Every Public Function; high / blocking / deterministic. Python public production functions require corresponding unit tests. Location: languages/python/rules/SE-TST-001-unit-tests-required.yaml.
- **SE-TST-002** — Regression Test Required for Every Bugfix; high / blocking / hybrid. Bug fixes require a regression test that reproduces the defect. Location: rules/testing/SE-TST-002-regression-test-for-bugfix.yaml.
- **SE-TST-003** — No Undocumented Skipped Tests; medium / blocking / deterministic. Skipped tests must have a documented reason, owner, and tracking entry. Location: rules/testing/SE-TST-003-no-skipped-tests.yaml.

---

## Rule Statistics

Current counts include 20 global rule files under rules/ and 3 Python-specific rule files under languages/python/rules/. Recalculate them when rules are added, removed, or their metadata changes.

| Domain | Count | Critical | High | Medium |
| :--- | ---: | ---: | ---: | ---: |
| Architecture | 1 | 0 | 1 | 0 |
| API Integration | 1 | 0 | 1 | 0 |
| Code Quality | 2 | 0 | 1 | 1 |
| Database | 1 | 1 | 0 | 0 |
| DevOps | 1 | 0 | 1 | 0 |
| Maintenance | 1 | 0 | 0 | 1 |
| Observability | 1 | 0 | 1 | 0 |
| Performance | 1 | 0 | 1 | 0 |
| Privacy & Compliance | 1 | 0 | 1 | 0 |
| Release | 1 | 0 | 0 | 1 |
| Reliability | 2 | 1 | 1 | 0 |
| Infrastructure | 1 | 0 | 1 | 0 |
| Requirements | 3 | 0 | 3 | 0 |
| Scalability | 1 | 0 | 1 | 0 |
| Software Security | 2 | 1 | 1 | 0 |
| Testing | 3 | 0 | 2 | 1 |
| **Total** | **23** | **3** | **16** | **4** |

### Verification Mode Statistics

| Mode | Count |
| :--- | ---: |
| deterministic | 12 |
| hybrid | 9 |
| delegated | 2 |
| **Total** | **23** |

## Inventory and Validation Notes

- Rule YAML files are authoritative; this changelog is a human-maintained inventory.
- tests/unit/rules/test_new_rules.py currently discovers YAML rules under rules/. It does not parse or validate this changelog and does not discover the three Python-specific rules under languages/python/rules/.
- A changelog entry alone is not validation evidence. Use the repository's current validation workflow before treating a rule as accepted.

## References

- docs/VERSIONING.md — versioning policy.
- docs/rule-authoring/HOW_TO_WRITE_A_RULE.md — authoring guide.
- docs/rule-authoring/RULE_LIFECYCLE.md — lifecycle.
- archive/README.md — archival guidance.
