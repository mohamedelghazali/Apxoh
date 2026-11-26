# Application Security and Operational Engineering Standard

**Status:** Governance standard proposed for review in this change  
**Audience:** AI coding agents, reviewers, release managers, security engineers, SREs  
**Purpose:** Define the minimum secure engineering and operational work an agent must
perform when creating or modifying software. This standard governs target projects; it
does not claim that GENCODE-GOV itself is a web application.

## 1. Required agent behavior

Before implementation, identify project type, deployment model, data classification, actors,
trust boundaries, entry points, external dependencies, privileged operations, and recovery
requirements. Load applicable rules and create a rule-to-implementation-to-test-to-evidence
traceability matrix.

PASS requires executed checks and valid evidence. FAIL means a check found a violation.
BLOCKED means a required tool, environment, permission, test, or evidence is unavailable.
NOT_APPLICABLE requires an architectural reason; "not implemented yet" is not a reason.
A rule file, method name, checklist, or scanner installation is not proof that enforcement ran.

## 2. Application security baseline

| Rule | Mandatory control family |
| --- | --- |
| SE-SEC-001 | Authentication, password hashing, session lifecycle, cookie safety |
| SE-SEC-002 | Authorization, ownership, tenant isolation, admin access |
| SE-SEC-003 | Server-side validation, SQL parameterization, injection prevention |
| SE-SEC-004 | HTTPS/TLS, certificate validation, CORS, headers, CSRF |
| SE-SEC-005 | Secret storage, environment configuration, redaction and rotation |
| SE-SEC-006 | Authentication rate limits, abuse detection, reset token lifetime |
| SE-SEC-007 | Security event logging, detection, alerting, retention, access |
| SE-SEC-008 | Dependency inventory, SCA, vulnerability triage, unused dependencies |
| SE-SEC-009 | Production hardening, debug-off, exposed resources, admin protection |
| SE-SEC-010 | Git history secret scanning and credential revocation/rotation |
| SE-DB-002 | Database least privilege, network isolation, data ownership |

### 2.1 Passwords and cryptography

Passwords are not encrypted for later recovery. Store only adaptive password hashes using
a vetted algorithm and reviewed parameters. Prefer Argon2id; use an approved equivalent
only when platform constraints are documented. Use maintained cryptographic libraries,
authenticated encryption for recoverable data, secure random generation, and explicit key
ownership/rotation. Never invent cryptographic primitives.

### 2.2 Secrets and environment configuration

Use a managed secret store or protected deployment secret facility. Environment variables
may deliver a secret to a process but are not themselves an encrypted vault. Keep live
.env files out of version control; provide placeholder-only .env.example, restrict access,
and use platform at-rest encryption. Redact secrets before logs, traces, reports, prompts,
or evidence. On exposure, revoke/rotate first; history rewriting is secondary and requires
repository-owner coordination.

### 2.3 Authentication and authorization

Authentication proves identity; authorization decides access. Test unauthenticated access,
expired/revoked sessions, privilege escalation, IDOR, cross-user and cross-tenant access,
admin routes, exports, and background jobs. Authorization is enforced server-side and
defaults to deny.

### 2.4 Input and database safety

Validate every untrusted input at the server trust boundary. Front-end checks improve UX
but do not satisfy security acceptance. Use parameterized SQL or safe ORM bindings; strict
allowlists are required for dynamic identifiers. Test malicious payloads, invalid types,
ranges, encodings, paths, uploads, commands, and serialized objects.

### 2.5 Transport and browser security

Production traffic uses HTTPS/TLS with certificate-chain and hostname validation. Never
disable certificate verification. Configure restrictive CORS, HSTS, appropriate security
headers/CSP, secure cookie attributes, and CSRF protection for cookie-authenticated
state-changing operations. Verify deployed configuration.

### 2.6 Account recovery

Reset tokens are cryptographically random, securely stored, single-use, invalidated on use
or new request, and expire no later than 60 seconds unless an authorized documented
exception explicitly changes this requirement. Test expiry and replay.

### 2.7 Security logs

Record login outcomes, access denials, privilege changes, admin actions, credential lifecycle,
suspicious behavior, and control failures in structured protected logs. Restrict access,
define retention and alert ownership. Never log passwords, API keys, tokens, session cookies,
private keys, usernames, or raw sensitive request payloads. Use correlation IDs and privacy-
safe pseudonymous references.

### 2.8 Dependencies and exposure

Inventory direct/transitive dependencies from lockfiles, run SCA, triage findings, review
provenance, and remove unused dependencies after impact analysis. Inspect public files,
object storage, backups, debug routes, source maps, metadata endpoints, and admin surfaces.
Production debug mode is disabled.

## 3. Operational engineering baseline

### 3.1 Database migrations

Every production migration requires reviewed schema/SQL diff, compatibility analysis,
lock/availability and data-volume assessment, recovery point, tested migration, rollback or
forward-recovery plan, and owner approval. Prefer expand/migrate/contract for zero-downtime
changes. Test upgrade and recovery against production-like engine versions and data volume.

### 3.2 Backups and recovery

Before destructive/high-risk changes, verify the latest recoverable backup meets required
RPO; take a fresh backup when it does not. Restore in isolation and validate checksums,
record counts, and domain invariants. Record RPO/RTO, encryption, retention, access controls,
and recovery owner.

### 3.3 Application logs

Logs must aid diagnosis using timestamp, severity, component, error code, correlation ID,
and sanitized remediation guidance. Do not include usernames, passwords, API keys, tokens,
cookies, connection strings, personal data, or raw request bodies unless explicitly approved
and minimized. Test redaction with sentinel secrets.

### 3.4 Monitoring

Monitor availability, latency percentiles, error rate, saturation, dependency health, and
critical background jobs. Detailed dashboards, metrics, traces, infrastructure metadata,
and alert controls are restricted to authenticated authorized operators. Public health
probes expose only minimal liveness/readiness state.

### 3.5 Rollback

Every release/change defines triggers, owner, exact artifact/configuration to restore,
database compatibility, data-loss boundaries, and communication steps. Test application
and database recovery together. If rollback is unsafe after writes, define a tested
forward-recovery path.

## 4. Required pre-release evidence

The release report MUST contain:
- Scope, architecture summary, threat model, and applicability decisions.
- Rule traceability matrix with rule ID, implementation/config reference, tests, evidence,
  status, finding, remediation owner, and approval.
- Security test results including positive, negative, abuse, and regression cases.
- Current-tree and Git-history secret scans plus sanitized credential-rotation evidence.
- SCA and vulnerability triage; TSAR evidence limited to its declared contract scope.
- Production configuration and exposed-resource review.
- Log-redaction/access tests and monitoring/alert evidence.
- Migration, backup/restore, RPO/RTO, and rollback/forward-recovery evidence.
- Exact commit SHA, tool names/versions, timestamps, evidence digests, and approvals.

A checklist, static declaration, or agent assertion is insufficient. Missing mandatory
checks remain BLOCKED. Critical/high findings block release unless policy permits an
explicit approved risk acceptance; critical controls are never silently waived.
