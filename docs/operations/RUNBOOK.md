# Apxoh Operations Runbook

**Version:** 1.0
**Status:** Active
**Last updated:** 2026-11-01

---

## 1. Daily Operations

### 1.1 Check Installation Health

```bash
arkhon doctor
```

Expected: `Apxoh doctor — OK`.

If TSAR is missing, `doctor` will warn but not fail. Security gate will
be `BLOCKED` until TSAR is installed.

### 1.2 Validate Rules

```bash
arkhon validate
```

Expected: `All validations passed.`

### 1.3 Check Available Tools

```bash
arkhon inspect /path/to/project
```

Expected: languages detected, profile resolved, tools listed.

---

## 2. Verification

### 2.1 Run a Single Domain

```bash
arkhon verify --domain testing --project /path/to/project
```

### 2.2 Run All Domains

```bash
arkhon verify --domain all --project /path/to/project
```

### 2.3 Interpret Output

| Status | Meaning |
| :--- | :--- |
| `PASS` | All runners passed |
| `FAIL` | At least one runner failed |
| `BLOCKED` | At least one runner could not run (missing tool, error) |

A `BLOCKED` result is **not** a failure of the project — it is a failure
of the environment. Fix the environment first.

---

## 3. Assessment

### 3.1 Compute Score

```bash
arkhon assess /path/to/project
```

Output includes:
- Total score /100
- Level (development → hyperscale-validated)
- Gate statuses

### 3.2 Interpret Score

| Score | Level | Action |
| :--- | :--- | :--- |
| 95–100 | Hyperscale Validated | Release |
| 90–94 | Enterprise Grade | Release |
| 80–89 | Production Ready | Release |
| 70–79 | Controlled Release | Release with monitoring |
| < 70 | Development | Do not release |

Even with score ≥ 80, a critical gate failure rejects the release.

---

## 4. Reporting

### 4.1 JSON Report

```bash
arkhon report /path/to/project --format json
```

Produces `.arkhon/reports/report.json`.

### 4.2 Markdown Report

```bash
arkhon report /path/to/project --format markdown
```

Produces `.arkhon/reports/report.md`.

---

## 5. Incident Response

### 5.1 Evidence Tampering Detected

**Symptom:** Gate `BLOCKED` with reason "evidence-tampered".

**Steps:**
1. Do not bypass the gate.
2. Check `.arkhon/state/incidents.log` for details.
3. Identify which artifact was tampered.
4. Determine who modified it (git log, file timestamps).
5. Re-run the audit from a clean state.
6. If tampering was malicious, escalate to Security Lead.
7. Do not re-enable the gate until the root cause is understood.

### 5.2 TSAR Unavailable

**Symptom:** Security gate `BLOCKED` with reason "tsar-unavailable".

**Steps:**
1. Check `tsar --version` on the machine.
2. If missing: `arkhon doctor` will tell you what's wrong.
3. Install TSAR per its documentation.
4. Re-run `arkhon verify --domain software-security`.
5. If TSAR is installed but still failing: check the contract
   (`integrations/tsar/contract.yaml`) for version requirements.

### 5.3 Stale Evidence

**Symptom:** Gate `BLOCKED` with reason "evidence-stale".

**Steps:**
1. Check the evidence timestamp in `.arkhon/evidence/<domain>/`.
2. Re-run `arkhon verify --domain <domain>` to produce fresh evidence.
3. The old evidence remains on disk (append-only); the new one supersedes it.

### 5.4 Rule Validation Failure

**Symptom:** `arkhon validate` fails with rule errors.

**Steps:**
1. Read the error carefully — it names the file and field.
2. Check `schemas/rule.schema.json` for the required structure.
3. Fix the rule.
4. Re-run `arkhon validate`.

---

## 6. Maintenance

### 6.1 Updating Dependencies

```bash
# Dependabot opens PRs automatically.
# To update manually:
pip install --upgrade <package>
# Then update pyproject.toml with the exact new version.
```

After updating, run:

```bash
make ci
```

### 6.2 Rotating Signing Keys

sigstore is keyless. There is no long-term signing key to rotate.

Identity is bound to OIDC (GitHub Actions or developer identity). To
rotate, change the OIDC provider or the identity.

### 6.3 Archiving Old Evidence

Apxoh does this automatically (moves to `_archive/` after 30 days,
prunes after 90 days unless attached to a release).

To manually archive:

```bash
mkdir -p .arkhon/evidence/_archive
find .arkhon/evidence -type f -mtime +30 -name "*.json" \
  -not -path "*/_archive/*" \
  -exec mv {} .arkhon/evidence/_archive/ ;
```

---

## 7. Escalation

| Situation | Escalate to | Time |
| :--- | :--- | :--- |
| Evidence tampering | Security Lead | Immediate |
| Critical gate failure | Engineering Lead | 24 hours |
| TSAR unavailable > 1 hour | Engineering Lead | 1 hour |
| Repeated verification failures (3+) | Engineering Lead | 24 hours |
| Suspected hostile agent | Security Lead | Immediate |

---

## 8. Reference

- `docs/operations/POSTMORTEM_TEMPLATE.md` — postmortem format
- `SECURITY.md` — vulnerability reporting
- `SECURITY_AGENTS.md` — hostile agent threat model
- `docs/threat-model/ARKHON_THREAT_MODEL.md` — system threat model
- `docs/VULNERABILITY_RESPONSE.md` — incident response policy

---

**End of Document**
