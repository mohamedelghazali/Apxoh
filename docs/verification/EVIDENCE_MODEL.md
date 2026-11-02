# Apxoh Evidence Model

**Version:** 1.0
**Status:** Active
**Last updated:** 2026-11-01

---

## 1. What Evidence Is

Evidence is any artifact that Apxoh uses to close a gate or produce a
release decision.

Evidence is not opinion. It is not a claim. It is not a summary.

Evidence is a **verifiable record** produced by an **independent tool**,
bound to a **specific commit**, and stored in a form that can be
**re-verified** at any time.

---

## 2. What Counts as Evidence

| Type | Produced by | Used for |
| :--- | :--- | :--- |
| Test result | `pytest` (run by Apxoh) | Testing gate |
| Security scan | TSAR | Security gate |
| Dependency audit | `pip-audit` | Supply chain gate |
| SBOM | `syft` | Supply chain gate |
| Provenance | `slsa-github-generator` | Release gate |
| Code quality report | `ruff`, `mypy` | Code quality gate |
| Performance benchmark | `k6` (via runner) | Performance gate |
| Manual review record | Human reviewer | Any gate (with signature) |

---

## 3. What Does NOT Count

- ❌ An agent's statement that "tests pass".
- ❌ A screenshot.
- ❌ A Markdown report without a signature.
- ❌ A report from a different commit.
- ❌ A report older than the freshness window.
- ❌ A report edited after signing.

These are **claims**, not evidence.

---

## 4. The Evidence Bundle

Every piece of evidence is a JSON file conforming to
`schemas/evidence.schema.json`.

### 4.1 Example

```json
{
  "evidence_id": "EVID-ARKHON-A3F2B1C4",
  "source": "arkhon",
  "source_version": "0.1.0.dev1",
  "commit_sha": "a1b2c3d4e5f6...",
  "executed_at": "2026-11-01T14:30:00Z",
  "status": "PASS",
  "summary": {"pass": 47, "fail": 0, "blocked": 0},
  "artifacts": [
    {"path": "pytest.xml", "sha256": "..."}
  ],
  "signature": {
    "bundle_path": "pytest.xml.sigstore",
    "identity": "https://github.com/.../ci.yml@refs/heads/main",
    "issuer": "https://token.actions.githubusercontent.com"
  }
}
```

### 4.2 Required Fields

| Field | Meaning |
| :--- | :--- |
| `evidence_id` | Unique, stable across re-runs |
| `source` | `arkhon`, `tsar`, or `external-tool` |
| `source_version` | Version of the tool |
| `commit_sha` | Exact commit this applies to |
| `executed_at` | UTC ISO 8601 |
| `status` | PASS / FAIL / BLOCKED / NOT_APPLICABLE / ACCEPTED_RISK |
| `artifacts` | Non-empty list of `{path, sha256}` |

---

## 5. Evidence Lifecycle

```
Produce  →  Hash  →  Sign  →  Store  →  Verify  →  Use  →  Archive
```

### 5.1 Produce

Produced by a runner (pytest, scanner, TSAR) — **not** by Apxoh itself,
**not** by the agent.

### 5.2 Hash

`sha256` of every artifact is computed and recorded.

### 5.3 Sign

The evidence bundle is signed with sigstore. The signature covers:
- The evidence ID
- The commit SHA
- The artifact hashes

### 5.4 Store

Stored under `.arkhon/evidence/<domain>/<evidence_id>.json`.

- **Append-only**: existing bundles are never modified.
- **Hash-verified**: reading a bundle re-computes its hash.

### 5.5 Verify

Before any gate closes, Apxoh re-verifies:
- The hash matches.
- The signature is valid.
- The `commit_sha` matches HEAD.
- The `executed_at` is within the freshness window.

Any failure → `BLOCKED`.

### 5.6 Use

Used by the assessment engine to decide gate status.

### 5.7 Archive

Older than 30 days → moved to `.arkhon/evidence/_archive/`.
Older than 90 days → pruned (unless attached to a release).

---

## 6. Freshness Window

| Evidence type | Freshness |
| :--- | :--- |
| Security scan | 7 days |
| Test results | 30 days |
| Dependency audit | 7 days |
| SBOM | 30 days |
| Provenance | Permanent (bound to release) |
| Manual review | 90 days |

Can be tightened per project, never loosened.

---

## 7. Commit Binding

Every evidence bundle is bound to a specific `commit_sha`.

If the code changes — even a comment — evidence becomes **stale**.

Rationale: Apxoh cannot know whether a comment change also changed
behavior. Re-verification is required.

---

## 8. Signature Model

Signatures use **sigstore** (keyless).

A signature proves:
- ✅ The bundle was signed by a specific identity
- ✅ The bundle has not been modified since signing

A signature does **not** prove:
- ❌ The evidence is correct
- ❌ The signer is trustworthy

Signing establishes provenance, not truth.

---

## 9. Tampering Detection

If any check fails, Apxoh:

1. Sets the gate to `BLOCKED`
2. Logs the incident in `.arkhon/state/incidents.log`
3. Notifies the Security Lead
4. Requires human review before any further work

The compromised evidence is **quarantined**, not deleted.

---

## 10. Evidence and the AI Agent

The AI agent **never** signs evidence. It **never** produces evidence
directly.

The agent produces **code**. Apxoh produces **evidence** by running
independent tools against that code.

This separation is the core of Apxoh's trust model: the agent cannot
fabricate what it did not sign.

---

## 11. Reference

- `schemas/evidence.schema.json` — format
- `docs/EVIDENCE_INTEGRITY.md` — integrity model
- `src/arkhon/evidence/collector.py` — collection
- `src/arkhon/evidence/integrity.py` — verification
- `src/arkhon/evidence/store.py` — storage
- `tools/signing/sign-artifacts.py` — signing

---

**End of Document**
