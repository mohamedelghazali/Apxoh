# Apxoh Architecture and Governance Glossary

**Version:** 1.0  
**Last updated:** 2026-11-02

This glossary defines terminology used in the Apxoh repository. Terms describing target controls or architecture do not, by themselves, prove that those controls are deployed.

## Core Concepts

**Apxoh** — Software Engineering Governance & Assurance System. The system this repository defines.

**ARKHON** — Latin identifier of Apxoh, used in package names, CLI, and file paths.

**АРХОН** — Cyrillic reference used in visual identity only.

**Apxoh Core** — The Python engine designed to run locally.

**Apxoh Agent Governance** — Instructions and skills intended for AI coding agents adopting Apxoh.

**Apxoh Assurance** — Independent verification, evidence collection, and release gating.

---

## Governance

**Charter** — The twelve founding principles of Apxoh's engineering policy, documented in `system/charter/ENGINEERING_CHARTER.md`.

**Rule** — A YAML document encoding an engineering requirement. Global rules live under `rules/`; language-specific rules may live under `languages/*/rules/`.

**Rule ID** — A stable identifier such as `SE-REQ-001`. The intended format is `SE-<DOMAIN>-[<SUBDOMAIN>-]<NUMBER>`.

**Policy** — A blocking, advisory, or exception policy that influences engine behavior. Policies are stored under `system/policies/`.

**Enforcement level** — The strictness with which a rule is applied: `advisory`, `required`, `blocking`, or `critical`.

**Severity** — The seriousness of a finding: `critical`, `high`, `medium`, or `low`.

**Gate** — A lifecycle checkpoint that aggregates applicable rule outcomes. The eight gate categories are requirements, architecture, implementation, testing, security, performance, reliability, and release.

**Exit criteria** — Conditions that must be satisfied before a lifecycle stage can advance.

---

## Verification

**Verification Engine** — The component that invokes independent runners against a project. It must not accept an agent's unsupported claim as verification evidence.

**Runner** — A component that executes a verification step, such as pytest, Ruff, Mypy, or the TSAR adapter.

**Evidence** — A record of a verification activity, ideally including the target commit, execution time, tool identity/version, result, and artifact references. SHA-256 digests detect changes to referenced bytes when the expected digest is trusted; a digest alone is not a signature.

**Evidence bundle** — A structured evidence document intended to conform to `schemas/evidence.schema.json`.

**Finding** — A single result of evaluating a rule against a target.

**Assessment** — The aggregation of rule outcomes and gate verdicts, including a weighted score.

**Score** — A number from 0 to 100. The current scorer defines eight weighted domains whose weights total 100.

**Level** — A score classification: `development`, `controlled-release`, `production-ready`, `enterprise-grade`, or `hyperscale-validated`. A level is not a substitute for gate approval.

**Gate verdict** — `PASS`, `FAIL`, or `BLOCKED`, derived from evaluated outcomes. Empty or missing required outcomes must not be treated as a pass.

**Release decision** — A decision such as `APPROVED`, `APPROVED_WITH_CONDITIONS`, `REJECTED`, or `PENDING_EVIDENCE`, as defined by the release decision model.

---

## Evidence Integrity

**SHA-256** — A cryptographic hash function used to detect changes to data.

**Sigstore** — A set of tools and services for keyless signing and verification. A dependency or design reference to Sigstore does not prove that evidence is signed or that signer identity is verified.

**Commit binding** — The association between an evidence record and the exact source commit to which it applies.

**Freshness window** — The maximum permitted age of evidence before it is considered stale. The TSAR contract specifies 168 hours (seven days) for its evidence.

**Append-only** — A storage property in which existing records are not silently replaced. The evidence store refuses to overwrite an existing evidence ID with different content; this does not by itself make the filesystem immutable or tamper-proof.

**Tampering** — Unauthorized modification, deletion, substitution, or path manipulation of evidence or its artifacts. Hash mismatch, missing artifacts, or commit mismatch must prevent acceptance.

---

## Integrations

**Integration** — An external system Apxoh communicates with, such as a model provider, coding platform, or security authority.

**Adapter** — Code that communicates with an integration and translates its inputs and outputs. An adapter should not make governance or release decisions.

**TSAR** — The delegated security authority named by the Apxoh integration contract. The contract assigns SAST, DAST, SCA, secrets, and cryptography-related verification responsibilities; actual coverage depends on the deployed TSAR version and configuration.

**Contract** — The declared interface between Apxoh and TSAR, located at `integrations/tsar/contract.yaml`. The current contract file labels its status as proposed.

**Model integration** — One of the eight model entries declared in the registry: Claude, OpenAI o, DeepSeek-Coder, GPT, Gemini, Code Llama, Qwen-Coder, and Kimi.

**Platform integration** — A coding platform integration such as GitHub Copilot. Apxoh cannot necessarily pin or observe the model selected internally by the platform.

**Generic agent** — A fallback integration path for an unlisted platform. Instructions may need to be applied manually; this does not establish activation or verification.

---

## Adoption Levels

**Installed (1)** — Required integration files are present on disk.

**Discoverable (2)** — The target agent/platform can locate the integration instructions.

**Activated (3)** — Evidence shows that the instructions were loaded into the active agent context.

**Configured (4)** — Platform settings are inspected and bound to the intended Apxoh integration.

**Verified (5)** — Repeatable behavioral verification passed for the exact model/platform version and the evidence was independently reviewed. This level may be unavailable for integrations without a suitable test interface.

A level must be supported by evidence. It must not be inferred from a manifest entry or successful installation alone.

---

## Lifecycle

**Stage** — One of the ten phases in the governed lifecycle:

1. Project Initialization
2. Requirements Engineering
3. Architecture Design
4. Implementation Planning
5. Controlled Development
6. Independent Verification
7. Remediation
8. Release Readiness Review
9. Release Approval
10. Post-Release Monitoring

**Stage transition** — Movement from one lifecycle stage to the next, subject to the exit criteria enforced for that stage.

**Blocked** — A stage or gate cannot advance because a required gate is not closed, required evidence is missing, or exit criteria remain unmet.

---

## Languages

**Language profile** — A YAML description of how Apxoh is intended to detect and verify a language. The repository's profile structure includes `language-profile.yaml`, `tools.yaml`, `testing.yaml`, and `security.yaml`.

**Language fixture** — A minimal project used to exercise language detection and verification. Fixtures belong under `tests/languages/fixtures/`.

**Tool resolver** — The component responsible for checking whether required verification tools are installed and available.

**Missing tool policy** — A required tool that is unavailable must result in `BLOCKED`; it must not silently pass.

---

## Statuses

**PASS** — The evaluated check passed with the required valid evidence.

**FAIL** — The evaluated check failed to meet its requirement.

**BLOCKED** — The check could not be completed or accepted, for example because a required tool or input was missing, evidence was stale or invalid, or TSAR was unavailable.

**NOT_APPLICABLE** — The check does not apply to the evaluated project/profile, where the rule and policy permit that status.

**ACCEPTED_RISK** — A specifically authorized exception accepts a documented risk within its scope. It is not equivalent to a technical PASS.

**No status can be converted to PASS by editing a report or changing an agent's claim.** A new verification run may produce a new result, but historical outcomes must remain intact.

---

## Repository Structure

**`manifest/`** — Registries for system identity, products, integrations, languages, and standards.

**`system/`** — Charter, policies, lifecycle, enforcement model, and risk model.

**`rules/`** — Global engineering rules organized by domain.

**`languages/`** — Language-specific profiles and rules.

**`projects/`** — Project-type profiles such as universal, web application, and API service.

**`schemas/`** — JSON Schemas for rules, evidence, findings, projects, and related documents.

**`src/arkhon/`** — The Python engine and CLI package.

**`skills/`** — Reusable capabilities and instructions for AI agents.

**`agents/`** — Role-to-skill bindings and agent definitions.

**`integrations/`** — Model, platform, TSAR, and generic integration contracts and artifacts.

**`tests/`** — Unit, integration, security, language, and fixture tests.

**`.arkhon/`** — Apxoh's project-local governance state and evidence area. Runtime-generated evidence should not be treated as immutable merely because it is stored here.

---

**End of Glossary**
