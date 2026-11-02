# Apxoh Roadmap

**Version:** 1.0
**Status:** Active
**Last updated:** 2026-11-01

---

## Current Status

Apxoh is in **pre-release** (`0.1.0-dev.1`), Milestone 0–1 complete,
Milestone 2 in progress.

---

## Milestones

### Milestone 0 — Repository Foundation ✅

- [x] Foundation files (README, LICENSE, VERSION, CHANGELOG, CONTRIBUTING, SECURITY)
- [x] AGENTS.md
- [x] Manifest (split into `manifest/`)
- [x] CLI skeleton (`version`, `doctor`)
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
- [ ] 20 initial rules across 6 domains
- [ ] Remaining 8 language profiles
- [ ] Language detector tests
- [ ] Language fixtures

**Status:** In progress.

### Milestone 3 — Verification & Evidence ✅ (Core) / 🔄 (Full)

- [x] Evidence collector, integrity, store
- [x] Evidence schema
- [x] Assessment scorer, gates, decision
- [x] Verification engine
- [x] Runners: pytest, ruff, mypy, tsar
- [x] TSAR adapter + verifier + contract
- [ ] Full integration tests for TSAR (requires TSAR installed)
- [ ] SBOM generation runner
- [ ] SLSA provenance runner

**Status:** Core complete. Full completion requires external tools.

### Milestone 4 — AI Agent Adoption 🔄

- [x] AGENTS.md (full)
- [x] SECURITY_AGENTS.md
- [x] 8 skills (arkhon-governance + 7 others)
- [x] 9 agent roles
- [ ] 8 model integration directories
- [ ] GitHub Copilot platform integration
- [ ] Integration adapters for models
- [ ] Integration tests for models
- [ ] `arkhon install --scope project|global` command

**Status:** In progress.

### Milestone 5 — Orchestrator & Full CLI 🔄

- [x] Lifecycle state machine
- [x] Stage manager
- [x] Reporting (JSON + Markdown)
- [x] CLI: version, doctor, validate, inspect, audit, assess, report, verify
- [ ] CLI: `install`, `status`, `exceptions`
- [ ] Report templates (16 engineering quality docs, currently stub)
- [ ] `arkhon project init` command

**Status:** In progress.

### Milestone 6 — Self-Governance & CI 🔄

- [x] `.pre-commit-config.yaml`
- [x] `.github/CODEOWNERS`
- [x] `.github/dependabot.yml`
- [x] `.github/workflows/ci.yml`
- [x] `.github/workflows/security.yml`
- [x] `.github/workflows/scorecard.yml`
- [x] `.github/workflows/slsa-release.yml`
- [ ] `workflows/validate-rules.yml`
- [ ] `workflows/schema-validation.yml`
- [ ] `workflows/self-test.yml`
- [ ] `workflows/agent-skills.yml`
- [ ] `workflows/installation-test.yml`
- [ ] Branch protection configured on GitHub
- [ ] First signed release with SLSA provenance

**Status:** In progress.

---

## After v0.1.0

### v0.2.0 — Rules Expansion
- 100+ rules across all 16 domains
- Full language profiles for all 9 languages
- Language fixtures for each
- Rule authoring guide with 20 examples

### v0.3.0 — Model Integration Depth
- Full adapters for all 8 models
- Behavioral verification tests
- Integration adoption guide per model
- Copilot platform integration

### v0.4.0 — Advanced Verification
- SBOM generation (CycloneDX)
- SLSA provenance end-to-end
- Mutation testing runner
- Chaos testing runner
- Load testing runner

### v0.5.0 — Enterprise Features
- Exception workflow (approval, expiry, revocation)
- Risk register
- Multi-party signing for releases
- SOC 2 / ISO 27001 gap assessment template

### v1.0.0 — Stable Release
- All milestones complete
- Public API frozen
- Semantic versioning from here on
- Documentation site live
- First SLSA Level 3 verified release

---

## Not Planned (Explicitly)

- ❌ Replacing human code review
- ❌ Proving the absence of bugs
- ❌ Certifying compliance with any standard (we reference, we don't certify)
- ❌ Replacing TSAR's security authority
- ❌ Replacing any specific AI provider

---

## How to Propose a Change

1. Open an issue describing the change.
2. Discuss with maintainers.
3. If accepted, open a PR linked to the issue.
4. Follow the PR template.

See `CONTRIBUTING.md` for details.

---

**End of Roadmap**
