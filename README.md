# АРХОН (ARKHON)

**Software Engineering Governance & Assurance System**

ARKHON is a local-first, evidence-driven framework for governing software engineering work. Its deterministic engine is authoritative for automated decisions; AI agents assist but do not independently certify results.

## Runtime

- Python 3.11+
- No AI provider required for deterministic core checks.
- Initial language profiles: Python, JavaScript, TypeScript, Java, C#, C++, Go, Rust, Ruby.
- Maturity is explicit: planned, detected, analyzable, verified.

## Quick start

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
arkhon version
arkhon doctor
pytest
```

## Project status and exceptions

```powershell
# Summarize the selected project's profile, detected languages, and evidence.
arkhon status .
arkhon status . --json

# Inspect the repository's exception registry without changing approvals.
arkhon exceptions list
arkhon exceptions list --json
```

The status command verifies evidence-store integrity before reporting counts. Exception inspection is read-only; approval, extension, and revocation remain governed operations and are not performed by this listing command.

## Trust model

Missing required tools or evidence are BLOCKED, not PASS. CI success alone is not proof of product quality. Standards mappings are informative and do not establish certification. TSAR is an optional, separately versioned integration; ARKHON remains independently usable. Consult COMPATIBILITY.md before relying on any integration.
