# Apxoh Evidence Integrity Model

**Version:** 1.0
**Status:** Runtime enforcement implemented for evidence integrity, SBOM, and release-attestation gates; validate against the exact CI/release run before claiming a release passed
**Owner:** Security Lead (TBD)
**Last reviewed:** 2026-11-03
**Review cadence:** Every release and after any evidence-integrity incident

---

## 1. What Counts as Evidence

**Evidence** is an artifact Apxoh uses to evaluate a rule, close a gate, or support a release decision. Evidence is not an agent's claim or an unsupported summary. It must be traceable to an actual check, review, or trusted source.

### 1.1 Evidence Types

| Type | Expected producer | Potential use |
| :--- | :--- | :--- |
| Test results | Trusted Apxoh runner executing `pytest` | Testing Gate |
| Security scan results | Configured security tool or TSAR integration | Security Gate |
| Dependency audit | `pip-audit` or equivalent | Dependency Gate |
| SBOM | Syft or another approved generator | Supply Chain Gate |
| Provenance | SLSA generator / trusted build platform | Release Gate |
| Code quality report | `ruff`, `mypy`, or configured tools | Code Quality Gate |
| Performance benchmarks | Trusted benchmark runner | Performance Gate |
| Manual review record | Authorized human reviewer | Gate requiring human approval |

The producer and suitability of each evidence type must be defined by the applicable gate policy. A tool name alone does not establish that a check ran.

### 1.2 Minimum Evidence Fields

The intended evidence contract should include:

- `evidence_id` — unique identifier for the evidence record.
- `source` — producer identity (for example, Apxoh or an external tool).
- `source_version` — producer/tool version.
- `commit_sha` — source revision to which the evidence applies.
- `executed_at` — trusted execution timestamp in ISO 8601 format.
- `status` — `PASS`, `FAIL`, `BLOCKED`, `NOT_APPLICABLE`, or `ACCEPTED_RISK`, as permitted by policy.
- `summary` — structured result counts and relevant findings.
- `artifacts` — artifact paths or identifiers and SHA-256 digests.
- `signature` — signature bundle or a reference to verifiable provenance, when required by the gate.

**Schema compatibility note:** the current `schemas/evidence.schema.json` is a minimal schema and does not yet define all fields listed above. The schema and producer/verifier implementations must be evolved and tested before this full contract is treated as enforced. Until then, missing required evidence must result in `BLOCKED`, not an assumed pass.

---

## 2. Storage Model

### 2.1 Location

Evidence is intended to be stored within the governed project:

```text
<project>/.arkhon/evidence/
├── requirements/
├── architecture/
├── code-quality/
├── testing/
├── security/
├── performance/
├── reliability/
├── scalability/
└── release/
```

The exact directory layout may vary by project profile. Consumers must not assume that every directory exists.

### 2.2 Retention

Target retention policy:

| Age | Target action |
| :--- | :--- |
| 0–30 days | Active evidence |
| 30–90 days | Archive, where configured |
| 90+ days | Prune only if not subject to audit, legal hold, incident investigation, or release retention |

Evidence attached to a released version should be retained with the release record for the supported lifetime of that release and any applicable audit/legal requirement. "Forever" retention must not be promised unless storage and retention controls support it.

### 2.3 Encryption at Rest

Apxoh does not claim to encrypt evidence at rest by itself. Encryption depends on the storage environment:

- In a Git repository, repository access controls and storage-provider encryption apply; Git content addressing is not encryption.
- In CI, use ephemeral workspaces and avoid unnecessary persistence.
- In cloud storage, use the provider's encryption controls and customer-managed keys where required.

Sensitive scan output must be redacted before storage. Do not store secret values, access tokens, private keys, or unnecessary personal data in evidence artifacts.

### 2.4 `.gitignore` Policy

Evidence persistence is a project decision governed by the project's configuration and audit needs. If `.arkhon/evidence/` is ignored, evidence will not be part of normal Git history unless explicitly included through an approved process.

Projects that commit evidence must assess repository visibility, size, sensitive-data exposure, and retention. Apxoh may publish aggregate reports while retaining raw evidence in a separately controlled store; this behavior must be verified for each deployment.

---

## 3. Integrity Mechanisms

### 3.1 SHA-256 Per Artifact

Every evidence artifact used by a gate should have a SHA-256 digest recorded in its evidence metadata or a tamper-evident manifest. At verification time, the digest must be recomputed from the actual artifact bytes.

A hash detects changes relative to a trusted recorded digest; it does not prove who created the artifact or whether its contents are truthful.

### 3.2 Chain of Custody

Evidence should record:

- The tool or reviewer that produced it, including version or identity.
- The source revision and relevant input identifiers.
- The execution time and environment.
- The workflow or runner identity, where applicable.
- The signer identity and signature bundle, when signing is required.

Any missing chain-of-custody field required by the relevant gate must produce `BLOCKED`.

### 3.3 Timestamps

Evidence timestamps should:

- Be generated by the trusted runner or Apxoh execution context, not supplied solely by the agent.
- Use UTC and ISO 8601.
- Be protected by the evidence signature or provenance when available.
- Include a defined policy for clock skew and timestamp validation.

A missing, malformed, or untrusted timestamp must block evidence when freshness is required.

---

## 4. Commit Binding

Every code-derived evidence artifact must be bound to the exact source state it evaluates.

### 4.1 How Binding Works

1. The proposed source revision is identified.
2. A trusted Apxoh runner executes the declared verification.
3. Evidence records the evaluated revision and relevant inputs.
4. If source or relevant inputs change, affected evidence must be regenerated.
5. Evidence for an earlier revision must not be treated as proof for a later revision without an explicit, validated baseline policy.

### 4.2 Verification of Binding

For a clean committed checkout, the gate may compare:

```text
evidence.commit_sha == evaluated_git_revision
```

A simple comparison with `git rev-parse HEAD` is insufficient when the working tree is dirty, submodules or generated inputs differ, or dependency lockfiles are not represented. The implementation must define and record the full evaluated source state.

Mismatch must produce `BLOCKED` with reason `evidence-commit-mismatch`.

### 4.3 Exception: Pre-approved Baselines

Some evidence may apply to an explicitly approved baseline, such as a dependency audit for a tagged release. In that case, the record must identify both the baseline and the evaluated revision, and the gate policy must define why the evidence remains applicable.

Illustrative metadata:

```yaml
commit_sha: "evaluated-commit"
baseline_commit: "approved-baseline-commit"
```

The baseline relationship must be verified; an ancestor relationship alone does not prove that evidence remains applicable to changed files or dependencies.

---

## 5. Signature Model

### 5.1 Sigstore Signing

Release artifacts are signed by the pinned Cosign CLI in `.github/workflows/slsa-release.yml` using GitHub Actions OIDC. The release workflow signs wheels, source distributions, and the generated CycloneDX source SBOM; it then verifies those bundles before the release evidence gate can pass.

- **Signing tool:** Cosign `v3.1.4` (`cosign sign-blob --bundle`).
- **Verifier:** Cosign `verify-blob` with issuer `https://token.actions.githubusercontent.com`.
- **Identity:** the exact `slsa-release.yml` workflow identity for the configured semantic release tag, not an arbitrary workflow or tag.
- **Bundle:** a Sigstore bundle stored beside the signed artifact.

The standalone `tools/signing/sign-artifacts.py` helper is optional; the protected release workflow uses Cosign directly. Local developer signing is not accepted by the release gate.

### 5.2 What Signing Proves

A valid signature can establish that:

1. The signed bytes match the artifact that was signed.
2. The signature verifies under the applicable cryptographic and trust policy.
3. The signing identity was authenticated according to the signing system's rules.

### 5.3 What Signing Does Not Prove

Signing does **not** prove:

- The artifact is correct.
- The signer is authorized for the particular gate unless policy checks that identity.
- The underlying check was executed honestly or in a trustworthy environment.
- The artifact was produced from the claimed source unless provenance binds it.

Signing establishes integrity and an identity assertion under a trust policy, not truth.

### 5.4 Signing Identity

| Context | Intended identity |
| :--- | :--- |
| CI | OIDC identity of the approved workflow |
| Local developer | Developer identity, only where explicitly permitted |
| Release provenance | Identity asserted by the configured SLSA generator |

The verifier must validate the expected issuer, identity, artifact subject, and workflow/repository context. Do not assume all identities above are currently configured.

---

## 6. Verification Procedure

Before a gate closes, Apxoh must verify the evidence required by that gate.

### 6.1 Verification Steps

```text
1. Evidence exists?                         No -> BLOCKED
2. Schema valid for the declared version?   No -> BLOCKED
3. Artifact digest matches?                 No -> BLOCKED
4. Required signature/provenance valid?     No -> BLOCKED
5. Signer identity authorized?              No -> BLOCKED
6. Source revision and inputs match?        No -> BLOCKED
7. Freshness within policy window?          No -> BLOCKED
8. Evidence status satisfies the gate?      No -> FAIL or BLOCKED
9. Summary and artifact references valid?   No -> BLOCKED
10. All required evidence types present?    No -> BLOCKED
```

Every step should produce an auditable verification result. The gate must not infer success from missing data or a tool that did not run.

### 6.2 Implemented supply-chain gates

The runtime separates source inventory from release authenticity:

- `arkhon verify <project> --domain supply-chain` runs Syft and writes a CycloneDX SBOM bound to the checked-out commit. CycloneDX versions 1.4–1.7 are accepted. The verification engine validates the commit binding before it records `PASS`.
- `arkhon verify <project> --domain release-attestations` is an explicit release-only gate. `.arkhon/supply-chain.json` must identify in-project `artifact`, `provenance`, `signature_bundle`, and `source_tag` paths/values.
- The release tag must be a semantic version tag and must resolve to the exact checked-out `HEAD`. `slsa-verifier` checks both the repository URI and exact tag; Cosign checks the exact workflow/tag certificate identity and GitHub OIDC issuer.
- The engine re-runs SLSA and Cosign verification before recording release-attestation `PASS`. The JSON reporter repeats cryptographic verification when consuming that evidence.
- `arkhon verify <project> --domain all` includes local SBOM generation but intentionally excludes `release-attestations`, because ordinary source checkouts do not have release artifacts/provenance.

The tag-triggered SLSA release workflow builds distributions, generates and signs a CycloneDX SBOM, creates SLSA provenance, verifies signatures, and runs both Apxoh evidence gates. A successful pull-request CI run proves the source SBOM path; it does not by itself prove that a real release tag has completed the OIDC/SLSA/Cosign workflow.

### 6.2 Re-verification

Evidence may be re-verified at any time. Re-verification must not modify the original signed evidence; it should create a separate verification record with verifier version, timestamp, policy version, and outcome.

---

## 7. Tampering Detection

### 7.1 Detection Chain

See `SECURITY_AGENTS.md` §4.1.

### 7.2 Tampering Indicators

| Indicator | Meaning | Required response |
| :--- | :--- | :--- |
| SHA-256 mismatch | Artifact differs from recorded digest | `BLOCKED` + investigation |
| Signature invalid | Signature cannot be trusted | `BLOCKED` + investigation |
| Signer identity mismatch | Signer is not authorized | `BLOCKED` |
| `commit_sha` mismatch | Evidence applies to another revision | `BLOCKED` + re-verification |
| Missing timestamp | Freshness/provenance cannot be established | `BLOCKED` where required |
| Missing tool version | Producer provenance is incomplete | `BLOCKED` where required |
| Duplicate `evidence_id` | Possible replay or collision | `BLOCKED` pending investigation |
| Evidence claims a future revision | Possible malformed or forged metadata | `BLOCKED` pending investigation |

### 7.3 What Happens on Detection

1. The affected gate becomes `BLOCKED`.
2. A security incident record is created in the configured incident store (target path: `.arkhon/state/incidents.log`).
3. The designated Security Lead is notified through a configured channel.
4. Human review is required before the affected gate is reconsidered.
5. The potentially compromised revision is marked or quarantined as untrusted; it is not silently deleted.
6. Relevant artifacts and logs are preserved under the applicable retention and privacy policy.

These actions are requirements; their implementation and notification paths must be verified before being described as automated.

---

## 8. References

- `schemas/evidence.schema.json` — current evidence schema (minimal; does not yet express the full contract above)
- `.github/workflows/slsa-release.yml` — pinned Cosign signing and SLSA provenance release workflow
- `src/arkhon/verification/runners/tsar_runner.py` — TSAR CLI runner; real CLI scan is exercised by `.github/workflows/tsar-e2e.yml`
- `SECURITY_AGENTS.md` §4 — evidence tampering defenses
- `docs/SUPPLY_CHAIN.md` §5 — artifact signing

---

**End of Document**
