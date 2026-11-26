# Apxoh Security Audit Subsystem

**Version:** 1.0.0
**Package:** `src/arkhon/security_audit/`
**Orchestrator:** `src/arkhon/orchestrator/task_dispatcher.py`

## Overview

The Apxoh Security Audit Subsystem provides deterministic, coverage-led, independently
verified, target-neutral source security auditing integrated directly with Apxoh's
`EvidenceStore`, `VerificationEngine`, `SE-*` rule catalog, and release gates. It
complements (and never replaces) external TSAR authority (`SE-SEC-GOV-001`).

## Subsystem Architecture

1. **Attack-Class Taxonomy (`taxonomy.py`)**: Extensible 19-class registry covering AI/LLM,
   memory/binary, web protocol, authn/authz, API, client-side, supply-chain/release,
   cloud/deployment, RPC/messaging, resource exhaustion, data/tenant isolation, data
   lifecycle/privacy, desktop, mobile, local IPC, cryptography, secrets/credentials,
   injection/input handling, and configuration/infrastructure, traced to `SE-*` rules.
2. **Coverage Ledger (`coverage.py`)**: RFC 3986 canonical `coverage_id` units tracking
   `planned`, `in_progress`, `examined`, `partially_examined`, `not_examined`, `blocked`,
   and `not_applicable` states with wave reassignment archives and cross-run comparison.
   `planned` units never count as `examined`.
3. **Reconnaissance & Hunting (`hunting.py`)**: Inventories surfaces and trust boundaries
   into `architecture.json` / `architecture.md`, executes deterministic AST and structural
   invariant checks per planned unit, and runs a post-wave Coverage Analyst gap check.
4. **Structured Findings Lifecycle (`findings.py`)**: Line-independent deterministic
   fingerprints, deduplication, state-transition enforcement (`candidate`, `confirmed`,
   `needs_validation`, `rejected`, `blocked`, `remediated`, `reopened`), and calibrated
   severity (`overall_severity <= impact`) permitted strictly on `confirmed` records.
5. **Independent Adversarial Verification (`verifier.py`)**: Enforces separation of duties
   (`verifier_id != discovery_provenance.agent_id`), inspects surrounding source context to
   disprove false positives, supports bounded sandbox checks, and runs Phase 5 record
   integrity verification.
6. **Enforceable OS Sandbox & Promotion (`sandbox.py`)**: Probes host `bwrap` and
   `unshare -r --net`, runs with an empty allowlisted environment, scratch-local `HOME` and
   `TMPDIR`, CPU/memory/fsize/process/file rlimits, source tree tamper checks, and 11-step
   `dir_fd` + `O_NOFOLLOW` regular-file (`st_nlink == 1`) artifact promotion. Fails closed
   to `BLOCKED` if required OS network isolation is unavailable.
7. **Deterministic Validators (`validators.py`)**: Enforces `O_NOFOLLOW`, 5 MiB byte cap,
   64 nesting depth cap, Draft 2020-12 schemas (`schemas/security-*.schema.json`), and
   cross-artifact consistency across ledger, findings, promoted artifacts, and reports.
8. **Target-Neutral Reporting & Reassessment (`reporting.py`, `reassessment.py`)**:
   Produces `security-audit-report.json`, `SECURITY-AUDIT-REPORT.md`, `FINDINGS-DETAIL.md`,
   and `NEEDS-VALIDATION.md`, and tracks remediations and reopened regressions across Git
   commits via `arkhon audit reassess`.
9. **Governance & CLI Bridge (`governance_bridge.py`, `cli_dispatch.py`)**: Connects audit
   runs to `.arkhon/evidence/software-security/` (`PASS`, `FAIL`, `BLOCKED`,
   `NOT_APPLICABLE`) and exposes `arkhon audit plan|run|status|coverage|verify-findings|validate|report|compare|reassess`
   backward-compatibly alongside legacy `arkhon audit [project] --domain <domain>`.
