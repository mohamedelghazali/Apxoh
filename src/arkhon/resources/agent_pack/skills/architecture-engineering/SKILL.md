---
name: architecture-engineering
description: >
  Design software architecture, document decisions, and produce a threat
  model. Ensures the architecture satisfies requirements and is defensible.
version: 1.0.0
applicable_to: [all-projects]
requires: [arkhon-governance, requirements-engineering]
---

# Architecture Engineering Skill

## Purpose

Architecture is the set of decisions that are expensive to change later.
This skill ensures those decisions are made deliberately, documented, and
defensible against requirements.

## Mandatory Rules

1. Every significant architectural decision must be recorded in an ADR (Architecture Decision Record).
2. Every component must have a single, documented responsibility.
3. Trust boundaries must be explicitly identified.
4. A threat model must exist before implementation begins.
5. No component may be introduced without a documented interface.
6. Circular dependencies are forbidden.

## Process

```
Analyze Requirements  →  Identify Constraints  →  Sketch Options  →  Choose  →  Document  →  Threat Model  →  Review
```

## What an ADR Contains

- **Title:** short, imperative
- **Status:** proposed / accepted / rejected / superseded
- **Context:** what problem we are solving
- **Decision:** what we chose
- **Consequences:** what becomes easier, what becomes harder
- **Alternatives considered:** what we rejected, and why

## Threat Model Requirements

A threat model must include:

- Assets (what must be protected)
- Actors (who can interact)
- Trust boundaries (where data crosses trust levels)
- Threats categorized (STRIDE or equivalent)
- Mitigations per threat
- Residual risks

## Evidence Required

- `architecture-decision-records` — one per major decision
- `threat-model` — with all sections populated
- `component-diagram` — visual or textual

## Interaction with Apxoh

- Rule domain: `architecture`
- Gate: `architecture_gate`
- Evidence type: `architecture-review`, `threat-model`
- Output goes to `.arkhon/evidence/architecture/`

## Reference

- `docs/threat-model/ARKHON_THREAT_MODEL.md` — example threat model
- `system/charter/ENGINEERING_CHARTER.md` — principles 2, 9

## Version History

- 1.0.0 (2026-11-01): Initial release.
