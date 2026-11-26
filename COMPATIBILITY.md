# COMPATIBILITY

## Purpose

This guide documents the **GENCODE-GOV** runtime foundation, platform verification bounds, and intentionally preserved backward-compatibility identifiers following the repository-wide `APXOH` -> `GENCODE-GOV` identity migration.

## Supported Runtime & Verification Procedure

1. Use Python `>=3.11, <3.14` (`3.11`, `3.12`, or `3.13`) in an isolated virtual environment across Linux, macOS, or Windows.
2. Install the package and development dependencies (`pip install -e ".[dev]"`).
3. Run `gencode-gov version`, `gencode-gov doctor`, `gencode-gov validate`, and `pytest`.
4. Inspect outputs and preserve commit-bound artifacts under `.arkhon/evidence/` where appropriate.
5. Treat missing dependencies, unavailable external agent binaries, unavailable OS sandbox isolation (`bwrap` or `unshare -r --net`), and incomplete integrations as `BLOCKED` or `needs_validation` rather than `PASS`.

## Security Audit & Multi-Agent Orchestration Compatibility

- `gencode-gov audit` (and the legacy `arkhon audit` alias) preserves domain verification (`gencode-gov audit examples/minimal-python --domain testing`) alongside `plan`, `run`, `resume`, `runtimes`, `status`, `coverage`, `verify-findings`, `validate`, `report`, `compare`, and `reassess`.
- Dynamic local security verification requires POSIX `O_NOFOLLOW`, `dir_fd`, `resource` rlimits, and Linux network-namespace isolation (`bwrap` or `unshare -r --net`). On hosts or containers where network-namespace creation is denied, `SandboxExecutor` fails closed to `BLOCKED` while static/structural source review remains available without fabricating sandbox claims.
- Multi-agent independent session mode (`--execution-mode multi_agent_independent_sessions`) requires at least two completed OS-isolated sessions (`pid != os.getpid()`) with distinct discovery and verification `session_id`s. Unavailable external vendor CLIs (`claude-cli`, `codex-cli`, `gemini-cli`) fail closed (`BLOCKED`, exit `1`).

## Intentional Backward-Compatibility Identifiers

To honor `manifest/compatibility.yaml` (`frozen_apis`) without duplicating Python modules or invalidating SHA-256-pinned evidence bundles, GENCODE-GOV intentionally retains the following technical identifiers while establishing **GENCODE-GOV** as the sole active project identity:

| Retained Identifier | Location / Scope | Compatibility Rationale |
| :--- | :--- | :--- |
| `src/arkhon/` (`import arkhon`) | Python package & module import path | Preserves `frozen_apis` (`src/arkhon/cli.py::main`, `src/arkhon/config.py::load_manifest`, `src/arkhon/evidence/store.py::read_evidence`, `src/arkhon/assessment/gates.py::evaluate`) and avoids module duplication |
| `arkhon` CLI entrypoint | `pyproject.toml` `[project.scripts]` | Retained alongside primary `gencode-gov` CLI entrypoint so existing scripts and CI pipelines continue working without modification |
| `.arkhon/` workspace directory | `.arkhon/{project.yaml,config.yaml,evidence,reports,state,agent-pack}` | Preserves relative artifact paths hashed inside tamper-evident evidence bundles and existing initialized repositories |
| `ArkhonError` / `ARKHON_ERROR` | `src/arkhon/core/errors.py` | Preserves programmatic exception class hierarchy and default machine error code |
| `source: "arkhon"` & `EVID-ARKHON-*` | `schemas/evidence.schema.json`, `EvidenceCollector` | Preserves schema validation compatibility with persisted evidence records |
| `arkhon:commit-sha` & `arkhon:generator` | CycloneDX SBOM component properties | Preserves commit-binding verification on persisted CycloneDX SBOM artifacts (`value` updated to `"GENCODE-GOV SyftRunner"`) |
| `skills/arkhon-governance` & `arkhon-*` product IDs | `skills/`, `agent_pack/`, `manifest/products.yaml` | Preserves cross-skill `requires:` dependency graph and staged agent-pack manifest compatibility while all human-facing titles/names use `GENCODE-GOV` |
| `APXOH_ROOT` & `ARKHON_*` env fallbacks | `config.py`, `security_audit/{runtime,sandbox}.py` | Supported strictly as fallback/co-exported environment variables behind primary `GENCODE_GOV_ROOT`, `GENCODE_GOV_AGENT_CMD`, `GENCODE_GOV_AGENT_SESSION_ID`, `GENCODE_GOV_TASK_FILE`, and `GENCODE_GOV_SANDBOX` |
| `apxoh_version` & `arkhon_version` | `schemas/report.schema.json`, `JsonReporter`, `agent-pack/manifest.json` | Optional schema/manifest compatibility keys retained alongside primary `gencode_gov_version` |

Do not infer that an external AI coding agent discovered or obeyed governance instructions merely because files exist on disk. Verify discovery, activation, persistence, and behavioral compliance per product version.
