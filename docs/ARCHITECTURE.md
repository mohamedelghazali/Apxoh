# Apxoh Architecture

**Version:** 1.0
**Status:** Active
**Last updated:** 2026-11-01

This document is the quick entry point for understanding Apxoh's architecture. Deep details live in `docs/architecture/`.

---

## The 30-Second Overview

Apxoh is a **software engineering governance and assurance system**.

It sits between AI-generated code and production release.

```
AI Agent  →  writes code  →  Apxoh verifies  →  Release decision
```

The agent produces. Apxoh decides.

---

## The Three Products

| Product | What it does | Where |
| :--- | :--- | :--- |
| **Core** | Runs rules, evaluates policies, verifies evidence | `src/arkhon/` |
| **Agent Governance** | Tells AI agents how to behave under Apxoh | `AGENTS.md`, `skills/`, `agents/`, `integrations/` |
| **Assurance** | Independent verification and release gating | `src/arkhon/verification/`, `src/arkhon/assessment/` |

---

## The Six Layers

```
┌──────────────────────────────────────────┐
│ 6. Integration    (11 integrations)      │  ← models, platform, TSAR, generic
├──────────────────────────────────────────┤
│ 5. Assessment     (gates + scoring)      │  ← release decision
├──────────────────────────────────────────┤
│ 4. Evidence       (signed, hashed)       │  ← integrity chain
├──────────────────────────────────────────┤
│ 3. Verification   (independent runs)     │  ← re-runs everything
├──────────────────────────────────────────┤
│ 2. Lifecycle      (10 stages)            │  ← orchestrator
├──────────────────────────────────────────┤
│ 1. Governance     (charter + rules)      │  ← the highest authority
└──────────────────────────────────────────┘
```

---

## The Core Principle

> **Evidence Before Approval. Verification Before Release.**

Translated to architecture:

- **Governance** (Layer 1) defines what "good" means.
- **Verification** (Layer 3) proves whether the code meets it.
- **Evidence** (Layer 4) records the proof.
- **Assessment** (Layer 5) uses evidence to decide.
- **Integration** (Layer 6) plugs in external authorities (TSAR for security, models for agents).

No layer trusts the layer above. Each verifies independently.

---

## The Security Authority: TSAR

Apxoh delegates all **security, vulnerability, encryption, and hardening** decisions to **TSAR**:

| Apxoh decides | TSAR decides |
| :--- | :--- |
| *When* security must be verified | *How* security is verified |
| *Whether* evidence closes a gate | *What* the evidence says |
| *What* to do if TSAR is unavailable | *Which* tools to run |

If TSAR is unavailable → security gate is `BLOCKED`, never `PASS`.

Contract: `integrations/tsar/contract.yaml`
Threat model: `docs/threat-model/ARKHON_THREAT_MODEL.md` §4.2

---

## The 8 Model Integrations

Apxoh supports these AI models:

| Model | Provider | Governance injection |
| :--- | :--- | :--- |
| Claude | Anthropic | system prompt |
| OpenAI o | OpenAI | system prompt |
| DeepSeek-Coder | DeepSeek | system prompt |
| GPT | OpenAI | system prompt |
| Gemini | Google | system prompt |
| Code Llama | Meta | plain-text delimited |
| Qwen-Coder | Alibaba | plain-text delimited |
| Kimi | Moonshot | system prompt |

Plus **GitHub Copilot** as a platform (uses GPT, o, Claude internally; verification capped at `configured`).

Registry: `manifest/integrations.yaml`

---

## The 9 Languages

Apxoh analyzes and verifies projects written in:

Python, JavaScript, TypeScript, Java, C#, C++, Go, Rust, Ruby.

Apxoh's engine is Python; the target languages are verified, not executed.

Registry: `languages/registry.yaml`, `manifest/languages.yaml`

---

## The 10 Lifecycle Stages

```
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
```

Each stage has entry criteria, exit criteria, and a gate. No stage can be skipped without a documented exception.

---

## The 5 Verification Levels

Used to describe how deeply Apxoh has verified an integration:

| Level | Meaning |
| :--- | :--- |
| Installed | Files present |
| Discoverable | Agent can locate skills |
| Activated | Instructions loaded |
| Configured | Agent bound to Apxoh |
| Verified | Behavioral verification passed |

Only `Verified` proves the agent obeys Apxoh. Copilot's max is `Configured`.

---

## Directory Map

| Directory | Purpose |
| :--- | :--- |
| `src/arkhon/` | Engine code |
| `system/` | Charter, policies, governance model |
| `rules/` | Engineering rules (global) |
| `languages/` | Per-language rules and profiles |
| `integrations/` | Model, platform, TSAR, generic integrations |
| `skills/` | Reusable capabilities for AI agents |
| `agents/` | Role bindings (roles → skills) |
| `projects/` | Project-type profiles |
| `schemas/` | JSON Schemas (contracts) |
| `manifest/` | System identity and registries |
| `tools/` | External tool bindings + signing |
| `tests/` | Test suite |
| `docs/` | Documentation |
| `.arkhon/` | Apxoh's own governance state |
| `.github/` | CI workflows, CODEOWNERS, dependabot |

---

## Where to Go Next

| If you want to know… | Read… |
| :--- | :--- |
| The threats Apxoh defends against | `docs/threat-model/ARKHON_THREAT_MODEL.md` |
| How Apxoh treats AI agents | `SECURITY_AGENTS.md` |
| Supply chain policy | `docs/SUPPLY_CHAIN.md` |
| How to write a rule | `docs/rule-authoring/HOW_TO_WRITE_A_RULE.md` |
| How to add an integration | `docs/integrations/` |
| How evidence is stored and verified | `docs/EVIDENCE_INTEGRITY.md` |
| The release decision model | `reports/templates/engineering-quality/` |
| How to contribute | `CONTRIBUTING.md` |
| How Apxoh governs itself | `.arkhon/project.yaml` |

---

## The One-Sentence Summary

Apxoh ensures that **no software is released without evidence, no evidence is accepted without verification, and no verification happens without independence.**
