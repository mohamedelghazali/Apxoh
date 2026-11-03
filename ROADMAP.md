# Apxoh Roadmap

**Version:** 1.2  
**Status:** Active — pre-release  
**Last updated:** 2026-11-03

---

## Current Status

Apxoh is in **pre-release** (0.1.0.dev1). Milestone checkboxes below distinguish implementation present in the repository from execution or external-environment verification. A checked implementation item is not, by itself, proof that CI or a production integration has passed.

The latest `main` commit at this update is `8da1c6da5a7105f804a8b8abecbc59dc1fedddc1`. Its GitHub Actions checks were queued when inspected; no successful result is claimed. The repository had no open pull requests or issues at that inspection time.

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
- [x] Language profiles and per-language tool, testing, and security metadata for all 9 registered languages
- [x] Initial rule catalog (20 rules across 14 domains: 17 global and 3 Python-specific)
- [x] Language detector, registry, profile-loader, tool-resolution tests, and 9 language fixtures
- [ ] CI execution and review of all 9 language fixture jobs
- [ ] Broader language-specific rule catalog and semantic verification

**Status:** Implementation and test fixtures are present for all 9 declared languages. Completion of the fixture/CI gate is pending successful execution against the current main commit. The initial rule catalog is intentionally limited; expansion remains planned for v0.2.0.

### Milestone 3 — Verification & Evidence 🔄

- [x] Evidence collector, integrity, store, and schema
- [x] Assessment scorer, gates, decision, and verification engine
- [x] Local verification runners: pytest, Ruff, mypy, TSAR, and Syft SBOM generation
- [x] Commit-bound CycloneDX SBOM acceptance and evidence persistence
- [x] SLSA/Sigstore release-attestation verification runner and release workflow
- [x] TSAR adapter, verifier, contract tests, and real-CLI end-to-end workflow definition
- [ ] Successful real TSAR end-to-end workflow execution on main
- [ ] Successful Syft SBOM end-to-end workflow execution on main
- [ ] First signed release with independently verified provenance
- [ ] End-to-end release-attestation evidence accepted from an actual tagged release

**Status:** Core and supply-chain implementations are present, including executable CI workflow definitions. The external-tool and release gates are not considered complete until their jobs run successfully and their generated evidence is verified. A source-code implementation or workflow file alone does not close these gates.

### Milestone 4 — AI Agent Adoption 🔄

- [x] AGENTS.md and SECURITY_AGENTS.md
- [x] 8 skills and 9 agent roles
- [x] Packaged 20-file agent governance resource bundle
- [x] `arkhon install --scope project|global` implementation, manifest, safe staging, and unit tests
- [x] Agent/model/platform integration contracts and integration test scaffolding
- [ ] Behavioral verification with each supported agent product in a real configured environment
- [ ] Verify instruction discovery, activation, precedence, and enforcement per supported platform
- [ ] Complete platform-specific integration validation, including GitHub Copilot
- [ ] Successful CI execution of agent integration checks

**Status:** The resource pack and installer are implemented. Integration scaffolding and contract tests do not establish that every third-party agent actually loads or obeys the instructions. The generic-agent adapter is explicitly marked manual; behavioral adoption remains open.

### Milestone 5 — Orchestrator & Full CLI 🔄

- [x] Lifecycle state machine and stage manager
- [x] JSON and Markdown reporting
- [x] CLI: version, doctor, validate, inspect, audit, assess, report, verify
- [x] CLI: install, status, exceptions list
- [x] `arkhon project init` with schema validation
- [x] CLI parser registration and unit tests for the added commands
- [ ] Full CLI test suite, packaging, and clean-install workflows passing on the current main commit
- [ ] Complete rule-outcome assessment integration; the current assessment command fails closed when rule-level outcomes are unavailable

**Status:** The listed commands are implemented and registered. Runtime/package validation remains pending the queued CI jobs. Assessment must not report a release-ready score until genuine rule-level outcomes are available.

### Milestone 6 — Self-Governance & CI 🔄

- [x] .pre-commit-config.yaml
- [x] .github/CODEOWNERS
- [x] .github/dependabot.yml
- [x] CI, integration, installation, security, schema, infrastructure, TSAR, supply-chain, and scorecard workflow definitions
- [ ] Current-main CI, unit, integration, installation, security, TSAR, and supply-chain workflows completed successfully
- [ ] Enable branch protection or a ruleset for main and require the CI/security status checks
- [ ] Read back the effective settings and verify that required checks are enforced
- [ ] First signed release with independently verified provenance

**Status:** Workflow definitions are present. The latest main commit had 53 check runs queued at the time of inspection, with no completed success/failure evidence. The GitHub branch API reports `main` as `protected: false`, and the repository rulesets endpoint returns an empty list. Branch protection is absent and must be configured before this milestone can close. Do not bypass checks or mark this milestone complete until both CI results and repository enforcement settings are confirmed.

---

## After v0.1.0

### v0.2.0 — Rules Expansion
- Expand the catalog beyond the initial 20 rules, targeting the roadmap's broader domain coverage.
- Add deeper language-specific rules and semantic verification for all 9 declared languages.
- Extend rule-authoring examples and semantic validation.

### v0.3.0 — Model and Agent Integration Depth
- Complete behavioral adapters and verification for supported integrations.
- Add integration adoption guidance for supported agent platforms.
- Verify Copilot platform integration behavior.

### v0.4.0 — Advanced Verification
- Mutation testing runner.
- Chaos testing runner.
- Load testing runner.
- Expand CycloneDX and SLSA verification coverage beyond the current initial implementation.

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
