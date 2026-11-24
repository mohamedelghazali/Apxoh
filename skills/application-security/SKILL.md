---
name: application-security
description: >
  Threat-model, implement, test, and verify application security controls for
  AI-generated software using Apxoh's security rules and evidence requirements.
version: 1.0.0
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
| SE-SEC-003 | Server-side validation, SQL injection, command/path/template injection |
| SE-SEC-004 | HTTPS/TLS, certificate validation, CORS, headers, CSRF |
| SE-SEC-005 | Secret manager, ENV hygiene, redaction and rotation |
| SE-SEC-006 | Rate limiting, account enumeration, 60-second reset-token maximum |
| SE-SEC-007 | Security logging, detection, privacy-safe redaction |
| SE-SEC-008 | SCA, dependency inventory, vulnerability triage, unused dependencies |
| SE-SEC-009 | Debug-off, admin protection, exposed-resource review |
| SE-SEC-010 | Git history secret scanning, credential revocation and rotation |
| SE-DB-002 | Database least privilege and data ownership isolation |

## Minimum security test matrix

Test unauthenticated and unauthorized access; cross-user/tenant reads and writes; expired,
replayed and revoked tokens; login/recovery throttling; account enumeration; SQL injection;
invalid input; invalid TLS certificates/hostnames; CORS abuse; CSRF; secret leakage through
source/history/logs/artifacts; public admin/monitoring/storage/debug resources; and vulnerable
dependency handling.

Every control receives PASS, FAIL, BLOCKED, or NOT_APPLICABLE with evidence and commit SHA.
A checklist alone is not machine verification. If a required checker does not exist, use
assisted/human review or BLOCKED as the rule requires; never manufacture PASS.
