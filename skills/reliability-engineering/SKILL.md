---
name: reliability-engineering
description: >
  Define SLOs, instrument services, test backup restoration and rollback, and
  prove operational recovery for AI-generated software.
version: 1.1.0
applicable_to: [all-projects]
requires: [arkhon-governance]
---

# Reliability Engineering Skill

Reliability is measured and recovery is demonstrated. A written procedure or successful
backup command is not proof that a system can be restored.

## Mandatory rules

1. Define service-specific SLIs, SLOs, measurement windows, and error budgets.
2. Monitor availability, latency percentiles, error rate, saturation, dependency health,
   and critical asynchronous jobs.
3. Assign owners and test alert delivery and escalation paths.
4. Restrict detailed monitoring dashboards and infrastructure diagnostics to authorized
   operators. Public health probes disclose only minimal liveness/readiness information.
5. Before destructive or high-risk production changes, verify a recovery point meets the
   required RPO; create a fresh backup when it does not.
6. Restore backups in isolation and validate checksums, record counts, and domain invariants.
   Record RPO/RTO and restore duration.
7. Test application and database rollback compatibility together. If rollback after writes
   is unsafe, define and test a forward-recovery strategy and disclose its data-loss boundary.
8. Test recovery procedures periodically and after material changes.
9. Never claim backup, monitoring, or rollback readiness without current evidence.

## Evidence

SLI/SLO and error-budget report; monitoring signal catalog and dashboard access matrix;
tested alerts; backup manifest; restore log and integrity report; RPO/RTO measurement;
application/database rollback or forward-recovery drill.
