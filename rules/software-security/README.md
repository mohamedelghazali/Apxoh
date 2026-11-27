# rules/software-security

This domain contains versioned, scoped security requirements for software governed by
GENCODE-GOV. Agents MUST load applicable SE-SEC-* rules before implementation, security
review, deployment, or release. Rules describe target-project controls; their presence
does not prove that a scanner or runtime enforcement mechanism executed.

## Application security baseline

- SE-SEC-001: authentication, password hashing, session lifecycle, cookie safety.
- SE-SEC-002: server-side authorization, ownership, tenant isolation, admin access.
- SE-SEC-003: server-side input validation and injection prevention.
- SE-SEC-004: HTTPS/TLS, certificate validation, CORS, headers, CSRF.
- SE-SEC-005: secrets, environment configuration, safe redaction and rotation.
- SE-SEC-006: rate limiting, abuse controls, password-reset token lifetime.
- SE-SEC-007: security event logging, detection, and alerting.
- SE-SEC-008: dependency inventory, SCA, vulnerability and unused-dependency review.
- SE-SEC-009: production hardening, debug-off, exposed resources and admin protection.
- SE-SEC-010: Git history secret scanning and credential revocation/rotation.

TSAR is a delegated provider for only the capabilities listed in
integrations/tsar/contract.yaml; it is not a substitute for the complete baseline.
Required checks that cannot run are BLOCKED, never PASS.
