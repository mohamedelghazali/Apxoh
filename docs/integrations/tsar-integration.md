# TSAR Integration Guide

**Contract version:** 1.0.0  
**Implementation status:** Initial adapter and verifier implementation; end-to-end compatibility with a released TSAR CLI is not yet certified.  
**Last reviewed:** 2026-11-02

---

## 1. Purpose and trust boundary

TSAR is the delegated security-scanning authority. Apxoh invokes TSAR, receives its output, validates the output and referenced artifacts, and then translates the verified result into a verification outcome.

Apxoh retains ownership of policy, evidence acceptance, gate placement, and release decisions. TSAR output is untrusted input until Apxoh has checked it.

If TSAR is unavailable, its version is incompatible, required evidence is missing, or verification cannot complete, the security result is **BLOCKED**, never PASS.

## 2. Responsibility split

| Apxoh owns | TSAR supplies |
| --- | --- |
| When security verification is required | Scanner execution and raw findings |
| Which project rules and gates apply | TSAR rule identifiers and scan metadata |
| Evidence acceptance criteria | Evidence payload and artifact references |
| Gate and release decisions | Tool results, not release approval |

## 3. Prerequisites

- A TSAR executable is installed and available on PATH.
- The installed TSAR release is within the contract range: >=1.1.0 and <2.0.0.
- The project is a Git checkout with a full 40-character commit SHA.
- The TSAR CLI supports the documented audit invocation and writes a JSON object to stdout.

The CLI invocation and JSON payload are integration assumptions until tested against a real supported TSAR release. A local unit test of the verifier does not prove CLI compatibility.

## 4. Verification sequence

1. Resolve the project commit from Git.
2. Invoke TSAR with the project root and commit.
3. Parse stdout as a JSON object.
4. Persist the raw response under .arkhon/evidence/security/.
5. Validate required fields, commit binding, semantic version, timezone-aware timestamp, freshness, required rule IDs, artifact paths, and SHA-256 hashes.
6. Reject unresolved critical or high findings.
7. Only a verified PASS payload can produce a PASS runner outcome. TSAR FAIL remains FAIL; unavailable or unverifiable evidence remains BLOCKED.

The verifier rejects artifact paths that escape the project evidence root and rejects future timestamps.

## 5. Failure behavior

| Condition | Outcome |
| --- | --- |
| TSAR missing, times out, or cannot start | BLOCKED |
| Non-zero CLI exit or malformed JSON | BLOCKED |
| Missing required payload field or rule ID | BLOCKED |
| Unsupported TSAR version | BLOCKED |
| Stale or future evidence timestamp | BLOCKED |
| Commit mismatch | BLOCKED |
| Missing artifact, path traversal, or hash mismatch | BLOCKED |
| TSAR reports BLOCKED | BLOCKED |
| TSAR reports FAIL or unresolved critical/high findings | FAIL |
| All checks pass and TSAR status is PASS | PASS |

## 6. Rule mapping

integrations/tsar/evidence-mapping.yaml maps TSAR rule identifiers to Apxoh rule identifiers. The mapping preserves the original TSAR finding; it does not imply that Apxoh independently re-ran the scanner rule.

A TSAR finding without a mapping must not silently disappear from governance evaluation. The configured behavior is BLOCKED until the mapping is resolved or an explicit policy is approved.

The mapping identifiers are proposed integration data and must be checked against the actual TSAR rule catalogue and Apxoh rule registry before production use.

## 7. Freshness

The default maximum age is 168 hours. Evidence older than this window is BLOCKED. Evidence with a future timestamp is also rejected.

A project may tighten this limit. The verifier must not silently accept a project-specific value greater than the contract maximum. Project-level configuration is not yet wired into this initial verifier; the current constant is 168 hours.

## 8. What TSAR does not prove

A successful TSAR scan does not prove the absence of all vulnerabilities or defects. It does not establish architectural soundness, performance, reliability, business correctness, or compliance beyond the tested rule set and scope.

## 9. CI and test coverage

tests/integration/tsar/test_tsar_contract.py exercises the contract and verifier without requiring the TSAR executable. It is not an end-to-end test of the external CLI.

A separate integration job is still required to install a supported TSAR release, execute a real scan, validate the payload, and retain the resulting evidence. Do not describe that job as active until its workflow exists and a successful run is recorded.

## 10. Source files

- integrations/tsar/contract.yaml — desired integration contract
- integrations/tsar/evidence-mapping.yaml — proposed rule mapping
- src/arkhon/integrations/tsar/adapter.py — CLI adapter
- src/arkhon/integrations/tsar/verifier.py — evidence verifier
- src/arkhon/verification/runners/tsar_runner.py — verification runner
- docs/threat-model/ARKHON_THREAT_MODEL.md — trust-boundary baseline
- SECURITY_AGENTS.md — agent and evidence-tampering threat model

---

**End of document**
