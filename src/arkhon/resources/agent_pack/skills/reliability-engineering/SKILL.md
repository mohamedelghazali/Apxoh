---
name: reliability-engineering
description: >
  Define SLOs, run reliability tests, and prove the system can recover
  from failure. Ensures reliability is engineered, not hoped for.
version: 1.0.0
applicable_to: [all-projects]
requires: [arkhon-governance]
---

# Reliability Engineering Skill

## Purpose

A reliable system is not one that never fails. It is one that fails
predictably and recovers quickly. This skill ensures that reliability
is measured, not assumed.

## Mandatory Rules

1. Every service must have an SLO (Service Level Objective).
2. Every SLO must have an error budget.
3. Error budget consumption must be monitored, not guessed.
4. Recovery procedures must be tested, not just documented.
5. Backups must be verified by restoring them, not just by creating them.
6. No release may proceed if the error budget is exhausted.

## SLO Examples

| SLO | Target | Error budget (30 days) |
| :--- | :--- | :--- |
| Availability | 99.9% | 43.2 minutes downtime |
| Availability | 99.99% | 4.32 minutes downtime |
| P95 latency | ≤ 200ms | 5% of requests may exceed |
| Error rate | ≤ 0.1% | 0.1% of requests may fail |

## Recovery Requirements

- **RTO** (Recovery Time Objective): how long until the service is restored
- **RPO** (Recovery Point Objective): how much data loss is acceptable
- **Failover:** tested, not assumed
- **Backup restore:** verified, not assumed

## What to Test

- Circuit breaker behavior under dependency failure
- Graceful degradation when a downstream service is down
- Recovery from a database restart
- Recovery from a network partition
- Recovery from a full region loss (if applicable)

## Evidence Required

- `reliability-report` — SLOs, error budgets, current status
- `chaos-test-results` — what failure was injected, what happened
- `backup-restore-verification` — proof that a restore works

## Interaction with Apxoh

- Rule domain: `reliability`
- Gate: `reliability_gate`
- Evidence type: `reliability_report`, `chaos_test_results`
- Output goes to `.arkhon/evidence/reliability/`

## Reference

- `system/charter/ENGINEERING_CHARTER.md` — principle 6
- `standards/sre/slo-guidelines.yaml` — SRE guidelines

## Version History

- 1.0.0 (2026-11-01): Initial release.
