# Apxoh Incident Response Plan

**Version:** 1.0  
**Status:** Response guidance; no 24/7 on-call service or response-time commitment is implied  
**Last updated:** 2026-11-02

## 1. Purpose and Scope

This document defines a repeatable response approach for suspected compromise, evidence tampering, security-gate failure, malicious agent behavior, and failures in required security integrations affecting Apxoh or a project governed by it.

It is a procedural guide. It does not establish a staffed incident-response team, automated alerting, immutable log service, or guaranteed response time. Deployment owners must assign responders and verify their contact paths.

## 2. Incident Severity

| Severity | Example | Initial handling |
| :--- | :--- | :--- |
| Critical | Confirmed credential theft, evidence forgery affecting release, active compromise | Stop affected release activity; preserve evidence; escalate immediately |
| High | Required security authority unavailable, suspected governance bypass, exploitable vulnerability | Keep relevant gate blocked; investigate and escalate promptly |
| Medium | Repeated verification failures, non-critical integrity anomaly | Record finding, investigate scope, remediate |
| Low | Documentation, configuration, or availability issue without security impact | Track and resolve through normal maintenance |

Severity is provisional until impact and scope are understood. Do not downgrade an incident solely because exploitation has not yet been demonstrated.

## 3. Roles

Assign these responsibilities for each deployment before relying on this plan:

- **Incident coordinator:** maintains timeline, scope, and decisions.
- **Security responder:** investigates security impact and coordinates containment.
- **Engineering owner:** preserves service and repository state and prepares remediation.
- **Approver:** authorizes recovery and release decisions.

If no role is assigned, record the ownership gap and escalate to the repository or deployment maintainer. This document does not claim that these roles are currently staffed.

## 4. First Response

1. Acknowledge and record the report through an approved private channel when sensitive details are involved.
2. Record the time, reporter, affected repository/project, commit SHA, environment, and observed symptoms.
3. Preserve relevant logs, evidence bundles, workflow runs, and artifacts before cleanup.
4. Stop or pause affected release activity when integrity or security approval is in doubt.
5. Restrict access only through verified administrative controls and authorized operators.
6. Do not delete, rewrite, or silently replace suspect evidence.
7. Establish an incident lead and communication channel.

## 5. Response Playbooks

### 5.1 Suspected Evidence Tampering

- Preserve the original evidence bundle and referenced artifacts.
- Record expected and observed SHA-256 digests, commit binding, timestamps, and storage paths.
- Check repository history and available CI execution records.
- Recompute hashes from preserved copies using a trusted environment.
- Treat missing, altered, or mismatched evidence as BLOCKED.
- Do not claim signature authenticity unless signature verification and signer identity checks actually ran.

### 5.2 TSAR Unavailable or Invalid Evidence

- Keep the applicable security gate BLOCKED.
- Record the TSAR version output, command, exit status, sanitized stderr, and target commit.
- Check the contract in `integrations/tsar/contract.yaml`.
- Restore the integration using its approved installation and configuration procedure.
- Re-run the audit against the exact target commit and validate required fields, rules, timestamps, paths, and digests.
- Do not substitute an unapproved scanner and label the result TSAR evidence.

### 5.3 Suspected Malicious Agent or Prompt Injection

- Preserve the source file, prompt, tool trace, and affected commit.
- Identify files, credentials, tools, network destinations, and repositories the agent could access.
- Revoke or rotate exposed credentials through their owning providers.
- Review changes to governance files, schemas, rules, workflows, and evidence.
- Re-run independent checks from a trusted checkout and environment.
- Treat agent-provided explanations and test output as untrusted statements, not evidence.

### 5.4 Secret Exposure

- Do not copy the secret into an issue, log, or incident document.
- Identify the credential owner and revoke/rotate it through the provider.
- Determine the exposure window and possible access.
- Review audit logs and repository history.
- Remove exposed values from active content; coordinate history rewriting only with maintainers because it affects clones and audit records.
- Record the remediation without reproducing the secret.

### 5.5 Release Gate Failure

- Stop the release decision for the affected commit.
- Record every FAIL and BLOCKED result and the rule/gate that produced it.
- Remediate only through reviewed changes.
- Re-run affected verification and regression checks.
- Obtain required human approval before release resumes.

## 6. Recovery and Closure

An incident may be closed only when scope and impact are assessed, containment is documented, required credentials and access are rotated or confirmed unaffected, remediation is reviewed, relevant verification is rerun, required gates are evaluated using current commit-bound evidence, residual risks are approved, and a postmortem is completed for Critical and High incidents.

Closure does not erase earlier FAIL or BLOCKED results. Historical records should remain available according to the applicable retention policy.

## 7. Communications and Disclosure

Use private communication for exploitable vulnerabilities, exposed secrets, and sensitive customer data. Follow [SECURITY.md](../../SECURITY.md) for the repository's reporting channel. Public disclosure should be coordinated with maintainers and affected parties.

Do not promise a response time unless a deployment-specific service agreement establishes one.

## 8. Postmortem

Use `docs/operations/POSTMORTEM_TEMPLATE.md` to record summary and impact, timeline, root and contributing causes, detection and response effectiveness, corrective actions and owners, evidence references, and lessons learned.

---

**End of Incident Response Plan**
