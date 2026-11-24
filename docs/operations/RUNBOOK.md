# Apxoh Operations Runbook

**Version:** 1.0
**Status:** Operational guidance — confirm command availability and controls against the installed release.
**Last updated:** 2026-11-01

---

## 1. Daily Operations

### 1.1 Check Installation Health

Where supported by the installed CLI:

```bash
arkhon doctor
```

Review the actual command output. Do not assume that a successful
installation check proves that optional tools or integrations work.

If TSAR is required by the active security policy but unavailable, the
security verification result must be `BLOCKED`, not `PASS`.

### 1.2 Validate Rules

```bash
arkhon validate
```

Review all reported validation errors and warnings. A successful
validation confirms only the checks actually performed by that command.

### 1.3 Inspect a Project

Where supported by the installed CLI:

```bash
arkhon inspect /path/to/project
```

Review detected languages, selected profiles, and resolved tools. A
detected language does not prove that its toolchain is installed.

---

## 2. Verification

### 2.1 Run a Single Domain

Where supported by the installed CLI:

```bash
arkhon verify --domain testing --project /path/to/project
```

### 2.2 Run All Domains

Where supported by the installed CLI:

```bash
arkhon verify --domain all --project /path/to/project
```

### 2.3 Interpret Output

| Status | Meaning |
| :--- | :--- |
| `PASS` | All required checks in the evaluated scope passed with valid evidence |
| `FAIL` | At least one evaluated check failed |
| `BLOCKED` | A required tool, input, evidence item, or verification step was unavailable |

A `BLOCKED` result is not a passing result and must not be treated as
approval. Resolve the missing prerequisite and rerun verification.

---

## 3. Assessment

### 3.1 Compute Score

Where supported by the installed CLI:

```bash
arkhon assess /path/to/project
```

Review the score, configured level, gate statuses, missing evidence,
and accepted risks. A score is meaningful only in the context of the
active profile and its configured weights.

### 3.2 Interpret Score

The following ranges are illustrative policy examples, not a statement
that these exact levels or thresholds are currently enforced:

| Score | Illustrative level | Action |
| :--- | :--- | :--- |
| 95–100 | Hyperscale Validated | Eligible for release review |
| 90–94 | Enterprise Grade | Eligible for release review |
| 80–89 | Production Ready | Eligible for release review |
| 70–79 | Controlled Release | Additional review and monitoring |
| < 70 | Development | Do not release |

A score must never override a failed critical gate or missing required
evidence. Release approval remains subject to the active policy and
authorized human approval.

---

## 4. Reporting

Use the report command and formats supported by the installed CLI.
Example invocations, if available:

### 4.1 JSON Report

```bash
arkhon report /path/to/project --format json
```

### 4.2 Markdown Report

```bash
arkhon report /path/to/project --format markdown
```

Confirm the output path from the command result. Do not assume a report
was generated merely because the command was invoked.

---

## 5. Incident Response

### 5.1 Evidence Tampering Suspected

**Symptom:** An evidence integrity or authenticity check fails, or a
gate is reported as `BLOCKED` for an evidence-integrity reason.

**Steps:**
1. Do not bypass the gate or overwrite the suspect evidence.
2. Preserve the affected evidence and relevant logs.
3. Identify the artifact and the expected versus observed digest.
4. Review repository history and available audit records.
5. Re-run verification from a trusted, clean state when authorized.
6. Escalate suspected malicious activity to the configured security contact.
7. Do not reuse suspect evidence until the cause is understood and reviewed.

### 5.2 TSAR Unavailable

**Symptom:** The required security delegation cannot be completed.

**Steps:**
1. Check whether `tsar --version` is available.
2. Review the Apxoh doctor output, if that command exists.
3. Install or repair TSAR using its official project documentation.
4. Re-run the security verification scope.
5. If TSAR is installed but integration still fails, inspect the
   configured contract under `integrations/tsar/`.
6. Keep the security gate `BLOCKED` until required evidence is verified.

### 5.3 Stale Evidence

**Symptom:** Evidence is outside the freshness window or bound to a
different commit.

**Steps:**
1. Inspect the evidence timestamp and target commit.
2. Re-run the relevant verification domain against the current commit.
3. Preserve older evidence according to the retention and incident policy.
4. Confirm that the new evidence passes schema, integrity, and freshness checks.

### 5.4 Rule Validation Failure

**Symptom:** Rule validation reports errors.

**Steps:**
1. Read the error; identify the file and field.
2. Check `schemas/rule.schema.json` and the rule-authoring guidance.
3. Correct the rule and add or update positive and negative tests.
4. Re-run validation.
5. Do not weaken a rule merely to make validation pass without an approved change.

---

## 6. Maintenance

### 6.1 Updating Dependencies

Use the repository's declared dependency-management workflow. For a
Python development environment, a manual upgrade may be performed only
as part of a reviewed dependency update:

```bash
python -m pip install --upgrade <package>
```

Update the declared dependency constraints and lock data, where used,
then run the repository's configured CI checks. Do not assume that
`make ci` exists unless the Makefile defines it.

### 6.2 Rotating Signing Identity

Sigstore keyless signing does not use a long-lived private signing key
in the same way as traditional key management. However, trust policy,
OIDC issuer, workflow identity, and allowed repository/ref constraints
still require review and maintenance.

### 6.3 Archiving Old Evidence

Retention and archival must follow the configured policy and preserve
evidence required for releases, audits, legal obligations, or incidents.
Do not run a destructive pruning command until retention behavior and
backup/recovery requirements have been verified.

---

## 7. Escalation

Use the contacts and response times approved for the deployment. The
following roles are suggested escalation targets:

| Situation | Escalate to | Priority |
| :--- | :--- | :--- |
| Evidence tampering | Security Lead | Immediate |
| Critical gate failure | Engineering Lead | High |
| Required TSAR integration unavailable | Engineering Lead / Security Lead | High |
| Repeated verification failures | Engineering Lead | High |
| Suspected hostile agent | Security Lead | Immediate |

---

## 8. Reference

- `docs/operations/POSTMORTEM_TEMPLATE.md` — postmortem format
- `SECURITY.md` — vulnerability reporting
- `SECURITY_AGENTS.md` — hostile-agent threat model
- `docs/threat-model/ARKHON_THREAT_MODEL.md` — system threat model
- `docs/VULNERABILITY_RESPONSE.md` — vulnerability response policy

---

**End of Document**
