---
name: performance-engineering
description: >
  Define performance budgets, run benchmarks, monitor runtime latency percentiles,
  and detect/alert on performance degradation with measured evidence.
version: 1.1.0
applicable_to: [all-projects]
requires: [gencode-gov]
---
# Performance Engineering Skill

## Purpose

Performance is a feature. It must be specified, measured, continuously monitored,
and defended against regression — not assumed.

## Mandatory Rules

1. Every user-facing endpoint must have a documented numeric latency target (`SE-PRF-001`).
2. Benchmarks must run under documented conditions (data, load, hardware).
3. Critical endpoints, queries, and queues must emit P50, P95, and P99 latency, throughput,
   error, and saturation telemetry (`SE-PRF-002`).
4. Automated degradation detection must compare release candidates and live telemetry against
   approved latency baselines and route actionable alerts with named owners and runbooks (`SE-PRF-002`).
5. No performance optimization may sacrifice correctness, tenant isolation, or security.

## The Metrics That Matter

| Metric | What it measures | Target example |
| :--- | :--- | :--- |
| P50 latency | Median response time | ≤ 100ms |
| P95 latency | 95th percentile (`SE-PRF-001`) | ≤ 200ms |
| P99 latency | Tail latency (`SE-PRF-002`) | ≤ 500ms |
| Latency regression delta | Shift vs. approved baseline (`SE-PRF-002`) | ≤ +15% P95 |
| Throughput | Requests per second | ≥ 1000 RPS |
| CPU / Memory saturation | Utilization under expected load | ≤ 70% CPU / ≤ 80% Mem |
| Query latency | Database query execution time | ≤ 50ms |

## Load Testing Levels

1. **Baseline:** expected load. Should always pass.
2. **Peak:** 2× expected. Should pass with bounded degradation.
3. **Stress:** 5× expected. Should fail gracefully, not catastrophically.
4. **Soak:** expected load for 24+ hours. Should show no leaks, no drift.

## Evidence Required

- `benchmark-results` & `performance-report` — load-test targets vs. actuals (`SE-PRF-001`)
- `latency-instrumentation-catalog` & `performance-regression-comparison-report` (`SE-PRF-002`)
- `degradation-alert-rules-and-owners` & `alert-delivery-verification-report` (`SE-PRF-002`)

## Interaction with GENCODE-GOV

- Rule domain: `performance` (`SE-PRF-001`, `SE-PRF-002`)
- Gate: `performance_gate`
- Evidence type: `benchmark_results`
- Output goes to `.gencode-gov/evidence/performance/`

## Reference

- `system/charter/ENGINEERING_CHARTER.md` — principle 5
- `docs/verification/VERIFICATION_PROFILES.md` — performance requirements per profile

## Version History

- 1.1.0 (2026-11-25): Added SE-PRF-002 continuous latency telemetry, degradation detection, and alerting.
- 1.0.0 (2026-11-01): Initial release.
- 
