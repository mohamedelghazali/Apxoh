# Apxoh Supply Chain Security Policy

**Version:** 1.0
**Status:** Operational controls implemented; release-specific SLSA/Sigstore evidence is verified per tagged release
**Owner:** Security Lead (TBD)
**Last reviewed:** 2026-11-01
**Review cadence:** Every release, and after any supply chain incident

---

## 1. Scope

This policy covers every artifact, dependency, and process that contributes to an Apxoh release:

- **Source:** repository code, rules, schemas, documentation
- **Build:** Python build chain (`setuptools`, `wheel`, `build`)
- **Dependencies:** direct and transitive Python packages
- **CI/CD:** GitHub Actions workflows and actions
- **Distribution:** PyPI packages, GitHub releases, signed artifacts
- **References:** external standards links (informational only)

The security of AI model providers is managed through the model integration contract, data-handling controls, and independent verification. It remains a third-party dependency risk and is not eliminated by this policy.

---

## 2. Threat Model

Apxoh's supply chain is exposed to:

| Threat | Potential impact | Likelihood |
| :--- | :--- | :--- |
| Compromised upstream dependency | Critical — arbitrary code execution | Medium–High |
| Typosquatted package | Critical — malicious installation | Medium |
| Tampered GitHub Action | Critical — CI compromise | Medium |
| Compromised maintainer account | Critical — repository control | Low–Medium |
| Stolen package-publishing credential | Critical — malicious release | Low–Medium |
| Compromised build environment | High — manipulated artifacts | Medium |
| Stale vulnerable dependency | High — exploitable weakness | Medium–High |

Likelihood values are qualitative planning estimates and must be revisited using repository and deployment evidence.

Full threat details: `docs/threat-model/ARKHON_THREAT_MODEL.md`.

---

## 3. Build Integrity

### 3.1 Target: SLSA Build Level 3

Apxoh targets **SLSA Build Level 3** for release artifacts. A target is not a conformance claim. The release process must be assessed against the applicable SLSA requirements before claiming a level.

| Requirement area | Intended implementation | Verification required |
| :--- | :--- | :--- |
| Scripted build | `pyproject.toml` and `python -m build` | Inspect build configuration and run |
| Hosted build | GitHub Actions hosted runner | Verify workflow run and runner provenance |
| Build isolation | Dedicated release workflow with least privilege | Review workflow permissions and isolation |
| Provenance | `slsa-github-generator` in `.github/workflows/slsa-release.yml` | Verify generated attestation and subject digests |
| Signing | Sigstore-backed provenance | Verify issuer, identity, and signature |
| Publication | Release-attached provenance | Inspect an actual published release |

The release workflow now stages signed build outputs in a draft GitHub release before generating provenance. The release remains a draft; it must not be published until the workflow's signature, provenance, and Apxoh evidence-verification job succeeds. The presence of a workflow file alone does not establish that provenance was generated, signed, published, or successfully verified.

### 3.2 Reproducible Builds

Apxoh does not currently claim bit-for-bit reproducible builds. Reproducibility remains a separate engineering objective. Provenance can bind an artifact to declared source and build inputs, but it does not by itself prove reproducibility or that the build is benign.

### 3.3 Build Environment

Release builds should:

- Run on approved hosted runners, not developer workstations.
- Use least-privilege workflow permissions and avoid exposing publishing credentials to untrusted pull-request code.
- Minimize network access during build execution; dependency acquisition should be controlled and auditable.
- Use reviewed, pinned build dependencies and actions wherever practical.
- Avoid shell injection and unsafe interpolation of untrusted values.
- Preserve build logs and provenance needed for later verification.

Any exception must be documented and reviewed.

---

## 4. Dependency Management

### 4.1 Pinning

Direct runtime and build dependencies should use exact version pins where practical. The current `pyproject.toml` uses exact pins for declared dependencies. This does not lock every transitive dependency: a fully repeatable environment also requires a maintained lock or constraints file with hashes and a defined installation process.

Example:

```toml
dependencies = [
    "PyYAML==6.0.2",
    "jsonschema==4.23.0",
]
```

No unreviewed range specifiers should be introduced for release-critical dependencies. Pin changes require a reviewed pull request.

### 4.2 Update Cadence

| Category | Target cadence | Review |
| :--- | :--- | :--- |
| Security patches | Immediate | Prioritized security PR |
| Minor versions | Monthly | Standard PR |
| Major versions | Quarterly | Full review + compatibility test |
| Development dependencies | Monthly | Standard PR |

Dependabot configuration and actual alert coverage must be verified in the repository settings and `.github/dependabot.yml`; this policy does not assume that every dependency category is already covered.

### 4.3 Verification

Every dependency update must pass, as applicable:

- `pip-audit` against the resolved environment or a correctly prepared dependency set.
- The full test suite.
- License compatibility review.
- Manual review when a package is new, security-sensitive, or introduces significant transitive dependencies.

Do not use hash-enforcement flags unless the dependency input file actually contains the required hashes.

### 4.4 License Compatibility

Apxoh is licensed under Apache-2.0. Dependency license decisions require package-specific legal and distribution review. The following is a screening policy, not legal advice:

| License family | Default treatment |
| :--- | :--- |
| MIT, BSD-2-Clause, BSD-3-Clause, ISC, Apache-2.0, PSF/Python-2.0 | Generally acceptable; preserve required notices |
| MPL-2.0 | Review file-level copyleft obligations and distribution model |
| LGPL-2.1 / LGPL-3.0 | Legal review required; comply with relinking and notice obligations |
| GPL-2.0 / GPL-3.0 | Do not include in distributed Apxoh artifacts without explicit legal approval |
| AGPL-3.0 | Do not include without explicit legal approval |
| SSPL and other non-OSI or source-available terms | Do not include without explicit legal approval |
| Proprietary | Requires explicit license rights and approval |

Automated license scanners are advisory inputs; ambiguous or dual-licensed packages require human review.

### 4.5 New Dependency Admission

Adding a new dependency requires a pull request that includes:

1. Purpose statement and why the standard library or existing dependencies are insufficient.
2. Alternatives considered.
3. License identifier and notice obligations.
4. Maintenance status and upstream security history.
5. Security audit results.
6. Package size and transitive dependency impact.
7. Tests for the integration and failure modes.

---

## 5. Artifact Signing

### 5.1 What Should Be Signed

| Artifact | Intended mechanism | Publication |
| :--- | :--- | :--- |
| Release wheel and sdist | SLSA provenance / Sigstore verification | GitHub release |
| Provenance statement | SLSA generator | GitHub release |
| Evidence bundles | Approved Sigstore workflow using `tools/signing/sign-artifacts.py` | Evidence store |
| Container images (future) | Cosign | To be defined |

Actual signing coverage must be verified per release. Do not describe an artifact as signed merely because a signing script or workflow exists.

### 5.2 Verification for Consumers

Consumers should follow the verification instructions published for the specific release. The following is an illustrative workflow; artifact names, provenance format, and verifier flags must match the actual release assets and generator version:

```bash
# Download the assets for a specific release.
gh release download v0.1.0 --repo mohamedelghazali/Apxoh

# Verify the artifact using the matching SLSA verifier and provenance.
slsa-verifier verify-artifact \
  arkhon-0.1.0-py3-none-any.whl \
  --provenance-path multiple.intoto.jsonl \
  --source-uri github.com/mohamedelghazali/Apxoh
```

Evidence-bundle verification must use the identity and OIDC issuer documented for the actual signer. Do not reuse a release-workflow identity for evidence unless that is the real signing identity.

If required verification fails, consumers must not rely on the artifact until the failure is resolved.

---

## 6. SBOM Generation

### 6.1 Format and Tool

Target release SBOM:

- **Format:** CycloneDX JSON (version selected by the generating tool and validated by CI)
- **Tool:** Syft (Anchore)
- **Frequency:** Every release
- **Publication:** Release attachment; additional package-index attestations only when supported and configured

The repository must verify the selected Syft version, command, output format, and publication workflow before claiming SBOM generation is active.

### 6.2 SBOM Contents

The SBOM should include, where available:

- Direct and transitive runtime components included in the release.
- Component names and versions.
- Package identifiers and supplier information.
- License declarations.
- Cryptographic hashes.
- Dependency relationships.
- Vulnerability findings as a separate, time-stamped scan result where a tool such as Grype is used.

A vulnerability scan is time-dependent and should not be represented as an intrinsic or permanent SBOM property.

### 6.3 Consumer Use

Downstream consumers can use the SBOM to:

- Cross-reference components against their vulnerability intelligence.
- Review transitive dependency changes.
- Automate license and inventory checks.
- Retain a component inventory for each release.

---

## 7. Release Verification

Before a release is published, the release pipeline must enforce the applicable checks:

| Step | Tool / evidence | Blocking target |
| :--- | :--- | :--- |
| Source commit authenticity | `git verify-commit` or trusted platform verification | Yes, when required by release policy |
| Tests | `pytest` | Yes |
| Dependency vulnerabilities | `pip-audit` | Yes, subject to documented exceptions |
| Secret scanning | Gitleaks | Yes |
| SBOM | Syft + schema validation | Yes, once release SBOM generation is configured |
| Provenance | SLSA generator + verifier | Yes, once release provenance is configured |
| Changelog | Manual review | Yes |
| Version consistency | `VERSION` and `pyproject.toml` | Yes |

Any required check that is missing, fails, or cannot be independently verified must block release. A policy table does not prove that the corresponding workflow currently enforces the check. The automated release workflow deliberately leaves the release in draft state after verification; publishing remains a separate maintainer action after reviewing the successful run and its attached assets.

---

## 8. Incident Response for Supply Chain

When a supply chain incident occurs (for example, a compromised dependency or tampered action):

1. **Detect:** Review scanner alerts, upstream advisories, Dependabot alerts, and CI anomalies.
2. **Assess:** Identify affected versions, build runs, releases, credentials, and downstream exposure.
3. **Contain:** Pause affected releases, revoke exposed credentials, and restrict compromised workflows or packages.
4. **Mitigate:** Upgrade to a verified safe version, remove the dependency, or apply a documented compensating control.
5. **Communicate:** Coordinate with reporters and affected users through the approved security channel.
6. **Recover:** Rebuild from a trusted revision and verify artifacts and provenance.
7. **Postmortem:** Record timeline, impact, root cause, and corrective actions in the approved operations location.

Full process: `docs/VULNERABILITY_RESPONSE.md`.

---

## 9. Compliance References

- SLSA 1.0 — Supply-chain Levels for Software Artifacts
- NIST SP 800-218 — Secure Software Development Framework (SSDF)
- OpenSSF Scorecard — Repository security posture
- CycloneDX — SBOM specification
- Sigstore — Keyless signing and verification
- PEP 740 — Index-hosted attestations

---

**End of Document**
