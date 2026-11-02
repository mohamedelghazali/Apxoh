# Python Fixture Project

**Purpose:** Minimal Python project used to test Apxoh's language detection.

## Structure

- `src/calc.py` — calculator module (add, subtract, multiply, divide)
- `tests/test_calc.py` — unit tests for calc
- `.arkhon/project.yaml` — Apxoh project declaration

## Expected Apxoh behavior

Running `arkhon inspect` on this directory is expected to:
1. Detect Python as the primary language
2. Match the `universal` profile
3. Report `pyproject.toml` as the build system

Running `arkhon verify --domain testing` is expected to:
1. Resolve and run pytest using the fixture environment
2. Produce evidence only if evidence collection is implemented and configured
3. Report the result from actual test execution; this fixture README does not assert a PASS in advance

## Notes

This project is intentionally minimal. It is a fixture for testing Apxoh's
detection and verification behavior, not proof that every governance
integration is implemented.
