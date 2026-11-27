---
name: security-audit
version: 1.1.0
description: >
  Conduct coverage-led, independently verified, target-neutral source security audits
  using GENCODE-GOV's coverage ledger, 19-class taxonomy, sandbox, and artifact validators.
applicable_to:
  - library
  - library-and-cli
  - web-application
  - api-service
  - mobile-application
  - distributed-system
  - enterprise
requires:
  - gencode-gov
  - secure-software-engineering
  - application-security
---

# Security Audit Skill

## Operating Modes

1. **Guidance Mode (Default)**: Answer focused security design, triage, or remediation
   questions using `gencode_gov.security_audit.taxonomy` and `SE-SEC-*` rules without creating
   full multi-artifact audit directories unless requested.
2. **Full Audit Mode**: Triggered when asked for a full repository security audit,
   structured coverage ledger, verified findings bundle, or audit reassessment. Execute all
   six phases via `gencode-gov audit plan|run|verify-findings|validate|report|reassess`.

## Six-Phase Defensive Audit Workflow

1. **Phase 1 — Reconnaissance (`gencode-gov audit plan`)**:
   Map components, entry points, trust boundaries, and interfaces into `architecture.json`,
   `architecture.md`, and `coverage-ledger.json` (`audit_status: initiated`). Never equate
   `planned` units with `examined` coverage.
2. **Phase 2 — Coverage-Led Hunting**:
   Assign isolated hunters per coverage unit across the 19-class taxonomy (`ai-llm-security`,
   `memory-binary-safety`, `web-protocol-security`, `authn-authz-boundaries`, `api-security`,
   `client-side-security`, `supply-chain-release`, `cloud-deployment-security`,
   `protocols-rpc-messaging`, `resource-exhaustion-availability`, `data-tenant-isolation`,
   `data-lifecycle-privacy`, `desktop-application-security`, `mobile-application-security`,
   `local-ipc-trust`, `cryptographic-implementation`, `secrets-credential-handling`,
   `injection-input-handling`, `configuration-infrastructure`), followed by a post-wave
   Coverage Analyst gap check.
3. **Phase 3 — Adversarial Candidate Verification (`gencode-gov audit verify-findings`)**:
   Assign every candidate to an independent verifier (`verifier_id != discovery agent_id`)
   that inspects surrounding source controls and attempts to disprove the hypothesis first.
4. **Phase 4 — Deterministic Artifact Validation (`gencode-gov audit validate`)**:
   Validate `coverage-ledger.json`, `findings.json`, and `security-audit-report.json` against
   Draft 2020-12 JSON Schemas and semantic invariants (`O_NOFOLLOW`, 5 MiB cap, canonical
   `coverage_id`, trace ordering, `overall_severity <= impact`, and zero severity on
   `needs_validation`, `rejected`, `blocked`, or `not_verified`).
5. **Phase 5 — Independent Record Verification**:
   Verify that every final `confirmed` and `needs_validation` source location and trace step
   matches the exact repository revision (`commit_sha`).
6. **Phase 6 — Target-Neutral Reporting & Reassessment (`gencode-gov audit report|reassess`)**:
   Emit `security-audit-report.json`, `SECURITY-AUDIT-REPORT.md`, `FINDINGS-DETAIL.md`, and
   `NEEDS-VALIDATION.md` without live-target probing instructions, and track `remediated` vs
   `reopened` findings across commits via `gencode-gov audit reassess`.

## Execution Safety & Fail-Closed Rules

- Never probe live or deployed endpoints, external services, or production credentials.
- Execute bounded local target checks only inside `SandboxExecutor` with OS network
  isolation (`bwrap` or `unshare -r --net`), empty allowlisted `env`, scratch-only writes,
  rlimits, and descriptor-pinned `O_NOFOLLOW` artifact promotion (`st_nlink == 1`).
- If required OS isolation is unavailable, fail closed as `BLOCKED` or `needs_validation`
  and never claim sandboxed verification occurred.
- Never convert `needs_validation`, `not_verified`, `blocked`, or partial coverage into
  `PASS` in `EvidenceStore` or release gates.

## Multi-Agent Independent Sessions

- Probe available external/isolated runtimes with `gencode-gov audit runtimes --json`.
- Run independent OS-isolated discovery, coverage-critic, candidate-verification, and
  record-verification sessions with:
  `gencode-gov audit run <project> --execution-mode multi_agent_independent_sessions --runtime auto --max-workers 4`.
- Resume an interrupted multi-agent audit checkpoint safely without repeating verified
  work via `gencode-gov audit resume <project> --audit-dir <dir>`.
- Never claim `multi_agent_independent_sessions` unless distinct OS sessions (`session_id`
  and `pid`) actually executed and verified findings independently of their discoverer.
