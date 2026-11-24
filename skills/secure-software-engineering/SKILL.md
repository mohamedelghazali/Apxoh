---
name: secure-software-engineering
description: >
  Apply Apxoh application-security rules to software built by AI agents.
  Produce threat models, security tests, remediation evidence, and honest gate outcomes.
  TSAR is one delegated scanner, not the complete security program.
version: 1.1.0
applicable_to: [all-projects]
requires: [arkhon-governance]
delegates_to: tsar
---

# Secure Software Engineering Skill

## Purpose

Apxoh defines security requirements; the agent implements and verifies them. TSAR provides
only the capabilities declared in integrations/tsar/contract.yaml. It does not replace
application security design, authorization testing, DAST, SCA, TLS review, privacy review,
or qualified human review.

## Mandatory workflow

1. Identify project type, deployment, data classification, actors, trust boundaries,
   entry points, sensitive data, and external dependencies.
2. Load every applicable SE-SEC-* and SE-DB-* rule, plus privacy rules where relevant.
3. Threat-model before security-sensitive implementation; map every rule to code,
   configuration, tests, evidence, and an owner.
4. Validate all untrusted input server-side. Use parameterized SQL or safe ORM bindings.
   Enforce deny-by-default server-side authorization and ownership checks.
5. Use vetted adaptive password hashing (Argon2id preferred), safe session lifecycle,
   TLS certificate validation, restrictive CORS, applicable security headers, CSRF
   protection, secure cookies, rate limiting, and single-use reset tokens with maximum
   60-second lifetime unless an approved exception exists.
6. Keep secrets in a managed secret store or protected deployment environment. ENV is
   a delivery interface, not a vault. Never commit live .env files or secrets.
7. Scan current tree and Git history. Revoke/rotate exposed credentials before closing
   findings. Run SCA separately from TSAR when not covered by its contract.
8. Review production debug settings, exposed files/resources, admin routes, security
   logs, redaction, alerting, and monitoring access.
9. Run positive, negative, abuse, and regression tests. Missing required tools/evidence
   are BLOCKED, never PASS.

## Required application-security review

- Authentication: password hashes only, session rotation/revocation, secure cookies.
- Authorization: deny by default; test IDOR, privilege escalation, ownership and tenant isolation.
- Input/data: server-side schema validation; parameterized queries; safe upload/path/command handling.
- Transport/browser: HTTPS, certificate and hostname validation, HSTS, restrictive CORS,
  CSP and applicable security headers, CSRF for cookie-authenticated mutations.
- Secrets: secret manager, sanitized .env.example, no committed live secrets, rotation/revocation.
- Abuse/recovery: rate-limit login and recovery; generic responses; single-use reset tokens,
  cryptographically random and expiring within 60 seconds unless approved exception.
- Detection: structured security events, access control, retention, alert owners, redaction.
- Dependencies: direct/transitive inventory, SCA, vulnerability triage, unused dependency review.
- Production: debug off, no unintended public files, admin routes protected.
- History: scan reachable Git history, branches, and tags in scope.

## TSAR scope

Run arkhon verify --domain software-security for security-relevant changes and release.
Validate TSAR version, evidence schema, target commit, freshness, and hashes. The current
TSAR contract covers secret scanning and static security review only; it does not prove
SCA, DAST, cryptographic inventory, or ASVS compliance. If required TSAR is unavailable
or evidence is invalid, the security gate is BLOCKED.

## Evidence

Threat model; rule traceability matrix; authentication/authorization and injection reports;
TLS/CORS/headers/CSRF reports; TSAR plus separate SCA/DAST evidence as applicable;
current-tree/history secret scans; sanitized rotation proof; log-redaction tests; findings,
remediation commits, retests, and human approval.

## Status semantics

PASS requires executed checks and valid evidence. FAIL means a check found a violation.
BLOCKED means a required tool, environment, permission, test, or evidence is unavailable.
NOT_APPLICABLE requires an architectural reason; lack of implementation is not a reason.
