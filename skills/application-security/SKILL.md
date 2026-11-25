---
name: application-security
description: >
  Threat-model, implement, test, and verify application security controls for
  AI-generated software using Apxoh's security rules and evidence requirements.
version: 1.1.0
applicable_to: [web-application, api-service, mobile-application, distributed-system, enterprise]
requires: [arkhon-governance, secure-software-engineering]
---

# Application Security Skill

Mandatory whenever an agent creates, changes, reviews, deploys, or releases software that
handles users, credentials, sensitive data, network traffic, or privileged operations.

## Execution contract

1. Read AGENTS.md, SECURITY_AGENTS.md, the engineering charter, enforcement model, this
   skill, and all applicable security/database/privacy rules before coding.
2. Build a threat model: assets, actors, trust boundaries, entry points, abuse cases,
   data classification, tenant boundaries, and deployment assumptions.
3. Create a traceability matrix mapping each applicable rule to code/configuration,
   positive and negative tests, evidence, owner, and result.
4. Apply controls appropriate to the architecture. Browser-only controls may be
   NOT_APPLICABLE only with a reason; they must not be omitted from web/API projects.
5. Test the actual server-side boundary using production-like configuration.
6. Use independent tools within their declared scope. Tool names or YAML method names
   do not prove that a check executed.
7. Block the relevant stage if a critical/high applicable control fails or evidence is
   missing. Escalate exceptions to an authorized human.
8. Re-run affected tests and scans after every remediation.

## Mandatory rule set

| Rule | Control family |
| --- | --- |
| SE-SEC-001 | Authentication, password hashing, sessions, cookie safety |
| SE-SEC-002 | Authorization, ownership, tenant isolation, admin privileges |
| SE-SEC-003 | Server-side input/form/API validation, SQLi, command/path/template injection |
| SE-SEC-004 | HTTPS/TLS, certificate validation, CORS, headers, CSRF |
| SE-SEC-005 | Secret manager, ENV hygiene, redaction and rotation |
| SE-SEC-006 | Rate limiting, account enumeration, 60-second reset-token maximum |
| SE-SEC-007 | Security logging, detection, privacy-safe redaction |
| SE-SEC-008 | SCA, dependency inventory, vulnerability triage, unused dependencies |
| SE-SEC-009 | Debug-off, admin protection, exposed-resource review |
| SE-SEC-010 | Git history secret scanning, credential revocation and rotation |
| SE-DB-002 | Database least privilege, credential security, and ownership isolation |
| SE-OBS-003 | Structured diagnostic logging, sanitized errors, log redaction, and crash dump governance |
| SE-TST-004 | Cross-language critical-path and scenario-traced negative security testing |

## Minimum security test matrix

Covers `.arkhon/security-test-matrix.yaml` traceability across unauthenticated access;
horizontal/vertical privilege escalation; IDOR and unauthorized resource access;
cross-user/tenant read/write/delete isolation; SQL/command/template injection; invalid
server-side form and API payloads; invalid TLS certificates/hostnames; CORS abuse; CSRF on
cookie-authenticated state changes; login/recovery rate-limit abuse; expired, replayed,
malformed, and revoked tokens; secret and sensitive-data redaction across logs/traces/errors;
crash dump disablement by default (or encrypted least-privilege short-retention controls);
public admin/monitoring/storage/debug resources; and vulnerable dependencies.

Supported outcome classifications: PASS, FAIL, BLOCKED, NOT VERIFIED, and NOT_APPLICABLE
bound to commit SHA and reproducible execution evidence.
