# Apxoh Rule Lifecycle

**Audience:** Contributors and maintainers.
**Last updated:** 2026-11-01

Every rule follows a controlled lifecycle. A status label is metadata; it does not, by itself, prove that the runtime enforces the corresponding behavior. No rule ID may be reused.

---

## 1. Lifecycle

~~~text
PROPOSED → VALIDATED → REVIEWED → ACTIVE → DEPRECATED → ARCHIVED
~~~

Each transition requires recorded evidence and an accountable reviewer.

## 2. Proposed

**Entry:** A contributor drafts a rule under the appropriate `rules/<domain>/` directory. A proposed subdirectory may be used only if the repository loader supports it.

**Requirements:**
- `metadata.status: proposed`
- YAML conforms to the current rule schema.
- Requirement statement and rationale are documented.
- Domain and ID prefix are selected from the repository's authoritative mapping.

**Exit:** The draft is ready for automated validation.

**Responsible:** Contributor.

## 3. Validated

**Entry:** The proposed rule is available to the validation process.

**Requirements:**
- `arkhon validate` completes successfully.
- Required fields and semantic constraints pass.
- Positive and negative tests are present; regression coverage is added where relevant.
- No duplicate ID or domain-prefix mismatch exists.

**Exit:** Validation evidence is available for review.

**Responsible:** Contributor.

## 4. Reviewed

**Entry:** Validation succeeds and a pull request is opened against the protected target branch.

**Review checklist:**
- Requirement is clear, measurable, and necessary.
- Scope and acceptance criteria are achievable.
- Evidence is meaningful and verifiable.
- Severity and enforcement are independently justified.
- Failure actions are supported by implementation.
- No duplicate, conflict, or unintended overlap exists.
- Tests cover positive and negative behavior.

**Exit:** Authorized reviewer approves and the change is merged.

**Responsible:** Maintainer or designated code owner.

A rejection returns the rule to Proposed with review comments.

## 5. Active

**Entry:** Reviewed change is merged and the rule is intentionally enabled.

**Requirements:**
- `metadata.status: active`.
- Rule is discovered by the loader and indexed by the registry.
- Applicable gates actually evaluate it.
- Enforcement behavior is covered by tests.
- Rule history/changelog is updated where that facility exists.

**Behavior:** Active rules are eligible for evaluation. Their effect on gate status is determined by the enforcement engine, not by documentation alone.

## 6. Deprecated

**Entry:** A rule is being replaced, narrowed, or retired.

**Requirements:**
- `metadata.status: deprecated`.
- Deprecation rationale and date are recorded.
- Replacement rule and migration instructions are provided when applicable.
- A target removal release or review date is specified.

**Behavior:** The repository must define whether deprecated rules remain advisory, continue enforcing, or are excluded. Do not assume deprecated rules still run or stop blocking unless the implementation explicitly establishes that behavior.

## 7. Archived

**Entry:** Deprecation period is complete, or an authorized emergency decision requires removal.

**Requirements:**
- Rule is moved to the repository's designated archive location.
- `metadata.status: archived`.
- Rule ID and historical content are preserved.
- Changelog/release notes record the archival.
- The loader demonstrably excludes archived rules.

**Behavior:** Archived rules are historical records and must not enter active gate evaluation.

## 8. Emergency Removal

For urgent cases, such as a rule causing severe false positives, maintainers may authorize an expedited transition. Record:
- Decision-maker and timestamp.
- Rule ID and affected versions.
- Reason and risk assessment.
- Evidence supporting removal.
- Whether a replacement or rollback is required.
- Follow-up review or postmortem, where appropriate.

Use the repository's established incident and archive locations. Do not reference an archive path as operational unless it exists.

## 9. Versioning

| Change | Suggested version |
| --- | --- |
| Typo or non-semantic clarification | Patch |
| Backward-compatible verification addition | Minor |
| Changed acceptance, scope, or behavior | Major |
| Rule ID change | Not allowed; create a new rule |

Record every approved version change in the project's rule history.

## 10. Rule Conflicts

When rules overlap or conflict:

1. Identify the exact conflicting requirements and scopes.
2. Determine whether one rule supersedes the other.
3. Compare enforcement and severity only after confirming their defined semantics.
4. Ask the maintainer to make and document a reasoned decision.
5. Add tests proving the conflict is resolved.

Do not rely on arbitrary version-number tie-breakers to resolve a substantive policy conflict.

## 11. Migration Guide Requirements

When replacing a rule, document:
1. Old and new rule IDs.
2. Behavioral, scope, and acceptance changes.
3. Required code or configuration changes.
4. Automated migration availability.
5. Deadline and consequences of not migrating.

Example format:

~~~markdown
## Migration: OLD-RULE → NEW-RULE

**What changed:** Describe the behavior change.

**Migration:** List required actions and verified dependencies.

**Deadline:** Target release or date.
~~~

## 12. References

- `docs/rule-authoring/HOW_TO_WRITE_A_RULE.md` — authoring guidance.
- `schemas/rule.schema.json` — machine-readable rule contract.
- `src/arkhon/rules/validator.py` — validation behavior.
- `src/arkhon/rules/registry.py` — registry behavior.

---

**End of Document**
