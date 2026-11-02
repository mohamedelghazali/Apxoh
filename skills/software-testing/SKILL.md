---
name: software-testing
description: >
  Design and run the test strategy. Ensures tests are meaningful, not
  just passing. Prevents test deletion as a way to make the gate close.
version: 1.0.0
applicable_to: [all-projects]
requires: [arkhon-governance]
---

# Software Testing Skill

## Purpose

Tests are evidence that the software does what it claims. A passing test
suite that tests nothing is worse than no test suite — it gives false
confidence.

## Mandatory Rules

1. Every public function must have at least one test.
2. Every bug fix must come with a regression test.
3. Tests must test behavior, not implementation.
4. Tests must not be deleted to make the build pass.
5. A failing test is a signal, not an obstacle. Fix the code, not the test.
6. Test coverage is a floor, not a target. 100% coverage with weak tests is worse than 60% with strong tests.

## Test Categories

| Category | What it proves | Where to run |
| :--- | :--- | :--- |
| Unit | A single function behaves correctly | Fast, on every save |
| Integration | Components work together | On every commit |
| Contract | Services honor their interfaces | On API changes |
| End-to-end | The user journey works | On release candidate |
| Regression | Old bugs stay fixed | On every commit |
| Load | The system handles expected load | Pre-release |
| Stress | The system handles peak load | Pre-release |
| Soak | The system remains stable over time | Weekly |
| Chaos | The system survives failure | Pre-release |
| Security | The system resists known attacks | Via TSAR |
| Recovery | The system recovers from failure | Pre-release |

## Anti-Patterns to Avoid

- **Tautological tests:** `assert f(2) == 4` when `f(x) = x * 2`. It tests nothing about correctness.
- **Testing implementation:** asserting internal state instead of observable behavior.
- **Sleep-based tests:** `sleep(1); assert ...`. Flaky and slow.
- **Mocked-into-uselessness:** mocking everything so the test only tests the mock.
- **Skipped tests:** a skipped test is a failing test you can't see.

## Evidence Required

- `test-results` — JUnit XML or equivalent
- `coverage-report` — line and branch coverage
- `test-plan` — what is tested, how, and why

## Interaction with Apxoh

- Rule domain: `testing`
- Gate: `testing_gate`
- Evidence type: `pytest_junit_xml` or `coverage_report`
- Output goes to `.arkhon/evidence/testing/`

## Reference

- `src/arkhon/verification/runners/pytest_runner.py` — the test runner
- `docs/verification/VERIFICATION_PROFILES.md` — which tests are required per profile

## Version History

- 1.0.0 (2026-11-01): Initial release.
