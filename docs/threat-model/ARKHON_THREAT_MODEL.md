# Apxoh Threat Model

**Version:** 1.0
**Status:** Active — initial baseline; implementation status of individual controls must be verified
**Owner:** Security Lead (TBD)
**Last reviewed:** 2026-11-01
**Review cadence:** Every minor release, and after any security incident

> **Assurance note:** This document defines the threat model and required controls. A control listed here is not evidence that it is already deployed or operating effectively. Verify implementation through repository configuration, CI results, and operational evidence before treating it as effective.

---

## 1. System Overview

### 1.1 The Three Products

Apxoh (also referred to as ARKHON) is a Software Engineering Governance & Assurance System. It operates as three interdependent products within a single repository:

| Product | Role | Runtime |
| :--- | :--- | :--- |
| **Apxoh Core** | Local governance and verification engine on the developer's machine | Python 3.11+, CLI |
| **Apxoh Agent Governance** | Instructions, skills, and reference files that AI coding agents adopt | Markdown + YAML, agent-consumed |
| **Apxoh Assurance** | Independent verification, evidence collection, and release gating | Local CLI + CI |

**Central principle:** *Evidence Before Approval. Verification Before Release.*

The AI agent writes the software. **Apxoh verifies it.**

### 1.2 System Boundaries

**In scope:**
- The Apxoh repository (code, rules, schemas, documentation)
- The Apxoh CLI and engine
- Evidence artifacts produced by Apxoh
- Release gating decisions
- The contract with TSAR (delegated security authority)
- The eight model integrations and one platform integration defined by the architecture

**Out of scope (owned by other parties):**
- AI model providers (Anthropic, OpenAI, DeepSeek, Google, Meta, Alibaba, Moonshot)
- Platform providers (GitHub Copilot)
- Security scanners operated by TSAR or other external parties
- The projects Apxoh governs
- The human developer's local environment

Out-of-scope systems remain relevant at trust boundaries; their outputs and claims must not automatically be trusted.

### 1.3 Core Components

| Component | Path | Trust Level |
| :--- | :--- | :--- |
| Charter & Policy | `system/` | **High** — governs evaluation; changes require strong review |
| Rule Engine | `src/arkhon/rules/` | **High** — reads and evaluates rules |
| Verification Engine | `src/arkhon/verification/` | **High** — performs independent verification |
| Evidence Store | `src/arkhon/evidence/` and project-local `.arkhon/evidence/` | **High** — integrity-critical; tamper evidence must be enforced |
| Assessment Engine | `src/arkhon/assessment/` | **High** — produces assessment and release-gate decisions |
| Orchestrator | `src/arkhon/orchestrator/` | **Medium** — coordinates; must not override verification or gate decisions |
| Model Integrations | `src/arkhon/integrations/models/` | **Low** — external outputs are untrusted |
| Platform Integrations | `src/arkhon/integrations/platforms/` | **Low** — external outputs are untrusted |
| TSAR Integration | `src/arkhon/integrations/tsar/` | **Medium** — delegated authority; returned evidence is still validated |
| CLI | `src/arkhon/cli.py` | **High** — user-facing entry point and security-sensitive command boundary |

### 1.4 Data Flows

```text
Developer / AI Agent
        │
        ▼
   ┌─────────┐    writes     ┌──────────┐
   │  Code   │──────────────▶│ Project  │
   └─────────┘               └────┬─────┘
                                  │
                                  ▼
                          ┌──────────────┐
                          │ Apxoh Engine │
                          └──────┬───────┘
                                 │
              ┌──────────────────┼──────────────────┐
              ▼                  ▼                  ▼
        ┌──────────┐      ┌──────────┐      ┌──────────┐
        │  Rules   │      │   TSAR   │      │  Model   │
        │ Engine   │      │  (Sec.)  │      │ Adapters │
        └────┬─────┘      └────┬─────┘      └────┬─────┘
             │                 │                 │
             └────────┬────────┴────────┬────────┘
                      ▼                 ▼
                ┌──────────┐      ┌──────────┐
                │ Evidence │      │ Findings │
                └────┬─────┘      └────┬─────┘
                     │                 │
                     └────────┬────────┘
                              ▼
                      ┌──────────────┐
                      │  Assessment  │
                      └──────┬───────┘
                             ▼
                      ┌──────────────┐
                      │   Release    │
                      │   Decision   │
                      └──────────────┘
```

---

## 2. Assets

Assets are ordered by criticality. Compromise of a higher-tier asset can invalidate decisions that depend on it.

### 2.1 Rules (`rules/`, `languages/*/rules/`)

- **Why critical:** Rules define what "acceptable" means. A poisoned rule can allow unacceptable code to pass.
- **Owner:** Apxoh maintainers
- **Impact if compromised:** Governance bypass
- **Format:** YAML, validated against `schemas/rule.schema.json`

### 2.2 Evidence (`src/arkhon/evidence/`, `.arkhon/evidence/`)

- **Why critical:** Evidence is the basis for assessment and release decisions. Forged or stale evidence can lead to false approval.
- **Owner:** Apxoh Evidence Engine
- **Impact if compromised:** False release, production incident, loss of trust
- **Format:** Structured artifacts (including JSON where applicable), content hashes, commit identity and signatures where the signing and verification workflow is implemented and enabled

### 2.3 Gates (`system/policies/blocking/`, `src/arkhon/assessment/gates.py`)

- **Why critical:** Gates are the last line of defense before release. Bypassed gates defeat the assurance model.
- **Owner:** Apxoh maintainers
- **Impact if compromised:** Unsafe release
- **Format:** YAML policies + Python enforcement

### 2.4 Schemas (`schemas/`)

- **Why critical:** Schemas define valid rules, evidence, and findings. A weakened schema can allow invalid data to pass.
- **Owner:** Apxoh maintainers
- **Impact if compromised:** Systematic validation bypass
- **Format:** JSON Schema

### 2.5 Secrets & Keys

- **Why critical:** Signing identities, API tokens, and credentials protect evidence and integrations.
- **Owner:** Apxoh maintainers + CI system
- **Impact if compromised:** Impersonation, evidence forgery, data exfiltration
- **Format:** Environment variables, short-lived OIDC tokens, Sigstore identities and other credential stores as applicable

### 2.6 System Identity (`manifest/`, `VERSION`, package metadata)

- **Why critical:** Identity determines which version is trusted and which rules apply.
- **Owner:** Apxoh maintainers
- **Impact if compromised:** Version confusion, downgrade attacks
- **Format:** YAML, JSON, semantic version strings

### 2.7 Trust (`SECURITY.md`, `GOVERNANCE.md`, integration contracts)

- **Why critical:** Trust is foundational. If trust in Apxoh is lost, its decisions lose value.
- **Owner:** Apxoh maintainers
- **Impact if compromised:** Rejection of the system and its assurance claims
- **Format:** Markdown, YAML contracts

---

## 3. Actors

### 3.1 Human Developers

- **Trust level:** Medium
- **Capabilities:** Read/write access to project, run Apxoh CLI, propose or approve exceptions according to authorization policy
- **Motivation:** Ship working software
- **Risk:** Negligence, fatigue, pressure to release, compromised accounts

### 3.2 AI Agents (eight model integrations + GitHub Copilot platform integration)

- **Trust level:** Low (untrusted by default)
- **Capabilities:** Generate code, propose rules, invoke tools within granted scope
- **Motivation:** Complete the requested task
- **Risk:** Hallucination, prompt-injection susceptibility, hostile behavior, silent failure, overbroad tool use

### 3.3 External Tools (TSAR, scanners)

- **Trust level:** Medium (verified per contract)
- **Capabilities:** Scan code and produce findings or evidence
- **Motivation:** Report accurate findings
- **Risk:** Misconfiguration, stale versions, compromised upstream, incomplete coverage, forged or malformed output

### 3.4 Hostile Agents

- **Trust level:** None
- **Capabilities:** Any capability granted to an AI agent, plus deliberate attempts to misuse those capabilities
- **Motivation:** Bypass governance, exfiltrate data, cause damage
- **Risk:** All categories of attack

### 3.5 Insider Threats

- **Trust level:** Role-dependent; privileged actions must still be verified
- **Capabilities:** Depending on permissions, modify rules, approve exceptions, alter workflows or influence gates
- **Motivation:** Financial, ideological, coercion, negligence
- **Risk:** High-impact, potentially difficult-to-detect attacks

---

## 4. Trust Boundaries

Trust boundaries mark points where data crosses from lower trust to higher trust. Every crossing must be validated, and authorization must be checked separately from data validity.

### 4.1 Between Apxoh and Model Providers

- **Direction:** Apxoh → Provider (prompts, code or context) → Apxoh (responses)
- **Risk:** Provider receives sensitive code; provider returns poisoned, manipulated or misleading output
- **Control:** Minimize transmitted data; never include secrets in prompts; treat all provider responses as untrusted; independently verify generated outputs; document provider data handling and retention

### 4.2 Between Evidence Producer and Consumer

- **Direction:** Engine/tool → Evidence Store → Assessor → Decision
- **Risk:** Evidence is tampered with in transit or at rest, replayed, detached from its source, or presented for the wrong commit
- **Control:** SHA-256 per artifact; signature verification where signing is enabled; commit SHA binding; timestamp and freshness checks; schema validation; any integrity or provenance mismatch → `BLOCKED`

### 4.3 Between Agent and Engine

- **Direction:** Agent → Filesystem / tool interface → Engine
- **Risk:** Agent writes malicious code, modifies governance files, tampers with evidence, or invokes tools beyond intended scope
- **Control:** Enforce repository permissions and protected paths outside agent instructions; separate agent and verification identities; independently rerun tests and checks; do not rely on a read-only instruction alone as an access-control mechanism

### 4.4 Between Development and Production

- **Direction:** Local → CI → Release
- **Risk:** Local success does not establish production safety; CI configuration or build inputs may differ
- **Control:** Consistent verification profiles; controlled build environments; provenance generation and verification; release gates; reproducibility checks where supported

### 4.5 Between Repositories

- **Direction:** External repositories and registries → Apxoh build and runtime
- **Risk:** Supply-chain compromise through dependencies, build tools, GitHub Actions, artifacts or maintainer accounts
- **Control:** Exact dependency pins where appropriate; vulnerability auditing; SBOM generation; action pinning to reviewed commit SHAs; signature and provenance verification

---

## 5. STRIDE Threat Categories

Likelihood and impact ratings below are initial qualitative estimates. They must be revisited using operational evidence and the deployment context.

### 5.1 Spoofing (الانتحال)

| Threat | Impact | Likelihood |
| :--- | :--- | :--- |
| Agent impersonates a different agent | Medium | Medium |
| Attacker impersonates an Apxoh release | High | Low |
| Fake TSAR evidence is accepted | Critical | Medium |
| Forged or misleading author identity in commits | High | Medium |

### 5.2 Tampering (العبث)

| Threat | Impact | Likelihood |
| :--- | :--- | :--- |
| Rules modified to weaken governance | Critical | High |
| Evidence modified after generation | Critical | Medium |
| Schema modified to allow invalid data | Critical | Medium |
| Gate disabled in CI | Critical | Low |
| `.github/workflows/` modified maliciously | High | Medium |

### 5.3 Repudiation (الإنكار)

| Threat | Impact | Likelihood |
| :--- | :--- | :--- |
| Agent denies making a change | Medium | High |
| Developer denies approving an exception | Medium | Low |
| CI execution cannot be independently established | Low | Low |

### 5.4 Information Disclosure (كشف المعلومات)

| Threat | Impact | Likelihood |
| :--- | :--- | :--- |
| Secrets sent to model providers | Critical | Medium |
| Evidence contains sensitive project data | High | Medium |
| Rule files reveal security posture | Medium | High |
| Logs contain credentials or sensitive payloads | High | Medium |

### 5.5 Denial of Service (تعطيل الخدمة)

| Threat | Impact | Likelihood |
| :--- | :--- | :--- |
| Agent floods engine with malformed input | Medium | Medium |
| Malicious or pathological rule causes excessive evaluation | Medium | Low |
| CI resource exhaustion via large diffs or artifacts | Low | Medium |
| Model provider rate limiting or outage | Medium | High |

### 5.6 Elevation of Privilege (رفع الصلاحيات)

| Threat | Impact | Likelihood |
| :--- | :--- | :--- |
| Agent gains unauthorized write access to rules | Critical | Medium |
| Exception approval is bypassed | Critical | Low |
| CI token is leaked and reused | Critical | Low |
| Local administrator account or host is compromised | High | Low |

---

## 6. Attack Scenarios

### 6.1 Poisoned Rule

**Scenario:** An attacker (hostile agent or malicious contributor) submits a rule that appears legitimate but weakens governance — for example, a rule that exempts a specific file pattern from security checks.

**Impact:** Critical — silently allows unsafe code to pass.

**Mitigations:**
- Rule changes require review by designated maintainers and security reviewers; enforce this through repository permissions and CODEOWNERS where configured
- Rules must reference the charter section they enforce
- Rule validation checks exclusion scope and rejects unsafe or unjustified exclusions
- Periodic audit of exclusion patterns
- Negative test required for every security-critical rule
- Rule changes must be covered by reviewable test evidence

### 6.2 Tampered Evidence

**Scenario:** An agent modifies evidence files after generation, changing `FAIL` to `PASS` or altering finding severity.

**Impact:** Critical — false release approval.

**Mitigations:**
- Every evidence artifact has a SHA-256 digest stored in a separately protected or independently verifiable record
- Evidence signatures are verified when the signing workflow is enabled
- Evidence is bound to `commit_sha` and the relevant tool/version identity
- Verification recomputes hashes and validates signatures, schema, freshness and provenance
- Any mismatch or missing required evidence → `BLOCKED`, never implicit `PASS`

### 6.3 Bypassed Gate

**Scenario:** An agent or developer modifies a CI workflow, disables a check, or changes gate thresholds to allow a failing release.

**Impact:** Critical — unsafe release.

**Mitigations:**
- Protect `.github/workflows/` and gate policy paths with CODEOWNERS and branch protection where configured
- Run workflow static analysis (for example, zizmor) in CI
- Keep gate thresholds in `system/policies/blocking/` version-controlled
- Require explicit review and approval for modifications to blocking policies
- Review workflow permission scopes and ensure untrusted pull-request code cannot access privileged secrets
- Audit changes to required checks and branch protection settings

### 6.4 Prompt Injection

**Scenario:** Malicious content in a file, dependency, issue, or web page instructs the agent to bypass governance, leak secrets, or fabricate evidence.

**Impact:** High — depends on the instruction, agent privileges and available tools.

**Mitigations:**
- Agents must treat repository content, tool output and external content as untrusted data unless explicitly authenticated
- Governance instructions in `AGENTS.md` establish project policy but do not replace technical access controls
- Verification is independent: even if an agent is fooled, its claims are not accepted without evidence
- Prompt-injection handling requirements are documented in `docs/PROMPT_INJECTION.md`
- Do not place secrets in agent context; restrict tool permissions and outbound network access

### 6.5 Fake Approval

**Scenario:** An agent claims "tests pass" or "security verified" without actually running verification, or runs only a subset and claims completeness.

**Impact:** High — false release.

**Mitigations:**
- Apxoh accepts verifiable evidence, not unsupported claims
- Evidence identifies tools, versions, commands, scope and results
- Evidence is bound to `commit_sha` and timestamped
- Missing required evidence → `BLOCKED`, not `PASS`
- Independent rerun is part of the release gate where feasible
- CI run identifiers and logs are retained as supporting evidence

### 6.6 Secret Leakage

**Scenario:** Secrets are committed, sent to model providers, exposed in logs, or included in evidence artifacts.

**Impact:** Critical — credential compromise.

**Mitigations:**
- Run secret scanning in pre-commit and CI (for example, Gitleaks)
- Maintain ignore rules for generated credentials and local secret files; do not rely on ignore rules as a substitute for scanning
- Adapter safety tests check that secrets are not included in prompts or outputs
- Redact sensitive values from logs and evidence; avoid logging secret-bearing environment variables
- Run secret scanning on pushes and pull requests, with appropriate history scanning for incidents
- Rotate and revoke any exposed credential immediately

### 6.7 Supply Chain Attack

**Scenario:** A dependency is compromised, a GitHub Action is tampered with, a build artifact is replaced, or a maintainer account is hijacked.

**Impact:** Critical — arbitrary code execution in CI or user environments.

**Mitigations:**
- Pin runtime and development dependencies to reviewed versions; use hashes for locked installation workflows where supported
- Run dependency vulnerability auditing and maintain an SBOM
- Pin GitHub Actions to reviewed full commit SHAs, not mutable tags
- Audit workflows with zizmor and least-privilege token permissions
- Use OpenSSF Scorecard to monitor repository posture
- Generate SLSA provenance for releases and verify it before distribution
- Verify artifact signatures and provenance independently
- Review Dependabot updates before merging; automated updates are not automatically trusted

### 6.8 Hostile Agent

**Scenario:** A malicious or compromised AI agent actively attempts to undermine Apxoh — modifying rules, deleting tests, editing evidence, or exfiltrating data.

**Impact:** Critical — potential governance bypass.

**Mitigations:**
- See `SECURITY_AGENTS.md` for the agent-specific threat model and operating constraints
- Enforce governance-file protections using repository permissions and isolated workspaces; instructions alone are insufficient
- Separate agent execution identity from verification and release identities
- Require verifiable evidence and signature validation where signing is enabled
- Log agent tool actions and security-relevant changes where technically available
- Detect and review anomalous modifications to rules, schemas, policies and evidence
- Require human review for exceptions and critical decisions
- Restrict network access and secrets according to least privilege

---

## 7. Mitigations

The controls below are the target control set. Their presence in this table does not establish implementation or successful operation; verify each against the live repository and CI configuration.

### 7.1 Preventive Controls

| Control | Where | What it prevents |
| :--- | :--- | :--- |
| CODEOWNERS | `.github/CODEOWNERS` | Unauthorized changes to governance, where enforced by repository settings |
| Branch protection / rulesets | GitHub repository settings | Unreviewed direct changes to protected branches |
| Pre-commit hooks | `.pre-commit-config.yaml` | Secrets, private keys and malformed files, subject to configured hooks |
| Pinned dependencies | `pyproject.toml` and lock/constraints files | Unreviewed dependency drift |
| Adapter safety tests | `tests/security/adapter-safety/` | Selected unsafe adapter behaviors and secret leakage |
| Agent governance instructions | `AGENTS.md` and `agents/` | Policy guidance against prompt injection; not a hard security boundary |
| Artifact signing and verification | `tools/signing/sign-artifacts.py` | Detects artifact substitution when correctly configured and independently verified |

### 7.2 Detective Controls

| Control | Where | What it detects |
| :--- | :--- | :--- |
| zizmor | `.github/workflows/security.yml` | GitHub Actions workflow security issues |
| Gitleaks | Pre-commit + CI | Secrets in tracked content and commits within scan scope |
| pip-audit | CI | Known vulnerable Python dependencies |
| Trivy | CI | Configured filesystem, dependency or container vulnerabilities |
| OpenSSF Scorecard | `.github/workflows/scorecard.yml` | Repository security posture signals |
| Evidence hash verification | Verification engine | Evidence tampering |
| Commit SHA binding check | Evidence validator | Stale or mismatched evidence |

### 7.3 Corrective Controls

| Control | Where | Response |
| :--- | :--- | :--- |
| Automatic `BLOCKED` on missing required evidence | Verification / assessment engine | Block release and request re-audit |
| CI failure handling | GitHub Actions and release process | Stop promotion; investigate and remediate before retry |
| Incident response plan | `docs/VULNERABILITY_RESPONSE.md` | Structured response to vulnerabilities and incidents |
| Blameless postmortem | `docs/operations/POSTMORTEM_TEMPLATE.md` | Root-cause analysis and tracked corrective actions |

---

## 8. Residual Risks

### 8.1 What Apxoh Cannot Defend Against

- **Compromised provider:** If Anthropic, OpenAI or another provider is compromised, Apxoh cannot establish the provider's internal integrity. Independent verification can reduce reliance on provider claims, but does not guarantee detection of all malicious generated output.
- **Compromised maintainer or signing identity:** A privileged maintainer or compromised OIDC identity may authorize malicious changes or signatures. Mitigations include least privilege, protected environments, auditable identity policies, independent review and separation of duties.
- **Kernel-level rootkit on developer machine:** User-space Apxoh controls cannot reliably detect a compromised host kernel. This remains outside the product's direct security boundary.
- **Coordinated insider attack:** Multiple privileged insiders colluding may bypass controls. Mitigations include separation of duties, independent audit trails and multi-party review for high-impact changes.

### 8.2 Accepted Risks

The following are proposed risk dispositions and require explicit owner acceptance; they are not automatically accepted merely by appearing in this document.

| Risk | Rationale | Review date |
| :--- | :--- | :--- |
| Local development environment compromise | Outside Apxoh's direct enforcement boundary | Every release |
| Model provider policy or service changes | External provider dependency cannot be controlled by Apxoh | Every release |
| Timing side channels in signature verification | Residual risk of cryptographic and implementation dependencies; reassess with the signing design | 2027-01-01 |

### 8.3 Deferred Risks

| Risk | Reason for deferral | Target resolution |
| :--- | :--- | :--- |
| Full hardware security module (HSM) integration | Cost and operational complexity | Post-v1.0 |
| Formal verification of rule engine | Requires dedicated scope and expertise | Post-v1.0 |
| Multi-party signing for every release | Operational overhead | Reassess before v0.5 |

---

## 9. References

### Apxoh Documents
- `SECURITY.md` — vulnerability reporting
- `SECURITY_AGENTS.md` — hostile agent threat model
- `GOVERNANCE.md` — decision-making process
- `docs/SUPPLY_CHAIN.md` — supply chain policy
- `docs/PROMPT_INJECTION.md` — prompt-injection defenses
- `docs/EVIDENCE_INTEGRITY.md` — evidence integrity model
- `docs/DEPENDENCY_POLICY.md` — dependency management

### External Standards
- STRIDE — Microsoft threat-modeling methodology
- ISO/IEC 27001:2022 — Annex A (organizational and other control themes)
- NIST SP 800-218 — Secure Software Development Framework (SSDF)
- OWASP ASVS 5.0.0 — architecture and security verification requirements
- OWASP SAMM 2.0 — governance
- SLSA 1.0 — software supply-chain levels
- OpenSSF Scorecard — repository security posture

---

**End of Threat Model**
