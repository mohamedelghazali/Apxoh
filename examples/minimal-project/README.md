# Minimal Project

**A compact example project for demonstrating Apxoh governance workflows.**

This example demonstrates:
- How to declare a project to Apxoh
- How to write a small, typed Python module
- How to add focused unit tests
- How to inspect and verify a project, subject to the commands supported by the installed Apxoh version

## What's Inside

```
minimal-project/
├── .arkhon/
│   └── project.yaml
├── src/
│   └── greeting.py
├── tests/
│   └── test_greeting.py
├── pyproject.toml
└── README.md
```

## Running Apxoh on It

From the Apxoh repository root, use the commands supported by the current CLI:

```bash
arkhon inspect examples/minimal-project
arkhon verify examples/minimal-project --domain testing
```

Assessment and report commands should be used only when present in the installed CLI; their availability is not asserted by this example.

## Expected Behavior

- Inspection should identify the declared Python project and its profile.
- Verification should execute the configured tests when the Python test runner is available.
- A PASS must come from actual verification evidence; this example does not pre-assert compliance.

## Scope

This minimal example does not demonstrate security integration, performance
benchmarks, reliability testing, or production-readiness review. Those
capabilities require their corresponding implementations and evidence.
