# Apxoh Data Flow

**Version:** 1.0
**Status:** Active — architectural specification; implementation status must be verified.
**Last updated:** 2026-11-01

---

## 1. The Big Picture

```
Developer / AI Agent
        │
        │  writes code
        ▼
   ┌─────────┐
   │ Project │
   └────┬────┘
        │
        │  `arkhon verify`
        ▼
   ┌──────────────┐
   │ Verification │
   │   Engine     │
   └──────┬───────┘
          │
          │  produces
          ▼
   ┌──────────────┐
   │   Evidence   │
   │    Store     │
   └──────┬───────┘
          │
          │  `arkhon assess`
          ▼
   ┌──────────────┐
   │  Assessment  │
   │   Engine     │
   └──────┬───────┘
          │
          │  `arkhon report`
          ▼
   ┌──────────────┐
   │    Report    │
   └──────────────┘
```

This diagram describes the intended flow. It does not assert that every
runner, signer, verifier, CLI command, or storage control is implemented.

---

## 2. Verification Flow (Detailed)

```
1. CLI invoked: arkhon verify --domain testing
        │
        ▼
2. Load manifest + rules + profile
        │
        ▼
3. Resolve runners for domain
        │
        ▼
4. Execute available runners
        │
        ├─→ Execute tool
        │       │
        │       ▼
        │   Produce artifacts
        │
        ├─→ Compute SHA-256 of artifacts
        │
        └─→ Determine outcome (PASS/FAIL/BLOCKED)
        │
        ▼
5. Aggregate outcomes → overall status
        │
        ▼
6. Build evidence bundle using the evidence schema
        │
        ▼
7. Apply signing only when a configured signer is available
        │
        ▼
8. Store evidence under .arkhon/evidence/<domain>/
        │
        ▼
9. Return verification result
```

The signing and storage steps above are design intent unless their
implementation and runtime configuration have been independently verified.
A missing required tool or evidence artifact must result in BLOCKED, not PASS.

---

## 3. Evidence Flow

```
Produce  →  Hash  →  Sign (if configured)  →  Store  →  Verify  →  Use
   │          │              │                 │          │         │
   │          │              │                 │          │         └─ Gate evaluation
   │          │              │                 │          └─ Hash, signature, commit, freshness
   │          │              │                 └─ Evidence storage
   │          │              └─ Optional configured signing workflow
   │          └─ SHA-256 integrity digest
   └─ Runner output
```

A digest detects content changes relative to a recorded digest; it does
not establish who produced an artifact or whether its contents are correct.

---

## 4. Assessment Flow

```
1. Assessment command invoked
        │
        ▼
2. Load available evidence
        │
        ▼
3. Validate evidence contracts and freshness
        │
        ▼
4. Compute configured domain ratios and weights
        │
        ▼
5. Evaluate required gates
        │
        ▼
6. Make a decision from score, gates, and accepted risks
        │
        ▼
7. Return assessment result
```

Weights, score thresholds, required gates, and accepted-risk behavior
must come from the active project/profile policy. The following is an
illustrative policy model, not a claim that these exact weights are
currently enforced:

| Domain | Illustrative weight |
| :--- | ---: |
| Requirements | 15% |
| Architecture & code | 10% |
| Testing | 15% |
| Security | 20% |
| Performance | 10% |
| Reliability | 10% |
| Scalability | 10% |
| Documentation & deployment | 10% |

A high numeric score must never override a failed critical gate. Missing
required evidence or a required verification tool must remain BLOCKED.

---

## 5. TSAR Integration Flow

```
Apxoh                           TSAR
  │                              │
  │  invoke configured contract  │
  ├─────────────────────────────▶│
  │                              │
  │                              │  security analysis
  │  structured result + evidence
  │◀─────────────────────────────┤
  │                              │
  │  verify TSAR evidence        │
  │   - required fields?         │
  │   - commit_sha match?        │
  │   - version in range?        │
  │   - freshness within policy? │
  │   - required rule IDs?       │
  │   - artifact hashes match?   │
  │                              │
  │  PASS / BLOCKED / FAIL       │
  │                              │
  ▼                              ▼
```

The actual command, payload, version range, rule IDs, and evidence
contract must match the separately maintained TSAR integration contract.
Do not infer successful delegation merely from a profile declaration.

---

## 6. Lifecycle Flow

```
project-init
    │
    ▼
requirements
    │
    ▼
architecture
    │
    ▼
implementation-planning
    │
    ▼
development
    │
    ▼
verification
    │
    ▼
remediation (loop back to development if needed)
    │
    ▼
release-review
    │
    ▼
release-approval
    │
    ▼
post-release
```

This is the intended lifecycle. A transition is gated only where an
enforcing implementation and required evidence exist. Documentation
alone does not enforce a stage transition.

---

## 7. Reporting Flow

```
Validated Assessment
        │
        ▼
   JSON Reporter
        │
        ├─→ Machine-readable report
        │
        └─→ Markdown Reporter
              │
              └─→ Human-readable report sections
```

Report formats and section counts are governed by the active report
schema and templates.

---

## 8. Agent Interaction Flow

```
AI Agent                      Apxoh
   │                            │
   │  reads governance guidance │
   │                            │
   │  writes code               │
   ├───────────────────────────▶│
   │                            │
   │  claims "tests pass"        │  claim is not evidence
   │                            │
   │                            │  runs configured tools
   │                            │  records verifiable outputs
   │                            │
   │  receives result           │
   │◀───────────────────────────┤
   │                            │
   ▼                            ▼
```

An agent's statement is not a verification result. Apxoh must rely on
independently executed tools and validated evidence artifacts.

---

## 9. Trust Boundaries

| Boundary | Crossing | Intended control |
| :--- | :--- | :--- |
| Agent → Code | Agent writes files | Governance-file protection and review |
| Code → Verification | Apxoh reads code | Independent configured runners |
| Verification → Evidence | Runner produces artifact | Hashing and schema validation |
| Evidence → Gate | Assessment reads evidence | Contract, commit, and freshness verification |
| Gate → Release | Human reviews | Recorded approval and configured authorization |
| Apxoh → TSAR | Apxoh calls TSAR | Versioned integration contract |
| TSAR → Apxoh | TSAR returns evidence | Independent evidence verification |

A listed control is an architectural requirement, not proof that the
control is deployed or effective.

---

**End of Document**
