---
name: requirements-engineering
description: >
  Extract, refine, and verify software requirements. Ensures every
  requirement has a measurable acceptance criterion before implementation.
version: 1.0.0
applicable_to: [all-projects]
requires: [arkhon-governance]
---

# Requirements Engineering Skill

## Purpose

Turn vague intentions into verifiable requirements. A requirement without
an acceptance criterion is not a requirement — it is a wish.

## Mandatory Rules

1. Every functional requirement must have at least one measurable acceptance criterion.
2. Requirements must be traceable to a business goal or a regulation.
3. Conflicting requirements must be resolved before design begins.
4. Non-functional requirements must specify a metric and a threshold.
5. No requirement may be marked "done" without evidence of verification.

## Process

```
Collect  →  Clarify  →  Specify  →  Validate  →  Baseline  →  Track
```

## What a Good Requirement Looks Like

- **Bad:** "The system should be fast."
- **Good:** "The API must return P95 latency ≤ 200ms under 1000 RPS for the search endpoint."

- **Bad:** "Login should be secure."
- **Good:** "Login must enforce ≥12-character passwords, reject the top 10,000 common passwords, and lock the account after 5 failed attempts in 15 minutes."

## Evidence Required

- A `requirements-register` artifact with all requirements and their acceptance criteria.
- A `validation-report` confirming that no requirement is unverified.
- Cross-references to the design and tests that satisfy each requirement.

## Interaction with Apxoh

- Rule domain: `requirements`
- Gate: `requirements_gate`
- Evidence type: `requirements-register`, `validation-report`
- Output goes to `.arkhon/evidence/requirements/`

## Reference

- `schemas/rule.schema.json` — how requirements rules are defined
- `rules/requirements/SE-REQ-001-verifiable-requirements.yaml` — example rule
- `system/charter/ENGINEERING_CHARTER.md` — principle 1

## Version History

- 1.0.0 (2026-11-01): Initial release.
