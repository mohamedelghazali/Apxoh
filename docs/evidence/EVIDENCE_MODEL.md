# Apxoh Evidence Model

**Version:** 1.0  
**Status:** Active — specification; implementation must be verified  
**Last updated:** 2026-11-01

---

## 1. What is Evidence

**Evidence** is an artifact or record used by Apxoh to evaluate a rule, close a gate, or inform a release decision.

Evidence is not an agent's opinion or an unsupported claim. A trustworthy evidence record should identify its producer, bind its results to a specific commit, preserve artifact integrity, and be independently re-verifiable.

A hash establishes byte-level integrity relative to a recorded digest. It does not establish that the artifact is correct, complete, authentic, or produced by a trustworthy tool. Signatures and provenance provide additional claims that require independent verification.

---

## 2. What Counts as Evidence

| Evidence type | Intended producer | Potential use |
| :--- | :--- | :--- |
| Test result | `pytest`, invoked by a controlled runner | Testing gate |
| Security scan | TSAR | Security gate |
| Dependency audit | `pip-audit` | Supply-chain assessment |
| SBOM | `syft` | Supply-chain assessment |
| Provenance | `slsa-github-generator` or an equivalent trusted workflow | Release assessment |
| Code-quality report | `ruff`, `mypy` | Code-quality assessment |
| Performance benchmark | `k6` via a controlled runner | Performance gate |
| Manual review record | Authorized human reviewer | Applicable gate, subject to identity and approval controls |

These are intended evidence sources, not a claim that all integrations are currently installed or operational.

---

## 3. What Does NOT Count as Evidence

- An agent's statement that tests pass.
- A screenshot without independently verifiable supporting records.
- An unsigned Markdown assertion presented as an approval.
- A report for a different commit.
- A report outside the applicable freshness window.
- An artifact modified after its integrity record or signature was created.
- A file's mere presence without validating its content, origin, scope, and relationship to the claim.

These may be useful context, but they do not independently establish a verification result.

---

## 4. The Evidence Bundle

Evidence bundles are JSON records intended to conform to `schemas/evidence.schema.json`.

### 4.1 Example

```json
{
  "evidence_id": "EVID-ARKHON-A3F2B1C4",
  "source": "arkhon",
  "source_version": "0.1.0.dev1",
  "commit_sha": "a1b2c3d4e5f6789012345678901234567890abcd",
  "executed_at": "2026-11-01T14:30:00Z",
  "status": "PASS",
  "summary": {"pass": 47, "fail": 0, "blocked": 0},
  "artifacts": [
    {"path": "testing/pytest.xml", "sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"}
  ]
}
```

The example is illustrative. The path is interpreted relative to the evidence root used by the verifier.

### 4.2 Required Fields

| Field | Meaning |
| :--- | :--- |
| `evidence_id` | Unique identifier for this evidence record |
| `source` | `arkhon`, `tsar`, or `external-tool` |
| `source_version` | Version of the tool or producer |
| `commit_sha` | Exact commit to which the result applies |
| `executed_at` | Timestamp in ISO 8601 format with timezone |
| `status` | PASS / FAIL / BLOCKED / NOT_APPLICABLE / ACCEPTED_RISK |
| `artifacts` | Non-empty list of `{path, sha256}` records |

The schema is the machine-readable contract. If this document and the schema disagree, resolve the discrepancy explicitly rather than assuming either representation has been enforced.

---

## 5. Evidence Lifecycle

```
Produce  →  Hash  →  Sign (when configured)  →  Store  →  Verify  →  Use  →  Archive
```

### 5.1 Produce

A controlled runner invokes a verification tool and captures its outputs. Apxoh may orchestrate the process, but it must not invent tool results or treat an agent's narrative as tool output.

### 5.2 Hash

A cryptographic digest such as SHA-256 is computed for each artifact. The verifier recomputes the digest when checking the artifact.

### 5.3 Sign

Where signing is configured, the evidence bundle or a canonical representation of it is signed using an established signing mechanism such as Sigstore.

The signed payload must unambiguously bind at least:

- Evidence identifier
- Commit SHA
- Artifact paths and hashes
- Relevant producer identity and execution metadata

The exact canonicalization and signing format must be specified by the implementation. Merely recording signature metadata does not verify a signature.

### 5.4 Store

The intended location is:

```
.arkhon/evidence/<domain>/<evidence_id>.json
```

Required storage properties:

- Append-only behavior at the application API boundary.
- Refusal to replace an existing identifier with different content.
- Safe path handling and validation.
- Integrity verification when records are consumed.

Filesystem permissions, repository controls, and external storage protections are separate controls; an append-only application method alone does not make storage tamper-proof.

### 5.5 Verify

Before evidence is used to close a gate, the verifier should check:

- Bundle structure and schema.
- Artifact existence and SHA-256 digest.
- Signature and signer identity, when signing is required.
- Commit binding against the target revision.
- Timestamp validity and configured freshness window.
- Producer, scope, and rule applicability.

Missing required evidence or unavailable verification capability must produce `BLOCKED`, never `PASS`.

### 5.6 Use

Only successfully verified evidence may support an assessment. A gate must not close merely because a path exists or a status field says `PASS`.

### 5.7 Archive

The proposed retention policy is:

- Evidence older than 30 days may be moved to `.arkhon/evidence/_archive/` when retention requirements permit.
- Evidence older than 90 days may be pruned only when it is not attached to a release and no legal, contractual, incident-response, or audit retention requirement applies.

Archival and deletion must be implemented as explicit, auditable operations. They are not implied by this document.

---

## 6. Freshness Window

Proposed default maximum ages:

| Evidence type | Freshness |
| :--- | :--- |
| Security scan | 7 days |
| Test results | 30 days |
| Dependency audit | 7 days |
| SBOM | 30 days |
| Provenance | Permanent only for the immutable release artifact it identifies |
| Manual review | 90 days |

A project may tighten these limits through `require_fresh_evidence_hours`. It must not loosen a stricter policy inherited from its profile or governing rules.

Freshness must be evaluated against a trusted clock and a valid timezone-aware timestamp. Future-dated evidence is invalid.

---

## 7. Commit Binding

Every evidence bundle is bound to a specific `commit_sha`.

When the target commit changes, evidence for the previous commit does not automatically apply to the new commit. A policy may permit carefully scoped reuse for immutable external artifacts, but such reuse must be explicit, justified, and independently verified.

The default policy is to re-run checks for the target commit.

---

## 8. Signature Model

The intended signing model uses keyless signing where supported.

- In CI, an OIDC identity may be issued by the CI platform.
- Local signing requires a supported identity flow and must not silently fall back to an unsigned success.
- Verification must validate the signature, certificate or identity claims, issuer, and trusted transparency/provenance context as applicable.

A valid signature can support claims about signer identity and post-signing integrity. It does **not** prove:

- The evidence is correct.
- The tool was configured appropriately.
- The signer is authorized to approve the result.
- The underlying system is secure.

Signing establishes provenance and integrity claims, not truth.

---

## 9. Tampering Detection

If an integrity, signature, commit, or freshness check fails, the intended response is:

1. Set the affected gate to `BLOCKED`.
2. Record an incident in the configured incident log or incident system.
3. Notify the designated security owner through a configured channel.
4. Quarantine the suspect record for forensic review.
5. Require authorized human review before relying on the affected evidence.

Quarantine must preserve the original bytes and relevant metadata. The implementation must not delete suspect evidence as part of routine error handling.

---

## 10. Evidence and the AI Agent

An AI agent is not an evidence authority. It may propose code or request checks, but it must not fabricate runner output, sign evidence on behalf of an authorized identity, or self-approve a release.

Apxoh should invoke independent verification tools and preserve their actual outputs. The verification engine must distinguish a successful tool execution from an unavailable, crashed, skipped, or inconclusive check.

---

## 11. Reference

- `schemas/evidence.schema.json` — evidence record format
- `docs/EVIDENCE_INTEGRITY.md` — integrity policy
- `src/arkhon/evidence/collector.py` — collection
- `src/arkhon/evidence/integrity.py` — integrity and freshness verification
- `src/arkhon/evidence/store.py` — storage
- `tools/signing/sign-artifacts.py` — intended signing tool; verify its presence and behavior before relying on it

---

**End of Document**
