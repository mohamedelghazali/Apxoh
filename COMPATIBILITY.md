# COMPATIBILITY

## Purpose

This guide documents the **GENCODE-GOV** runtime foundation, platform verification bounds, Agent Skills compatibility, and fail-closed execution posture.

## Supported Runtime & Verification Procedure

1. Use Python `>=3.11, <3.14` (`3.11`, `3.12`, or `3.13`) in an isolated virtual environment across Linux, macOS, or Windows.
2. Install the package and development dependencies (`pip install -e ".[dev]"`).
3. Run `gencode-gov version`, `gencode-gov doctor`, `gencode-gov validate`, and `pytest`.
4. Inspect outputs and preserve commit-bound artifacts under `.gencode-gov/evidence/` where appropriate.
5. Treat missing dependencies, unavailable external agent binaries, unavailable OS sandbox isolation (`bwrap` or `unshare -r --net`), and incomplete integrations as `BLOCKED` or `needs_validation` rather than `PASS`.

## Agent Skills Ecosystem Compatibility (`npx skills`)

- `skills/gencode-gov/` (together with its bundled `references/` directory and the 9 companion specialist skills under `skills/`) conforms to the open Agent Skills `SKILL.md` format (`npx skills` / Node.js `>=22.20`).
- Project-scoped installation (`npx skills add https://github.com/mohamedelghazali/GENCODE-GOV`) stages skills under `.agents/skills/` and records commit and SHA-256 file digests in `skills-lock.json`.
- User-level persistent installation (`npx skills add https://github.com/mohamedelghazali/GENCODE-GOV --skill gencode-gov -g`) stages skills into supported user-scope agent directories (such as `~/.claude/skills/`, `~/.codex/skills/`, `~/.cursor/skills/`, and `~/.gemini/skills/`).
- Persistent discovery and automatic skill consultation apply only to coding agents and environments that support the Agent Skills specification or configured instruction files; agents without persistent skill support must be given the conversation-scoped adoption prompt explicitly.

## Security Audit & Multi-Agent Orchestration Compatibility

- `gencode-gov audit` preserves domain verification (`gencode-gov audit examples/minimal-project --domain testing`) alongside `plan`, `run`, `resume`, `runtimes`, `status`, `coverage`, `verify-findings`, `validate`, `report`, `compare`, and `reassess`.
- Dynamic local security verification requires POSIX `O_NOFOLLOW`, `dir_fd`, `resource` rlimits, and Linux network-namespace isolation (`bwrap` or `unshare -r --net`). On hosts or containers where network-namespace creation is denied, `SandboxExecutor` fails closed to `BLOCKED` while static/structural source review remains available without fabricating sandbox claims.
- Multi-agent independent session mode (`--execution-mode multi_agent_independent_sessions`) requires at least two completed OS-isolated sessions (`pid != os.getpid()`) with distinct discovery and verification `session_id`s. Unavailable external vendor CLIs (`claude-cli`, `codex-cli`, `gemini-cli`) fail closed (`BLOCKED`, exit `1`).

## Core API & Artifact Contracts

Canonical entrypoints and artifact locations are declared in `manifest/compatibility.yaml`:

| Surface | Canonical Identifier / Path | Notes |
| :--- | :--- | :--- |
| Python package | `src/gencode_gov/` (`import gencode_gov`) | Frozen entrypoints: `src/gencode_gov/cli.py::main`, `src/gencode_gov/config.py::load_manifest`, `src/gencode_gov/evidence/store.py::read_evidence`, `src/gencode_gov/assessment/gates.py::evaluate` |
| CLI command | `gencode-gov` | Installed via `pyproject.toml` `[project.scripts]` |
| Workspace directory | `.gencode-gov/` | Contains `project.yaml`, `config.yaml`, `evidence/`, `reports/`, `state/`, and `agent-pack/` |
| Primary Agent Skill | `skills/gencode-gov/` (`name: gencode-gov`) | Includes `SKILL.md` and self-contained `references/` for `npx skills add` |
| Base exception | `GencodeGovError` (`GENCODE_GOV_ERROR`) | Defined in `src/gencode_gov/core/errors.py` |
| Evidence & SBOM keys | `source: "gencode-gov"`, `EVID-GENCODE-GOV-*`, `gencode-gov:commit-sha`, `gencode-gov:generator` | Validated by `schemas/evidence.schema.json` and `supply_chain.py` |
| Environment variables | `GENCODE_GOV_ROOT`, `GENCODE_GOV_AGENT_CMD`, `GENCODE_GOV_AGENT_SESSION_ID`, `GENCODE_GOV_TASK_FILE`, `GENCODE_GOV_SANDBOX` | Validated fail-closed in `config.py`, `runtime.py`, and `sandbox.py` |

Do not infer that an external AI coding agent discovered or obeyed governance instructions merely because files exist on disk. Verify discovery, activation, persistence, and behavioral compliance per product version.
