# Apxoh System Overview

**Version:** 1.0
**Status:** Active
**Last updated:** 2026-11-01

---

## 1. What Apxoh Is

Apxoh is a **Software Engineering Governance & Assurance System**.

It exists to answer one question with verifiable evidence:

> *Is this software actually ready to be trusted with real users?*

Not with opinion. Not with a claim. With evidence.

---

## 2. The Central Principle

> **Evidence Before Approval. Verification Before Release.**
> **No approval without evidence. No release without verification.**
> **No trust without testing. No claim without proof.**

---

## 3. The Three Products

| Product | Role |
| :--- | :--- |
| **Apxoh Core** | Local governance and verification engine (Python, CLI) |
| **Apxoh Agent Governance** | Instructions and skills for AI coding agents |
| **Apxoh Assurance** | Independent verification, evidence, release gating |

All three live in one repository, share one manifest, and obey one charter.

---

## 4. The Six Layers

```
┌────────────────────────────────────────────────────┐
│ 6. Integration   — models, platform, TSAR, generic │
├────────────────────────────────────────────────────┤
│ 5. Assessment    — gates + scoring + decision      │
├────────────────────────────────────────────────────┤
│ 4. Evidence      — signed, hashed, commit-bound    │
├────────────────────────────────────────────────────┤
│ 3. Verification  — independent runs, no trust      │
├────────────────────────────────────────────────────┤
│ 2. Lifecycle     — 10 stages, each with a gate     │
├────────────────────────────────────────────────────┤
│ 1. Governance    — charter, rules, policies        │
└────────────────────────────────────────────────────┘
```

Each layer is deterministic. Each layer trusts the layer above only
after verification. No layer trusts an AI agent.

---

## 5. The 10 Lifecycle Stages

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

A stage cannot be entered until its predecessor's exit criteria are met
with evidence.

---

## 6. The 11 Integrations

### 6.1 Models (8)
- Claude (Anthropic)
- OpenAI o (OpenAI)
- DeepSeek-Coder (DeepSeek)
- GPT (OpenAI)
- Gemini (Google)
- Code Llama (Meta)
- Qwen-Coder (Alibaba)
- Kimi (Moonshot)

### 6.2 Platforms (1)
- GitHub Copilot

### 6.3 Security (1)
- TSAR (delegated security authority)

### 6.4 Generic (1)
- Generic agents (fallback)

---

## 7. The 9 Languages

Python, JavaScript, TypeScript, Java, C#, C++, Go, Rust, Ruby.

Apxoh itself is Python. The other languages are **verified**, not executed.

---

## 8. The Score

| Domain | Weight |
| :--- | ---: |
| Requirements | 15 |
| Architecture & Code Quality | 10 |
| Testing & QA | 15 |
| Security | 20 |
| Performance | 10 |
| Reliability | 10 |
| Scalability | 10 |
| Documentation, Deployment & Maintenance | 10 |
| **Total** | **100** |

| Score | Level |
| :--- | :--- |
| 95–100 | Hyperscale Validated |
| 90–94 | Enterprise Grade |
| 80–89 | Production Ready |
| 70–79 | Controlled Release |
| < 70 | Development |

A critical gate failure rejects the release regardless of score.

---

## 9. The Security Authority: TSAR

All security decisions are delegated to TSAR:

- Vulnerability scanning
- Cryptographic audit
- Secret scanning
- ASVS compliance
- Dependency vulnerabilities

If TSAR is unavailable, the security gate is `BLOCKED`. Never `PASS`.

Contract: `integrations/tsar/contract.yaml`

---

## 10. The Evidence Model

Every claim requires evidence:

- Bound to a specific commit SHA
- Timestamped
- SHA-256 hashed
- Signed with sigstore (for gate-closing evidence)
- Fresh (within a defined window)

Tampered evidence → gate `BLOCKED` → incident → human review.

---

## 11. What Apxoh Is Not

- Not a prompt library.
- Not a linter.
- Not a replacement for human engineering judgment.
- Not a certificate from any standards body.

Apxoh is a governance and assurance layer between AI-generated code
and production release.

---

## 12. The One-Sentence Summary

Apxoh ensures that **no software is released without evidence, no
evidence is accepted without verification, and no verification happens
without independence.**

---

**End of Document**
