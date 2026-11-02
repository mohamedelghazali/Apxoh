# Apxoh Evidence Model

**Version:** 1.0
**Status:** Active — specification; implementation status of individual controls must be verified.
**Last updated:** 2026-11-01

---

## 1. What Evidence Is

Evidence is an artifact that Apxoh may use to evaluate a rule, close a
gate, or support a release decision.

Evidence is not opinion, an agent's claim, or an unverified summary. A
useful evidence record identifies its producer, the tool and version,
the target commit, execution time, result, and the artifacts needed for
independent review.

Evidence quality depends on provenance and validation as well as
integrity. A SHA-256 digest alone does not prove who produced an artifact
or whether the artifact supports the claim.

---

## 2. What May Count as Evidence

| Type | Potential producer | Possible use |
| :--- | :--- | :--- |
| Test result | Test runner executed by Apxoh | Testing gate |
| Security scan | TSAR or another configured scanner | Security gate |
| Dependency audit | Configured dependency auditor | Supply-chain gate |
| SBOM | Configured SBOM generator | Supply-chain gate |
| Provenance | Configured build-provenance workflow | Release gate |
| Code quality report | Configured linter/type checker | Code-quality gate |
| Performance benchmark | Configured benchmark runner | Performance gate |
| Manual review record | Authorized human reviewer | Gate when policy permits |

A tool name in this table does not mean that the tool is installed,
configured, executed, or trusted in a given repository.

---

## 3. What Does NOT Count by Itself

- An agent's statement that "tests pass".
- A screenshot without verifiable source artifacts.
- A Markdown report without traceable underlying evidence.
- A report from a different commit when commit binding is required.
- A report outside the applicable freshness window.
- A report edited after its integrity/authenticity protection was applied.

These may provide context, but they do not independently establish a
passing verification result.

---

## 4. The Evidence Bundle

Evidence bundles are intended to conform to
`schemas/evidence.schema.json`.

### 4.1 Illustrative Example

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
    {"path": "pytest.xml", "sha256": "replace-with-real-sha256"}
  ]
}
```

This example is illustrative and must be made schema-valid before use.

### 4.2 Core Fields

| Field | Meaning |
| :--- | :--- |
| `evidence_id` | Unique identifier for this evidence record |
| `source` | Producer, such as `arkhon`, `tsar`, or `external-tool` |
| `source_version` | Version of the producing tool |
| `commit_sha` | Exact commit to which the evidence applies |
| `executed_at` | Execution timestamp |
| `status` | Result allowed by the evidence schema |
| `artifacts` | Artifact references and integrity digests |

The schema is authoritative for required fields and allowed values.

---

## 5. Evidence Lifecycle

```
Produce  →  Hash  →  Sign (when configured)  →  Store  →  Verify  →  Use
```

### 5.1 Produce

A configured runner executes an independent tool and captures its
outputs. The runner's identity and execution context should be recorded.
An agent's unsupported assertion is not a substitute for execution.

### 5.2 Hash

A SHA-256 digest may be computed for every artifact. Hashing supports
integrity checking against a recorded digest; it does not establish
authenticity or correctness.

### 5.3 Sign

Evidence signing is a required capability only when the active project
policy and signing workflow require it. Sigstore is a proposed keyless
signing mechanism. Do not claim a bundle is signed unless a signature
was actually produced and independently verified.

A signature may bind an identity and artifact bytes. It does not prove
that the evidence is correct or that the signer is trustworthy.

### 5.4 Store

The intended location is:

`.arkhon/evidence/<domain>/<evidence_id>.json`

Append-only storage, atomic writes, retention, encryption, and access
controls are requirements to be implemented and verified. A directory
or file existing at this path does not prove those properties.

### 5.5 Verify

Before evidence is used to close a gate, the implementation should
validate, as required by policy:

- Evidence schema and required fields.
- Artifact existence and SHA-256 digests.
- Signature and signer identity, when signing is required.
- Commit binding.
- Timestamp validity and freshness.
- Producer and tool identity.
- Rule/domain association and completeness.

Any missing required artifact, tool, or verification step must result
in `BLOCKED`, not `PASS`.

### 5.6 Use

Only validated evidence may contribute to assessment and gate decisions.
The assessment engine must apply the active policy and must not treat
unavailable evidence as a successful result.

### 5.7 Retention and Archive

Retention periods and archive behavior must be configured by policy.
The following are example policy values, not claims of implemented
automatic retention:

- Archive after 30 days.
- Prune after 90 days unless attached to a release.

Deletion must account for legal, contractual, security, and incident
preservation requirements.

---

## 6. Freshness Window

Freshness is policy-specific. Example defaults:

| Evidence type | Example freshness |
| :--- | :--- |
| Security scan | 7 days |
| Test results | 30 days |
| Dependency audit | 7 days |
| SBOM | 30 days |
| Provenance | Bound to a specific release |
| Manual review | 90 days |

Projects may tighten these windows. A policy must explicitly define
whether any extension is permitted; do not silently reuse stale evidence.

---

## 7. Commit Binding

Where commit binding is required, every evidence bundle identifies the
exact commit it evaluates.

If the target commit changes, evidence for the previous commit is not
evidence for the new commit. Re-verification is required unless a
documented policy explicitly defines a narrower impact model.

---

## 8. Signature Model

Sigstore keyless signing is a supported design option.

A successfully verified signature can provide evidence that:
- The signed bytes have not changed since signing.
- The signing identity satisfies the configured trust policy.

A signature does **not** prove:
- The evidence is correct.
- The tool was configured correctly.
- The signer is trustworthy for every purpose.
- The underlying project is secure.

Signing establishes provenance and integrity, not truth.

---

## 9. Tampering Detection

The intended response to failed integrity or authenticity checks is:

1. Set the affected gate to `BLOCKED`.
2. Preserve relevant incident details in a protected audit record.
3. Notify the configured security contact.
4. Quarantine suspect evidence without destroying forensic material.
5. Require authorized review before the evidence is reused.

Logging, notification, quarantine, and access controls must be verified
in the implementation before being described as operational behavior.

---

## 10. Evidence and the AI Agent

The AI agent must not fabricate evidence or claim that a check passed
without a real result. Evidence production, signing, and gate decisions
belong to the configured verification and governance mechanisms.

The agent may help interpret results, but its interpretation is not a
replacement for independently validated evidence.

---

## 11. Reference

- `schemas/evidence.schema.json` — evidence contract
- `docs/EVIDENCE_INTEGRITY.md` — integrity policy
- `src/arkhon/evidence/collector.py` — evidence collection
- `src/arkhon/evidence/integrity.py` — integrity verification
- `src/arkhon/evidence/store.py` — evidence storage
- `tools/signing/sign-artifacts.py` — signing workflow, if present and configured

---

**End of Document**
