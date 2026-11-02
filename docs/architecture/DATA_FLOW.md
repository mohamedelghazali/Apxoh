# Apxoh Data Flow

**Version:** 1.0
**Status:** Active
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
   │ Verification │ ← runs pytest, ruff, mypy, TSAR
   │   Engine     │
   └──────┬───────┘
          │
          │  produces
          ▼
   ┌──────────────┐
   │   Evidence   │ ← SHA-256, sigstore, commit-binding
   │    Store     │
   └──────┬───────┘
          │
          │  `arkhon assess`
          ▼
   ┌──────────────┐
   │  Assessment  │ ← score, gates, decision
   │   Engine     │
   └──────┬───────┘
          │
          │  `arkhon report`
          ▼
   ┌──────────────┐
   │    Report    │ ← JSON + Markdown
   └──────────────┘
```

---

## 2. Verification Flow (Detailed)

```
1. CLI invoked: `arkhon verify --domain testing`
        │
        ▼
2. Load manifest + rules + profile
        │
        ▼
3. Resolve runners for domain
   (testing → PytestRunner)
        │
        ▼
4. For each runner:
        │
        ├─→ Execute tool (pytest)
        │       │
        │       ▼
        │   Produce artifacts (JUnit XML)
        │
        ├─→ Compute SHA-256 of artifacts
        │
        └─→ Determine outcome (PASS/FAIL/BLOCKED)
        │
        ▼
5. Aggregate outcomes → overall status
        │
        ▼
6. Build evidence bundle:
   {
     evidence_id,
     source: "arkhon",
     commit_sha,
     executed_at,
     status,
     artifacts: [{path, sha256}]
   }
        │
        ▼
7. Sign evidence (sigstore)
        │
        ▼
8. Write to .arkhon/evidence/testing/
        │
        ▼
9. Return VerificationRun with evidence_id
```

---

## 3. Evidence Flow

```
Produce  →  Hash  →  Sign  →  Store  →  Verify  →  Use
   │          │       │        │          │         │
   │          │       │        │          │         └─ Gate closes
   │          │       │        │          └─ Hash + signature + commit + freshness
   │          │       │        └─ .arkhon/evidence/<domain>/
   │          │       └─ sigstore OIDC
   │          └─ SHA-256
   └─ Runner output
```

---

## 4. Assessment Flow

```
1. `arkhon assess` invoked
        │
        ▼
2. Load all evidence under .arkhon/evidence/
        │
        ▼
3. For each domain, compute ratio (pass/total)
        │
        ▼
4. Apply weights:
   requirements             15%
   architecture & code      10%
   testing                  15%
   security                 20%
   performance              10%
   reliability              10%
   scalability              10%
   docs & deployment        10%
        │
        ▼
5. Compute score = Σ(ratio × weight)
        │
        ▼
6. Evaluate gates:
   - Group outcomes by gate
   - Critical failures → FAIL
   - Blocking failures → BLOCKED
   - Otherwise → PASS
        │
        ▼
7. Make decision:
   - Critical gate FAIL → REJECTED
   - Blocking gate BLOCKED → PENDING_EVIDENCE
   - Score < 80 → REJECTED
   - Accepted risks → APPROVED_WITH_CONDITIONS
   - Otherwise → APPROVED
        │
        ▼
8. Return Assessment
```

---

## 5. TSAR Integration Flow

```
Apxoh                           TSAR
  │                              │
  │  `tsar audit --project . ...`│
  ├─────────────────────────────▶│
  │                              │
  │                              │  runs SAST, DAST, SCA, secrets
  │                              │
  │  JSON payload + artifacts    │
  │◀─────────────────────────────┤
  │                              │
  │  verify_tsar_evidence()      │
  │   - required fields?         │
  │   - commit_sha match?        │
  │   - version in range?        │
  │   - freshness ≤ 168h?        │
  │   - rule_ids complete?       │
  │   - artifact hashes match?   │
  │   - no critical/high?        │
  │                              │
  │  PASS → gate closes          │
  │  BLOCKED → gate blocked      │
  │  FAIL → gate fails           │
  │                              │
  ▼                              ▼
```

---

## 6. Lifecycle Flow

```
project-init
    │ exit: .arkhon/project.yaml valid
    ▼
requirements
    │ exit: all requirements have acceptance criteria
    ▼
architecture
    │ exit: architecture reviewed, threat model documented
    ▼
implementation-planning
    │ exit: all tasks have rule bindings
    ▼
development
    │ exit: code compiles, no critical local findings
    ▼
verification
    │ exit: all runners pass
    ▼
remediation (loop back to development if needed)
    │ exit: all failures resolved or accepted
    ▼
release-review
    │ exit: PRR checklist complete
    ▼
release-approval
    │ exit: decision recorded
    ▼
post-release
```

Each transition is gated. No stage can be skipped.

---

## 7. Reporting Flow

```
Evidence Bundle (JSON)
        │
        ▼
   JsonReporter
        │
        ├─→ report.json (machine-readable)
        │
        └─→ MarkdownReporter
              │
              ├─→ report.md (human-readable)
              │
              └─→ EngineeringQualityRenderer
                    │
                    └─→ 16 .md files (one per section)
```

---

## 8. Agent Interaction Flow

```
AI Agent                      Apxoh
   │                            │
   │  reads AGENTS.md           │
   │  reads SECURITY_AGENTS.md  │
   │  reads system/charter/     │
   │                            │
   │  writes code               │
   ├───────────────────────────▶│
   │                            │
   │  "tests pass"              │  ignores claim
   │                            │
   │                            │  runs pytest
   │                            │  (independently)
   │                            │
   │  receives verification     │
   │◀───────────────────────────┤
   │                            │
   │  if FAIL: remediate        │
   │  if PASS: continue         │
   │                            │
   ▼                            ▼
```

The agent never produces evidence. Apxoh produces evidence by running
independent tools against the agent's code.

---

## 9. Trust Boundaries

| Boundary | Crossing | Control |
| :--- | :--- | :--- |
| Agent → Code | Agent writes files | Governance files read-only |
| Code → Verification | Apxoh reads code | Independent runner |
| Verification → Evidence | Runner produces artifact | SHA-256 + sigstore |
| Evidence → Gate | Assessment reads evidence | Contract verification |
| Gate → Release | Human reviews | Signature + approval |
| Apxoh → TSAR | Apxoh calls TSAR | CLI contract |
| TSAR → Apxoh | TSAR returns evidence | Full verification |

---

**End of Document**
