# Rule Authoring — 20 Illustrative Patterns

**Version:** 1.0  
**Status:** Guidance; examples are illustrative, not guaranteed schema-valid rule files  
**Last updated:** 2026-11-01

Twenty patterns for expressing common rule intents. Each example describes the intended verification approach and evidence. Treat the YAML fragments as conceptual sketches: confirm field names and allowed values against `schemas/rule.schema.json` and the current rule-authoring guide before copying them into the active catalog.

For the normative syntax, see `schemas/rule.schema.json` and `docs/rule-authoring/HOW_TO_WRITE_A_RULE.md`.

---

## Pattern 1: Deterministic — “No X”

**Example:** SE-CQ-001 — No unused imports.

```yaml
verification:
  mode: deterministic
  methods: [ruff-check, ast-analysis]
acceptance:
  unused_imports: 0
```

**Use when:** a deterministic tool can decide the result unambiguously.  
**Evidence:** tool identity/version, command, exit status, and findings.

## Pattern 2: Deterministic — “X must exist”

**Example:** SE-OBS-001 — Health endpoint required.

```yaml
verification:
  mode: deterministic
  methods: [endpoint-detection]
acceptance:
  health_endpoint_present: true
```

**Use when:** the presence of a required artifact is the check.  
**Evidence:** detected endpoint and the source files or configuration supporting it.

## Pattern 3: Deterministic — “X must be above threshold”

**Example:** SE-TST-001 — Unit-test coverage threshold.

```yaml
verification:
  mode: deterministic
  methods: [coverage-analysis]
acceptance:
  coverage_percent_min: 80
```

**Use when:** the result is a measurable quantity.  
**Evidence:** coverage report, measurement scope, and executed test command.

## Pattern 4: Deterministic — “X must match commit”

**Example:** SE-MNT-001 — Release metadata is consistent.

```yaml
verification:
  mode: deterministic
  methods: [version-consistency-check]
acceptance:
  version_consistent: true
```

**Use when:** two versioned artifacts must agree.  
**Evidence:** values read from each artifact and the target commit.

## Pattern 5: Deterministic — “X must be fresh”

**Example:** SE-SEC-GOV-002 — TSAR evidence freshness.

```yaml
verification:
  mode: deterministic
  methods: [timestamp-verification]
acceptance:
  evidence_age_hours_max: 168
```

**Use when:** age is a defined condition of trust.  
**Evidence:** evidence timestamp, evaluation timestamp, and freshness policy.

## Pattern 6: Deterministic — “No dangerous pattern”

**Example:** Python code must not call `eval()`.

```yaml
verification:
  mode: deterministic
  methods: [ast-pattern-check]
acceptance:
  eval_calls: 0
```

**Use when:** a prohibited construct can be identified reliably.  
**Evidence:** scanned file set, analyzer output, and exclusions.

## Pattern 7: Hybrid — “Tool plus human interpretation”

**Example:** SE-ARC-001 — Architecture decision record required.

```yaml
verification:
  mode: hybrid
  methods: [adr-presence-check, human-review]
human_review:
  required: true
  approver_role: Software Architect
```

**Use when:** automation can find an artifact but a person must judge its adequacy.  
**Evidence:** artifact reference and a recorded review decision.

## Pattern 8: Hybrid — “Conflict analysis”

**Example:** SE-REQ-002 — No unresolved requirements conflicts.

```yaml
verification:
  mode: hybrid
  methods: [requirements-conflict-analysis, human-review]
acceptance:
  unresolved_conflicts: 0
```

**Use when:** a tool can flag possible conflicts but cannot reliably resolve intent.  
**Evidence:** conflict report and reviewer disposition for each item.

## Pattern 9: Hybrid — “Commit message plus diff”

**Example:** SE-TST-002 — Regression test accompanies a bug fix.

```yaml
verification:
  mode: hybrid
  methods: [commit-message-analysis, test-diff-analysis, human-review]
acceptance:
  regression_test_reviewed: true
```

**Use when:** intent must be assessed from change metadata and code.  
**Evidence:** commit, diff, related test, and review record.

## Pattern 10: Hybrid — “Document presence plus review”

**Example:** SE-PRI-001 — Data inventory.

```yaml
verification:
  mode: hybrid
  methods: [data-inventory-presence, human-review]
acceptance:
  data_inventory_present: true
```

**Use when:** a document must exist and a domain expert must assess completeness.  
**Evidence:** inventory revision and reviewer decision.

## Pattern 11: Delegated — “TSAR decides”

**Example:** SE-SEC-GOV-001 — Required TSAR audit.

```yaml
verification:
  mode: delegated
  delegate_to: tsar
  methods:
    - tsar-audit-invocation
    - evidence-integrity-check
    - evidence-commit-match
acceptance:
  tsar_evidence_status: PASS
  unresolved_critical_findings: 0
```

**Use when:** a security decision is explicitly delegated to TSAR.  
**Evidence:** TSAR contract version, invocation record, target commit, and validated output. Missing or invalid evidence is BLOCKED, not PASS.

## Pattern 12: Delegated — “TSAR plus freshness”

**Example:** SE-SEC-GOV-002 — TSAR evidence is recent enough.

```yaml
verification:
  mode: delegated
  delegate_to: tsar
  methods: [timestamp-verification]
acceptance:
  evidence_age_hours_max: 168
```

**Use when:** a delegated result must also satisfy a freshness window.  
**Evidence:** original TSAR evidence and the freshness calculation.

## Pattern 13: Human — “Judgment call”

**Example:** SE-REL-002 — Backup restore attestation.

```yaml
verification:
  mode: human
  methods: [restore-attestation]
human_review:
  required: true
  approver_role: Reliability Engineer
```

**Use when:** only an authorized person can attest to the real-world activity.  
**Evidence:** restore record, environment, timestamp, outcome, and approver.

## Pattern 14: Critical — “Multiple gates”

**Example:** Backup restoration is a critical release condition.

```yaml
metadata:
  severity: critical
  enforcement: critical
failure:
  actions:
    - block-release-gate
    - create-finding
    - require-remediation
    - escalate-to-human
```

**Use when:** failure can cause severe harm or irreversible data loss.  
**Evidence:** the failed check and the gate decision. Confirm action identifiers against the schema.

## Pattern 15: Blocking — “Stage cannot proceed”

**Example:** SE-REQ-001 — Requirements are verifiable.

```yaml
metadata:
  severity: high
  enforcement: blocking
failure:
  actions:
    - create-finding
    - block-stage
    - require-remediation
```

**Use when:** a lifecycle stage must not advance until the issue is resolved.  
**Evidence:** failed acceptance criteria and blocked stage transition.

## Pattern 16: Required — “Must be done before release”

**Example:** SE-MNT-001 — Changelog updated.

```yaml
metadata:
  severity: medium
  enforcement: required
```

**Use when:** the check is mandatory but is not necessarily an immediate stage blocker.  
**Evidence:** changelog entry and the release revision it describes.

## Pattern 17: Advisory — “Recommendation only”

**Example:** SE-CQ-003 — Prefer explicit types.

```yaml
metadata:
  severity: low
  enforcement: advisory
failure:
  actions:
    - create-finding
```

**Use when:** the guidance improves maintainability but is not a release requirement.  
**Evidence:** finding and affected source location.

## Pattern 18: Language-specific — “Python only”

**Example:** No dead code in Python modules.

```yaml
scope:
  languages: [python]
```

**Use when:** the rule is meaningful only for a specific language.  
**Evidence:** detected language and scanned file set.

## Pattern 19: Domain-specific — “Only for API services”

**Example:** Health endpoint requirement.

```yaml
scope:
  project_types: [web-application, api-service, distributed-system]
```

**Use when:** a rule applies only to defined project types.  
**Evidence:** project classification and the rule's applicability decision.

## Pattern 20: Exception-allowed — “Waivable with approval”

**Example:** A unit-test requirement may have a documented exception.

```yaml
exception_policy:
  allowed: true
  requires:
    - documented_justification
    - engineering_lead_approval
```

**Use when:** an exception is permitted under a controlled, reviewable process.  
**Evidence:** justification, approver identity, scope, expiry, and exception record. An exception must not silently convert missing evidence into PASS.

---

## Summary

| # | Pattern | Purpose |
| :--- | :--- | :--- |
| 1–6 | Deterministic | Tool decides a clearly measurable condition |
| 7–10 | Hybrid | Tool output plus human judgment |
| 11–12 | Delegated | Decision delegated to TSAR with evidence checks |
| 13 | Human | Authorized human attestation |
| 14–17 | Enforcement | Critical, blocking, required, or advisory handling |
| 18–19 | Scope | Language- or project-specific applicability |
| 20 | Exception | Controlled waiver with documented approval |

**Important:** The pattern names and YAML fragments are teaching examples. A rule is not deployable until it passes the repository's current schema and semantic validation.
