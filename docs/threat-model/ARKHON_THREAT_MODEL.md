# Apxoh Threat Model

**Version:** 1.0
**Status:** Active
**Owner:** Security Lead (TBD)
**Last reviewed:** 2026-11-01
**Review cadence:** Every minor release, and after any security incident

---

## 1. System Overview

### 1.1 The Three Products

| Product | Role | Runtime |
| :--- | :--- | :--- |
| **Apxoh Core** | Local governance and verification engine | Python 3.11+, CLI |
| **Apxoh Agent Governance** | Instructions and skills for AI coding agents | Markdown + YAML |
| **Apxoh Assurance** | Independent verification, evidence, release gating | Local CLI + CI |

**Central principle:** *Evidence Before Approval. Verification Before Release.*

### 1.2 System Boundaries

**In scope:**
- The Apxoh repository (code, rules, schemas, documentation)
- The Apxoh CLI and engine
- Evidence artifacts produced by Apxoh
- Release gating decisions
- The contract with TSAR (delegated security authority)
- The 8 model integrations and 1 platform integration

**Out of scope:**
- AI model providers (Anthropic, OpenAI, DeepSeek, Google, Meta, Alibaba, Moonshot)
- Platform providers (GitHub Copilot)
- Security scanners (owned by TSAR)
- The projects Apxoh governs
- The human developer's local environment

### 1.3 Core Components

| Component | Path | Trust Level |
| :--- | :--- | :--- |
| Charter & Policy | `system/` | **High** |
| Rule Engine | `src/arkhon/rules/` | **High** |
| Verification Engine | `src/arkhon/verification/` | **High** |
| Evidence Store | `src/arkhon/evidence/` | **High** |
| Assessment Engine | `src/arkhon/assessment/` | **High** |
| Orchestrator | `src/arkhon/orchestrator/` | **Medium** |
| Model Integrations | `src/arkhon/integrations/models/` | **Low** |
| Platform Integrations | `src/arkhon/integrations/platforms/` | **Low** |
| TSAR Integration | `src/arkhon/integrations/tsar/` | **Medium** |

### 1.4 Data Flows

```
Developer / AI Agent
        │ writes code
        ▼
   ┌─────────┐
   │ Project │
   └────┬────┘
        │ `arkhon verify`
        ▼
   ┌──────────────┐
   │ Verification │ ← runs pytest, ruff, mypy, TSAR
   │   Engine     │
   └──────┬───────┘
          │ produces
          ▼
   ┌──────────────┐
   │   Evidence   │ ← SHA-256, sigstore, commit-bound
   │    Store     │
   └──────┬───────┘
          │ `arkhon assess`
          ▼
   ┌──────────────┐
   │  Assessment  │ ← score, gates, decision
   │   Engine     │
   └──────┬───────┘
          │ `arkhon report`
          ▼
   ┌──────────────┐
   │    Report    │ ← JSON + Markdown
   └──────────────┘
```

---

## 2. Assets

### 2.1 Rules (`rules/`, `languages/*/rules/`)

- **Why critical:** Rules define what "acceptable" means.
- **Impact if compromised:** Complete governance bypass.
- **Format:** YAML, validated against `schemas/rule.schema.json`.

### 2.2 Evidence (`evidence/`, `.arkhon/evidence/`)

- **Why critical:** Evidence is the basis for every release decision.
- **Impact if compromised:** False release, production incident, loss of trust.
- **Format:** JSON, signed with sigstore, bound to commit SHA.

### 2.3 Gates (`policies/blocking/`, `src/arkhon/assessment/gates.py`)

- **Why critical:** Last line of defense before release.
- **Impact if compromised:** Unsafe release.
- **Format:** YAML policies + Python enforcement.

### 2.4 Schemas (`schemas/`)

- **Why critical:** Define what valid rules, evidence, and findings look like.
- **Impact if compromised:** Systematic validation bypass.
- **Format:** JSON Schema.

### 2.5 Secrets & Keys

- **Why critical:** Signing keys, API tokens, credentials.
- **Impact if compromised:** Impersonation, evidence forgery, data exfiltration.
- **Format:** Environment variables, OIDC tokens, sigstore identities.

### 2.6 System Identity (`manifest/`, `VERSION`, package metadata)

- **Why critical:** Identity determines which version is trusted.
- **Impact if compromised:** Version confusion, downgrade attacks.
- **Format:** YAML, JSON, semantic version strings.

### 2.7 Trust (`SECURITY.md`, `GOVERNANCE.md`, integration contracts)

- **Why critical:** Trust is the foundation. If trust is lost, decisions are worthless.
- **Impact if compromised:** Total system rejection.
- **Format:** Markdown, YAML contracts.

---

## 3. Actors

| Actor | Trust Level | Capabilities | Risk |
| :--- | :--- | :--- | :--- |
| Human developers | Medium | Read/write project, run CLI | Negligence, pressure |
| AI agents (8 models) | Low (untrusted) | Generate code, propose rules | Hallucination, injection, hostile |
| External tools (TSAR) | Medium (verified) | Scan code, produce evidence | Misconfiguration, stale |
| Hostile agents | None | All AI capabilities + deliberate misbehavior | Bypass, exfiltration |
| Insider threats | High (by role) | Modify rules, approve exceptions | Financial, ideological |

---

## 4. Trust Boundaries

### 4.1 Between Apxoh and Model Providers

- **Direction:** Apxoh → Provider → Apxoh
- **Risk:** Provider sees sensitive code; provider returns poisoned output
- **Control:** No secrets in prompts; treat all responses as untrusted; verify outputs independently

### 4.2 Between Evidence Producer and Consumer

- **Direction:** Engine → Store → Assessor → Decision
- **Risk:** Evidence tampered in transit or at rest
- **Control:** SHA-256 per artifact; sigstore signing; commit SHA binding; freshness check

### 4.3 Between Agent and Engine

- **Direction:** Agent → Filesystem → Engine
- **Risk:** Agent writes malicious code or modifies governance files
- **Control:** Read-only governance files; separate verification identity; independent tests

### 4.4 Between Development and Production

- **Direction:** Local → CI → Release
- **Risk:** Local success ≠ production safety
- **Control:** Same verification in both environments; reproducible builds; SLSA provenance

### 4.5 Between TSAR and Apxoh

- **Direction:** Apxoh → TSAR → Apxoh
- **Risk:** TSAR compromised; evidence forged or tampered
- **Control:** Full evidence verification (commit match, freshness, version, hashes, required rules); fail-closed on any check

---

## 5. STRIDE Threat Categories

### 5.1 Spoofing

| Threat | Impact | Likelihood |
| :--- | :--- | :--- |
| Agent impersonates another agent | Medium | Medium |
| Attacker impersonates Apxoh release | High | Low |
| Fake TSAR evidence | Critical | Medium |
| Forged user identity in commits | High | Medium |

### 5.2 Tampering

| Threat | Impact | Likelihood |
| :--- | :--- | :--- |
| Rules modified to weaken governance | Critical | High |
| Evidence modified after generation | Critical | Medium |
| Schema modified to allow invalid data | Critical | Medium |
| Gate disabled in CI | Critical | Low |
| `.github/workflows/` modified | High | Medium |

### 5.3 Repudiation

| Threat | Impact | Likelihood |
| :--- | :--- | :--- |
| Agent denies making a change | Medium | High |
| Developer denies approving exception | Medium | Low |

### 5.4 Information Disclosure

| Threat | Impact | Likelihood |
| :--- | :--- | :--- |
| Secrets sent to model providers | Critical | Medium |
| Evidence contains sensitive data | High | Medium |
| Logs contain credentials | High | Medium |

### 5.5 Denial of Service

| Threat | Impact | Likelihood |
| :--- | :--- | :--- |
| Agent floods engine with malformed input | Medium | Medium |
| Malicious rule causes infinite loop | Medium | Low |
| Model provider rate limiting | Medium | High |

### 5.6 Elevation of Privilege

| Threat | Impact | Likelihood |
| :--- | :--- | :--- |
| Agent gains write access to rules | Critical | Medium |
| Exception approval bypassed | Critical | Low |
| CI token leaked and reused | Critical | Low |

---

## 6. Attack Scenarios

### 6.1 Poisoned Rule

**Scenario:** Attacker submits a rule that appears legitimate but weakens governance.

**Impact:** Critical.

**Mitigation:** `CODEOWNERS` review; rule must reference charter; `scope.exclude` audited; negative test required.

### 6.2 Tampered Evidence

**Scenario:** Agent modifies evidence files after generation.

**Impact:** Critical.

**Mitigation:** SHA-256; sigstore signing; commit binding; verification recomputes; mismatch → `BLOCKED`.

### 6.3 Bypassed Gate

**Scenario:** Agent or developer modifies CI workflow or gate thresholds.

**Impact:** Critical.

**Mitigation:** `.github/workflows/` protected by `CODEOWNERS`; `zizmor` audits; thresholds in version control; post-merge self-audit.

### 6.4 Prompt Injection

**Scenario:** Malicious content instructs agent to bypass governance or leak secrets.

**Impact:** High.

**Mitigation:** Instruction hierarchy in `AGENTS.md`; independent verification; injection detection; no secrets in context.

### 6.5 Fake Approval

**Scenario:** Agent claims "tests pass" without running them.

**Impact:** High.

**Mitigation:** Evidence required; named tools with versions; commit-bound; missing evidence → `BLOCKED`.

### 6.6 Secret Leakage

**Scenario:** Secrets committed, sent to providers, or logged.

**Impact:** Critical.

**Mitigation:** `gitleaks`; `.gitignore` patterns; adapter safety tests; no logging of `*_key`, `*_token`; secret scanning on every push.

### 6.7 Supply Chain Attack

**Scenario:** Dependency compromised; GitHub Action tampered; maintainer hijacked.

**Impact:** Critical.

**Mitigation:** Pinned deps; `pip-audit`; `Dependabot`; Actions pinned to SHA; `zizmor`; `scorecard`; SLSA; sigstore.

### 6.8 Hostile Agent

**Scenario:** Malicious agent attempts to undermine Apxoh.

**Impact:** Critical.

**Mitigation:** See `SECURITY_AGENTS.md`. Read-only governance; separate signing identity; sigstore evidence; all actions logged; anomaly detection; human review.

### 6.9 TSAR Compromise

**Scenario:** TSAR binary or output is compromised or replaced.

**Impact:** Critical.

**Mitigation:** TSAR output is verified end-to-end (commit, freshness, version, hashes, required rules); any mismatch → `BLOCKED`; sigstore-signed TSAR releases (future).

### 6.10 Stale Evidence Replay

**Scenario:** Attacker replays old evidence from a previous commit.

**Impact:** High.

**Mitigation:** Commit SHA binding; freshness window; sigstore signature covers commit SHA; any mismatch → `BLOCKED`.

---

## 7. Mitigations

### 7.1 Preventive

| Control | Where | Prevents |
| :--- | :--- | :--- |
| `CODEOWNERS` | `.github/` | Unauthorized governance changes |
| Branch protection | GitHub | Direct pushes to `main` |
| `pre-commit` hooks | `.pre-commit-config.yaml` | Secrets, private keys, syntax |
| Pinned dependencies | `pyproject.toml` | Supply chain drift |
| Adapter safety tests | `tests/security/adapter-safety/` | Secrets in prompts, unapproved domains |
| Instruction hierarchy | `AGENTS.md` | Prompt injection |
| Signed evidence | `tools/signing/sign-artifacts.py` | Tampered evidence |

### 7.2 Detective

| Control | Where | Detects |
| :--- | :--- | :--- |
| `zizmor` | `security.yml` | Workflow security issues |
| `gitleaks` | pre-commit + CI | Secrets in commits |
| `pip-audit` | CI | Vulnerable dependencies |
| `trivy` | CI | Filesystem vulnerabilities |
| `scorecard` | `scorecard.yml` | Repository posture |
| Evidence hash verification | Engine | Tampered evidence |
| Commit SHA binding check | Engine | Stale evidence |

### 7.3 Corrective

| Control | Where | Response |
| :--- | :--- | :--- |
| Automatic `BLOCKED` | Engine | Block release, request re-audit |
| Automatic revert | GitHub Actions | Revert merge, notify |
| Incident response | `docs/VULNERABILITY_RESPONSE.md` | Structured response |
| Blameless postmortem | `docs/operations/POSTMORTEM_TEMPLATE.md` | Root cause analysis |

---

## 8. Residual Risks

### 8.1 What Apxoh Cannot Defend Against

- **Compromised provider:** Verification is independent; a compromised provider cannot forge signed evidence.
- **Compromised maintainer:** sigstore requires OIDC; multiple maintainers for critical changes.
- **Kernel-level rootkit:** Out of scope.
- **Coordinated insider attack:** Separation of duties; audit trail.

### 8.2 Accepted Risks

| Risk | Rationale | Review date |
| :--- | :--- | :--- |
| Local environment compromise | Outside Apxoh's scope | Every release |
| Provider policy changes | Cannot control external providers | Every release |
| Timing side channels | sigstore limitation | 2027-01-01 |

### 8.3 Deferred Risks

| Risk | Reason | Target |
| :--- | :--- | :--- |
| HSM integration | Cost/complexity | Post-v1.0 |
| Formal verification | Time | Post-v1.0 |
| Multi-party signing | Operational overhead | v0.5 |

---

## 9. References

### Apxoh Documents
- `SECURITY.md` — vulnerability reporting
- `SECURITY_AGENTS.md` — hostile agent threat model
- `GOVERNANCE.md` — decision-making
- `docs/SUPPLY_CHAIN.md` — supply chain policy
- `docs/PROMPT_INJECTION.md` — prompt injection defenses
- `docs/EVIDENCE_INTEGRITY.md` — evidence integrity
- `docs/DEPENDENCY_POLICY.md` — dependency management
- `integrations/tsar/contract.yaml` — TSAR contract

### External Standards
- STRIDE (Microsoft)
- ISO/IEC 27001:2022 — Annex A.5
- NIST SP 800-218 (SSDF)
- OWASP ASVS 5.0.0 — V1 (Architecture)
- OWASP SAMM 2.0 — Governance
- SLSA 1.0
- OpenSSF Scorecard

---

**End of Threat Model**
