# Changelog

All notable changes to **GENCODE-GOV** are documented in this file.

The format follows Keep a Changelog and adheres to Semantic Versioning (`0.x` pre-1.0 policy in `docs/VERSIONING.md`).

## [Unreleased]

### Changed
- Completed full repository-wide `GENCODE-GOV` identity consolidation (`src/gencode_gov/`, `.gencode-gov/`, `GencodeGovError`, `EVID-GENCODE-GOV-*`, `gencode-gov:commit-sha`, and `skills/gencode-gov/`).
- Packaged `skills/gencode-gov/` with self-contained `references/` (`OPERATIONAL_CONTRACT.md`, `SECURITY_POSTURE.md`, `ENGINEERING_CHARTER_AND_DOMAINS.md`, and `VERIFICATION_AND_ADOPTION.md`) for persistent and project-scoped installation via `npx skills add`.
- Added the `Adopting GENCODE-GOV in AI Agent Workflows` guide in `README.md` covering persistent global/project Agent Skills installation and conversation-only adoption.

## [0.1.0] - 2026-11-26

### Added
- Normative `SE-*` YAML governance rule catalog across 16 software engineering domains, 9 language profiles, and 8 project governance profiles validated by Draft 2020-12 JSON Schemas.
- Deterministic Python verification, tamper-evident SHA-256 evidence store, CycloneDX SBOM and SLSA/Sigstore attestation verifiers, weighted gate scorer, and commit-bound Markdown/JSON reporting engine (`gencode-gov`).
- Six-phase coverage-led source security audit subsystem (`gencode_gov.security_audit`) across 19 attack classes with both deterministic single-process execution and OS-isolated multi-agent session orchestration (`gencode-gov audit`).
- Specialist agent role definitions (`agents/`), 10 portable `SKILL.md` packages (`skills/`), packaged model HTTP adapters, TSAR security-authority contract, and multi-platform CI workflows.
