---
name: arkhon-governance
description: >
  Apply the Apxoh software engineering governance charter throughout
  software planning, implementation, verification, maintenance, and release.
  Use this skill when writing, modifying, reviewing, or verifying code in a
  project governed by Apxoh.
version: 1.0.0
applicable_to: [all-projects]
requires: [arkhon-core]
---

# Apxoh Governance Skill

## Mandatory Operating Principles

1. Read the applicable engineering charter before acting.
2. Identify the project profile before proposing changes.
3. Load only the engineering rules that apply to the task.
4. Analyze the impact of proposed changes before modifying files.
5. Do not claim successful verification without evidence.
6. Run required independent checks after changes when authorized and available.
7. Record findings and remediation results in the project's evidence store.
8. Never bypass critical release gates.
9. Request human review when a rule requires it.
10. Preserve project integrity and existing protections.
11. Delegate security decisions to TSAR where the configured integration requires it.
12. Do not modify governance files contrary to the applicable protection policy.

## Required Workflow

```
Inspect → Plan → Design → Implement → Verify → Remediate → Re-verify → Report
```

## What Governance Means

Governance is the discipline of:

- **Stating** what the code must do (requirements).
- **Designing** how it will do it (architecture).
- **Building** it (implementation).
- **Proving** it works (verification).
- **Recording** the proof (evidence).
- **Deciding** whether to release (assessment).

Each step should leave a trace that Apxoh can inspect. A trace is not proof until its integrity, provenance, and relevance have been checked.

## Failure Handling

A failed mandatory requirement must remain visible.

Never report PASS for a check that was not run. Never delete a failing test. Never modify a governance file to make a check succeed.

A false PASS is more serious than an honest BLOCKED.

## Prohibited Actions

- Never claim verification without evidence.
- Never bypass a critical gate.
- Never sign evidence unless an authorized Apxoh signing component performs the operation.
- Never merge without required checks passing.
- Never claim that a prompt alone enforces filesystem or repository permissions.
- Never reimplement delegated security decisions in place of TSAR.

## Evidence Requirements

Claims about verification must be backed by evidence stored in the governed project's evidence store. A record should identify its source, commit, status, artifacts, and hashes. For example:

```json
{
  "evidence_id": "EVID-ARKHON-...",
  "source": "arkhon",
  "commit_sha": "...",
  "status": "PASS",
  "artifacts": [{"path": "...", "sha256": "..."}]
}
```

This example is illustrative only. If the record was not produced and independently checked, do not claim that evidence exists or that verification passed.

## References

- `AGENTS.md` — full operating instructions
- `SECURITY_AGENTS.md` — hostile agent threat model
- `system/charter/ENGINEERING_CHARTER.md` — engineering charter
- `docs/rule-authoring/HOW_TO_WRITE_A_RULE.md` — writing rules
- `docs/agent-adoption/ADOPTION_GUIDE.md` — adoption process

## Version History

- 1.0.0 (2026-11-01): Initial release.
