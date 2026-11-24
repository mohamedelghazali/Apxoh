# Apxoh Project Governance

**Project:** Apxoh — Software Engineering Governance & Assurance System  
**Repository identifier:** `arkhon`  
**Status:** Governance policy; repository settings must be checked independently.

## 1. Purpose

This document describes how changes to Apxoh are proposed, reviewed, accepted, and maintained. It does not itself configure GitHub branch protection, CODEOWNERS enforcement, mandatory reviews, or access controls. Those controls are effective only when configured in the repository and independently checked.

The governing principles are:

- Evidence Before Approval.
- Verification Before Release.
- Fail closed when required evidence or a required tool is unavailable.
- Keep policy, implementation, and verification evidence distinct.
- Treat AI-generated changes as untrusted until independently reviewed and verified.

## 2. Governance Authority

Project maintainers administer the repository and coordinate decisions. Security-sensitive changes should receive review from a maintainer with appropriate security competence. Until named role assignments and repository permissions are published, role names in project documentation are responsibilities to be assigned, not proof of an active organizational control.

No contributor or automated agent may approve their own change where the applicable policy requires independent review.

## 3. Change Classes

| Change class | Minimum review expectation |
| :--- | :--- |
| Documentation | Content and link review |
| Application code | Code review and relevant tests |
| Rule or policy | Governance review, schema validation, positive and negative tests |
| Schema | Compatibility review and validation of affected documents |
| Model/platform integration | Adapter safety review, contract tests, manifest and compatibility updates |
| Security-sensitive code | Security review and relevant independent verification |
| Release configuration | Maintainer review and release-readiness evidence |

## 4. Pull Requests

Contributions should be made through pull requests. A pull request should state its scope, rationale, risks, tests, and evidence. Reviewers should verify that the change addresses the stated problem, preserves existing protections, introduces no secrets, and accurately distinguishes implemented behavior from intended design.

A green CI run is evidence only for the checks that actually ran. It is not blanket proof of security or production readiness.

## 5. Rules and Exceptions

Every rule should have a stable identifier, a measurable statement, a verification method, an enforcement level, and documented evidence requirements. Rule changes must be validated against the current schema and reviewed for unintended weakening.

Exceptions must be explicit, scoped, justified, approved by an authorized human, and time-bounded where appropriate. An exception must not rewrite historical evidence or convert a prior FAIL or BLOCKED result into PASS.

## 6. Evidence and Release Decisions

Evidence should identify the tool and version, execution time, target commit, scope, result, and referenced artifacts. SHA-256 detects changes to bytes whose expected digest is trusted; it does not independently establish authorship or correctness. Signature verification, provenance, and retention controls must be reported as active only when their implementation and execution evidence are available.

A release decision must consider required gate verdicts, open findings, accepted risks, and human approval requirements. A weighted score cannot override a failed critical gate or missing mandatory evidence.

## 7. Security and Disclosure

Do not publish exploitable vulnerability details in public issues. Follow [SECURITY.md](SECURITY.md) for the private reporting channel and response targets. Do not commit credentials, tokens, private keys, or personal data.

## 8. Records and Review

Significant architectural or policy decisions should be recorded in [docs/architecture/DECISION_LOG.md](docs/architecture/DECISION_LOG.md). Operational incidents should be documented using the incident response guidance and postmortem template. Review this policy when repository ownership, security responsibilities, or release controls materially change.

---

**End of Governance Policy**
