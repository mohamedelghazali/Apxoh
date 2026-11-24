---
name: release-readiness
description: >
  Conduct evidence-based Production Readiness Review for secure, reliable,
  observable, and recoverable software before release.
version: 1.1.0
applicable_to: [all-projects]
requires: [arkhon-governance, software-testing, secure-software-engineering, reliability-engineering]
---

# Release Readiness Skill

A release is ready only when every applicable mandatory gate has current evidence,
critical risks are resolved or formally accepted by authorized approvers, and recovery
has been demonstrated.

## Mandatory rules

1. Every applicable required gate must be PASS before release.
2. Critical gates require signed approval by the designated human authority.
3. Exceptions must be scoped, time-bounded, justified, owned, and approved.
4. The release decision cites the exact commit, build artifact, configuration, and evidence.
5. Stale, missing, mismatched, or unverifiable evidence produces BLOCKED.
6. Destructive/high-risk data changes require a verified recovery point and tested recovery.

## Production Readiness Review

### Application security
- [ ] Threat model and trust boundaries reviewed.
- [ ] Authentication, password hashing, sessions, recovery, and rate limits tested.
- [ ] Authorization, ownership, tenant isolation, and admin routes tested.
- [ ] Server-side validation and parameterized database access verified.
- [ ] HTTPS/TLS and certificate validation verified in deployment.
- [ ] CORS, headers, CSRF, and cookie controls verified where applicable.
- [ ] Current-tree and Git-history secret scans clean; exposed credentials revoked/rotated.
- [ ] SCA and vulnerability triage complete; unused dependency review complete.
- [ ] Debug disabled; exposed files/resources and storage permissions reviewed.
- [ ] Security logs redact sensitive data; alerts have owners.
- [ ] TSAR evidence valid for its declared scope; not a substitute for SCA/DAST.

### Operations and reliability
- [ ] Actionable structured logs exist without passwords, usernames, tokens, keys, or PII.
- [ ] Monitoring covers availability, latency, errors, saturation, and dependencies.
- [ ] Dashboards and detailed health data are restricted to authorized operators.
- [ ] Alerts and incident ownership tested.
- [ ] Suitable pre-change backup verified; restore integrity, RPO, and RTO demonstrated.
- [ ] Application/database rollback or forward-recovery plan tested.

### Release evidence
- [ ] Functional, negative, regression, integration, and security tests pass.
- [ ] Findings remediated or formally accepted under policy.
- [ ] Evidence is commit-bound, fresh, integrity-checked, and reproducible.
- [ ] PASS, FAIL, BLOCKED, and NOT_APPLICABLE are reported separately.
- [ ] Named human approvers approve the exact release candidate.

Missing mandatory evidence is BLOCKED. A checklist or agent assertion is not proof.
