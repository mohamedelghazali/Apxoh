---
name: software-testing
description: >
  Design and run cross-language test strategies, critical functional workflows, and
  scenario-traced negative security tests without false-assurance shortcuts.
version: 1.1.0
applicable_to: [all-projects]
requires: [arkhon-governance]
---
# Software Testing Skill

## Purpose

Tests are evidence that the software does what it claims and rejects what it must forbid.
A passing test suite that tests nothing is worse than no test suite — it gives false confidence.

## Mandatory Rules

1. Verified test runner selection matches the project's actual language ecosystem (`pytest` for
   Python, `go test` for Go, `cargo test` for Rust, and `node --test` for Node.js); non-Python
   projects never require Python tooling, and unavailable runners never produce `PASS`.
2. Every public function and critical user or API workflow requires automated behavioral tests.
3. Every bug fix includes a regression test (`SE-TST-002`).
4. Production branches exclude undocumented skipped tests (`SE-TST-003`).
5. Scenario-level traceability in `.arkhon/security-test-matrix.yaml` (`SE-TST-004`) maps each
   applicable adversarial scenario — unauthenticated requests, horizontal and vertical privilege
   escalation, IDOR, cross-user and cross-tenant isolation, SQL and command and template
   injection, CSRF on cookie-authenticated state changes, rate-limit abuse, and expired or
   replayed or revoked credentials — to its test file, test ID, and runner outcome.
6. Negative security tests exercise real authentication, authorization, tenant, and CSRF
   boundaries without mocking or overriding permission guards.
7. Failing tests are remediated in production code rather than deleted or weakened.

## Test Categories

| Category | What it proves | Where to run |
| :--- | :--- | :--- |
| Unit | A single function behaves correctly | Fast, on every save |
| Integration | Components and real boundaries work together | On every commit |
| Negative Security | Server rejects all applicable adversarial scenarios (`SE-TST-004`) | On every commit & release gate |
| Contract | Services honor their interfaces | On API changes |
| End-to-end | Critical user journeys succeed end-to-end | On release candidate |
| Regression | Old bugs and CVEs stay fixed (`SE-TST-002`) | On every commit |
| Load / Stress / Soak | System meets latency and throughput budgets (`SE-PRF-001`, `SE-PRF-002`) | Pre-release / Weekly |
| Chaos / Recovery | System survives failure and restores cleanly (`SE-REL-002`, `SE-REL-004`) | Pre-release |

## Anti-Patterns to Avoid

- **Tautological tests:** `assert True`, `assert isinstance(errors, list)`, or `assert f(2) == 4` when `f(x) = x * 2`.
- **Mocked-out authorization:** patching `check_permission`, `require_auth`, or `dependency_overrides` on security guards.
- **Generic count substitution:** claiming security coverage from total test count without scenario traceability.
- **Sleep-based tests:** `sleep(1); assert ...`. Flaky and slow.
- **Skipped tests:** a skipped test is a failing test you can't see.

## Evidence Required

- `normalized-test-execution-report` — `.arkhon/evidence/testing/test-execution-report.json`
- `security-scenario-traceability-report` — `.arkhon/evidence/testing/security-scenario-traceability.json`
- `critical-functionality-test-matrix` — mapping critical workflows to automated tests
- `coverage-report` — line and branch coverage

## Interaction with Apxoh

- Rule domain: `testing` (`SE-TST-001` through `SE-TST-004`)
- Gate: `testing_gate`
- Evidence output: `.arkhon/evidence/testing/`

## Reference

- `src/arkhon/verification/runners/test_suite_runner.py` — cross-language test runner
- `src/arkhon/verification/scenario_verifier.py` — negative-security scenario verifier
- `docs/verification/VERIFICATION_PROFILES.md` — which tests are required per profile

## Version History

- 1.1.0 (2026-11-25): Added cross-language test runner support and SE-TST-004 scenario traceability.
- 1.0.0 (2026-11-01): Initial release.
