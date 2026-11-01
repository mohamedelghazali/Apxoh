# Apxoh Dependency Policy

**Version:** 1.0
**Status:** Policy baseline — CI enforcement must be verified
**Owner:** Engineering Lead (TBD)
**Last reviewed:** 2026-11-01
**Review cadence:** Every release

---

## 1. Scope

This policy governs all software dependencies of Apxoh:

- **Direct dependencies:** declared in `pyproject.toml` under `[project.dependencies]` or `[project.optional-dependencies]`
- **Transitive dependencies:** pulled in by direct dependencies
- **Build dependencies:** declared in `[build-system].requires`
- **CI dependencies:** actions and tools used in `.github/workflows/`
- **Development dependencies:** packages used for testing, linting, typing, and security checks

AI model providers are managed through the model integration contract. They remain external service and data-handling risks and are not exempt from security review.

---

## 2. Version Pinning

### 2.1 Rule

Direct runtime and build dependencies must use exact version pins unless an approved exception is documented. Development dependencies should also be pinned to keep CI and contributor environments predictable.

Illustrative declaration consistent with the current project configuration:

```toml
dependencies = [
    "PyYAML==6.0.2",
    "jsonschema==4.23.0",
]

[project.optional-dependencies]
dev = [
    "pytest==8.3.3",
    "pytest-cov==5.0.0",
    "ruff==0.7.4",
    "mypy==1.13.0",
    "bandit==1.7.10",
    "pip-audit==2.7.3",
    "sigstore==3.5.1",
    "check-jsonschema==0.29.4",
]
```

The example is illustrative; `pyproject.toml` is the source of truth for the actual declared versions.

### 2.2 Rationale

- **Predictability:** upstream releases do not silently change declared direct dependency versions.
- **Auditability:** version changes are visible in Git history.
- **Reviewability:** updates can be assessed through a pull request.

Exact direct pins alone do not lock transitive dependencies or guarantee identical environments. A lock/constraints mechanism with hashes is required for stronger reproducibility.

### 2.3 Interpreter and Build Tools

The supported Python interpreter range is declared separately in `requires-python` because it is a runtime compatibility range, not a package pin. Build requirements such as `setuptools` and `wheel` should be pinned in `[build-system].requires`.

---

## 3. License Compatibility

### 3.1 Apxoh's License

Apxoh is licensed under **Apache-2.0**.

### 3.2 Generally Acceptable Licenses

| License | Default status | Notes |
| :--- | :--- | :--- |
| MIT | ✅ | Preserve notices |
| BSD-2-Clause | ✅ | Preserve notices |
| BSD-3-Clause | ✅ | Preserve notices |
| Apache-2.0 | ✅ | Preserve notices and license text |
| ISC | ✅ | Preserve notices |
| Python-2.0 (PSF) | ✅ | Preserve notices |
| MPL-2.0 | ⚠️ Review | File-level copyleft and distribution obligations must be assessed |

### 3.3 Restricted Licenses

| License | Status | Condition |
| :--- | :--- | :--- |
| LGPL-2.1 | ⚠️ Review required | Assess linking, modification, relinking, and notice obligations |
| LGPL-3.0 | ⚠️ Review required | Assess linking, modification, relinking, and notice obligations |

### 3.4 Licenses Requiring Explicit Legal Approval

| License | Default treatment |
| :--- | :--- |
| GPL-2.0 | Do not include in distributed Apxoh artifacts without explicit legal approval |
| GPL-3.0 | Do not include in distributed Apxoh artifacts without explicit legal approval |
| AGPL-3.0 | Do not include without explicit legal approval |
| SSPL | Do not include without explicit legal approval |
| Proprietary / source-available | Requires documented license rights and approval |

License compatibility is context-dependent. This table is an engineering screening rule, not legal advice. Dual licensing, exceptions, and transitive dependencies require human review.

### 3.5 Enforcement

The security workflow may run `pip-licenses` or an equivalent scanner. Its actual coverage, failure conditions, and license normalization must be verified. A scanner result does not replace review of ambiguous license terms.

---

## 4. New Dependency Admission

Adding a new direct dependency requires a pull request that includes:

### 4.1 Required Information

1. **Purpose:** what problem does this solve?
2. **Alternatives considered:** why not the standard library or an existing dependency?
3. **License:** SPDX identifier and notice obligations.
4. **Maintenance status:** release activity, maintainers, and known project health indicators.
5. **Security audit:** known advisories and audit result.
6. **Size:** installation size and transitive dependency count.
7. **Test coverage:** tests for the dependency's integration and failure behavior.

### 4.2 Review Process

1. Open a PR with the required information.
2. Run dependency audit, license review, and tests.
3. Obtain at least one maintainer review.
4. Obtain a second reviewer for security-sensitive dependencies (authentication, cryptography, network, parsing of untrusted input).
5. Merge only after required checks pass.

### 4.3 Fast-Track

Security patches for existing dependencies may be fast-tracked with one maintainer approval when:

- The update is a patch or minor release that addresses the vulnerability.
- New transitive dependencies and material behavior changes are reviewed.
- CI and relevant regression tests pass.
- The reason for expedited review is recorded.

---

## 5. Vulnerability Scanning

### 5.1 Tools

| Tool | Purpose | Target cadence |
| :--- | :--- | :--- |
| `pip-audit` | Known vulnerabilities in Python packages | CI and scheduled checks |
| Dependabot | Dependency update and vulnerability PRs | Configured schedule and alerts |
| Trivy | Filesystem, dependency, and container scanning where applicable | CI / scheduled |
| GitHub Advisory Database | Advisory intelligence | Continuous platform service |

Tool presence in a workflow does not prove successful coverage. The project must verify workflow results, scan scope, and failure behavior.

### 5.2 Severity Response Targets

| Severity | Target response |
| :--- | :--- |
| Critical | Mitigate within 24 hours |
| High | Mitigate within 7 days |
| Medium | Mitigate within 30 days |
| Low | Address in the next scheduled update |

These are response targets, not guaranteed remediation deadlines. If a fix is unavailable, document the exposure and compensating controls.

### 5.3 Exceptions

If a vulnerability has no available fix:

1. Record the affected package, versions, advisory, and exposure.
2. Document the exception in the designated vulnerability/operations record.
3. Apply a compensating control where possible (for example, disable the affected feature).
4. Assign an owner and review date.
5. Reassess at least monthly until resolved.

---

## 6. Update Strategy

| Category | Target cadence | Reviewer | Tests required |
| :--- | :--- | :--- | :--- |
| Security patches | Immediate | 1 maintainer, expedited | Relevant regression tests + full suite where feasible |
| Minor updates | Monthly | 1 maintainer | Full suite |
| Major updates | Quarterly | 2 maintainers | Full suite + compatibility review |
| Development-only updates | Monthly | 1 maintainer | CI suite |
| Build-system updates | Quarterly | 2 maintainers | Clean build and installation |

Every update must be reviewed through a PR. Automatic merging is prohibited unless a separately approved automation policy defines strict eligibility, required checks, and rollback.

---

## 7. SBOM

Apxoh's target release process is to publish a CycloneDX SBOM with each release. The SBOM must be generated from the release artifact or an equivalent locked build environment, validated, and retained with that release.

See `docs/SUPPLY_CHAIN.md` §6. Do not describe SBOM publication as active until a release asset has been generated and verified.

---

## 8. Cross-References

- `docs/SUPPLY_CHAIN.md` — broader supply chain policy
- `.github/dependabot.yml` — automated update configuration, if present and enabled
- `.github/workflows/security.yml` — security scanning workflow
- `pyproject.toml` — dependency declarations

---

**End of Document**
