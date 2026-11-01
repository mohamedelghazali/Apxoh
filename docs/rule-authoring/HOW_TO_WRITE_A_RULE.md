# How to Write an Apxoh Rule

**Audience:** Contributors adding or modifying rules in `rules/`.
**Last updated:** 2026-11-01

---

## 1. Before You Write

Answer these questions first:

1. **What domain does this rule belong to?** Choose one of the domains declared by the manifest and implemented in `src/arkhon/core/constants.py`.
2. **What does it enforce?** State the requirement in one sentence with a measurable acceptance criterion.
3. **How is it verified?** Choose deterministic, assisted, human, delegated, or hybrid verification.
4. **What evidence does it require?** Name the artifacts that must be produced and checked.
5. **What happens on failure?** Define FAIL, BLOCKED, or an approved ACCEPTED_RISK outcome.

If any answer is unknown, keep the rule proposed; do not activate it.

## 2. File Layout

Rules live in `rules/<domain>/`. Use this naming convention:

~~~text
<RULE_ID>-<kebab-case-slug>.yaml
~~~

Example: `rules/requirements/SE-REQ-001-verifiable-requirements.yaml`.

The ID prefix must match the domain mapping in `DOMAIN_RULE_PREFIX`.

## 3. Minimal Rule Template

~~~yaml
id: SE-REQ-001
metadata:
  title: Verifiable Requirements
  domain: requirements
  version: 1.0.0
  status: proposed
  severity: high
  enforcement: blocking
scope:
  project_types: [all]
  lifecycle_stages: [requirements]
requirement:
  statement: >
    Every approved functional requirement must have at least one
    measurable and verifiable acceptance criterion.
verification:
  mode: deterministic
  methods: [schema-validation, requirements-audit]
acceptance:
  unverified_requirements: 0
evidence:
  required:
    - requirements-register
    - validation-report
failure:
  actions: [create-finding, block-stage, require-remediation]
tests:
  positive: required
  negative: required
  regression: required
~~~

The actual accepted fields and constraints are defined by `schemas/rule.schema.json` and semantic validation in `src/arkhon/rules/validator.py`. Treat the schema and validator as authoritative if this guide differs.

## 4. Field-by-Field Guidance

### `id`
- Must match `^SE-[A-Z]+(-[A-Z]+)?-\\d{3,}$`.
- Must use the prefix assigned to its domain.
- Never reuse an ID, including after archival.

### `metadata.domain`
Use a domain declared in the current manifest/constants. Do not invent a domain locally; propose a manifest change first.

### `metadata.version`
- `1.0.0`: first approved version.
- Patch: wording or clarification without behavior change.
- Minor: backward-compatible verification additions.
- Major: changed acceptance criteria, scope, or behavior.

### `metadata.status`
- `proposed`: under review; not enforced.
- `active`: eligible for enforcement after approval and merge.
- `deprecated`: retained during migration; enforcement behavior must follow the engine's explicit policy.
- `archived`: historical only and excluded from active loading.

Do not assume that setting a YAML status alone activates enforcement; confirm loader, registry, and gate behavior.

### `metadata.severity`
- `critical`: highest impact; release-blocking under the configured policy.
- `high`: serious impact.
- `medium`: moderate impact.
- `low`: limited impact or informational.

Severity and enforcement are separate dimensions. Do not infer one from the other.

### `metadata.enforcement`
- `advisory`: report without blocking.
- `required`: required before the applicable stage completes.
- `blocking`: prevents the configured transition when unsatisfied.
- `critical`: highest enforcement level.

An exception must never silently convert missing evidence into PASS.

### `scope`
Declare applicable project types, lifecycle stages, and any language constraints supported by the schema. Prefer explicit scope over broad assumptions.

### `requirement.statement`
Write one unambiguous, testable statement. Avoid subjective terms such as “good”, “secure enough”, or “fast” unless quantified.

### `verification.mode`
| Mode | Meaning |
| --- | --- |
| `deterministic` | A deterministic tool can decide the result. |
| `assisted` | A tool produces data that requires human interpretation. |
| `human` | A qualified reviewer makes the decision. |
| `delegated` | A named external authority performs verification. |
| `hybrid` | More than one verification mode is combined. |

For delegated verification, identify the delegate using the field required by the current schema and validator. Do not assume TSAR is available unless its integration is configured and verified.

### `verification.methods`
List concrete methods such as `schema-validation`, `unit-tests`, or a configured SAST integration. A method name is not proof that the tool ran.

### `acceptance`
Use measurable thresholds. Acceptance values must be independently interpretable and must not merely restate a tool's exit code.

### `evidence.required`
Name required artifacts and define how their content, integrity, provenance, freshness, and target commit will be verified. File presence alone is not proof of validity.

### `failure.actions`
Declare the intended response, such as creating a finding, blocking a stage, or requiring remediation. Confirm that the runtime implements each action before describing it as enforced.

### `tests`
Every production rule should have:
- A positive test for compliant input.
- A negative test for non-compliant input.
- A regression test for previously observed defects.

## 5. Validation

From the repository checkout, run:

~~~bash
arkhon validate
pytest
~~~

The validation command should check schema validity, rule semantics, ID/domain consistency, and duplicate IDs. Run tests separately; do not treat a successful schema check as proof that enforcement works.

## 6. Writing Tests

Place rule behavior tests in the rule-test locations defined by the repository. Example patterns:

~~~python
def test_rule_passes_on_verified_requirements(valid_project):
    result = evaluate_rule("SE-REQ-001", valid_project)
    assert result.status == "PASS"


def test_rule_blocks_unverified_requirement(invalid_project):
    result = evaluate_rule("SE-REQ-001", invalid_project)
    assert result.status in {"FAIL", "BLOCKED"}
~~~

Use the actual public API and fixtures present in the codebase. These snippets are illustrative and are not executable until those fixtures and APIs exist.

## 7. Review Checklist

- [ ] Rule ID follows the required pattern.
- [ ] Domain prefix matches the declared domain.
- [ ] Schema and semantic validation pass.
- [ ] Acceptance criteria are measurable.
- [ ] Evidence requirements are explicit.
- [ ] Failure behavior is implemented, not merely declared.
- [ ] Positive, negative, and regression tests exist.
- [ ] No duplicate or conflicting rule exists.
- [ ] `arkhon validate` and relevant tests pass.
- [ ] Rule changelog is updated if that changelog is maintained.

## 8. References

- `schemas/rule.schema.json` — machine-readable rule contract.
- `docs/rule-authoring/RULE_LIFECYCLE.md` — lifecycle and review process.
- `src/arkhon/rules/validator.py` — semantic validation.
- `src/arkhon/rules/registry.py` — rule indexing and lookup.

---

**End of Guide**
