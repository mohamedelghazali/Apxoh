---
name: secure-software-engineering
description: >
  Write, review, and verify code that delegates security decisions to
  TSAR. Ensures no security claim is made without TSAR evidence.
version: 1.0.0
applicable_to: [all-projects]
requires: [arkhon-governance]
delegates_to: tsar
---

# Secure Software Engineering Skill

## Purpose

Apxoh does not implement its own security scanners. All security
decisions are delegated to **TSAR**. This skill ensures the developer
or agent:

1. Does not reimplement security rules.
2. Calls TSAR at the right moments.
3. Interprets TSAR evidence correctly.
4. Blocks the gate when TSAR is unavailable.

## Mandatory Rules

1. Never claim "this is secure" without TSAR evidence.
2. Never hardcode secrets — TSAR scans for them.
3. Never disable a security check to make a build pass.
4. Never implement cryptography from scratch — use vetted libraries, and let TSAR audit them.
5. Never bypass the security gate when TSAR reports critical or high findings.
6. If TSAR is unavailable, the gate is `BLOCKED`. Do not work around it.

## When to Call TSAR

| Trigger | Action |
| :--- | :--- |
| Code touches authentication | `arkhon verify --domain software-security` |
| Code touches cryptography | `arkhon verify --domain software-security` |
| New dependency added | `arkhon verify --domain software-security` |
| Pre-release | `arkhon verify --domain software-security` |
| Any change to security-relevant code | `arkhon verify --domain software-security` |

## How to Read TSAR Evidence

- `PASS` with no critical/high findings → gate can close.
- `PASS` with medium/low findings → gate closes, findings tracked.
- `FAIL` with critical/high findings → gate cannot close; remediate and re-audit.
- `BLOCKED` with reason "TSAR unavailable" → fix the environment; do not bypass.

## What This Skill Does NOT Do

- It does not run scanners. TSAR does.
- It does not interpret vulnerabilities. TSAR does.
- It does not decide severity. TSAR does.

## Evidence Required

- `tsar-evidence` — the JSON produced by TSAR, verified against the contract.
- `security-findings` — the derived findings with severity mapping.

## Interaction with Apxoh

- Rule domain: `software-security`
- Gate: `security_gate`
- Evidence type: `tsar_evidence_bundle`
- Output goes to `.arkhon/evidence/security/`

## Reference

- `integrations/tsar/contract.yaml` — the integration contract
- `docs/integrations/tsar-integration.md` — integration guide
- `SECURITY_AGENTS.md` — hostile agent threat model
- `docs/threat-model/ARKHON_THREAT_MODEL.md` §4.2

## Version History

- 1.0.0 (2026-11-01): Initial release.
