# Apxoh System Overview

**Version:** 1.1  
**Status:** Active  
**Last updated:** 2026-11-02

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
| **Apxoh Agent Governance** | Instructions, skills, and integration guidance for AI coding agents |
| **Apxoh Assurance** | Independent verification, evidence evaluation, and release gating |

All three are defined in the same repository and share the engineering charter and manifest. Their implementation status must be assessed from code and execution evidence, not from this product description alone.

---

## 4. Working User Personas

These are working product-planning personas derived from the current product scope. They are not claims of completed user research or validated market segmentation.

| Persona | Primary need | Apxoh touchpoint |
| :--- | :--- | :--- |
| **Software developer / maintainer** | Understand requirements, run local checks, resolve findings, and prepare changes | Apxoh Core, rules, CLI, reports |
| **AI coding agent** | Discover project rules, follow role/skill guidance, and provide work that can be independently checked | Agent Governance, skills, agent integrations |
| **Reviewer / software architect** | Evaluate requirements, design decisions, code changes, and supporting evidence | ADRs, rule catalog, review workflows |
| **Assurance / release decision-maker** | Determine whether required checks and evidence support a release decision | Verification, evidence, assessment, gates |
| **Security reviewer / integration operator** | Configure and review delegated security checks and their evidence | TSAR integration contract, security gates, incident procedures |

AI agents are governed participants, not trusted approvers. An agent's assertion that work is complete is not a substitute for independent verification.

These personas should be reviewed using feedback from actual users and revised when the product scope changes.

---

## 5. The Six Layers

~~~text
┌────────────────────────────────────────────────────┐
│ 6. Integration   — models, platforms, TSAR, generic │
├────────────────────────────────────────────────────┤
│ 5. Assessment    — gates + scoring + decision      │
├────────────────────────────────────────────────────┤
│ 4. Evidence      — collected, hashed, commit-bound │
├────────────────────────────────────────────────────┤
│ 3. Verification  — tool execution and review       │
├────────────────────────────────────────────────────┤
│ 2. Lifecycle     — 10 stages and defined criteria  │
├────────────────────────────────────────────────────┤
│ 1. Governance    — charter, rules, policies        │
└────────────────────────────────────────────────────┘
~~~

This is a logical architecture view. Not every layer or control is fully automated. Human review remains required where rules or policies specify it. Evidence hashing and commit binding do not, by themselves, prove who produced an artifact or establish a trusted signature.

---

## 6. The 10 Lifecycle Stages

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

A stage transition is subject to the criteria implemented for that stage. The presence of a lifecycle definition does not prove that every organizational handoff is automated.

---

## 7. Declared Integrations

The manifest currently declares eight model integrations, one platform integration, one delegated security authority, and one generic fallback category. The repository also contains agent/editor integration packages. These are distinct catalog and implementation views; neither should be interpreted as proof that every provider or adapter has passed behavioral verification.

### 7.1 Model integrations declared in the manifest
- Claude (Anthropic)
- OpenAI o (OpenAI)
- DeepSeek-Coder (DeepSeek)
- GPT (OpenAI)
- Gemini (Google)
- Code Llama (Meta)
- Qwen-Coder (Alibaba)
- Kimi (Moonshot)

### 7.2 Platform
- GitHub Copilot

### 7.3 Delegated security authority
- TSAR, for security checks specified by the integration contract.

### 7.4 Generic fallback
- Generic agent integration material.

If TSAR or required evidence is unavailable, the applicable required security gate must remain BLOCKED, not PASS.

---

## 8. The 9 Declared Languages

Python, JavaScript, TypeScript, Java, C#, C++, Go, Rust, and Ruby.

Apxoh's engine is Python. The language registry declares supported targets, but registry presence alone does not prove that every profile, external toolchain, or fixture has been fully implemented and executed.

---

## 9. The Score

The scoring model and thresholds are defined by the active configuration and policy. Any displayed weights or levels must be checked against the code and profile used for a particular assessment. A critical gate failure must not be overridden by a high numeric score.

---

## 10. The Security Authority: TSAR

Security checks delegated by the Apxoh integration contract are handled by TSAR. The documented scope includes vulnerability scanning, cryptographic audit, secret scanning, ASVS-related evidence, and dependency vulnerability checks, subject to the current contract.

The repository contains an adapter, verifier, and proposed contract. Their presence does not prove that an external TSAR installation is available in a deployment. If the required authority or its evidence is unavailable, the relevant security gate is BLOCKED.

Contract: integrations/tsar/contract.yaml

---

## 11. The Evidence Model

The evidence implementation and design distinguish integrity from authenticity:

- Evidence can identify a target commit.
- Artifact digests can be calculated and checked.
- Evidence timestamps can be evaluated against freshness policy.
- Signing and signer-identity verification must only be claimed when a configured signer and independent verification have actually run successfully.

A digest detects a mismatch against recorded bytes; it does not establish who produced the evidence or whether the evidence is truthful. Missing or invalid required evidence must not produce PASS.

---

## 12. What Apxoh Is Not

- Not a prompt library.
- Not a linter alone.
- Not a replacement for human engineering judgment.
- Not a certificate from any standards body.

Apxoh is intended to provide a governance and assurance layer between software development—including AI-assisted development—and production release.

---

## 13. The One-Sentence Summary

Apxoh aims to ensure that **software release decisions are supported by evidence, that evidence is independently checked, and that missing verification is not mistaken for success.**

---

**End of Document**
