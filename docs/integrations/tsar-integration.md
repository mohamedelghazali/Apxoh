# TSAR Integration Guide

**Contract version:** 1.1.0  
**Implementation status:** Adapter targets the released TSAR 1.1.x `scan --format sarif` CLI. CI runs a real scanner integration test; this does not imply crypto, dependency, or ASVS coverage.  
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
- The TSAR CLI supports `tsar scan <path> --format sarif --output <file>` and writes SARIF 2.1.0.

The CLI invocation is exercised against the pinned TSAR source revision in the dedicated GitHub Actions end-to-end job. Unit tests alone are not treated as proof of CLI compatibility.

## 4. Verification sequence

1. Resolve the project commit from Git.
2. Invoke TSAR with the project root using its supported `scan` command.
3. Parse the generated SARIF 2.1.0 file and verify the driver identity and version.
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

A TSAR finding without a mapping must not silently disappear from governance evaluation. The original SARIF rule ID and finding are retained. Apxoh does not invent a mapping for rules absent from its verified mapping registry.

The mapping identifiers are proposed integration data and must be checked against the actual TSAR rule catalogue and Apxoh rule registry before production use.

## 7. Freshness

The default maximum age is 168 hours. Evidence older than this window is BLOCKED. Evidence with a future timestamp is also rejected.

A project may tighten this limit. The verifier must not silently accept a project-specific value greater than the contract maximum. Project-level configuration is not yet wired into this initial verifier; the current constant is 168 hours.

## 8. Coverage boundary

The current TSAR 1.1.x CLI executes secret scanning and static security review. Its SARIF output does not prove cryptographic inventory, dependency vulnerability scanning, authentication/authorization testing, or ASVS compliance. Those controls require separate tools and evidence. The synthetic `TSAR-SCAN-EXECUTED` marker records only that the scanner ran; it is not a claim that every security domain was tested.

## 9. What TSAR does not prove

A successful TSAR scan does not prove the absence of all vulnerabilities or defects. It does not establish architectural soundness, performance, reliability, business correctness, or compliance beyond the tested rule set and scope.

## 10. CI and test coverage

tests/integration/tsar/test_tsar_contract.py exercises the contract and verifier without requiring the TSAR executable. It is not an end-to-end test of the external CLI.

The `tsar-e2e` workflow job installs the pinned TSAR source checkout, runs the actual CLI against a clean Git fixture, and asserts a verified PASS outcome. Its run must pass before claiming operational compatibility.

## 11. Source files

- integrations/tsar/contract.yaml — desired integration contract
- integrations/tsar/evidence-mapping.yaml — proposed rule mapping
- src/arkhon/integrations/tsar/adapter.py — CLI adapter
- src/arkhon/integrations/tsar/verifier.py — evidence verifier
- src/arkhon/verification/runners/tsar_runner.py — verification runner
- docs/threat-model/ARKHON_THREAT_MODEL.md — trust-boundary baseline
- SECURITY_AGENTS.md — agent and evidence-tampering threat model

---

**End of document**
