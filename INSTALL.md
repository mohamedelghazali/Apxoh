# INSTALL

## Purpose

This guide documents deterministic, hash-verified installation and lockfile management for GENCODE-GOV.

## Clean Hash-Verified Installation

1. Create and activate an isolated Python 3.11-3.13 virtual environment (`python -m venv .venv`).
2. **Runtime installation** (`requirements.lock`):
   ```bash
   python scripts/dependencies/lock_dependencies.py install --target runtime
   ```
3. **Development & testing installation** (`requirements-dev.lock`):
   ```bash
   python -m pip install --require-hashes --no-deps -r requirements-dev.lock
   python -m pip install --no-build-isolation --no-deps -e .
   python -m pip check
   ```
4. Verify installation and repository governance:
   ```bash
   gencode-gov version
   gencode-gov doctor
   gencode-gov validate
   pytest
   ```

## Deterministic Lockfile Maintenance & Auditing

`pyproject.toml` is the single source of truth for declared dependencies. Committed root lockfiles (`requirements.lock` and `requirements-dev.lock`) are compiled via `pip-tools==7.7.0`:

- Compile runtime lockfile: `python scripts/dependencies/lock_dependencies.py compile --target runtime` (`make lock-runtime`)
- Compile development lockfile: `python scripts/dependencies/lock_dependencies.py compile --target dev` (`make lock-dev`)
- Compile both lockfiles: `python scripts/dependencies/lock_dependencies.py compile --target all` (`make lock`)
- Verify lockfile integrity and drift without writing: `python scripts/dependencies/lock_dependencies.py check-drift` (`make lock-check`)
- Audit locked dependencies via `pip-audit`: `python scripts/dependencies/lock_dependencies.py audit` (`make audit`)

Treat missing dependencies, unavailable agent features, and incomplete integrations as BLOCKED.
