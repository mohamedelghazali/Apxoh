# Compact Verification Gate Summary

- Generated UTC: 2026-11-28T06:52:10Z
- origin/main HEAD: 8f99a1186a0d6ca18202590a1663b6cbd61bc70b
- origin/feat/integrate-staged-governance HEAD (pre-integration): 8f99a1186a0d6ca18202590a1663b6cbd61bc70b
- Python: Python 3.13.18
- Node / npx: v24.22.3 / 11.19.1
- arkhon CLI on runner PATH: NOT_INSTALLED
## 1. Staged Bundle Integrity & Provenance Table
Decoded `__UPGRADER__` + 31 validated files with 0 duplicates and 0 syntax/schema errors.
## 2. Baseline Reconnaissance on origin/main
## 3. Per-File Integration & Staged-vs-Main Reconciliation
- `.gencode-gov/architecture-contracts.yaml`: NEW_FILE
- `docs/governance/ENGINEERING_GAP_REGISTER.md`: NEW_FILE
- `rules/README.md`: NEW_FILE
- `rules/api-integration/SE-API-002-frozen-api-and-schema-compatibility.yaml`: NEW_FILE
- `rules/architecture/SE-ARC-002-executable-architecture-boundaries.yaml`: NEW_FILE
- `rules/code-quality/SE-CQ-003-ai-anti-fabrication-and-complexity.yaml`: NEW_FILE
- `rules/database/SE-DB-003-zero-downtime-migration-safety.yaml`: NEW_FILE
- `rules/devops/SE-DEV-002-deterministic-dependency-and-action-pinning.yaml`: NEW_FILE
- `rules/reliability/SE-REL-005-outbound-timeout-and-bounded-retry.yaml`: NEW_FILE
- `rules/software-security/SE-SEC-011-sbom-license-and-vulnerability-gate.yaml`: NEW_FILE
- `rules/testing/SE-TST-005-test-assertion-adequacy-and-anti-tampering.yaml`: NEW_FILE
- `schemas/architecture-contracts.schema.json`: NEW_FILE
- `schemas/drift-ledger.schema.json`: NEW_FILE
- `schemas/review-attestation.schema.json`: NEW_FILE
- `src/gencode_gov/assessment/drift.py`: NEW_FILE
- `src/gencode_gov/cli_extensions.py`: NEW_FILE
- `src/gencode_gov/evidence/attestation.py`: NEW_FILE
- `src/gencode_gov/reporting/html_reporter.py`: REPLACED_EXISTING (95B -> 4888B)
- `src/gencode_gov/reporting/sarif_reporter.py`: NEW_FILE
- `src/gencode_gov/rules/evaluator.py`: REPLACED_EXISTING (95B -> 8385B)
- `src/gencode_gov/validation.py`: NEW_FILE
- `src/gencode_gov/verification/architecture_verifier.py`: NEW_FILE
- `src/gencode_gov/verification/assess_dispatch.py`: REPLACED_EXISTING (6356B -> 7378B)
- `src/gencode_gov/verification/code_and_test_integrity.py`: NEW_FILE
- `src/gencode_gov/verification/diff_governance.py`: NEW_FILE
- `src/gencode_gov/verification/domain_verifiers.py`: NEW_FILE
- `src/gencode_gov/verification/methods.py`: REPLACED_EXISTING (4955B -> 13027B)
- `src/gencode_gov/verification/runners/polyglot_quality_runner.py`: NEW_FILE
- `tests/integration/test_end_to_end_governance_excellence.py`: NEW_FILE
- `tests/unit/verification/test_engineering_governance_edge_branches.py`: NEW_FILE
- `tests/unit/verification/test_engineering_governance_upgrades.py`: NEW_FILE
Frozen API self-check: PASS — verified 4 frozen_apis entrypoint(s) ()
## 4. Ruff Lint (src tests scripts)
Found 2 errors.
[EXIT 1]
## 5. Ruff Format Check (src tests scripts)
[EXIT 0]
## 6. Mypy Type Check (src)
[EXIT 0]
## 7. Bandit Security Scan (src)
[EXIT 0]
## 8. Full Pytest & Coverage Suite
TOTAL                                                                  9753     44    99%
1448 passed in 32.32s
[EXIT 0]
## 9. New Modules 100% Coverage Gate
TOTAL                                                              1901     82    96%
[EXIT 1]
## 10. Repository Governance Validation (gencode-gov validate --json)
  "ok": true,
  "rules_checked": 47,
  "schemas_checked": 15,
  "skills_checked": 10,
[EXIT 0]
## 11. Polyglot Tool Matrix Inspection (gencode-gov inspect . --tools --json)
[EXIT 0]
## 12. Clean Working Tree Check
 62 files changed, 7018 insertions(+), 5568 deletions(-)
[EXIT 0]
## 13. Diff-Check Without --allow-protected (Protected File Inventory)
## 14. Diff-Check With --allow-protected (Compatibility & Schema Gate)
[EXIT 0]
## 15. Longitudinal Drift Snapshot (gencode-gov drift . --no-persist --json)
[EXIT 0]
## 16. Self-Governance Assessment Summary (gencode-gov assess . --json)
Decision: BLOCKED
Total rules evaluated: 44
  BLOCKED (28): ['SE-ARC-001', 'SE-DB-001', 'SE-DB-002', 'SE-INF-001', 'SE-OBS-001', 'SE-OBS-002', 'SE-OBS-003', 'SE-PRF-002', 'SE-PRI-001', 'SE-REL-001', 'SE-REL-002', 'SE-REL-004', 'SE-REQ-002', 'SE-REQ-003', 'SE-SEC-001', 'SE-SEC-002', 'SE-SEC-003', 'SE-SEC-004', 'SE-SEC-005', 'SE-SEC-006', 'SE-SEC-007', 'SE-SEC-009', 'SE-SEC-010', 'SE-SEC-011', 'SE-SEC-GOV-001', 'SE-SEC-GOV-002', 'SE-TST-002', 'SE-TST-004']
  FAIL (4): ['SE-ARC-002', 'SE-CQ-003', 'SE-DEV-002', 'SE-SEC-008']
  NOT_APPLICABLE (3): ['SE-API-001', 'SE-PRF-001', 'SE-SCL-001']
  PASS (9): ['SE-API-002', 'SE-CQ-002', 'SE-DB-003', 'SE-DEV-001', 'SE-MNT-001', 'SE-REL-003', 'SE-REL-005', 'SE-TST-003', 'SE-TST-005']
## 17. Wheel Build, Clean Venv Install & Post-Install CLI Smoke Tests
  "ok": true,
  "rules_checked": 47,
  "schemas_checked": 15,
  "skills_checked": 10,
[EXIT 1]
## 17b. Cross-Python Wheel & Test Compatibility (Python 3.11 & 3.13)
=== Verifying on Python 3.11.18 ===
  "ok": true,
  "rules_checked": 47,
  "schemas_checked": 15,
  "skills_checked": 10,
  "ok": true,
  "rules_checked": 47,
  "schemas_checked": 15,
  "skills_checked": 10,
[EXIT 1]
## 18. Agent Skills Discovery (npx skills)
[EXIT 0]
## 19. Post-Implementation Diff & Security Audit vs origin/main
 62 files changed, 7018 insertions(+), 5568 deletions(-)
Audited 1034 tracked files: 0 staging residue, 0 legacy tokens.
[EXIT 0]
## 20. Final Integration Commit & Gate Verdict
- Integrated commit on feat/integrate-staged-governance: 5b040e47d0b6d56214c9ec9b68f6b9d42d995278
- Overall FAIL flag: 1
- Fast-forward push to origin/feat/integrate-staged-governance: SKIPPED (FAIL=1)
