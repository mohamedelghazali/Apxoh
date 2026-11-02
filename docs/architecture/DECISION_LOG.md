# Apxoh Architecture Decision Log

**Version:** 1.1  
**Status:** Accepted design record with implementation notes  
**Last updated:** 2026-11-02

This log records architectural choices and their rationale. An accepted design decision does not prove that every associated control is implemented. Implementation status is stated separately and must be checked against code, configuration, and execution evidence.

## ADR-001 — Separate Product Name and Technical Identifier

**Status:** Accepted  
**Decision:** Use **Apxoh** as the product/system name, arkhon as the Python package and CLI identifier, and **АРХОН** only as a Cyrillic visual-identity reference.  
**Rationale:** Product identity can remain stable while technical identifiers follow package and tooling conventions.  
**Implementation note:** Package metadata and CLI use arkhon; visual identity usage is a documentation/brand convention.

## ADR-002 — Delegate Security Authority to TSAR

**Status:** Accepted; integration contract proposed  
**Decision:** Apxoh owns governance policy, gate placement, evidence acceptance, and release decisions. TSAR is the delegated authority for the security checks specified by the integration contract.  
**Rationale:** Keep governance orchestration separate from specialized security analysis.  
**Implementation note:** The repository contains a TSAR adapter, verifier, contract, and offline contract tests. The contract is marked proposed; these files do not prove that an external TSAR binary is available in a deployment. Required security checks remain BLOCKED when the authority or its evidence is unavailable.

## ADR-003 — Use a Split Manifest Registry

**Status:** Accepted  
**Decision:** Keep system identity, products, languages, integrations, and standards in separately maintained manifest files, indexed through manifest/index.yaml.  
**Rationale:** Smaller registries are easier to review and validate than a single monolithic file.  
**Implementation note:** The repository contains split manifest files and a manifest loader/validation path. Registry contents remain subject to schema and semantic validation.

## ADR-004 — Bind Evidence to Source Revision and Artifact Digests

**Status:** Accepted; partial implementation  
**Decision:** Evidence must identify the target commit and include SHA-256 digests for referenced artifacts. Re-running a check should create a new evidence record rather than silently overwrite a different record.  
**Rationale:** A result detached from its source revision or artifact bytes cannot reliably support a release decision.  
**Implementation note:** The evidence integrity module verifies commit binding and artifact digests; the evidence store uses exclusive creation and refuses to overwrite a record with different content. These controls do not authenticate the evidence JSON itself or prove who produced it. Sigstore signing, signer-identity verification, and provenance must not be claimed as operational until independently implemented and verified.

## ADR-005 — Fail Closed for Missing Required Verification

**Status:** Accepted; implementation in progress  
**Decision:** Missing required tools, missing evidence, stale evidence, malformed evidence, or unavailable required security authority must not produce PASS.  
**Rationale:** An incomplete verification is not a successful verification.  
**Implementation note:** The TSAR contract and verifier use BLOCKED/exception paths for missing or invalid evidence. Gate aggregation must treat an empty outcome set as BLOCKED rather than implicitly passing.

## ADR-006 — Use Declarative Language Profiles

**Status:** Accepted  
**Decision:** Describe language-specific tooling, testing, and security expectations in YAML profiles and fixtures rather than hard-coding every language into the core engine.  
**Rationale:** This supports incremental language coverage while keeping the core engine local-first.  
**Implementation note:** The repository contains a nine-language registry and profile directories. Registry presence is not proof that every external toolchain or language fixture has been executed successfully.

## ADR-007 — Keep the Core Local-First and Provider-Neutral

**Status:** Accepted  
**Decision:** The core engine should run locally and must not require a hosted AI provider for its core governance and verification functions. Model integrations are optional adapters.  
**Rationale:** Governance should remain available when external model APIs are unavailable and should not be tied to a single provider.  
**Implementation note:** Python package dependencies define the core runtime; provider adapters are kept under the integrations tree. External API availability is deployment-specific.

## ADR-008 — Separate Agent Instructions from Enforcement

**Status:** Accepted  
**Decision:** Agent instruction files and skills communicate expected behavior, but they do not by themselves enforce filesystem permissions, branch protection, or trusted execution.  
**Rationale:** Text instructions can be ignored, overridden, or manipulated by untrusted content.  
**Implementation note:** Repository policy must be backed by code, CI, protected-branch configuration, and human review where required. The presence of AGENTS.md is not a technical security boundary.

## ADR-009 — Model the Lifecycle as Ten Explicit Stages

**Status:** Accepted; lifecycle model implemented  
**Decision:** Use ten ordered lifecycle stages from project initialization through post-release monitoring, with explicit entry/exit criteria and gates where applicable.  
**Rationale:** A defined lifecycle makes handoffs and release readiness reviewable.  
**Implementation note:** The ten-stage enum and stage definitions are present in src/arkhon/orchestrator/lifecycle.py; stage transition enforcement is implemented in stage_manager.py for the criteria currently encoded there. This does not imply every organizational process is automated.

## ADR-010 — Keep Repository Documentation in English by Default

**Status:** Accepted  
**Decision:** Technical source, code comments, and canonical repository documentation use English by default. Localized material may be added when explicitly intended.  
**Rationale:** A consistent canonical language supports cross-team review and tooling.  
**Implementation note:** This is a documentation convention, not a restriction on user-facing localization or multilingual product capabilities.

## Decision Change Process

A decision may be superseded when new evidence, constraints, or requirements justify a change. Record the replacement decision, rationale, affected components, migration implications, and implementation status. Do not silently rewrite historical decisions to imply that a previous design was never adopted.

---

## ADR Template

Use this template for new decisions. Do not retroactively rewrite accepted ADRs merely to fill fields that were not part of their original record.

~~~markdown
## ADR-NNN — [Decision title]

**Status:** Proposed / Accepted / Rejected / Superseded  
**Date:** YYYY-MM-DD  
**Decision owner:** [Role or name]  
**Target user(s):** [Developer / AI coding agent / Reviewer / Assurance or release decision-maker / Security reviewer / Other]

### Context
[Problem, constraints, and evidence.]

### Decision
[The chosen approach.]

### Alternatives considered
[Options and reasons for rejecting them.]

### Consequences
[Benefits, trade-offs, risks, and migration implications.]

### Implementation status
[Proposed / Partial / Implemented / Independently verified, with evidence references.]

### Related decisions
[ADR IDs.]
~~~

**Target user(s)** is required for new significant product or architecture decisions. It records the intended user or actor affected by the decision; it is not a substitute for user research.

---

**End of Decision Log**
