---
name: performance-engineering
description: >
  Define performance budgets, run benchmarks, and prove the system meets
  its performance targets with measured evidence.
version: 1.0.0
applicable_to: [all-projects]
requires: [arkhon-governance]
---

# Performance Engineering Skill

## Purpose

Performance is a feature. It must be specified, measured, and defended —
not assumed.

## Mandatory Rules

1. Every performance claim must have a numeric target (P50, P95, P99, throughput, etc.).
2. Benchmarks must run under documented conditions (data, load, hardware).
3. A "fast" system is not fast until measured against its target.
4. Performance regressions must be caught by tests, not by users.
5. No performance optimization may sacrifice correctness or security.

## The Metrics That Matter

| Metric | What it measures | Target example |
| :--- | :--- | :--- |
| P50 latency | Median response time | ≤ 100ms |
| P95 latency | 95th percentile | ≤ 200ms |
| P99 latency | 99th percentile | ≤ 500ms |
| Throughput | Requests per second | ≥ 1000 RPS |
| Concurrent users | Simultaneous sessions | ≥ 5000 |
| CPU utilization | Under expected load | ≤ 70% |
| Memory utilization | Under expected load | ≤ 80% |
| Query latency | Database query time | ≤ 50ms |

## Load Testing Levels

1. **Baseline:** expected load. Should always pass.
2. **Peak:** 2× expected. Should pass with degradation.
3. **Stress:** 5× expected. Should fail gracefully, not catastrophically.
4. **Soak:** expected load for 24+ hours. Should show no leaks, no drift.

## Evidence Required

- `benchmark-results` — raw output from the load test
- `performance-report` — summary with targets vs. actuals
- Environment documentation: hardware, network, data, load generator

## Interaction with Apxoh

- Rule domain: `performance`
- Gate: `performance_gate`
- Evidence type: `benchmark_results`
- Output goes to `.arkhon/evidence/performance/`

## Reference

- `system/charter/ENGINEERING_CHARTER.md` — principle 5
- `docs/verification/VERIFICATION_PROFILES.md` — performance requirements per profile

## Version History

- 1.0.0 (2026-11-01): Initial release.
