# GENCODE-GOV Verification, Evidence & Persistent Adoption Reference

## 1. Applying GENCODE-GOV With or Without the Python CLI

GENCODE-GOV operates in two complementary modes so AI coding agents can apply rigorous engineering governance across any codebase:

1. **Full Engine Mode (`gencode-gov` CLI Installed)**:
   - Run `gencode-gov inspect . --json` to detect languages and active profile (`.gencode-gov/project.yaml`).
   - Run `gencode-gov verify . --domain testing` (or `code-quality`, `software-security`, `security-audit`, `supply-chain`, `release-readiness`, or `all`) to execute independent tool runners and write SHA-256-pinned evidence under `.gencode-gov/evidence/`.
   - Run `gencode-gov assess .` on a clean Git `HEAD` commit to evaluate all applicable `SE-*` rules and domain gates fail-closed.
   - Run `gencode-gov audit run .` (deterministic single-process or `--execution-mode multi_agent_independent_sessions`) for 6-phase coverage-led source security auditing.
   - Run `gencode-gov report . --format markdown` (or `--format json`) to generate commit-bound readiness reports.
2. **Skill-Only Mode (Target Project Without `gencode-gov` Python Package)**:
   - Follow the 8-stage closed loop (`Inspect -> Plan -> Design -> Implement -> Verify -> Remediate -> Re-verify -> Report`) and all applicable domain rules in `OPERATIONAL_CONTRACT.md`, `SECURITY_POSTURE.md`, and `ENGINEERING_CHARTER_AND_DOMAINS.md`.
   - Execute the repository's native deterministic verifiers directly (for example: `pytest`, `ruff`, `mypy`, `cargo test`/`clippy`, `go test`/`go vet`, `npm test`/`tsc`/`eslint`, `mvn test`, `dotnet test`, `ctest`, `bundle exec rspec`).
   - Report exact commands executed, pass/fail counts, and coverage metrics; explicitly mark any unexecuted or unavailable check as `BLOCKED` rather than `PASS`.

## 2. Workspace Layout (`.gencode-gov/`)

Governed repositories store project declarations and tamper-evident verification records under `.gencode-gov/`:

- `.gencode-gov/project.yaml` — Explicit project profile (`universal`, `api-service`, `web-application`, `mobile-application`, `desktop-application`, `distributed-system`, `enterprise`, `safety-critical`), risk level, languages, and required gates.
- `.gencode-gov/config.yaml` — Fail-closed engine settings, evidence freshness windows (`168h` security/supply-chain, `720h` general), TSAR contract path, and exception bounds.
- `.gencode-gov/evidence/testing/EVID-GENCODE-GOV-*.json` — Commit-pinned (`commit_sha`), SHA-256-hashed evidence bundles organized by domain directory.
- `.gencode-gov/reports/` — Generated assessment, SBOM (`gencode-gov:commit-sha`), attestation, and quality reports.
- `.gencode-gov/state/` — Append-only operational state and incident logs.
- `.gencode-gov/agent-pack/` — Project-staged governance instructions (`gencode-gov install --scope project --project .`).

## 3. Maintaining Persistent Adoption Across Supported Agents

- **User-Scope Persistent Skills (`npx skills add ... -g`)**:
  - `npx skills add https://github.com/mohamedelghazali/GENCODE-GOV --skill gencode-gov -g` installs `gencode-gov` (including this `references/` directory) into user-level skill directories for selected agents (`~/.claude/skills/gencode-gov`, `~/.codex/skills/gencode-gov`, `~/.cursor/skills/gencode-gov`, `~/.gemini/skills/gencode-gov`, and other `npx skills`-supported clients).
  - Run `npx skills update -g` periodically to pull upstream governance updates.
- **Project-Pinned Skills (`skills-lock.json`)**:
  - `npx skills add https://github.com/mohamedelghazali/GENCODE-GOV --skill gencode-gov` installs into `.agents/skills/gencode-gov/`, links configured project agent folders, and writes commit/content-hash pins to `skills-lock.json`.
- **Supplementary Persistent Instruction Files**:
  - Where supported by an agent, reference GENCODE-GOV in repository `AGENTS.md`, `~/.claude/CLAUDE.md`, `~/.codex/AGENTS.md`, `.cursor/rules/`, or `.github/copilot-instructions.md` so non-Skill instruction loaders also apply the governance contract consistently.
- **Verification Honesty**:
  - Skill installation makes governance instructions discoverable to compatible agents; it does not substitute for independent CI/CLI execution or enforce compliance on agents that do not load Skills or instruction files.
