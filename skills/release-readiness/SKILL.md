---
name: release-readiness
description: >
  Conduct the Production Readiness Review (PRR). Ensures every gate is
  closed with evidence before a release is approved.
version: 1.0.0
applicable_to: [all-projects]
requires: [arkhon-governance, software-testing, secure-software-engineering]
---

# Release Readiness Skill

## Purpose

A release is not ready because someone says it is. A release is ready
when every gate is closed with valid evidence, and a named human has
approved the decision.

## Mandatory Rules

1. Every required gate must be `PASS` before release.
2. Every critical gate must have a signed human approval.
3. No exception may bypass a critical gate without a documented risk acceptance.
4. The release decision must cite the exact commit being released.
5. No release may proceed if evidence is stale or missing.

## The PRR Checklist

Before any release, verify:

### Monitoring
- [ ] Dashboards exist for all critical paths
- [ ] Alerts are configured and tested
- [ ] Health checks are reachable

### Incident Response
- [ ] Incident management plan exists
- [ ] On-call rotation is defined
- [ ] Runbooks are up to date

### Security
- [ ] TSAR evidence is fresh (≤ 7 days)
- [ ] No critical or high findings open
- [ ] Secrets scan is clean

### Performance
- [ ] Load tests pass at expected load
- [ ] P95 latency meets target
- [ ] Throughput meets target

### Reliability
- [ ] SLOs are defined
- [ ] Error budget is not exhausted
- [ ] Backup restore has been verified

### Documentation
- [ ] Architecture is documented
- [ ] Deployment is documented
- [ ] Rollback plan exists and is tested

## Release Decision Options

| Decision | When to use |
| :--- | :--- |
| `APPROVED` | All gates pass, no conditions |
| `APPROVED_WITH_CONDITIONS` | All gates pass, but with accepted risks |
| `REJECTED` | At least one critical gate fails |
| `PENDING_EVIDENCE` | A gate is `BLOCKED` due to missing evidence |

## Evidence Required

- `release-decision` — the decision document with commit SHA
- `production-readiness-review` — the completed PRR checklist
- Signatures from the required approvers

## Interaction with Apxoh

- Rule domain: `release`
- Gate: `release_gate`
- Evidence type: `release_decision`
- Output goes to `.arkhon/evidence/release/`

## Reference

- `system/charter/ENGINEERING_CHARTER.md` — principle 7
- `docs/operations/RUNBOOK.md`
- `docs/operations/POSTMORTEM_TEMPLATE.md`

## Version History

- 1.0.0 (2026-11-01): Initial release.
