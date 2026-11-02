# Apxoh Roadmap

**Version:** 1.1  
**Status:** Active  
**Last updated:** 2026-11-02

---

## Current Status

Apxoh is in **pre-release** (0.1.0.dev1). Milestone completion is tracked below; a checked item indicates repository work recorded as complete, not necessarily successful execution in every environment.

---

## Target Personas

The following are working personas for product planning. They are derived from the current product scope and have not yet been validated through a formal user-research process.

| Persona | Primary workflow |
| :--- | :--- |
| **Software developer / maintainer** | Uses the local CLI, interprets findings, fixes issues, and prepares changes. |
| **AI coding agent** | Consumes repository instructions, skills, and integration guidance while producing code or documentation. |
| **Reviewer / software architect** | Reviews requirements, architecture decisions, implementation changes, and evidence. |
| **Assurance / release decision-maker** | Reviews verification outcomes, required evidence, exceptions, and release gates. |
| **Security reviewer / integration operator** | Configures and evaluates delegated security checks and TSAR evidence. |

The personas are planning aids, not verified market segments. Review them using feedback from real users at major releases. Each significant feature proposal should identify its target persona and workflow before design begins.

Product definitions and component boundaries are in manifest/products.yaml. Named accountable owners for each product have not yet been recorded in that registry.

---

## Milestones

### Milestone 0 — Repository Foundation ✅

- [x] Foundation files (README, LICENSE, VERSION, CHANGELOG, CONTRIBUTING, SECURITY)
- [x] AGENTS.md
- [x] Manifest (split into manifest/)
- [x] CLI skeleton (version, doctor)
- [x] Foundation tests

**Status:** Complete.

### Milestone 1 — Engineering Charter & Governance ✅

- [x] Engineering charter
- [x] Governance model
- [x] Risk classification
- [x] Exception policy
- [x] Software lifecycle
- [x] Enforcement model
- [x] Seven security documents

**Status:** Complete.

### Milestone 2 — Rule Engine & Languages 🔄

- [x] Rule loader, validator, registry
- [x] Rule schema
- [x] 9-language registry
- [x] Python language profile
- [x] 20 initial rule files across 14 domains (17 global and 3 Python-specific)
- [ ] Remaining language profiles and their verification evidence
- [ ] Language detector tests and fixture coverage review

**Status:** Rule files and the registry are present. Language maturity and execution coverage remain subject to validation.

### Milestone 3 — Verification & Evidence ✅ (Core) / 🔄 (Full)

- [x] Evidence collector, integrity, store
- [x] Evidence schema
- [x] Assessment scorer, gates, decision
- [x] Verification engine
- [x] Runners: pytest, ruff, mypy, tsar
- [x] TSAR adapter + verifier + proposed contract
- [ ] Full integration tests for TSAR (requires TSAR installed)
- [ ] SBOM generation runner
- [ ] SLSA provenance runner

**Status:** Core components are present. Full completion requires external tools and verified end-to-end execution.

### Milestone 4 — AI Agent Adoption 🔄

- [x] AGENTS.md
- [x] SECURITY_AGENTS.md
- [x] 8 skills
- [x] 9 agent roles
- [ ] Complete behavioral verification for agent integrations
- [ ] Integration tests and environment-specific validation
- [ ] arkhon install --scope project|global command

**Status:** Agent instructions, skills, roles, and integration packages are present; operational adoption and behavioral verification remain distinct tasks.

### Milestone 5 — Orchestrator & Full CLI 🔄

- [x] Lifecycle state machine
- [x] Stage manager
- [x] Reporting (JSON + Markdown)
- [x] CLI: version, doctor, validate, inspect, audit, assess, report, verify
- [ ] CLI: install, status, exceptions
- [ ] arkhon project init command

**Status:** In progress.

### Milestone 6 — Self-Governance & CI 🔄

- [x] .pre-commit-config.yaml
- [x] .github/CODEOWNERS
- [x] .github/dependabot.yml
- [x] .github/workflows/ci.yml
- [x] .github/workflows/security.yml
- [x] .github/workflows/scorecard.yml
- [x] .github/workflows/slsa-release.yml
- [ ] Branch protection configured and verified on GitHub
- [ ] First signed release with independently verified provenance

**Status:** Workflow files are present. Branch protection and release-signing/provenance status require live configuration and execution evidence.

---

## After v0.1.0

### v0.2.0 — Rules Expansion
- Expand the catalog beyond the initial 20 rules, targeting the roadmap's broader domain coverage.
- Complete language profiles and fixture verification for all 9 declared languages.
- Extend rule-authoring examples and semantic validation.

### v0.3.0 — Model and Agent Integration Depth
- Complete behavioral adapters and verification for supported integrations.
- Add integration adoption guidance for supported agent platforms.
- Verify Copilot platform integration behavior.

### v0.4.0 — Advanced Verification
- SBOM generation (CycloneDX).
- SLSA provenance end-to-end.
- Mutation testing runner.
- Chaos testing runner.
- Load testing runner.

### v0.5.0 — Enterprise Features
- Exception workflow (approval, expiry, revocation).
- Risk register.
- Multi-party signing for releases.
- SOC 2 / ISO 27001 gap-assessment template.

### v1.0.0 — Stable Release
- All milestones complete.
- Public API frozen.
- Semantic versioning from this release onward.
- Documentation site live.
- First independently verified SLSA Level 3 release.

---

## Not Planned (Explicitly)

- Replacing human code review.
- Proving the absence of bugs.
- Certifying compliance with any standard (Apxoh references standards; it does not certify).
- Replacing TSAR's delegated security authority.
- Replacing any specific AI provider.

---

## How to Propose a Change

1. Open an issue describing the change.
2. Discuss with maintainers.
3. If accepted, open a PR linked to the issue.
4. Follow the PR template.
5. Identify the target persona, workflow, and product area in the proposal.

See CONTRIBUTING.md for details.

---

**End of Roadmap**
