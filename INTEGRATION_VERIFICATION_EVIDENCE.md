# GENCODE-GOV Staged Integration & Independent Verification Evidence

- Generated UTC: 2026-11-28T00:23:10Z
- origin/main HEAD: 8f99a1186a0d6ca18202590a1663b6cbd61bc70b
- origin/feat/integrate-staged-governance HEAD (pre-integration): 8f99a1186a0d6ca18202590a1663b6cbd61bc70b
- Python: Python 3.13.18
- Node / npx: v24.22.3 / 11.19.1
- arkhon CLI on runner PATH: NOT_INSTALLED

## 1. Staged Bundle Integrity & Provenance Table

| Part | Bytes | Lines | SHA-256 |
| --- | --- | --- | --- |
| `part_01` | 27818 | 550 | `dfa2d58a35e3223328baeb45f23f2b800009e22c060811c2e641850394f2cedc` |
| `part_02` | 27448 | 536 | `5d1511d4e36b953f7197d9ca44db0dd1f8d5f281976d2a68474c4cd998ce577d` |
| `part_03` | 18182 | 476 | `f40987b72e1c62afc5167fbda500537810b623bff7867cedd9c47ffee7872ff3` |
| `part_04` | 22093 | 559 | `afdba4870d33d05e8aafc3a5537e08295abf33bcdd38784294bbfd6e7d944925` |
| `part_05` | 27770 | 698 | `fa13790ec231541b490e2daa92338adc7844c543f0150336349b0f0beffa22ec` |
| `part_06` | 22990 | 535 | `0b6d1280028363ff09488bb6a0dd27a8958b6c540077737e95007188fab16a3d` |
| `part_07` | 22991 | 535 | `faae0d0bea473fdf1dbf99c288b7dddc0b1091db4d0032c6d3379e30c1f95565` |
| `part_08` | 22991 | 437 | `9ae4f59cb188659dc4a0e5a1db50c7b7193a75f8cc755dcf5e12896804ed9b6a` |
| `part_09` | 21519 | 541 | `67d4f5f3a518b8b21c50824436708bcebcccdcfbedc58d900ad931a69362fd78` |
| `part_10` | 5983 | 140 | `bbd2b6a4a822c0867a71532122af56e911b04b775e21676d156d48f667c172d2` |
| `part_11` | 19758 | 511 | `e024dbd43b3ab6bcc32b0cf9ef35c66adf64ffadc0da3704a468b862b5059b0a` |
| `part_12` | 19764 | 379 | `018f89dbf8a2e3f0e27f48e9056f650c6119faa19309c822045e2b3121d0d6d7` |
| `part_13` | 19777 | 479 | `2ba43c03c3457382aec17bb59e437583d76dbd8e286d1c4d0efb875893e14b24` |
| `part_14` | 16728 | 371 | `66390d32f44d11fb3549d8d35418ae825b3d38902f4cfc045822ec7e7727b858` |

Decoded `__UPGRADER__` + 31 validated files with 0 duplicates and 0 syntax/schema errors.

## 2. Baseline Reconnaissance on origin/main
```text
=== gencode-gov --help ===
usage: gencode-gov [-h]
                   {version,doctor,validate,inspect,audit,assess,install,project,status,exceptions,report,verify}
                   ...

GENCODE-GOV - AI-Agent-Generated Software Governance

positional arguments:
  {version,doctor,validate,inspect,audit,assess,install,project,status,exceptions,report,verify}
    version             Print GENCODE-GOV version
    doctor              Check installation and environment
    validate            Validate manifest, schemas, and rules
    inspect             Inspect a project (languages, profile)
    audit               Run domain verification or coverage-led security audit
                        subcommands
    assess              Compute engineering score and gate status
    install             Stage the agent governance pack
    project             Initialize and manage project configuration
    status              Summarize project configuration and evidence
    exceptions          Inspect governance exceptions
    report              Generate an engineering-quality report
    verify              Run verification runners on a project

options:
  -h, --help            show this help message and exit
=== manifest/compatibility.yaml ===
# GENCODE-GOV Compatibility Matrix

runtime:
  python:
    minimum: "3.11"
    maximum_exclusive: "3.14"
    tested: ["3.11", "3.12", "3.13"]
  platforms:
    - linux
    - macos
    - windows

schemas:
  - id: rule
    version: "1.0.0"
    path: "schemas/rule.schema.json"
    backwards_compatible_with: []
    migrations: []

  - id: evidence
    version: "1.0.0"
    path: "schemas/evidence.schema.json"

  - id: finding
    version: "1.0.0"
    path: "schemas/finding.schema.json"

  - id: assessment
    version: "1.0.0"
    path: "schemas/assessment.schema.json"

  - id: exception
    version: "1.0.0"
    path: "schemas/exception.schema.json"

  - id: report
    version: "1.0.0"
    path: "schemas/report.schema.json"

  - id: project
    version: "1.0.0"
    path: "schemas/project.schema.json"

  - id: state
    version: "1.0.0"
    path: "schemas/state.schema.json"

  - id: integration-contract
    version: "1.0.0"
    path: "schemas/integration-contract.schema.json"

  - id: security-audit-report
    version: "1.0.0"
    path: "schemas/security-audit-report.schema.json"

  - id: security-coverage-ledger
    version: "1.0.0"
    path: "schemas/security-coverage-ledger.schema.json"

  - id: security-finding
    version: "1.0.0"
    path: "schemas/security-finding.schema.json"

integrations:
    
  - id: tsar
    minimum_version: "1.1.0"
    maximum_version: "1.x.x"
    evidence_format: "1.0.0"
    contract_schema: "integration-contract/1.0.0"

formats:
  rule: yaml
  evidence: json
  report: [json, markdown, html]
  sbom: [cyclonedx-json, cyclonedx-xml]

frozen_apis:
  - "src/gencode_gov/cli.py::main"
  - "src/gencode_gov.config::load_manifest"
  - "src/gencode_gov.evidence.store::read_evidence"
  - "src/gencode_gov.assessment.gates::evaluate"

policy: |
  Backward compatibility is promised within a major version.
  Breaking changes require a major version bump and a migration path.
  Deprecations are announced at least one minor version ahead.
=== .gencode-gov/project.yaml ===
# GENCODE-GOV governs itself.
# This file declares GENCODE-GOV-as-a-project to its own engine.

project:
  name: "GENCODE-GOV"
  identifier: "gencode-gov"
  type: "library-and-cli"
  profile: "enterprise"
  risk_level: "high"
  description: "Self-governance declaration for the GENCODE-GOV repository"

languages:
  primary: python
  secondary: []
  notes: "GENCODE-GOV itself is Python-only. Multi-language support exists in the governed projects, not in GENCODE-GOV."

lifecycle:
  current_stage: "development"
  current_milestone: 0
  release_channel: "pre-release"

stakeholders:
  maintainer: "mohamedelghazali"
  security_lead: TBD
  engineering_lead: TBD

policy_profile:
  strictness: "maximum"
  allow_exceptions: true
  require_signed_evidence: true
  require_human_review_for_critical: true

gates:
  requirements_gate: required
  architecture_gate: required
  implementation_gate: required
  testing_gate: required
  security_gate: required
  performance_gate: required
  reliability_gate: required
  release_gate: required

governance_files:
  read_only:
    - "system/"
    - "schemas/"
    - "policies/blocking/"
    - "manifest/"
    - "AGENTS.md"
    - "SECURITY_AGENTS.md"
    - "SECURITY.md"
    - ".github/workflows/"
  write_once:
    - ".gencode-gov/evidence/"
  append_only:
    - ".gencode-gov/state/"

security:
  authority: tsar
  require_fresh_evidence_hours: 168
  require_commit_binding: true
  require_signature: true

metadata:
  created: "2026-11-01"
  last_reviewed: "2026-11-04"
=== Baseline pytest -q ===
........................................................................ [ 82%]
........................................................................ [ 87%]
........................................................................ [ 92%]
........................................................................ [ 97%]
..................................                                       [100%]
```

## 3. Per-File Integration & Staged-vs-Main Reconciliation

- `.gencode-gov/architecture-contracts.yaml`: NEW_FILE
- `docs/governance/ENGINEERING_GAP_REGISTER.md`: NEW_FILE
- `rules/README.md`: NEW_FILE
- `rules/api-integration/SE-API-002-frozen-api-and-schema-compatibility.yaml`: NEW_FILE
- `rules/architecture/SE-ARC-002-executable-architecture-boundaries.yaml`: NEW_FILE
- `rules/code-quality/SE-CQ-003-ai-anti-fabrication-and-complexity.yaml`: NEW_FILE
- `rules/database/SE-DB-003-zero-downtime-migration-safety.yaml`: NEW_FILE
- `rules/devops/SE-DEV-002-deterministic-dependency-and-action-pinning.yaml`: NEW_FILE
- `rules/reliability/SE-REL-005-outbound-timeout-and-bounded-retry.yaml`: NEW_FILE
- `rules/software-security/SE-SEC-011-sbom-license-and-vulnerability-gate.yaml`: NEW_FILE
- `rules/testing/SE-TST-005-test-assertion-adequacy-and-anti-tampering.yaml`: NEW_FILE
- `schemas/architecture-contracts.schema.json`: NEW_FILE
- `schemas/drift-ledger.schema.json`: NEW_FILE
- `schemas/review-attestation.schema.json`: NEW_FILE
- `src/gencode_gov/assessment/drift.py`: NEW_FILE
- `src/gencode_gov/cli_extensions.py`: NEW_FILE
- `src/gencode_gov/evidence/attestation.py`: NEW_FILE
- `src/gencode_gov/reporting/html_reporter.py`: REPLACED_EXISTING (95B -> 4888B)
- `src/gencode_gov/reporting/sarif_reporter.py`: NEW_FILE
- `src/gencode_gov/rules/evaluator.py`: REPLACED_EXISTING (95B -> 8385B)
- `src/gencode_gov/validation.py`: NEW_FILE
- `src/gencode_gov/verification/architecture_verifier.py`: NEW_FILE
- `src/gencode_gov/verification/assess_dispatch.py`: REPLACED_EXISTING (6356B -> 7378B)
- `src/gencode_gov/verification/code_and_test_integrity.py`: NEW_FILE
- `src/gencode_gov/verification/diff_governance.py`: NEW_FILE
- `src/gencode_gov/verification/domain_verifiers.py`: NEW_FILE
- `src/gencode_gov/verification/methods.py`: REPLACED_EXISTING (4955B -> 13027B)
- `src/gencode_gov/verification/runners/polyglot_quality_runner.py`: NEW_FILE
- `tests/integration/test_end_to_end_governance_excellence.py`: NEW_FILE
- `tests/unit/verification/test_engineering_governance_edge_branches.py`: NEW_FILE
- `tests/unit/verification/test_engineering_governance_upgrades.py`: NEW_FILE
agent_pack total files after bundling references/: 27

Frozen API self-check: PASS — verified 4 frozen_apis entrypoint(s) ()

## 4. Ruff Lint (src tests scripts)
```text
E402 Module level import not at top of file
  --> tests/integration/test_end_to_end_governance_excellence.py:12:1
   |
10 | _GIT = shutil.which("git") or "/usr/bin/git"
11 |
12 | import pytest
   | ^^^^^^^^^^^^^
13 |
14 | from gencode_gov.cli import main
   |
help: Move module level imports to top of file

E402 Module level import not at top of file
  --> tests/integration/test_end_to_end_governance_excellence.py:14:1
   |
12 | import pytest
13 |
14 | from gencode_gov.cli import main
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
help: Move module level imports to top of file

E402 Module level import not at top of file
  --> tests/unit/verification/test_engineering_governance_edge_branches.py:12:1
   |
11 | _GIT = shutil.which("git") or "/usr/bin/git"
12 | from types import SimpleNamespace
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
13 |
14 | import pytest
   |
help: Move module level imports to top of file

E402 Module level import not at top of file
  --> tests/unit/verification/test_engineering_governance_edge_branches.py:14:1
   |
12 | from types import SimpleNamespace
13 |
14 | import pytest
   | ^^^^^^^^^^^^^
15 |
16 | from gencode_gov.assessment.drift import record_and_evaluate_drift
   |
help: Move module level imports to top of file

E402 Module level import not at top of file
  --> tests/unit/verification/test_engineering_governance_edge_branches.py:16:1
   |
14 | import pytest
15 |
16 | from gencode_gov.assessment.drift import record_and_evaluate_drift
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
17 | from gencode_gov.cli_extensions import (
18 |     build_tools_matrix,
   |
help: Move module level imports to top of file

E402 Module level import not at top of file
  --> tests/unit/verification/test_engineering_governance_edge_branches.py:17:1
   |
16 |   from gencode_gov.assessment.drift import record_and_evaluate_drift
17 | / from gencode_gov.cli_extensions import (
18 | |     build_tools_matrix,
19 | |     cmd_attest,
20 | |     cmd_diff_check,
21 | |     cmd_drift,
22 | |     register_extended_subcommands,
23 | |     render_extended_report_format,
24 | | )
   | |_^
25 |   from gencode_gov.core.constants import STATUS_BLOCKED, STATUS_FAIL, STATUS_PASS
26 |   from gencode_gov.core.errors import EvidenceError, GovernanceError
   |
help: Move module level imports to top of file

E402 Module level import not at top of file
  --> tests/unit/verification/test_engineering_governance_edge_branches.py:25:1
   |
23 |     render_extended_report_format,
24 | )
25 | from gencode_gov.core.constants import STATUS_BLOCKED, STATUS_FAIL, STATUS_PASS
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
26 | from gencode_gov.core.errors import EvidenceError, GovernanceError
27 | from gencode_gov.evidence.attestation import (
   |
help: Move module level imports to top of file

E402 Module level import not at top of file
  --> tests/unit/verification/test_engineering_governance_edge_branches.py:26:1
   |
24 | )
25 | from gencode_gov.core.constants import STATUS_BLOCKED, STATUS_FAIL, STATUS_PASS
26 | from gencode_gov.core.errors import EvidenceError, GovernanceError
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
27 | from gencode_gov.evidence.attestation import (
28 |     _parse_utc,
   |
help: Move module level imports to top of file

E402 Module level import not at top of file
  --> tests/unit/verification/test_engineering_governance_edge_branches.py:27:1
   |
25 |   from gencode_gov.core.constants import STATUS_BLOCKED, STATUS_FAIL, STATUS_PASS
26 |   from gencode_gov.core.errors import EvidenceError, GovernanceError
27 | / from gencode_gov.evidence.attestation import (
28 | |     _parse_utc,
29 | |     create_human_attestation,
30 | |     verify_human_attestation,
31 | | )
   | |_^
32 |   from gencode_gov.reporting.html_reporter import HtmlReporter, _atomic_safe_write
33 |   from gencode_gov.reporting.sarif_reporter import SarifReporter
   |
help: Move module level imports to top of file

E402 Module level import not at top of file
  --> tests/unit/verification/test_engineering_governance_edge_branches.py:32:1
   |
30 |     verify_human_attestation,
31 | )
32 | from gencode_gov.reporting.html_reporter import HtmlReporter, _atomic_safe_write
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
33 | from gencode_gov.reporting.sarif_reporter import SarifReporter
34 | from gencode_gov.rules.evaluator import RuleEvaluator
   |
help: Move module level imports to top of file

E402 Module level import not at top of file
  --> tests/unit/verification/test_engineering_governance_edge_branches.py:33:1
   |
31 | )
32 | from gencode_gov.reporting.html_reporter import HtmlReporter, _atomic_safe_write
33 | from gencode_gov.reporting.sarif_reporter import SarifReporter
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
34 | from gencode_gov.rules.evaluator import RuleEvaluator
35 | from gencode_gov.validation import run_cli_validate, validate_repository
   |
help: Move module level imports to top of file

E402 Module level import not at top of file
  --> tests/unit/verification/test_engineering_governance_edge_branches.py:34:1
   |
32 | from gencode_gov.reporting.html_reporter import HtmlReporter, _atomic_safe_write
33 | from gencode_gov.reporting.sarif_reporter import SarifReporter
34 | from gencode_gov.rules.evaluator import RuleEvaluator
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
35 | from gencode_gov.validation import run_cli_validate, validate_repository
36 | from gencode_gov.verification.architecture_verifier import _extract_submodules
   |
help: Move module level imports to top of file

E402 Module level import not at top of file
  --> tests/unit/verification/test_engineering_governance_edge_branches.py:35:1
   |
33 | from gencode_gov.reporting.sarif_reporter import SarifReporter
34 | from gencode_gov.rules.evaluator import RuleEvaluator
35 | from gencode_gov.validation import run_cli_validate, validate_repository
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
36 | from gencode_gov.verification.architecture_verifier import _extract_submodules
37 | from gencode_gov.verification.code_and_test_integrity import (
   |
help: Move module level imports to top of file

E402 Module level import not at top of file
  --> tests/unit/verification/test_engineering_governance_edge_branches.py:36:1
   |
34 | from gencode_gov.rules.evaluator import RuleEvaluator
35 | from gencode_gov.validation import run_cli_validate, validate_repository
36 | from gencode_gov.verification.architecture_verifier import _extract_submodules
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
37 | from gencode_gov.verification.code_and_test_integrity import (
38 |     analyze_production_code,
   |
help: Move module level imports to top of file

E402 Module level import not at top of file
  --> tests/unit/verification/test_engineering_governance_edge_branches.py:37:1
   |
35 |   from gencode_gov.validation import run_cli_validate, validate_repository
36 |   from gencode_gov.verification.architecture_verifier import _extract_submodules
37 | / from gencode_gov.verification.code_and_test_integrity import (
38 | |     analyze_production_code,
39 | |     verify_test_adequacy_method,
40 | | )
   | |_^
41 |   from gencode_gov.verification.diff_governance import (
42 |       evaluate_diff_governance,
   |
help: Move module level imports to top of file

E402 Module level import not at top of file
  --> tests/unit/verification/test_engineering_governance_edge_branches.py:41:1
   |
39 |       verify_test_adequacy_method,
40 |   )
41 | / from gencode_gov.verification.diff_governance import (
42 | |     evaluate_diff_governance,
43 | |     verify_frozen_apis,
44 | | )
   | |_^
45 |   from gencode_gov.verification.domain_verifiers import evaluate_domain_method
46 |   from gencode_gov.verification.runners.base import Runner, RunnerOutcome, RunnerResult
   |
help: Move module level imports to top of file

E402 Module level import not at top of file
  --> tests/unit/verification/test_engineering_governance_edge_branches.py:45:1
   |
43 |     verify_frozen_apis,
44 | )
45 | from gencode_gov.verification.domain_verifiers import evaluate_domain_method
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
46 | from gencode_gov.verification.runners.base import Runner, RunnerOutcome, RunnerResult
47 | from gencode_gov.verification.runners.polyglot_quality_runner import PolyglotQualityRunner
   |
help: Move module level imports to top of file

E402 Module level import not at top of file
  --> tests/unit/verification/test_engineering_governance_edge_branches.py:46:1
   |
44 | )
45 | from gencode_gov.verification.domain_verifiers import evaluate_domain_method
46 | from gencode_gov.verification.runners.base import Runner, RunnerOutcome, RunnerResult
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
47 | from gencode_gov.verification.runners.polyglot_quality_runner import PolyglotQualityRunner
   |
help: Move module level imports to top of file

E402 Module level import not at top of file
  --> tests/unit/verification/test_engineering_governance_edge_branches.py:47:1
   |
45 | from gencode_gov.verification.domain_verifiers import evaluate_domain_method
46 | from gencode_gov.verification.runners.base import Runner, RunnerOutcome, RunnerResult
47 | from gencode_gov.verification.runners.polyglot_quality_runner import PolyglotQualityRunner
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
48 |
49 | SHA_1 = "1" * 40
   |
help: Move module level imports to top of file

E402 Module level import not at top of file
  --> tests/unit/verification/test_engineering_governance_upgrades.py:12:1
   |
11 | _GIT = shutil.which("git") or "/usr/bin/git"
12 | from types import SimpleNamespace
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
13 |
14 | import pytest
   |
help: Move module level imports to top of file

E402 Module level import not at top of file
  --> tests/unit/verification/test_engineering_governance_upgrades.py:14:1
   |
12 | from types import SimpleNamespace
13 |
14 | import pytest
   | ^^^^^^^^^^^^^
15 |
16 | from gencode_gov.assessment.drift import compute_drift_snapshot, record_and_evaluate_drift
   |
help: Move module level imports to top of file

E402 Module level import not at top of file
  --> tests/unit/verification/test_engineering_governance_upgrades.py:16:1
   |
14 | import pytest
15 |
16 | from gencode_gov.assessment.drift import compute_drift_snapshot, record_and_evaluate_drift
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
17 | from gencode_gov.cli_extensions import (
18 |     build_tools_matrix,
   |
help: Move module level imports to top of file

E402 Module level import not at top of file
  --> tests/unit/verification/test_engineering_governance_upgrades.py:17:1
   |
16 |   from gencode_gov.assessment.drift import compute_drift_snapshot, record_and_evaluate_drift
17 | / from gencode_gov.cli_extensions import (
18 | |     build_tools_matrix,
19 | |     cmd_attest,
20 | |     cmd_diff_check,
21 | |     cmd_drift,
22 | |     register_extended_subcommands,
23 | |     render_extended_report_format,
24 | | )
   | |_^
25 |   from gencode_gov.core.constants import (
26 |       ALL_RULE_DOMAINS,
   |
help: Move module level imports to top of file

E402 Module level import not at top of file
  --> tests/unit/verification/test_engineering_governance_upgrades.py:25:1
   |
23 |       render_extended_report_format,
24 |   )
25 | / from gencode_gov.core.constants import (
26 | |     ALL_RULE_DOMAINS,
27 | |     STATUS_ACCEPTED_RISK,
28 | |     STATUS_BLOCKED,
29 | |     STATUS_FAIL,
30 | |     STATUS_PASS,
31 | | )
   | |_^
32 |   from gencode_gov.core.errors import EvidenceError, GovernanceError
33 |   from gencode_gov.evidence.attestation import (
   |
help: Move module level imports to top of file

E402 Module level import not at top of file
  --> tests/unit/verification/test_engineering_governance_upgrades.py:32:1
   |
30 |     STATUS_PASS,
31 | )
32 | from gencode_gov.core.errors import EvidenceError, GovernanceError
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
33 | from gencode_gov.evidence.attestation import (
34 |     create_human_attestation,
   |
help: Move module level imports to top of file

E402 Module level import not at top of file
  --> tests/unit/verification/test_engineering_governance_upgrades.py:33:1
   |
31 |   )
32 |   from gencode_gov.core.errors import EvidenceError, GovernanceError
33 | / from gencode_gov.evidence.attestation import (
34 | |     create_human_attestation,
35 | |     verify_human_attestation,
36 | | )
   | |_^
37 |   from gencode_gov.reporting.html_reporter import HtmlReporter, _atomic_safe_write
38 |   from gencode_gov.reporting.sarif_reporter import SarifReporter
   |
help: Move module level imports to top of file

E402 Module level import not at top of file
  --> tests/unit/verification/test_engineering_governance_upgrades.py:37:1
   |
35 |     verify_human_attestation,
36 | )
37 | from gencode_gov.reporting.html_reporter import HtmlReporter, _atomic_safe_write
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
38 | from gencode_gov.reporting.sarif_reporter import SarifReporter
39 | from gencode_gov.rules.evaluator import RuleEvaluator
   |
help: Move module level imports to top of file

E402 Module level import not at top of file
  --> tests/unit/verification/test_engineering_governance_upgrades.py:38:1
   |
36 | )
37 | from gencode_gov.reporting.html_reporter import HtmlReporter, _atomic_safe_write
38 | from gencode_gov.reporting.sarif_reporter import SarifReporter
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
39 | from gencode_gov.rules.evaluator import RuleEvaluator
40 | from gencode_gov.validation import run_cli_validate, validate_repository
   |
help: Move module level imports to top of file

E402 Module level import not at top of file
  --> tests/unit/verification/test_engineering_governance_upgrades.py:39:1
   |
37 | from gencode_gov.reporting.html_reporter import HtmlReporter, _atomic_safe_write
38 | from gencode_gov.reporting.sarif_reporter import SarifReporter
39 | from gencode_gov.rules.evaluator import RuleEvaluator
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
40 | from gencode_gov.validation import run_cli_validate, validate_repository
41 | from gencode_gov.verification.architecture_verifier import verify_architecture_contracts
   |
help: Move module level imports to top of file

E402 Module level import not at top of file
  --> tests/unit/verification/test_engineering_governance_upgrades.py:40:1
   |
38 | from gencode_gov.reporting.sarif_reporter import SarifReporter
39 | from gencode_gov.rules.evaluator import RuleEvaluator
40 | from gencode_gov.validation import run_cli_validate, validate_repository
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
41 | from gencode_gov.verification.architecture_verifier import verify_architecture_contracts
42 | from gencode_gov.verification.assess_dispatch import (
   |
help: Move module level imports to top of file

E402 Module level import not at top of file
  --> tests/unit/verification/test_engineering_governance_upgrades.py:41:1
   |
39 | from gencode_gov.rules.evaluator import RuleEvaluator
40 | from gencode_gov.validation import run_cli_validate, validate_repository
41 | from gencode_gov.verification.architecture_verifier import verify_architecture_contracts
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
42 | from gencode_gov.verification.assess_dispatch import (
43 |     create_assess_runner,
   |
help: Move module level imports to top of file

E402 Module level import not at top of file
  --> tests/unit/verification/test_engineering_governance_upgrades.py:42:1
   |
40 |   from gencode_gov.validation import run_cli_validate, validate_repository
41 |   from gencode_gov.verification.architecture_verifier import verify_architecture_contracts
42 | / from gencode_gov.verification.assess_dispatch import (
43 | |     create_assess_runner,
44 | |     evaluate_extended_method,
45 | |     inspect_junit_artifact,
46 | | )
   | |_^
47 |   from gencode_gov.verification.code_and_test_integrity import (
48 |       analyze_production_code,
   |
help: Move module level imports to top of file

E402 Module level import not at top of file
  --> tests/unit/verification/test_engineering_governance_upgrades.py:47:1
   |
45 |       inspect_junit_artifact,
46 |   )
47 | / from gencode_gov.verification.code_and_test_integrity import (
48 | |     analyze_production_code,
49 | |     compute_cyclomatic_complexity,
50 | |     verify_code_integrity_method,
51 | |     verify_test_adequacy_method,
52 | | )
   | |_^
53 |   from gencode_gov.verification.diff_governance import (
54 |       evaluate_diff_governance,
   |
help: Move module level imports to top of file

E402 Module level import not at top of file
  --> tests/unit/verification/test_engineering_governance_upgrades.py:53:1
   |
51 |       verify_test_adequacy_method,
52 |   )
53 | / from gencode_gov.verification.diff_governance import (
54 | |     evaluate_diff_governance,
55 | |     verify_frozen_apis,
56 | | )
   | |_^
57 |   from gencode_gov.verification.domain_verifiers import (
58 |       GovernanceDomainRunner,
   |
help: Move module level imports to top of file

E402 Module level import not at top of file
  --> tests/unit/verification/test_engineering_governance_upgrades.py:57:1
   |
55 |       verify_frozen_apis,
56 |   )
57 | / from gencode_gov.verification.domain_verifiers import (
58 | |     GovernanceDomainRunner,
59 | |     HumanAttestationRunner,
60 | |     evaluate_domain_method,
61 | | )
   | |_^
62 |   from gencode_gov.verification.methods import METHOD_REGISTRY, resolve_method, resolve_methods
63 |   from gencode_gov.verification.runners.base import RunnerOutcome, RunnerResult
   |
help: Move module level imports to top of file

E402 Module level import not at top of file
  --> tests/unit/verification/test_engineering_governance_upgrades.py:62:1
   |
60 |     evaluate_domain_method,
61 | )
62 | from gencode_gov.verification.methods import METHOD_REGISTRY, resolve_method, resolve_methods
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
63 | from gencode_gov.verification.runners.base import RunnerOutcome, RunnerResult
64 | from gencode_gov.verification.runners.polyglot_quality_runner import PolyglotQualityRunner
   |
help: Move module level imports to top of file

E402 Module level import not at top of file
  --> tests/unit/verification/test_engineering_governance_upgrades.py:63:1
   |
61 | )
62 | from gencode_gov.verification.methods import METHOD_REGISTRY, resolve_method, resolve_methods
63 | from gencode_gov.verification.runners.base import RunnerOutcome, RunnerResult
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
64 | from gencode_gov.verification.runners.polyglot_quality_runner import PolyglotQualityRunner
   |
help: Move module level imports to top of file

E402 Module level import not at top of file
  --> tests/unit/verification/test_engineering_governance_upgrades.py:64:1
   |
62 | from gencode_gov.verification.methods import METHOD_REGISTRY, resolve_method, resolve_methods
63 | from gencode_gov.verification.runners.base import RunnerOutcome, RunnerResult
64 | from gencode_gov.verification.runners.polyglot_quality_runner import PolyglotQualityRunner
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
65 |
66 | SHA_A = "a" * 40
   |
help: Move module level imports to top of file

Found 38 errors.
[EXIT 1]
```

## 5. Ruff Format Check (src tests scripts)
```text
370 files already formatted
[EXIT 0]
```

## 6. Mypy Type Check (src)
```text
pyproject.toml: note: unused section(s): module = ['scripts.*']
Success: no issues found in 134 source files
[EXIT 0]
```

## 7. Bandit Security Scan (src)
```text
[main]	INFO	profile include tests: None
[main]	INFO	profile exclude tests: B105,B404,B603,B310,B607
[main]	INFO	cli include tests: None
[main]	INFO	cli exclude tests: None
[main]	INFO	using config: pyproject.toml
[main]	INFO	running on Python 3.12.16
Working... ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100% 0:00:01
Run started:2026-11-28 00:24:03.659054+00:00

Test results:
	No issues identified.

Code scanned:
	Total lines of code: 18309
	Total lines skipped (#nosec): 0
	Total potential issues skipped due to specifically being disabled (e.g., #nosec BXXX): 0

Run metrics:
	Total issues (by severity):
		Undefined: 0
		Low: 0
		Medium: 0
		High: 0
	Total issues (by confidence):
		Undefined: 0
		Low: 0
		Medium: 0
		High: 0
Files skipped (0):
[EXIT 0]
```

## 8. Full Pytest & Coverage Suite
```text
........................................................................ [  4%]
........................................................................ [  9%]
................................F....................................... [ 14%]
........................................................................ [ 19%]
........................................................................ [ 24%]
........................................................................ [ 29%]
........................................................................ [ 34%]
........................................................................ [ 39%]
........................................................................ [ 44%]
........................................................................ [ 49%]
........................................................................ [ 54%]
........................................................................ [ 59%]
........................................................................ [ 64%]
.............................................F.......................... [ 69%]
........................................................................ [ 74%]
......................F...............................................F. [ 79%]
........................................................................ [ 84%]
..FF.................................................................... [ 89%]
.......................................................................F [ 94%]
FF.F....FFFF.F..F..........F............................................ [ 99%]
.........                                                                [100%]
=================================== FAILURES ===================================
________ test_cli_validate_inspect_tools_attest_diff_drift_and_reports _________

tmp_path = PosixPath('/tmp/pytest-of-runner/pytest-1/test_cli_validate_inspect_tool0')
capsys = <_pytest.capture.CaptureFixture object at 0x73884016b710>
monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x738840011a90>

    def test_cli_validate_inspect_tools_attest_diff_drift_and_reports(
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.delenv("GENCODE_GOV_AGENT_SESSION_ID", raising=False)
        monkeypatch.delenv("GENCODE_GOV_SANDBOX", raising=False)
    
        sha = _init_governed_python_project(tmp_path)
    
        # 1. inspect --tools --json
>       rc_ins = main(["inspect", str(tmp_path), "--tools", "--json"])
                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

tests/integration/test_end_to_end_governance_excellence.py:85: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
src/gencode_gov/cli.py:1274: in main
    return int(args.func(args))
               ^^^^^^^^^^^^^^^
src/gencode_gov/cli.py:103: in cmd_inspect
    profile = match_profile(project)
              ^^^^^^^^^^^^^^^^^^^^^^
src/gencode_gov/projects/matcher.py:73: in match_profile
    declared = _read_declared_profile(root)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

project_root = PosixPath('/tmp/pytest-of-runner/pytest-1/test_cli_validate_inspect_tool0')

    def _read_declared_profile(project_root: Path) -> str | None:
        path = project_root / ".gencode-gov" / "project.yaml"
        if not path.is_file():
            return None
        try:
            with path.open("r", encoding="utf-8") as stream:
                data = yaml.safe_load(stream)
        except (yaml.YAMLError, OSError) as exc:
            raise ConfigError(f"cannot read project declaration {path}: {exc}") from exc
        if not isinstance(data, dict):
            raise ConfigError(f"project declaration must be a YAML mapping: {path}")
        project: Any = data.get("project")
        if not isinstance(project, dict):
>           raise ConfigError(f"project declaration is missing its 'project' mapping: {path}")
E           gencode_gov.core.errors.ConfigError: project declaration is missing its 'project' mapping: /tmp/pytest-of-runner/pytest-1/test_cli_validate_inspect_tool0/.gencode-gov/project.yaml

src/gencode_gov/projects/matcher.py:37: ConfigError
_ test_rule_validates[SE-TST-005-test-assertion-adequacy-and-anti-tampering.yaml] _

rule_path = PosixPath('/home/runner/work/GENCODE-GOV/GENCODE-GOV/rules/testing/SE-TST-005-test-assertion-adequacy-and-anti-tampering.yaml')

    @pytest.mark.parametrize("rule_path", RULES, ids=lambda path: path.name)
    def test_rule_validates(rule_path: Path) -> None:
        rule = load_rule_file(rule_path)
        errors = validate_rule(rule, SCHEMA if SCHEMA.is_file() else None)
>       assert errors == [], f"{rule_path}: {errors}"
E       AssertionError: /home/runner/work/GENCODE-GOV/GENCODE-GOV/rules/testing/SE-TST-005-test-assertion-adequacy-and-anti-tampering.yaml: [RuleValidationError("SE-TST-005 [SE-TST-005-test-assertion-adequacy-and-anti-tampering.yaml]: metadata: 'severity' is a required property"), RuleValidationError("SE-TST-005 [SE-TST-005-test-assertion-adequacy-and-anti-tampering.yaml]: metadata.status: 'critical' is not one of ['proposed', 'active', 'deprecated', 'archived']"), RuleValidationError("SE-TST-005: invalid severity 'None'"), RuleValidationError("SE-TST-005: invalid status 'critical'")]
E       assert [RuleValidati... 'critical'")] == []
E         
E         Left contains 4 more items, first extra item: RuleValidationError("SE-TST-005 [SE-TST-005-test-assertion-adequacy-and-anti-tampering.yaml]: metadata: 'severity' is a required property")
E         
E         Full diff: (-: missing in left side, +: extra in left side)
E         - []
E         + [
E         +     RuleValidationError("SE-TST-005 [SE-TST-005-test-assertion-adequacy-and-anti-tampering.yaml]: metadata: 'severity' is a required property"),
E         +     RuleValidationError("SE-TST-005 [SE-TST-005-test-assertion-adequacy-and-anti-tampering.yaml]: metadata.status: 'critical' is not one of ['proposed', 'active', 'deprecated', 'archived']"),
E         +     RuleValidationError("SE-TST-005: invalid severity 'None'"),
E         +     RuleValidationError("SE-TST-005: invalid status 'critical'"),
E         + ]

tests/unit/rules/test_new_rules.py:42: AssertionError
________________ test_manifest_compatibility_lists_all_schemas _________________

    def test_manifest_compatibility_lists_all_schemas() -> None:
        compat = REPO_ROOT / "manifest" / "compatibility.yaml"
        if not compat.is_file():
            pytest.skip("compatibility.yaml missing")
        data = yaml.safe_load(compat.read_text(encoding="utf-8"))
        declared = {item["path"] for item in data.get("schemas", [])}
        actual = {str(path.relative_to(REPO_ROOT)) for path in _all_schema_files()}
>       assert actual == declared, (
            f"manifest/compatibility.yaml out of sync: declared={declared} actual={actual}"
        )
E       AssertionError: manifest/compatibility.yaml out of sync: declared={'schemas/exception.schema.json', 'schemas/security-coverage-ledger.schema.json', 'schemas/security-audit-report.schema.json', 'schemas/assessment.schema.json', 'schemas/rule.schema.json', 'schemas/state.schema.json', 'schemas/project.schema.json', 'schemas/security-finding.schema.json', 'schemas/finding.schema.json', 'schemas/evidence.schema.json', 'schemas/integration-contract.schema.json', 'schemas/report.schema.json'} actual={'schemas/drift-ledger.schema.json', 'schemas/exception.schema.json', 'schemas/security-audit-report.schema.json', 'schemas/review-attestation.schema.json', 'schemas/assessment.schema.json', 'schemas/rule.schema.json', 'schemas/security-coverage-ledger.schema.json', 'schemas/state.schema.json', 'schemas/project.schema.json', 'schemas/security-finding.schema.json', 'schemas/architecture-contracts.schema.json', 'schemas/finding.schema.json', 'schemas/evidence.schema.json', 'schemas/integration-contract.schema.json', 'schemas/report.schema.json'}
E       assert {'schemas/arc...ma.json', ...} == {'schemas/ass...ma.json', ...}
E         
E         Extra items in the left set:
E         'schemas/drift-ledger.schema.json'
E         'schemas/review-attestation.schema.json'
E         'schemas/architecture-contracts.schema.json'
E         
E         Full diff: (-: missing in left side, +: extra in left side)
E           {
E         +     'schemas/architecture-contracts.schema.json',
E               'schemas/assessment.schema.json',
E         +     'schemas/drift-ledger.schema.json',
E               'schemas/evidence.schema.json',
E               'schemas/exception.schema.json',
E               'schemas/finding.schema.json',
E               'schemas/integration-contract.schema.json',
E               'schemas/project.schema.json',
E               'schemas/report.schema.json',
E         +     'schemas/review-attestation.schema.json',
E               'schemas/rule.schema.json',
E               'schemas/security-audit-report.schema.json',
E               'schemas/security-coverage-ledger.schema.json',
E               'schemas/security-finding.schema.json',
E               'schemas/state.schema.json',
E           }

tests/unit/schemas/test_schemas.py:72: AssertionError
_____________________ test_cli_validate_and_import_failure _____________________

monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x73883fceafc0>
capsys = <_pytest.capture.CaptureFixture object at 0x738840098e30>

    def test_cli_validate_and_import_failure(monkeypatch, capsys) -> None:
        assert main(["validate"]) in {0, 1}
        original_import = builtins.__import__
    
        def fail_validate(name, *args, **kwargs):
            if name == "scripts.validation.validate_all":
                raise ImportError("validation module absent")
            return original_import(name, *args, **kwargs)
    
        monkeypatch.setattr(builtins, "__import__", fail_validate)
        assert main(["validate"]) == 1
>       assert "not available" in capsys.readouterr().err
E       assert 'not available' in ''
E        +  where '' = CaptureResult(out="[FAIL] SE-TST-005 [SE-TST-005-test-assertion-adequacy-and-anti-tampering.yaml]: metadata: 'severity...ted', 'archived']\n[FAIL] SE-TST-005: invalid severity 'None'\n[FAIL] SE-TST-005: invalid status 'critical'\n", err='').err
E        +    where CaptureResult(out="[FAIL] SE-TST-005 [SE-TST-005-test-assertion-adequacy-and-anti-tampering.yaml]: metadata: 'severity...ted', 'archived']\n[FAIL] SE-TST-005: invalid severity 'None'\n[FAIL] SE-TST-005: invalid status 'critical'\n", err='') = readouterr()
E        +      where readouterr = <_pytest.capture.CaptureFixture object at 0x738840098e30>.readouterr

tests/unit/test_coverage_cli.py:46: AssertionError
_ test_reserved_extension_modules_are_importable_and_empty[gencode_gov.reporting.html_reporter] _

module_name = 'gencode_gov.reporting.html_reporter'

    @pytest.mark.parametrize("module_name", _EMPTY_MODULES)
    def test_reserved_extension_modules_are_importable_and_empty(module_name: str) -> None:
        module = importlib.import_module(module_name)
>       assert module.__all__ == []
               ^^^^^^^^^^^^^^
E       AttributeError: module 'gencode_gov.reporting.html_reporter' has no attribute '__all__'. Did you mean: '__file__'?

tests/unit/test_import_facades.py:41: AttributeError
_ test_reserved_extension_modules_are_importable_and_empty[gencode_gov.rules.evaluator] _

module_name = 'gencode_gov.rules.evaluator'

    @pytest.mark.parametrize("module_name", _EMPTY_MODULES)
    def test_reserved_extension_modules_are_importable_and_empty(module_name: str) -> None:
        module = importlib.import_module(module_name)
>       assert module.__all__ == []
               ^^^^^^^^^^^^^^
E       AttributeError: module 'gencode_gov.rules.evaluator' has no attribute '__all__'. Did you mean: '__file__'?

tests/unit/test_import_facades.py:41: AttributeError
____________ test_attestation_and_drift_symlink_and_timestamp_edges ____________

tmp_path = PosixPath('/tmp/pytest-of-runner/pytest-1/test_attestation_and_drift_sym0')
monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x73883fc105c0>

    def test_attestation_and_drift_symlink_and_timestamp_edges(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("GENCODE_GOV_AGENT_SESSION_ID", raising=False)
        monkeypatch.delenv("GENCODE_GOV_SANDBOX", raising=False)
    
        with pytest.raises(EvidenceError):
            _parse_utc("not-a-date", "attested_at")
        with pytest.raises(EvidenceError):
            _parse_utc("2026-01-01T00:00:00", "attested_at")
    
        # Symlinked .gencode-gov rejected in create_human_attestation
        real_dir = tmp_path / "real"
        real_dir.mkdir()
        p1 = tmp_path / "p1"
        p1.mkdir()
        (p1 / ".gencode-gov").symlink_to(real_dir)
        with pytest.raises(EvidenceError):
            create_human_attestation(
                p1,
                rule_ids=["SE-ARC-001"],
                reviewer="lead_reviewer_role",
                approver_role="lead",
                commit_sha=SHA_1,
                rationale="Valid rationale text here.",
            )
    
        p2 = tmp_path / "p2"
        (p2 / ".gencode-gov").mkdir(parents=True)
        (p2 / ".gencode-gov" / "evidence").symlink_to(real_dir)
        with pytest.raises(EvidenceError):
            create_human_attestation(
                p2,
                rule_ids=["SE-ARC-001"],
                reviewer="lead_reviewer_role",
                approver_role="lead",
                commit_sha=SHA_1,
                rationale="Valid rationale text here.",
            )
    
        p3 = tmp_path / "p3"
        (p3 / ".gencode-gov" / "evidence").mkdir(parents=True)
        (p3 / ".gencode-gov" / "evidence" / "attestations").symlink_to(real_dir)
        with pytest.raises(EvidenceError):
            create_human_attestation(
                p3,
                rule_ids=["SE-ARC-001"],
                reviewer="lead_reviewer_role",
                approver_role="lead",
                commit_sha=SHA_1,
                rationale="Valid rationale text here.",
            )
    
        # Bot reviewer & bad timestamp inside stored attestation JSON
        p4 = tmp_path / "p4"
        att_dir = p4 / ".gencode-gov" / "evidence" / "attestations"
        att_dir.mkdir(parents=True)
        (att_dir / "ATTEST-AUTO0001.json").write_text(
            json.dumps(
                {
                    "attestation_id": "ATTEST-AUTO0001",
                    "rule_ids": ["SE-ARC-001"],
                    "reviewer": "bot-service",
                    "approver_role": "lead",
                    "commit_sha": SHA_1,
                    "attested_at": "2026-01-01T00:00:00Z",
                    "expires_at": "2026-02-01T00:00:00Z",
                    "rationale": "Automated service check.",
                    "reviewed_artifacts": [],
                }
            ),
            encoding="utf-8",
        )
        (att_dir / "ATTEST-BADTIME1.json").write_text(
            json.dumps(
                {
                    "attestation_id": "ATTEST-BADTIME1",
                    "rule_ids": ["SE-ARC-001"],
                    "reviewer": "lead_reviewer_role",
                    "approver_role": "lead",
                    "commit_sha": SHA_1,
                    "attested_at": "bad-date",
                    "expires_at": "2026-02-01T00:00:00Z",
                    "rationale": "Malformed timestamp test.",
                    "reviewed_artifacts": [],
                }
            ),
            encoding="utf-8",
        )
        st, rsn = verify_human_attestation(p4, rule_id="SE-ARC-001", expected_commit_sha=SHA_1)
        assert st == STATUS_BLOCKED
>       assert "bot/agent" in rsn and "invalid attested_at" in rsn
E       assert ('bot/agent' in "attestation ATTEST-AUTO0001 is expired; invalid attested_at timestamp: 'bad-date'")

tests/unit/verification/test_engineering_governance_edge_branches.py:144: AssertionError
__________________ test_cli_extensions_text_modes_and_errors ___________________

tmp_path = PosixPath('/tmp/pytest-of-runner/pytest-1/test_cli_extensions_text_modes0')
capsys = <_pytest.capture.CaptureFixture object at 0x73883fc02f00>
monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x73883fc02c30>

    def test_cli_extensions_text_modes_and_errors(
        tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("GENCODE_GOV_AGENT_SESSION_ID", raising=False)
        monkeypatch.delenv("GENCODE_GOV_SANDBOX", raising=False)
    
        parser = argparse.ArgumentParser()
        sub = parser.add_subparsers(dest="command")
        register_extended_subcommands(sub, lambda _p: None)
    
        # cmd_attest missing commit & error path & text output
        args_no_sha = parser.parse_args(
            [
                "attest",
                str(tmp_path),
                "--rule",
                "SE-ARC-001",
                "--reviewer",
                "lead_reviewer_role",
                "--role",
                "lead",
                "--rationale",
                "Valid rationale text.",
            ]
        )
        assert cmd_attest(args_no_sha, commit_resolver=lambda _p: None) == 1
    
        args_bad = parser.parse_args(
            [
                "attest",
                str(tmp_path),
                "--rule",
                "SE-ARC-001",
                "--reviewer",
                "ci-worker",
                "--role",
                "lead",
                "--rationale",
                "Valid rationale text.",
                "--commit",
                SHA_1,
            ]
        )
>       assert cmd_attest(args_bad, commit_resolver=lambda _p: SHA_1) == 1
E       AssertionError: assert 0 == 1
E        +  where 0 = cmd_attest(Namespace(command='attest', project='/tmp/pytest-of-runner/pytest-1/test_cli_extensions_text_modes0', rules=['SE-ARC-0...1111111111111111111111', json=False, func=<function register_extended_subcommands.<locals>.<lambda> at 0x73883fc2ee80>), commit_resolver=<function test_cli_extensions_text_modes_and_errors.<locals>.<lambda> at 0x73883fc2dda0>)

tests/unit/verification/test_engineering_governance_edge_branches.py:224: AssertionError
----------------------------- Captured stdout call -----------------------------
[OK] Recorded attestation ATTEST-GENCODE-GOV-9CC86ABBD8C7 -> .gencode-gov/evidence/attestations/ATTEST-GENCODE-GOV-9CC86ABBD8C7.json
----------------------------- Captured stderr call -----------------------------
[FAIL] could not resolve 40-char Git HEAD commit SHA
_______________ test_evaluator_validator_and_diff_edge_branches ________________

tmp_path = PosixPath('/tmp/pytest-of-runner/pytest-1/test_evaluator_validator_and_d0')

    def test_evaluator_validator_and_diff_edge_branches(tmp_path: Path) -> None:
        # RuleEvaluator: unregistered method, disallowed domain, custom runner PASS/FAIL/BLOCKED
        class CustomRunner(Runner):
            def __init__(self, outcome: RunnerOutcome) -> None:
                self._outcome = outcome
    
            def run(self, project_root: Path, artifact_dir: Path | None = None) -> RunnerResult:
                _ = project_root, artifact_dir
                return RunnerResult(runner="mypy", outcome=self._outcome, reason="done")
    
        r_unreg = SimpleNamespace(
            id="SE-CQ-999",
            raw={
                "metadata": {"domain": "code-quality", "enforcement": "blocking"},
                "verification": {"methods": ["nonexistent-method", "slo-document-presence"]},
            },
        )
        ev = RuleEvaluator(tmp_path, commit_sha=SHA_1)
        assert ev.evaluate_rule(r_unreg).status == STATUS_BLOCKED
    
        r_mypy = SimpleNamespace(
            id="SE-CQ-002",
            raw={
                "metadata": {"domain": "code-quality", "enforcement": "critical"},
                "verification": {"methods": ["type-checker-execution"]},
            },
        )
        assert (
            RuleEvaluator(
                tmp_path,
                commit_sha=SHA_1,
>               runner_overrides={"mypy": CustomRunner(RunnerOutcome.PASS)},
                                          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
            )
            .evaluate_rule(r_mypy)
            .status
            == STATUS_PASS
        )
E       TypeError: Can't instantiate abstract class CustomRunner without an implementation for abstract method 'name'

tests/unit/verification/test_engineering_governance_edge_branches.py:312: TypeError
____________ test_human_attestation_lifecycle_and_anti_agent_guards ____________

tmp_path = PosixPath('/tmp/pytest-of-runner/pytest-1/test_human_attestation_lifecyc0')
monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x73883ff8a630>

    def test_human_attestation_lifecycle_and_anti_agent_guards(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("GENCODE_GOV_AGENT_SESSION_ID", raising=False)
        monkeypatch.delenv("GENCODE_GOV_SANDBOX", raising=False)
    
        doc = tmp_path / "docs" / "adr" / "0001-init.md"
        doc.parent.mkdir(parents=True)
        doc.write_text("# Status\nAccepted\n", encoding="utf-8")
    
        # Missing attestation blocks fail-closed
        st, rsn = verify_human_attestation(tmp_path, rule_id="SE-ARC-001", expected_commit_sha=SHA_A)
        assert st == STATUS_BLOCKED
        assert "missing" in rsn
    
        # Invalid commit SHA blocks
        st_no_sha, _ = verify_human_attestation(
            tmp_path, rule_id="SE-ARC-001", expected_commit_sha=None
        )
        assert st_no_sha == STATUS_BLOCKED
    
        # Reject bot / coding-agent identities and sandbox env vars
        for bot_name in ("bot-runner", "agent-worker", "ci-worker", "x"):
>           with pytest.raises(EvidenceError):
                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E           Failed: DID NOT RAISE EvidenceError

tests/unit/verification/test_engineering_governance_upgrades.py:117: Failed
___________ test_domain_verifiers_and_polyglot_runner_comprehensive ____________

tmp_path = PosixPath('/tmp/pytest-of-runner/pytest-1/test_domain_verifiers_and_poly0')
monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x73883fc142c0>

    def test_domain_verifiers_and_polyglot_runner_comprehensive(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("GENCODE_GOV_AGENT_SESSION_ID", raising=False)
        monkeypatch.delenv("GENCODE_GOV_SANDBOX", raising=False)
    
        # Runners
        assert GovernanceDomainRunner().run(tmp_path).outcome == RunnerOutcome.PASS
        assert GovernanceDomainRunner().run(tmp_path / "missing").outcome == RunnerOutcome.BLOCKED
        assert HumanAttestationRunner().run(tmp_path).outcome == RunnerOutcome.PASS
        assert HumanAttestationRunner().run(tmp_path / "missing").outcome == RunnerOutcome.BLOCKED
    
        (tmp_path / "pyproject.toml").write_text(
            '[project]\nname = "demo"\nversion = "1.2.3"\n[tool.coverage.report]\nfail_under = 95\n',
            encoding="utf-8",
        )
        (tmp_path / "src" / "demo").mkdir(parents=True)
        init_py = tmp_path / "src" / "demo" / "__init__.py"
        init_py.write_text('__version__ = "1.2.3"\n', encoding="utf-8")
        (tmp_path / "src" / "demo" / "http_client.py").write_text(
            "import requests\ndef fetch(u: str):\n    return requests.get(u, timeout=5)\n",
            encoding="utf-8",
        )
        (tmp_path / "tests").mkdir()
        (tmp_path / "tests" / "test_demo.py").write_text(
            "def test_demo():\n    assert 2 == 2\n", encoding="utf-8"
        )
        (tmp_path / "CHANGELOG.md").write_text(
            "# Changelog\n\n## [1.2.3] - 2026-11-27\n- Added deterministic governance checks.\n",
            encoding="utf-8",
        )
        (tmp_path / "requirements.lock").write_text("pyyaml==6.0.2\n", encoding="utf-8")
        (tmp_path / ".github" / "workflows").mkdir(parents=True)
        (tmp_path / ".github" / "workflows" / "ci.yml").write_text(
            "name: CI\non: [push]\njobs:\n  test:\n    runs-on: ubuntu-latest\n"
            f"    steps:\n      - uses: actions/checkout@{SHA_A}\n",
            encoding="utf-8",
        )
        (tmp_path / "docs" / "adr").mkdir(parents=True)
        (tmp_path / "docs" / "adr" / "0001-arch.md").write_text(
            "## Status\nAccepted\n## Context\nNeed safety.\n"
            "## Decision\nUse AST checks.\n## Consequences\nDeterministic gates.\n",
            encoding="utf-8",
        )
        (tmp_path / "schemas").mkdir()
        (tmp_path / "schemas" / "demo.schema.json").write_text(
            json.dumps({"$id": "https://example.invalid/demo/1.0.0", "type": "object"}),
            encoding="utf-8",
        )
        gov = tmp_path / ".gencode-gov"
>       gov.mkdir()

tests/unit/verification/test_engineering_governance_upgrades.py:610: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

self = PosixPath('/tmp/pytest-of-runner/pytest-1/test_domain_verifiers_and_poly0/.gencode-gov')
mode = 511, parents = False, exist_ok = False

    def mkdir(self, mode=0o777, parents=False, exist_ok=False):
        """
        Create a new directory at this given path.
        """
        try:
>           os.mkdir(self, mode)
E           FileExistsError: [Errno 17] File exists: '/tmp/pytest-of-runner/pytest-1/test_domain_verifiers_and_poly0/.gencode-gov'

/opt/hostedtoolcache/Python/3.12.16/x64/lib/python3.12/pathlib.py:1311: FileExistsError
___________ test_assess_dispatch_method_registry_and_rule_evaluator ____________

tmp_path = PosixPath('/tmp/pytest-of-runner/pytest-1/test_assess_dispatch_method_re0')

    def test_assess_dispatch_method_registry_and_rule_evaluator(tmp_path: Path) -> None:
        # GAP-01 regression check: security-audit runner instantiates without ModuleNotFoundError!
        runner_names = (
            "test-suite",
            "ruff",
            "security-audit",
            "polyglot-quality",
            "governance-domain",
            "human-attestation",
        )
        for rname in runner_names:
            assert create_assess_runner(rname) is not None
        assert create_assess_runner("unknown-runner") is None
    
        # JUnit XML inspector
        junit = tmp_path / "junit.xml"
        junit.write_text(
            '<testsuite tests="4" failures="0" errors="0" skipped="0"></testsuite>',
            encoding="utf-8",
        )
        assert inspect_junit_artifact(junit) == (4, 0, 0, 0)
        assert inspect_junit_artifact(tmp_path / "missing.xml") is None
    
        # METHOD_REGISTRY validation
        assert len(METHOD_REGISTRY) >= 115
        assert resolve_method("anti-fabrication-ast-check") is not None
        with pytest.raises(ValueError):
            resolve_method("")
        with pytest.raises(ValueError):
            resolve_methods("not-a-list")
        with pytest.raises(ValueError):
            resolve_methods(["dup", "dup"])
        with pytest.raises(ValueError):
            resolve_methods([""])
    
        # RuleEvaluator with PASS, BLOCKED (dirty tree), and ACCEPTED_RISK exception
        (tmp_path / "src" / "pkg").mkdir(parents=True)
        (tmp_path / "src" / "pkg" / "ok.py").write_text(
            "def add(a: int, b: int) -> int:\n    return a + b\n", encoding="utf-8"
        )
        fake_rule = SimpleNamespace(
            id="SE-CQ-003",
            raw={
                "metadata": {"domain": "code-quality", "enforcement": "blocking"},
                "verification": {"methods": ["anti-fabrication-ast-check", "complexity-budget-check"]},
                "human_review": {"required": False},
            },
        )
        ev = RuleEvaluator(tmp_path, commit_sha=SHA_A, working_tree_clean=True)
        res_ok = ev.evaluate_all([fake_rule])[0]
        assert res_ok.status == STATUS_PASS
    
        ev_dirty = RuleEvaluator(tmp_path, commit_sha=SHA_A, working_tree_clean=False)
        assert ev_dirty.evaluate_rule(fake_rule).status == STATUS_BLOCKED
    
        # Accepted risk via active exception on non-critical rule
>       (tmp_path / ".gencode-gov").mkdir()

tests/unit/verification/test_engineering_governance_upgrades.py:801: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

self = PosixPath('/tmp/pytest-of-runner/pytest-1/test_assess_dispatch_method_re0/.gencode-gov')
mode = 511, parents = False, exist_ok = False

    def mkdir(self, mode=0o777, parents=False, exist_ok=False):
        """
        Create a new directory at this given path.
        """
        try:
>           os.mkdir(self, mode)
E           FileExistsError: [Errno 17] File exists: '/tmp/pytest-of-runner/pytest-1/test_assess_dispatch_method_re0/.gencode-gov'

/opt/hostedtoolcache/Python/3.12.16/x64/lib/python3.12/pathlib.py:1311: FileExistsError
_________________ test_cli_extensions_and_repository_validator _________________

tmp_path = PosixPath('/tmp/pytest-of-runner/pytest-1/test_cli_extensions_and_reposi0')
monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x73883fc05070>

    def test_cli_extensions_and_repository_validator(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("GENCODE_GOV_AGENT_SESSION_ID", raising=False)
        monkeypatch.delenv("GENCODE_GOV_SANDBOX", raising=False)
    
        repo_root = Path(__file__).resolve().parents[3]
        val_summary = validate_repository(repo_root)
>       assert val_summary.ok, f"Repository validation errors: {val_summary.errors}"
E       AssertionError: Repository validation errors: ("SE-TST-005 [SE-TST-005-test-assertion-adequacy-and-anti-tampering.yaml]: metadata: 'severity' is a required property", "SE-TST-005 [SE-TST-005-test-assertion-adequacy-and-anti-tampering.yaml]: metadata.status: 'critical' is not one of ['proposed', 'active', 'deprecated', 'archived']", "SE-TST-005: invalid severity 'None'", "SE-TST-005: invalid status 'critical'")
E       assert False
E        +  where False = ValidationSummary(ok=False, rules_checked=47, schemas_checked=15, skills_checked=10, errors=("SE-TST-005 [SE-TST-005-t... 'active', 'deprecated', 'archived']", "SE-TST-005: invalid severity 'None'", "SE-TST-005: invalid status 'critical'")).ok

tests/unit/verification/test_engineering_governance_upgrades.py:846: AssertionError
______________ test_repository_frozen_apis_and_clean_integration _______________

tmp_path = PosixPath('/tmp/pytest-of-runner/pytest-1/test_repository_frozen_apis_an0')

    def test_repository_frozen_apis_and_clean_integration(tmp_path: Path) -> None:
        from gencode_gov.assessment.gates import evaluate
        from gencode_gov.cli import main as cli_main
        from gencode_gov.config import load_manifest
        from gencode_gov.evidence.store import read_evidence
    
        repo_root = Path(__file__).resolve().parents[3]
        assert callable(cli_main)
        assert callable(load_manifest)
        assert callable(read_evidence)
        assert callable(evaluate)
        assert verify_frozen_apis(repo_root)[0] == STATUS_PASS
        assert not (repo_root / "staging").exists()
        assert not (repo_root / ".github" / "workflows" / "recon_full_audit.yml").exists()
    
        # Package __init__.py fallback when frozen_apis specifies module.py path
        pkg_dir = tmp_path / "src" / "demo_pkg" / "cfg"
        pkg_dir.mkdir(parents=True)
        (pkg_dir / "__init__.py").write_text(
            "def load_manifest() -> dict:\n    return {}\n", encoding="utf-8"
        )
        (tmp_path / "manifest").mkdir()
        (tmp_path / "manifest" / "compatibility.yaml").write_text(
            "frozen_apis:\n  - src/demo_pkg/cfg.py::load_manifest\n",
            encoding="utf-8",
        )
        assert verify_frozen_apis(tmp_path)[0] == STATUS_PASS
>       assert read_evidence(tmp_path, "testing") is not None
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

tests/unit/verification/test_engineering_governance_upgrades.py:921: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

project_root = PosixPath('/tmp/pytest-of-runner/pytest-1/test_repository_frozen_apis_an0')
domain = 'testing'

    def read_evidence(project_root: Path, domain: str) -> object:
        """Read persisted domain evidence via EvidenceStore (frozen public API helper)."""
        store = EvidenceStore(project_root)
        reader = getattr(store, "read", None) or getattr(store, "load", None)
>       return reader(domain) if callable(reader) else store
               ^^^^^^^^^^^^^^
E       TypeError: EvidenceStore.read() missing 1 required positional argument: 'evidence_id'

src/gencode_gov/evidence/store.py:294: TypeError
______________ test_unknown_method_is_not_claimed_as_implemented _______________

    def test_unknown_method_is_not_claimed_as_implemented() -> None:
>       assert resolve_method("load-test-execution") is None
E       AssertionError: assert MethodImplementation(method_id='load-test-execution', component='evaluate_domain_method', runner='governance-domain', allowed_domains=frozenset({'performance', 'scalability'})) is None
E        +  where MethodImplementation(method_id='load-test-execution', component='evaluate_domain_method', runner='governance-domain', allowed_domains=frozenset({'performance', 'scalability'})) = resolve_method('load-test-execution')

tests/unit/verification/test_method_registry.py:32: AssertionError
_______ test_resolve_methods_preserves_supported_and_unsupported_methods _______

    def test_resolve_methods_preserves_supported_and_unsupported_methods() -> None:
        result = resolve_methods(["type-checker-execution", "api-contract-analysis"])
        assert result[0][1] is not None
>       assert result[1] == ("api-contract-analysis", None)
E       AssertionError: assert ('api-contrac...tegration'}))) == ('api-contrac...alysis', None)
E         
E         At index 1 diff: MethodImplementation(method_id='api-contract-analysis', component='evaluate_domain_method', runner='governance-domain', allowed_domains=frozenset({'api-integration'})) != None
E         
E         Full diff: (-: missing in left side, +: extra in left side)
E           (
E               'api-contract-analysis',
E         -     None,
E         +     MethodImplementation(
E         +         method_id='api-contract-analysis',
E         +         component='evaluate_domain_method',
E         +         runner='governance-domain',
E         +         allowed_domains=frozenset({
E         +                             'api-integration',
E         +                         }),
E         +     ),
E           )

tests/unit/verification/test_method_registry.py:44: AssertionError
_______ test_assess_blocks_when_project_head_changes_during_verification _______

tmp_path = PosixPath('/tmp/pytest-of-runner/pytest-1/test_assess_blocks_when_projec0')
monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x73883ff3b350>
capsys = <_pytest.capture.CaptureFixture object at 0x73883ff3bf20>

    def test_assess_blocks_when_project_head_changes_during_verification(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        from gencode_gov.cli import main
        from gencode_gov.verification.runners.base import RunnerOutcome, RunnerResult
        from gencode_gov.verification.runners.mypy_runner import MypyRunner
    
        project = tmp_path / "project"
        project.mkdir()
        repository = tmp_path / "repository"
        rules = repository / "rules"
        rules.mkdir(parents=True)
        _write_assessment_rule(rules, "SE-CQ-002", "code-quality", "[type-checker-execution]")
        monkeypatch.setattr("gencode_gov.cli._repo_root", lambda: repository)
        commits = iter(["a" * 40, "b" * 40])
        monkeypatch.setattr("gencode_gov.cli._commit_sha", lambda _project: next(commits))
        monkeypatch.setattr("gencode_gov.cli._working_tree_clean", lambda _project: True)
    
        def passing_mypy(self: MypyRunner, root: Path) -> RunnerResult:
            artifact = root / ".gencode-gov" / "reports" / "mypy.txt"
            artifact.parent.mkdir(parents=True, exist_ok=True)
            artifact.write_text("Success", encoding="utf-8")
            return RunnerResult(self.name, RunnerOutcome.PASS, artifacts=[artifact])
    
        monkeypatch.setattr(MypyRunner, "run", passing_mypy)
>       assert main(["assess", str(project)]) == 1
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

tests/unit/verification/test_method_registry.py:323: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
src/gencode_gov/cli.py:1274: in main
    return int(args.func(args))
               ^^^^^^^^^^^^^^^
src/gencode_gov/cli.py:252: in cmd_assess
    "commit_sha": _commit_sha(project) or "uncommitted",
                  ^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

_project = PosixPath('/tmp/pytest-of-runner/pytest-1/test_assess_blocks_when_projec0/project')

>   monkeypatch.setattr("gencode_gov.cli._commit_sha", lambda _project: next(commits))
                                                                        ^^^^^^^^^^^^^
E   StopIteration

tests/unit/verification/test_method_registry.py:313: StopIteration
----------------------------- Captured stdout call -----------------------------
Project profile: universal (no specific project markers found)
Rule verification execution:
  SE-CQ-002: 1/1 methods implemented; human review not required
Rule outcomes:
  SE-CQ-002: BLOCKED
    [BLOCKED] type-checker-execution: project commit or working tree changed during assessment; rerun required
Active rules inspected: 1
Method implementations present: 1/1; rules requiring human review: 0; malformed rule declarations: 0
Evidence records inspected: 0 (integrity-checked)
New rule-level evidence records persisted: 1
Commit assessed: aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
Working tree clean: no
Gates:
  requirements_gate: BLOCKED
  architecture_gate: BLOCKED
  implementation_gate: BLOCKED
  testing_gate: BLOCKED
  security_gate: BLOCKED
  performance_gate: BLOCKED
  reliability_gate: BLOCKED
  release_gate: BLOCKED
[BLOCKED] one or more rules lack complete, commit-bound verification
[BLOCKED] no score or readiness level has been computed

---------- coverage: platform linux, python 3.12.16-final-0 ----------
Name                                                                  Stmts   Miss  Cover   Missing
---------------------------------------------------------------------------------------------------
src/gencode_gov/__init__.py                                               1      0   100%
src/gencode_gov/assessment/__init__.py                                    2      0   100%
src/gencode_gov/assessment/decision.py                                   41      0   100%
src/gencode_gov/assessment/drift.py                                      92      6    93%   83-85, 111, 114, 149
src/gencode_gov/assessment/gates.py                                      59      0   100%
src/gencode_gov/assessment/scorer.py                                     72      0   100%
src/gencode_gov/cli.py                                                  781     18    98%   123-125, 182, 185, 187, 227-229, 267, 1025-1037
src/gencode_gov/cli_extensions.py                                       112     54    52%   87-89, 101, 108-122, 130-157, 162-195, 205-219
src/gencode_gov/config.py                                                88      0   100%
src/gencode_gov/core/__init__.py                                          2      0   100%
src/gencode_gov/core/constants.py                                        34      0   100%
src/gencode_gov/core/errors.py                                           42      0   100%
src/gencode_gov/core/logging.py                                          33      0   100%
src/gencode_gov/evidence/__init__.py                                      2      0   100%
src/gencode_gov/evidence/attestation.py                                 157     41    74%   112, 118, 139, 143, 146, 148, 150, 152, 156-166, 264, 268-269, 272-276, 289-317, 325
src/gencode_gov/evidence/collector.py                                    84      0   100%
src/gencode_gov/evidence/integrity.py                                    77      0   100%
src/gencode_gov/evidence/store.py                                       202      0   100%
src/gencode_gov/evidence/supply_chain.py                                113      0   100%
src/gencode_gov/governance/__init__.py                                    2      0   100%
src/gencode_gov/governance/charter_loader.py                             74      0   100%
src/gencode_gov/governance/enforcement.py                                80      0   100%
src/gencode_gov/governance/policy_loader.py                             102      0   100%
src/gencode_gov/integrations/__init__.py                                  2      0   100%
src/gencode_gov/integrations/_model_impl/__init__.py                      0      0   100%
src/gencode_gov/integrations/_model_impl/code_llama/__init__.py           0      0   100%
src/gencode_gov/integrations/_model_impl/code_llama/adapter.py            5      0   100%
src/gencode_gov/integrations/_model_impl/deepseek_coder/__init__.py       0      0   100%
src/gencode_gov/integrations/_model_impl/deepseek_coder/adapter.py        5      0   100%
src/gencode_gov/integrations/_model_impl/openai_o/__init__.py             0      0   100%
src/gencode_gov/integrations/_model_impl/openai_o/adapter.py              5      0   100%
src/gencode_gov/integrations/_model_impl/qwen_coder/__init__.py           0      0   100%
src/gencode_gov/integrations/_model_impl/qwen_coder/adapter.py            5      0   100%
src/gencode_gov/integrations/agents/__init__.py                           2      0   100%
src/gencode_gov/integrations/agents/aider.py                              2      0   100%
src/gencode_gov/integrations/agents/amazon_q.py                           2      0   100%
src/gencode_gov/integrations/agents/claude_code.py                        2      0   100%
src/gencode_gov/integrations/agents/cline.py                              2      0   100%
src/gencode_gov/integrations/agents/codex_openai.py                       2      0   100%
src/gencode_gov/integrations/agents/continue_agent.py                     2      0   100%
src/gencode_gov/integrations/agents/cursor.py                             2      0   100%
src/gencode_gov/integrations/agents/devin.py                              2      0   100%
src/gencode_gov/integrations/agents/gemini.py                             2      0   100%
src/gencode_gov/integrations/agents/gemini_cli.py                         2      0   100%
src/gencode_gov/integrations/agents/github_copilot.py                     2      0   100%
src/gencode_gov/integrations/agents/gpt.py                                2      0   100%
src/gencode_gov/integrations/agents/jetbrains_ai.py                       2      0   100%
src/gencode_gov/integrations/agents/replit_agent.py                       2      0   100%
src/gencode_gov/integrations/agents/sourcegraph_cody.py                   2      0   100%
src/gencode_gov/integrations/agents/tabnine.py                            2      0   100%
src/gencode_gov/integrations/agents/windsurf.py                           2      0   100%
src/gencode_gov/integrations/base.py                                     27      0   100%
src/gencode_gov/integrations/generic_agents/__init__.py                   0      0   100%
src/gencode_gov/integrations/generic_agents/adapter.py                   15      0   100%
src/gencode_gov/integrations/models/__init__.py                          50      0   100%
src/gencode_gov/integrations/models/_openai_compatible.py               117      0   100%
src/gencode_gov/integrations/models/claude/__init__.py                    0      0   100%
src/gencode_gov/integrations/models/claude/adapter.py                    82      0   100%
src/gencode_gov/integrations/models/code-llama/__init__.py                0      0   100%
src/gencode_gov/integrations/models/code-llama/adapter.py                 2      0   100%
src/gencode_gov/integrations/models/deepseek-coder/__init__.py            0      0   100%
src/gencode_gov/integrations/models/deepseek-coder/adapter.py             2      0   100%
src/gencode_gov/integrations/models/gemini/__init__.py                    0      0   100%
src/gencode_gov/integrations/models/gemini/adapter.py                    82      0   100%
src/gencode_gov/integrations/models/gpt/__init__.py                       0      0   100%
src/gencode_gov/integrations/models/gpt/adapter.py                        5      0   100%
src/gencode_gov/integrations/models/kimi/__init__.py                      0      0   100%
src/gencode_gov/integrations/models/kimi/adapter.py                       5      0   100%
src/gencode_gov/integrations/models/openai-o/__init__.py                  0      0   100%
src/gencode_gov/integrations/models/openai-o/adapter.py                   2      0   100%
src/gencode_gov/integrations/models/qwen-coder/__init__.py                0      0   100%
src/gencode_gov/integrations/models/qwen-coder/adapter.py                 2      0   100%
src/gencode_gov/integrations/platforms/__init__.py                       11      0   100%
src/gencode_gov/integrations/platforms/github_copilot/__init__.py         2      0   100%
src/gencode_gov/integrations/platforms/github_copilot/adapter.py         62      0   100%
src/gencode_gov/integrations/tsar/__init__.py                             2      0   100%
src/gencode_gov/integrations/tsar/adapter.py                            149      0   100%
src/gencode_gov/integrations/tsar/verifier.py                           144      0   100%
src/gencode_gov/language_support/__init__.py                              2      0   100%
src/gencode_gov/language_support/compatibility.py                         2      0   100%
src/gencode_gov/language_support/detector.py                             72      1    99%   76
src/gencode_gov/language_support/language_profile_loader.py              75      0   100%
src/gencode_gov/language_support/registry.py                            100      0   100%
src/gencode_gov/language_support/tool_resolver.py                        48      0   100%
src/gencode_gov/orchestrator/__init__.py                                  2      0   100%
src/gencode_gov/orchestrator/lifecycle.py                                55      0   100%
src/gencode_gov/orchestrator/stage_manager.py                            39      0   100%
src/gencode_gov/orchestrator/task_dispatcher.py                           2      0   100%
src/gencode_gov/policies/__init__.py                                      2      0   100%
src/gencode_gov/policies/advisory.py                                     32      0   100%
src/gencode_gov/policies/blocking.py                                     49      0   100%
src/gencode_gov/policies/exceptions.py                                  154      0   100%
src/gencode_gov/projects/__init__.py                                      2      0   100%
src/gencode_gov/projects/loader.py                                       82      0   100%
src/gencode_gov/projects/matcher.py                                      57      0   100%
src/gencode_gov/reporting/__init__.py                                     2      0   100%
src/gencode_gov/reporting/html_reporter.py                               50      2    96%   19, 63
src/gencode_gov/reporting/json_reporter.py                              105      0   100%
src/gencode_gov/reporting/markdown_reporter.py                           27      0   100%
src/gencode_gov/reporting/sarif_reporter.py                              33      1    97%   27
src/gencode_gov/rules/__init__.py                                         2      0   100%
src/gencode_gov/rules/evaluator.py                                      106     20    81%   73-77, 96, 148-153, 158-170, 174-178, 195
src/gencode_gov/rules/loader.py                                          90      0   100%
src/gencode_gov/rules/registry.py                                        59      0   100%
src/gencode_gov/rules/validator.py                                      108      0   100%
src/gencode_gov/security_audit/__init__.py                               15      0   100%
src/gencode_gov/security_audit/cli_dispatch.py                          180      0   100%
src/gencode_gov/security_audit/coverage.py                              242      0   100%
src/gencode_gov/security_audit/dispatcher.py                             89      0   100%
src/gencode_gov/security_audit/findings.py                              232      0   100%
src/gencode_gov/security_audit/governance_bridge.py                     114      0   100%
src/gencode_gov/security_audit/hunting.py                               292      0   100%
src/gencode_gov/security_audit/orchestrator.py                          356      0   100%
src/gencode_gov/security_audit/reassessment.py                          136      0   100%
src/gencode_gov/security_audit/reporting.py                             130      0   100%
src/gencode_gov/security_audit/runtime.py                               193      0   100%
src/gencode_gov/security_audit/sandbox.py                               274      0   100%
src/gencode_gov/security_audit/taxonomy.py                               43      0   100%
src/gencode_gov/security_audit/validators.py                            349      0   100%
src/gencode_gov/security_audit/verifier.py                              164      0   100%
src/gencode_gov/security_audit/worker_entry.py                           86      0   100%
src/gencode_gov/validation.py                                           150     29    81%   47, 51-53, 55, 67-72, 85, 92-93, 105-106, 109, 115, 135, 137, 149, 166, 171-175, 208-220, 226-230
src/gencode_gov/verification/__init__.py                                  2      0   100%
src/gencode_gov/verification/architecture_verifier.py                   136      1    99%   47
src/gencode_gov/verification/assess_dispatch.py                         103      1    99%   95
src/gencode_gov/verification/code_and_test_integrity.py                 188     26    86%   77, 86-92, 110-111, 130, 132, 160, 241-253, 280, 290-291, 306, 331, 339
src/gencode_gov/verification/diff_governance.py                         163     14    91%   63, 80-81, 83, 87, 89, 94-95, 203, 248, 265-266, 282, 286
src/gencode_gov/verification/domain_verifiers.py                        526     97    82%   196, 200, 204, 208, 211, 227, 239, 269-273, 276, 278-280, 291, 298, 304, 320, 330, 350, 356, 384, 405, 416, 433, 441-443, 452, 455, 465-495, 499, 503, 533-543, 545, 565-589, 617, 638, 650-653, 666, 681, 687, 698-700, 732, 741-743, 747, 757, 813
src/gencode_gov/verification/engine.py                                  118      0   100%
src/gencode_gov/verification/methods.py                                  27      0   100%
src/gencode_gov/verification/profiles.py                                  2      0   100%
src/gencode_gov/verification/runners/__init__.py                          2      0   100%
src/gencode_gov/verification/runners/base.py                             21      0   100%
src/gencode_gov/verification/runners/mypy_runner.py                      52      0   100%
src/gencode_gov/verification/runners/polyglot_quality_runner.py          55     16    71%   45, 56-76
src/gencode_gov/verification/runners/pytest_runner.py                    56      0   100%
src/gencode_gov/verification/runners/ruff_runner.py                      50      0   100%
src/gencode_gov/verification/runners/supply_chain_runner.py             180      0   100%
src/gencode_gov/verification/runners/test_suite_runner.py               266      0   100%
src/gencode_gov/verification/runners/tsar_runner.py                      45      0   100%
src/gencode_gov/verification/scenario_verifier.py                       266      0   100%
---------------------------------------------------------------------------------------------------
TOTAL                                                                  9731    327    97%

=========================== short test summary info ============================
FAILED tests/integration/test_end_to_end_governance_excellence.py::test_cli_validate_inspect_tools_attest_diff_drift_and_reports - gencode_gov.core.errors.ConfigError: project declaration is missing its 'project' mapping: /tmp/pytest-of-runner/pytest-1/test_cli_validate_inspect_tool0/.gencode-gov/project.yaml
FAILED tests/unit/rules/test_new_rules.py::test_rule_validates[SE-TST-005-test-assertion-adequacy-and-anti-tampering.yaml] - AssertionError: /home/runner/work/GENCODE-GOV/GENCODE-GOV/rules/testing/SE-TST-005-test-assertion-adequacy-and-anti-tampering.yaml: [RuleValidationError("SE-TST-005 [SE-TST-005-test-assertion-adequacy-and-anti-tampering.yaml]: metadata: 'severity' is a required property"), RuleValidationError("SE-TST-005 [SE-TST-005-test-assertion-adequacy-and-anti-tampering.yaml]: metadata.status: 'critical' is not one of ['proposed', 'active', 'deprecated', 'archived']"), RuleValidationError("SE-TST-005: invalid severity 'None'"), RuleValidationError("SE-TST-005: invalid status 'critical'")]
assert [RuleValidati... 'critical'")] == []
  
  Left contains 4 more items, first extra item: RuleValidationError("SE-TST-005 [SE-TST-005-test-assertion-adequacy-and-anti-tampering.yaml]: metadata: 'severity' is a required property")
  
  Full diff: (-: missing in left side, +: extra in left side)
  - []
  + [
  +     RuleValidationError("SE-TST-005 [SE-TST-005-test-assertion-adequacy-and-anti-tampering.yaml]: metadata: 'severity' is a required property"),
  +     RuleValidationError("SE-TST-005 [SE-TST-005-test-assertion-adequacy-and-anti-tampering.yaml]: metadata.status: 'critical' is not one of ['proposed', 'active', 'deprecated', 'archived']"),
  +     RuleValidationError("SE-TST-005: invalid severity 'None'"),
  +     RuleValidationError("SE-TST-005: invalid status 'critical'"),
  + ]
FAILED tests/unit/schemas/test_schemas.py::test_manifest_compatibility_lists_all_schemas - AssertionError: manifest/compatibility.yaml out of sync: declared={'schemas/exception.schema.json', 'schemas/security-coverage-ledger.schema.json', 'schemas/security-audit-report.schema.json', 'schemas/assessment.schema.json', 'schemas/rule.schema.json', 'schemas/state.schema.json', 'schemas/project.schema.json', 'schemas/security-finding.schema.json', 'schemas/finding.schema.json', 'schemas/evidence.schema.json', 'schemas/integration-contract.schema.json', 'schemas/report.schema.json'} actual={'schemas/drift-ledger.schema.json', 'schemas/exception.schema.json', 'schemas/security-audit-report.schema.json', 'schemas/review-attestation.schema.json', 'schemas/assessment.schema.json', 'schemas/rule.schema.json', 'schemas/security-coverage-ledger.schema.json', 'schemas/state.schema.json', 'schemas/project.schema.json', 'schemas/security-finding.schema.json', 'schemas/architecture-contracts.schema.json', 'schemas/finding.schema.json', 'schemas/evidence.schema.json', 'schemas/integration-contract.schema.json', 'schemas/report.schema.json'}
assert {'schemas/arc...ma.json', ...} == {'schemas/ass...ma.json', ...}
  
  Extra items in the left set:
  'schemas/drift-ledger.schema.json'
  'schemas/review-attestation.schema.json'
  'schemas/architecture-contracts.schema.json'
  
  Full diff: (-: missing in left side, +: extra in left side)
    {
  +     'schemas/architecture-contracts.schema.json',
        'schemas/assessment.schema.json',
  +     'schemas/drift-ledger.schema.json',
        'schemas/evidence.schema.json',
        'schemas/exception.schema.json',
        'schemas/finding.schema.json',
        'schemas/integration-contract.schema.json',
        'schemas/project.schema.json',
        'schemas/report.schema.json',
  +     'schemas/review-attestation.schema.json',
        'schemas/rule.schema.json',
        'schemas/security-audit-report.schema.json',
        'schemas/security-coverage-ledger.schema.json',
        'schemas/security-finding.schema.json',
        'schemas/state.schema.json',
    }
FAILED tests/unit/test_coverage_cli.py::test_cli_validate_and_import_failure - assert 'not available' in ''
 +  where '' = CaptureResult(out="[FAIL] SE-TST-005 [SE-TST-005-test-assertion-adequacy-and-anti-tampering.yaml]: metadata: 'severity...ted', 'archived']\n[FAIL] SE-TST-005: invalid severity 'None'\n[FAIL] SE-TST-005: invalid status 'critical'\n", err='').err
 +    where CaptureResult(out="[FAIL] SE-TST-005 [SE-TST-005-test-assertion-adequacy-and-anti-tampering.yaml]: metadata: 'severity...ted', 'archived']\n[FAIL] SE-TST-005: invalid severity 'None'\n[FAIL] SE-TST-005: invalid status 'critical'\n", err='') = readouterr()
 +      where readouterr = <_pytest.capture.CaptureFixture object at 0x738840098e30>.readouterr
FAILED tests/unit/test_import_facades.py::test_reserved_extension_modules_are_importable_and_empty[gencode_gov.reporting.html_reporter] - AttributeError: module 'gencode_gov.reporting.html_reporter' has no attribute '__all__'. Did you mean: '__file__'?
FAILED tests/unit/test_import_facades.py::test_reserved_extension_modules_are_importable_and_empty[gencode_gov.rules.evaluator] - AttributeError: module 'gencode_gov.rules.evaluator' has no attribute '__all__'. Did you mean: '__file__'?
FAILED tests/unit/verification/test_engineering_governance_edge_branches.py::test_attestation_and_drift_symlink_and_timestamp_edges - assert ('bot/agent' in "attestation ATTEST-AUTO0001 is expired; invalid attested_at timestamp: 'bad-date'")
FAILED tests/unit/verification/test_engineering_governance_edge_branches.py::test_cli_extensions_text_modes_and_errors - AssertionError: assert 0 == 1
 +  where 0 = cmd_attest(Namespace(command='attest', project='/tmp/pytest-of-runner/pytest-1/test_cli_extensions_text_modes0', rules=['SE-ARC-0...1111111111111111111111', json=False, func=<function register_extended_subcommands.<locals>.<lambda> at 0x73883fc2ee80>), commit_resolver=<function test_cli_extensions_text_modes_and_errors.<locals>.<lambda> at 0x73883fc2dda0>)
FAILED tests/unit/verification/test_engineering_governance_edge_branches.py::test_evaluator_validator_and_diff_edge_branches - TypeError: Can't instantiate abstract class CustomRunner without an implementation for abstract method 'name'
FAILED tests/unit/verification/test_engineering_governance_upgrades.py::test_human_attestation_lifecycle_and_anti_agent_guards - Failed: DID NOT RAISE EvidenceError
FAILED tests/unit/verification/test_engineering_governance_upgrades.py::test_domain_verifiers_and_polyglot_runner_comprehensive - FileExistsError: [Errno 17] File exists: '/tmp/pytest-of-runner/pytest-1/test_domain_verifiers_and_poly0/.gencode-gov'
FAILED tests/unit/verification/test_engineering_governance_upgrades.py::test_assess_dispatch_method_registry_and_rule_evaluator - FileExistsError: [Errno 17] File exists: '/tmp/pytest-of-runner/pytest-1/test_assess_dispatch_method_re0/.gencode-gov'
FAILED tests/unit/verification/test_engineering_governance_upgrades.py::test_cli_extensions_and_repository_validator - AssertionError: Repository validation errors: ("SE-TST-005 [SE-TST-005-test-assertion-adequacy-and-anti-tampering.yaml]: metadata: 'severity' is a required property", "SE-TST-005 [SE-TST-005-test-assertion-adequacy-and-anti-tampering.yaml]: metadata.status: 'critical' is not one of ['proposed', 'active', 'deprecated', 'archived']", "SE-TST-005: invalid severity 'None'", "SE-TST-005: invalid status 'critical'")
assert False
 +  where False = ValidationSummary(ok=False, rules_checked=47, schemas_checked=15, skills_checked=10, errors=("SE-TST-005 [SE-TST-005-t... 'active', 'deprecated', 'archived']", "SE-TST-005: invalid severity 'None'", "SE-TST-005: invalid status 'critical'")).ok
FAILED tests/unit/verification/test_engineering_governance_upgrades.py::test_repository_frozen_apis_and_clean_integration - TypeError: EvidenceStore.read() missing 1 required positional argument: 'evidence_id'
FAILED tests/unit/verification/test_method_registry.py::test_unknown_method_is_not_claimed_as_implemented - AssertionError: assert MethodImplementation(method_id='load-test-execution', component='evaluate_domain_method', runner='governance-domain', allowed_domains=frozenset({'performance', 'scalability'})) is None
 +  where MethodImplementation(method_id='load-test-execution', component='evaluate_domain_method', runner='governance-domain', allowed_domains=frozenset({'performance', 'scalability'})) = resolve_method('load-test-execution')
FAILED tests/unit/verification/test_method_registry.py::test_resolve_methods_preserves_supported_and_unsupported_methods - AssertionError: assert ('api-contrac...tegration'}))) == ('api-contrac...alysis', None)
  
  At index 1 diff: MethodImplementation(method_id='api-contract-analysis', component='evaluate_domain_method', runner='governance-domain', allowed_domains=frozenset({'api-integration'})) != None
  
  Full diff: (-: missing in left side, +: extra in left side)
    (
        'api-contract-analysis',
  -     None,
  +     MethodImplementation(
  +         method_id='api-contract-analysis',
  +         component='evaluate_domain_method',
  +         runner='governance-domain',
  +         allowed_domains=frozenset({
  +                             'api-integration',
  +                         }),
  +     ),
    )
FAILED tests/unit/verification/test_method_registry.py::test_assess_blocks_when_project_head_changes_during_verification - StopIteration
17 failed, 1432 passed in 44.40s
[EXIT 1]
```

## 9. New Modules 100% Coverage Gate
```text
F....FFFFFFF.F                                                           [100%]
=================================== FAILURES ===================================
____________ test_human_attestation_lifecycle_and_anti_agent_guards ____________

tmp_path = PosixPath('/tmp/pytest-of-runner/pytest-2/test_human_attestation_lifecyc0')
monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x7b8dde51efc0>

    def test_human_attestation_lifecycle_and_anti_agent_guards(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("GENCODE_GOV_AGENT_SESSION_ID", raising=False)
        monkeypatch.delenv("GENCODE_GOV_SANDBOX", raising=False)
    
        doc = tmp_path / "docs" / "adr" / "0001-init.md"
        doc.parent.mkdir(parents=True)
        doc.write_text("# Status\nAccepted\n", encoding="utf-8")
    
        # Missing attestation blocks fail-closed
        st, rsn = verify_human_attestation(tmp_path, rule_id="SE-ARC-001", expected_commit_sha=SHA_A)
        assert st == STATUS_BLOCKED
        assert "missing" in rsn
    
        # Invalid commit SHA blocks
        st_no_sha, _ = verify_human_attestation(
            tmp_path, rule_id="SE-ARC-001", expected_commit_sha=None
        )
        assert st_no_sha == STATUS_BLOCKED
    
        # Reject bot / coding-agent identities and sandbox env vars
        for bot_name in ("bot-runner", "agent-worker", "ci-worker", "x"):
>           with pytest.raises(EvidenceError):
                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E           Failed: DID NOT RAISE EvidenceError

tests/unit/verification/test_engineering_governance_upgrades.py:117: Failed
___________ test_domain_verifiers_and_polyglot_runner_comprehensive ____________

tmp_path = PosixPath('/tmp/pytest-of-runner/pytest-2/test_domain_verifiers_and_poly0')
monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x7b8dde591c10>

    def test_domain_verifiers_and_polyglot_runner_comprehensive(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("GENCODE_GOV_AGENT_SESSION_ID", raising=False)
        monkeypatch.delenv("GENCODE_GOV_SANDBOX", raising=False)
    
        # Runners
        assert GovernanceDomainRunner().run(tmp_path).outcome == RunnerOutcome.PASS
        assert GovernanceDomainRunner().run(tmp_path / "missing").outcome == RunnerOutcome.BLOCKED
        assert HumanAttestationRunner().run(tmp_path).outcome == RunnerOutcome.PASS
        assert HumanAttestationRunner().run(tmp_path / "missing").outcome == RunnerOutcome.BLOCKED
    
        (tmp_path / "pyproject.toml").write_text(
            '[project]\nname = "demo"\nversion = "1.2.3"\n[tool.coverage.report]\nfail_under = 95\n',
            encoding="utf-8",
        )
        (tmp_path / "src" / "demo").mkdir(parents=True)
        init_py = tmp_path / "src" / "demo" / "__init__.py"
        init_py.write_text('__version__ = "1.2.3"\n', encoding="utf-8")
        (tmp_path / "src" / "demo" / "http_client.py").write_text(
            "import requests\ndef fetch(u: str):\n    return requests.get(u, timeout=5)\n",
            encoding="utf-8",
        )
        (tmp_path / "tests").mkdir()
        (tmp_path / "tests" / "test_demo.py").write_text(
            "def test_demo():\n    assert 2 == 2\n", encoding="utf-8"
        )
        (tmp_path / "CHANGELOG.md").write_text(
            "# Changelog\n\n## [1.2.3] - 2026-11-27\n- Added deterministic governance checks.\n",
            encoding="utf-8",
        )
        (tmp_path / "requirements.lock").write_text("pyyaml==6.0.2\n", encoding="utf-8")
        (tmp_path / ".github" / "workflows").mkdir(parents=True)
        (tmp_path / ".github" / "workflows" / "ci.yml").write_text(
            "name: CI\non: [push]\njobs:\n  test:\n    runs-on: ubuntu-latest\n"
            f"    steps:\n      - uses: actions/checkout@{SHA_A}\n",
            encoding="utf-8",
        )
        (tmp_path / "docs" / "adr").mkdir(parents=True)
        (tmp_path / "docs" / "adr" / "0001-arch.md").write_text(
            "## Status\nAccepted\n## Context\nNeed safety.\n"
            "## Decision\nUse AST checks.\n## Consequences\nDeterministic gates.\n",
            encoding="utf-8",
        )
        (tmp_path / "schemas").mkdir()
        (tmp_path / "schemas" / "demo.schema.json").write_text(
            json.dumps({"$id": "https://example.invalid/demo/1.0.0", "type": "object"}),
            encoding="utf-8",
        )
        gov = tmp_path / ".gencode-gov"
>       gov.mkdir()

tests/unit/verification/test_engineering_governance_upgrades.py:610: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

self = PosixPath('/tmp/pytest-of-runner/pytest-2/test_domain_verifiers_and_poly0/.gencode-gov')
mode = 511, parents = False, exist_ok = False

    def mkdir(self, mode=0o777, parents=False, exist_ok=False):
        """
        Create a new directory at this given path.
        """
        try:
>           os.mkdir(self, mode)
E           FileExistsError: [Errno 17] File exists: '/tmp/pytest-of-runner/pytest-2/test_domain_verifiers_and_poly0/.gencode-gov'

/opt/hostedtoolcache/Python/3.12.16/x64/lib/python3.12/pathlib.py:1311: FileExistsError
___________ test_assess_dispatch_method_registry_and_rule_evaluator ____________

tmp_path = PosixPath('/tmp/pytest-of-runner/pytest-2/test_assess_dispatch_method_re0')

    def test_assess_dispatch_method_registry_and_rule_evaluator(tmp_path: Path) -> None:
        # GAP-01 regression check: security-audit runner instantiates without ModuleNotFoundError!
        runner_names = (
            "test-suite",
            "ruff",
            "security-audit",
            "polyglot-quality",
            "governance-domain",
            "human-attestation",
        )
        for rname in runner_names:
            assert create_assess_runner(rname) is not None
        assert create_assess_runner("unknown-runner") is None
    
        # JUnit XML inspector
        junit = tmp_path / "junit.xml"
        junit.write_text(
            '<testsuite tests="4" failures="0" errors="0" skipped="0"></testsuite>',
            encoding="utf-8",
        )
        assert inspect_junit_artifact(junit) == (4, 0, 0, 0)
        assert inspect_junit_artifact(tmp_path / "missing.xml") is None
    
        # METHOD_REGISTRY validation
        assert len(METHOD_REGISTRY) >= 115
        assert resolve_method("anti-fabrication-ast-check") is not None
        with pytest.raises(ValueError):
            resolve_method("")
        with pytest.raises(ValueError):
            resolve_methods("not-a-list")
        with pytest.raises(ValueError):
            resolve_methods(["dup", "dup"])
        with pytest.raises(ValueError):
            resolve_methods([""])
    
        # RuleEvaluator with PASS, BLOCKED (dirty tree), and ACCEPTED_RISK exception
        (tmp_path / "src" / "pkg").mkdir(parents=True)
        (tmp_path / "src" / "pkg" / "ok.py").write_text(
            "def add(a: int, b: int) -> int:\n    return a + b\n", encoding="utf-8"
        )
        fake_rule = SimpleNamespace(
            id="SE-CQ-003",
            raw={
                "metadata": {"domain": "code-quality", "enforcement": "blocking"},
                "verification": {"methods": ["anti-fabrication-ast-check", "complexity-budget-check"]},
                "human_review": {"required": False},
            },
        )
        ev = RuleEvaluator(tmp_path, commit_sha=SHA_A, working_tree_clean=True)
        res_ok = ev.evaluate_all([fake_rule])[0]
        assert res_ok.status == STATUS_PASS
    
        ev_dirty = RuleEvaluator(tmp_path, commit_sha=SHA_A, working_tree_clean=False)
        assert ev_dirty.evaluate_rule(fake_rule).status == STATUS_BLOCKED
    
        # Accepted risk via active exception on non-critical rule
>       (tmp_path / ".gencode-gov").mkdir()

tests/unit/verification/test_engineering_governance_upgrades.py:801: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

self = PosixPath('/tmp/pytest-of-runner/pytest-2/test_assess_dispatch_method_re0/.gencode-gov')
mode = 511, parents = False, exist_ok = False

    def mkdir(self, mode=0o777, parents=False, exist_ok=False):
        """
        Create a new directory at this given path.
        """
        try:
>           os.mkdir(self, mode)
E           FileExistsError: [Errno 17] File exists: '/tmp/pytest-of-runner/pytest-2/test_assess_dispatch_method_re0/.gencode-gov'

/opt/hostedtoolcache/Python/3.12.16/x64/lib/python3.12/pathlib.py:1311: FileExistsError
_________________ test_cli_extensions_and_repository_validator _________________

tmp_path = PosixPath('/tmp/pytest-of-runner/pytest-2/test_cli_extensions_and_reposi0')
monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x7b8dde3dec60>

    def test_cli_extensions_and_repository_validator(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("GENCODE_GOV_AGENT_SESSION_ID", raising=False)
        monkeypatch.delenv("GENCODE_GOV_SANDBOX", raising=False)
    
        repo_root = Path(__file__).resolve().parents[3]
        val_summary = validate_repository(repo_root)
>       assert val_summary.ok, f"Repository validation errors: {val_summary.errors}"
E       AssertionError: Repository validation errors: ("SE-TST-005 [SE-TST-005-test-assertion-adequacy-and-anti-tampering.yaml]: metadata: 'severity' is a required property", "SE-TST-005 [SE-TST-005-test-assertion-adequacy-and-anti-tampering.yaml]: metadata.status: 'critical' is not one of ['proposed', 'active', 'deprecated', 'archived']", "SE-TST-005: invalid severity 'None'", "SE-TST-005: invalid status 'critical'")
E       assert False
E        +  where False = ValidationSummary(ok=False, rules_checked=47, schemas_checked=15, skills_checked=10, errors=("SE-TST-005 [SE-TST-005-t... 'active', 'deprecated', 'archived']", "SE-TST-005: invalid severity 'None'", "SE-TST-005: invalid status 'critical'")).ok

tests/unit/verification/test_engineering_governance_upgrades.py:846: AssertionError
______________ test_repository_frozen_apis_and_clean_integration _______________

tmp_path = PosixPath('/tmp/pytest-of-runner/pytest-2/test_repository_frozen_apis_an0')

    def test_repository_frozen_apis_and_clean_integration(tmp_path: Path) -> None:
        from gencode_gov.assessment.gates import evaluate
        from gencode_gov.cli import main as cli_main
        from gencode_gov.config import load_manifest
        from gencode_gov.evidence.store import read_evidence
    
        repo_root = Path(__file__).resolve().parents[3]
        assert callable(cli_main)
        assert callable(load_manifest)
        assert callable(read_evidence)
        assert callable(evaluate)
        assert verify_frozen_apis(repo_root)[0] == STATUS_PASS
        assert not (repo_root / "staging").exists()
        assert not (repo_root / ".github" / "workflows" / "recon_full_audit.yml").exists()
    
        # Package __init__.py fallback when frozen_apis specifies module.py path
        pkg_dir = tmp_path / "src" / "demo_pkg" / "cfg"
        pkg_dir.mkdir(parents=True)
        (pkg_dir / "__init__.py").write_text(
            "def load_manifest() -> dict:\n    return {}\n", encoding="utf-8"
        )
        (tmp_path / "manifest").mkdir()
        (tmp_path / "manifest" / "compatibility.yaml").write_text(
            "frozen_apis:\n  - src/demo_pkg/cfg.py::load_manifest\n",
            encoding="utf-8",
        )
        assert verify_frozen_apis(tmp_path)[0] == STATUS_PASS
>       assert read_evidence(tmp_path, "testing") is not None
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

tests/unit/verification/test_engineering_governance_upgrades.py:921: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

project_root = PosixPath('/tmp/pytest-of-runner/pytest-2/test_repository_frozen_apis_an0')
domain = 'testing'

    def read_evidence(project_root: Path, domain: str) -> object:
        """Read persisted domain evidence via EvidenceStore (frozen public API helper)."""
        store = EvidenceStore(project_root)
        reader = getattr(store, "read", None) or getattr(store, "load", None)
>       return reader(domain) if callable(reader) else store
               ^^^^^^^^^^^^^^
E       TypeError: EvidenceStore.read() missing 1 required positional argument: 'evidence_id'

src/gencode_gov/evidence/store.py:294: TypeError
____________ test_attestation_and_drift_symlink_and_timestamp_edges ____________

tmp_path = PosixPath('/tmp/pytest-of-runner/pytest-2/test_attestation_and_drift_sym0')
monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x7b8dde476900>

    def test_attestation_and_drift_symlink_and_timestamp_edges(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("GENCODE_GOV_AGENT_SESSION_ID", raising=False)
        monkeypatch.delenv("GENCODE_GOV_SANDBOX", raising=False)
    
        with pytest.raises(EvidenceError):
            _parse_utc("not-a-date", "attested_at")
        with pytest.raises(EvidenceError):
            _parse_utc("2026-01-01T00:00:00", "attested_at")
    
        # Symlinked .gencode-gov rejected in create_human_attestation
        real_dir = tmp_path / "real"
        real_dir.mkdir()
        p1 = tmp_path / "p1"
        p1.mkdir()
        (p1 / ".gencode-gov").symlink_to(real_dir)
        with pytest.raises(EvidenceError):
            create_human_attestation(
                p1,
                rule_ids=["SE-ARC-001"],
                reviewer="lead_reviewer_role",
                approver_role="lead",
                commit_sha=SHA_1,
                rationale="Valid rationale text here.",
            )
    
        p2 = tmp_path / "p2"
        (p2 / ".gencode-gov").mkdir(parents=True)
        (p2 / ".gencode-gov" / "evidence").symlink_to(real_dir)
        with pytest.raises(EvidenceError):
            create_human_attestation(
                p2,
                rule_ids=["SE-ARC-001"],
                reviewer="lead_reviewer_role",
                approver_role="lead",
                commit_sha=SHA_1,
                rationale="Valid rationale text here.",
            )
    
        p3 = tmp_path / "p3"
        (p3 / ".gencode-gov" / "evidence").mkdir(parents=True)
        (p3 / ".gencode-gov" / "evidence" / "attestations").symlink_to(real_dir)
        with pytest.raises(EvidenceError):
            create_human_attestation(
                p3,
                rule_ids=["SE-ARC-001"],
                reviewer="lead_reviewer_role",
                approver_role="lead",
                commit_sha=SHA_1,
                rationale="Valid rationale text here.",
            )
    
        # Bot reviewer & bad timestamp inside stored attestation JSON
        p4 = tmp_path / "p4"
        att_dir = p4 / ".gencode-gov" / "evidence" / "attestations"
        att_dir.mkdir(parents=True)
        (att_dir / "ATTEST-AUTO0001.json").write_text(
            json.dumps(
                {
                    "attestation_id": "ATTEST-AUTO0001",
                    "rule_ids": ["SE-ARC-001"],
                    "reviewer": "bot-service",
                    "approver_role": "lead",
                    "commit_sha": SHA_1,
                    "attested_at": "2026-01-01T00:00:00Z",
                    "expires_at": "2026-02-01T00:00:00Z",
                    "rationale": "Automated service check.",
                    "reviewed_artifacts": [],
                }
            ),
            encoding="utf-8",
        )
        (att_dir / "ATTEST-BADTIME1.json").write_text(
            json.dumps(
                {
                    "attestation_id": "ATTEST-BADTIME1",
                    "rule_ids": ["SE-ARC-001"],
                    "reviewer": "lead_reviewer_role",
                    "approver_role": "lead",
                    "commit_sha": SHA_1,
                    "attested_at": "bad-date",
                    "expires_at": "2026-02-01T00:00:00Z",
                    "rationale": "Malformed timestamp test.",
                    "reviewed_artifacts": [],
                }
            ),
            encoding="utf-8",
        )
        st, rsn = verify_human_attestation(p4, rule_id="SE-ARC-001", expected_commit_sha=SHA_1)
        assert st == STATUS_BLOCKED
>       assert "bot/agent" in rsn and "invalid attested_at" in rsn
E       assert ('bot/agent' in "attestation ATTEST-AUTO0001 is expired; invalid attested_at timestamp: 'bad-date'")

tests/unit/verification/test_engineering_governance_edge_branches.py:144: AssertionError
__________________ test_cli_extensions_text_modes_and_errors ___________________

tmp_path = PosixPath('/tmp/pytest-of-runner/pytest-2/test_cli_extensions_text_modes0')
capsys = <_pytest.capture.CaptureFixture object at 0x7b8dde572bd0>
monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x7b8dde570ce0>

    def test_cli_extensions_text_modes_and_errors(
        tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("GENCODE_GOV_AGENT_SESSION_ID", raising=False)
        monkeypatch.delenv("GENCODE_GOV_SANDBOX", raising=False)
    
        parser = argparse.ArgumentParser()
        sub = parser.add_subparsers(dest="command")
        register_extended_subcommands(sub, lambda _p: None)
    
        # cmd_attest missing commit & error path & text output
        args_no_sha = parser.parse_args(
            [
                "attest",
                str(tmp_path),
                "--rule",
                "SE-ARC-001",
                "--reviewer",
                "lead_reviewer_role",
                "--role",
                "lead",
                "--rationale",
                "Valid rationale text.",
            ]
        )
        assert cmd_attest(args_no_sha, commit_resolver=lambda _p: None) == 1
    
        args_bad = parser.parse_args(
            [
                "attest",
                str(tmp_path),
                "--rule",
                "SE-ARC-001",
                "--reviewer",
                "ci-worker",
                "--role",
                "lead",
                "--rationale",
                "Valid rationale text.",
                "--commit",
                SHA_1,
            ]
        )
>       assert cmd_attest(args_bad, commit_resolver=lambda _p: SHA_1) == 1
E       AssertionError: assert 0 == 1
E        +  where 0 = cmd_attest(Namespace(command='attest', project='/tmp/pytest-of-runner/pytest-2/test_cli_extensions_text_modes0', rules=['SE-ARC-0...1111111111111111111111', json=False, func=<function register_extended_subcommands.<locals>.<lambda> at 0x7b8dde3da5c0>), commit_resolver=<function test_cli_extensions_text_modes_and_errors.<locals>.<lambda> at 0x7b8dde3dade0>)

tests/unit/verification/test_engineering_governance_edge_branches.py:224: AssertionError
----------------------------- Captured stdout call -----------------------------
[OK] Recorded attestation ATTEST-GENCODE-GOV-90989374C879 -> .gencode-gov/evidence/attestations/ATTEST-GENCODE-GOV-90989374C879.json
----------------------------- Captured stderr call -----------------------------
[FAIL] could not resolve 40-char Git HEAD commit SHA
_______________ test_evaluator_validator_and_diff_edge_branches ________________

tmp_path = PosixPath('/tmp/pytest-of-runner/pytest-2/test_evaluator_validator_and_d0')

    def test_evaluator_validator_and_diff_edge_branches(tmp_path: Path) -> None:
        # RuleEvaluator: unregistered method, disallowed domain, custom runner PASS/FAIL/BLOCKED
        class CustomRunner(Runner):
            def __init__(self, outcome: RunnerOutcome) -> None:
                self._outcome = outcome
    
            def run(self, project_root: Path, artifact_dir: Path | None = None) -> RunnerResult:
                _ = project_root, artifact_dir
                return RunnerResult(runner="mypy", outcome=self._outcome, reason="done")
    
        r_unreg = SimpleNamespace(
            id="SE-CQ-999",
            raw={
                "metadata": {"domain": "code-quality", "enforcement": "blocking"},
                "verification": {"methods": ["nonexistent-method", "slo-document-presence"]},
            },
        )
        ev = RuleEvaluator(tmp_path, commit_sha=SHA_1)
        assert ev.evaluate_rule(r_unreg).status == STATUS_BLOCKED
    
        r_mypy = SimpleNamespace(
            id="SE-CQ-002",
            raw={
                "metadata": {"domain": "code-quality", "enforcement": "critical"},
                "verification": {"methods": ["type-checker-execution"]},
            },
        )
        assert (
            RuleEvaluator(
                tmp_path,
                commit_sha=SHA_1,
>               runner_overrides={"mypy": CustomRunner(RunnerOutcome.PASS)},
                                          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
            )
            .evaluate_rule(r_mypy)
            .status
            == STATUS_PASS
        )
E       TypeError: Can't instantiate abstract class CustomRunner without an implementation for abstract method 'name'

tests/unit/verification/test_engineering_governance_edge_branches.py:312: TypeError
________ test_cli_validate_inspect_tools_attest_diff_drift_and_reports _________

tmp_path = PosixPath('/tmp/pytest-of-runner/pytest-2/test_cli_validate_inspect_tool0')
capsys = <_pytest.capture.CaptureFixture object at 0x7b8dde3de480>
monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x7b8dde3dd2b0>

    def test_cli_validate_inspect_tools_attest_diff_drift_and_reports(
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.delenv("GENCODE_GOV_AGENT_SESSION_ID", raising=False)
        monkeypatch.delenv("GENCODE_GOV_SANDBOX", raising=False)
    
        sha = _init_governed_python_project(tmp_path)
    
        # 1. inspect --tools --json
>       rc_ins = main(["inspect", str(tmp_path), "--tools", "--json"])
                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

tests/integration/test_end_to_end_governance_excellence.py:85: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
src/gencode_gov/cli.py:1274: in main
    return int(args.func(args))
               ^^^^^^^^^^^^^^^
src/gencode_gov/cli.py:103: in cmd_inspect
    profile = match_profile(project)
              ^^^^^^^^^^^^^^^^^^^^^^
src/gencode_gov/projects/matcher.py:73: in match_profile
    declared = _read_declared_profile(root)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

project_root = PosixPath('/tmp/pytest-of-runner/pytest-2/test_cli_validate_inspect_tool0')

    def _read_declared_profile(project_root: Path) -> str | None:
        path = project_root / ".gencode-gov" / "project.yaml"
        if not path.is_file():
            return None
        try:
            with path.open("r", encoding="utf-8") as stream:
                data = yaml.safe_load(stream)
        except (yaml.YAMLError, OSError) as exc:
            raise ConfigError(f"cannot read project declaration {path}: {exc}") from exc
        if not isinstance(data, dict):
            raise ConfigError(f"project declaration must be a YAML mapping: {path}")
        project: Any = data.get("project")
        if not isinstance(project, dict):
>           raise ConfigError(f"project declaration is missing its 'project' mapping: {path}")
E           gencode_gov.core.errors.ConfigError: project declaration is missing its 'project' mapping: /tmp/pytest-of-runner/pytest-2/test_cli_validate_inspect_tool0/.gencode-gov/project.yaml

src/gencode_gov/projects/matcher.py:37: ConfigError

---------- coverage: platform linux, python 3.12.16-final-0 ----------
Name                                                              Stmts   Miss  Cover   Missing
-----------------------------------------------------------------------------------------------
src/gencode_gov/assessment/drift.py                                  92      6    93%   83-85, 111, 114, 149
src/gencode_gov/cli_extensions.py                                   112     54    52%   87-89, 101, 108-122, 130-157, 162-195, 205-219
src/gencode_gov/evidence/attestation.py                             157     41    74%   112, 118, 139, 143, 146, 148, 150, 152, 156-166, 264, 268-269, 272-276, 289-317, 325
src/gencode_gov/reporting/html_reporter.py                           50      2    96%   19, 63
src/gencode_gov/reporting/sarif_reporter.py                          33      1    97%   27
src/gencode_gov/rules/evaluator.py                                  106     20    81%   73-77, 96, 148-153, 158-170, 174-178, 195
src/gencode_gov/validation.py                                       150     35    77%   47, 51-53, 55, 67-72, 85, 92-93, 105-106, 109, 115, 135, 137, 149, 166, 171-175, 206-230
src/gencode_gov/verification/architecture_verifier.py               136      1    99%   47
src/gencode_gov/verification/assess_dispatch.py                     103     52    50%   57, 62-63, 65, 82-84, 87, 90, 93-95, 103-140, 143-156
src/gencode_gov/verification/code_and_test_integrity.py             188     26    86%   77, 86-92, 110-111, 130, 132, 160, 241-253, 280, 290-291, 306, 331, 339
src/gencode_gov/verification/diff_governance.py                     163     14    91%   63, 80-81, 83, 87, 89, 94-95, 203, 248, 265-266, 282, 286
src/gencode_gov/verification/domain_verifiers.py                    526    147    72%   156, 196, 200, 204, 208, 211, 225, 227, 239, 262, 269-273, 276, 278-280, 291, 298, 302-305, 315, 320, 330, 348-350, 353-357, 361, 384, 402, 405, 412, 416, 421, 433, 441-443, 449, 452, 455, 459-504, 522-546, 549, 565-589, 596, 608, 617, 630, 638, 650-653, 666, 681, 684-687, 694, 698-700, 732, 741-743, 747, 757, 769-770, 813, 829, 861, 874, 880, 886, 960
src/gencode_gov/verification/methods.py                              27      0   100%
src/gencode_gov/verification/runners/polyglot_quality_runner.py      55     39    29%   31-33, 43-121
-----------------------------------------------------------------------------------------------
TOTAL                                                              1898    438    77%

FAIL Required test coverage of 100% not reached. Total coverage: 76.92%
=========================== short test summary info ============================
FAILED tests/unit/verification/test_engineering_governance_upgrades.py::test_human_attestation_lifecycle_and_anti_agent_guards - Failed: DID NOT RAISE EvidenceError
FAILED tests/unit/verification/test_engineering_governance_upgrades.py::test_domain_verifiers_and_polyglot_runner_comprehensive - FileExistsError: [Errno 17] File exists: '/tmp/pytest-of-runner/pytest-2/test_domain_verifiers_and_poly0/.gencode-gov'
FAILED tests/unit/verification/test_engineering_governance_upgrades.py::test_assess_dispatch_method_registry_and_rule_evaluator - FileExistsError: [Errno 17] File exists: '/tmp/pytest-of-runner/pytest-2/test_assess_dispatch_method_re0/.gencode-gov'
FAILED tests/unit/verification/test_engineering_governance_upgrades.py::test_cli_extensions_and_repository_validator - AssertionError: Repository validation errors: ("SE-TST-005 [SE-TST-005-test-assertion-adequacy-and-anti-tampering.yaml]: metadata: 'severity' is a required property", "SE-TST-005 [SE-TST-005-test-assertion-adequacy-and-anti-tampering.yaml]: metadata.status: 'critical' is not one of ['proposed', 'active', 'deprecated', 'archived']", "SE-TST-005: invalid severity 'None'", "SE-TST-005: invalid status 'critical'")
assert False
 +  where False = ValidationSummary(ok=False, rules_checked=47, schemas_checked=15, skills_checked=10, errors=("SE-TST-005 [SE-TST-005-t... 'active', 'deprecated', 'archived']", "SE-TST-005: invalid severity 'None'", "SE-TST-005: invalid status 'critical'")).ok
FAILED tests/unit/verification/test_engineering_governance_upgrades.py::test_repository_frozen_apis_and_clean_integration - TypeError: EvidenceStore.read() missing 1 required positional argument: 'evidence_id'
FAILED tests/unit/verification/test_engineering_governance_edge_branches.py::test_attestation_and_drift_symlink_and_timestamp_edges - assert ('bot/agent' in "attestation ATTEST-AUTO0001 is expired; invalid attested_at timestamp: 'bad-date'")
FAILED tests/unit/verification/test_engineering_governance_edge_branches.py::test_cli_extensions_text_modes_and_errors - AssertionError: assert 0 == 1
 +  where 0 = cmd_attest(Namespace(command='attest', project='/tmp/pytest-of-runner/pytest-2/test_cli_extensions_text_modes0', rules=['SE-ARC-0...1111111111111111111111', json=False, func=<function register_extended_subcommands.<locals>.<lambda> at 0x7b8dde3da5c0>), commit_resolver=<function test_cli_extensions_text_modes_and_errors.<locals>.<lambda> at 0x7b8dde3dade0>)
FAILED tests/unit/verification/test_engineering_governance_edge_branches.py::test_evaluator_validator_and_diff_edge_branches - TypeError: Can't instantiate abstract class CustomRunner without an implementation for abstract method 'name'
FAILED tests/integration/test_end_to_end_governance_excellence.py::test_cli_validate_inspect_tools_attest_diff_drift_and_reports - gencode_gov.core.errors.ConfigError: project declaration is missing its 'project' mapping: /tmp/pytest-of-runner/pytest-2/test_cli_validate_inspect_tool0/.gencode-gov/project.yaml
[EXIT 1]
```

## 10. Repository Governance Validation (gencode-gov validate --json)
```text
{
  "ok": false,
  "rules_checked": 47,
  "schemas_checked": 15,
  "skills_checked": 10,
  "errors": [
    "SE-TST-005 [SE-TST-005-test-assertion-adequacy-and-anti-tampering.yaml]: metadata: 'severity' is a required property",
    "SE-TST-005 [SE-TST-005-test-assertion-adequacy-and-anti-tampering.yaml]: metadata.status: 'critical' is not one of ['proposed', 'active', 'deprecated', 'archived']",
    "SE-TST-005: invalid severity 'None'",
    "SE-TST-005: invalid status 'critical'"
  ]
}
[EXIT 1]
```

## 11. Polyglot Tool Matrix Inspection (gencode-gov inspect . --tools --json)
```text
{
  "project": "/home/runner/work/GENCODE-GOV/GENCODE-GOV",
  "profile": {
    "name": "enterprise",
    "reason": "declared in .gencode-gov/project.yaml",
    "explicit": true
  },
  "languages": {
    "detected": [
      "python"
    ],
    "unknown": [
      ".j2",
      ".json",
      ".md",
      ".ps1",
      ".sh",
      ".svg",
      ".toml",
      ".txt",
      ".typed",
      ".yaml",
      ".yml"
    ]
  },
  "system": {
    "name": "GENCODE-GOV",
    "version": "0.1.0"
  },
  "tools": [
    {
      "language": "python",
      "profile_loaded": true,
      "tools": [
        {
          "tool": "ruff",
          "available": true,
          "path": "/tmp/gov_venv/bin/ruff"
        },
        {
          "tool": "mypy",
          "available": true,
          "path": "/tmp/gov_venv/bin/mypy"
        },
        {
          "tool": "pytest",
          "available": true,
          "path": "/tmp/gov_venv/bin/pytest"
        }
      ]
    }
  ]
}
[EXIT 0]
```

## 12. Clean Working Tree Check
```text
commit 4620052bd4370794a34f683b3ca0c1468191eee8
Author: github-actions <github-actions-bot>
Date:   Sat Nov 28 00:24:54 2026 +0000

    feat(governance): integrate verified engineering governance and verification upgrades

 .gencode-gov/architecture-contracts.yaml           |  39 +
 .gencode-gov/project.yaml                          |   4 +-
 .github/workflows/recon_full_audit.yml             | 132 ---
 AGENTS.md                                          |   5 +
 docs/evidence/EVIDENCE_MODEL.md                    | 243 +-----
 docs/governance/ENGINEERING_GAP_REGISTER.md        |  30 +
 rules/README.md                                    |  31 +
 ...PI-002-frozen-api-and-schema-compatibility.yaml |  42 +
 ...ARC-002-executable-architecture-boundaries.yaml |  42 +
 ...-CQ-003-ai-anti-fabrication-and-complexity.yaml |  49 ++
 .../SE-DB-003-zero-downtime-migration-safety.yaml  |  42 +
 ...eterministic-dependency-and-action-pinning.yaml |  43 +
 ...REL-005-outbound-timeout-and-bounded-retry.yaml |  41 +
 ...EC-011-sbom-license-and-vulnerability-gate.yaml |  43 +
 ...test-assertion-adequacy-and-anti-tampering.yaml |  43 +
 schemas/architecture-contracts.schema.json         |  66 ++
 schemas/drift-ledger.schema.json                   |  52 ++
 schemas/review-attestation.schema.json             |  82 ++
 scripts/validation/validate_all.py                 |  87 +-
 .../gencode-gov/references/OPERATIONAL_CONTRACT.md |   5 +
 src/gencode_gov/assessment/drift.py                | 173 ++++
 src/gencode_gov/assessment/gates.py                |   3 +
 src/gencode_gov/cli.py                             | 154 +++-
 src/gencode_gov/cli_extensions.py                  | 219 +++++
 src/gencode_gov/evidence/attestation.py            | 329 +++++++
 src/gencode_gov/evidence/store.py                  |   7 +
 src/gencode_gov/language_support/detector.py       |   6 +
 src/gencode_gov/reporting/html_reporter.py         | 130 ++-
 src/gencode_gov/reporting/markdown_reporter.py     |   3 +-
 src/gencode_gov/reporting/sarif_reporter.py        |  94 ++
 src/gencode_gov/resources/agent_pack/AGENTS.md     |   5 +
 .../references/ENGINEERING_CHARTER_AND_DOMAINS.md  |  20 +
 .../gencode-gov/references/OPERATIONAL_CONTRACT.md | 201 +++++
 .../skills/gencode-gov/references/README.md        |   8 +
 .../gencode-gov/references/SECURITY_POSTURE.md     | 506 +++++++++++
 .../references/VERIFICATION_AND_ADOPTION.md        |  39 +
 src/gencode_gov/rules/evaluator.py                 | 214 ++++-
 src/gencode_gov/validation.py                      | 230 +++++
 .../verification/architecture_verifier.py          | 244 ++++++
 src/gencode_gov/verification/assess_dispatch.py    |  32 +-
 .../verification/code_and_test_integrity.py        | 341 ++++++++
 src/gencode_gov/verification/diff_governance.py    | 298 +++++++
 src/gencode_gov/verification/domain_verifiers.py   | 960 +++++++++++++++++++++
 src/gencode_gov/verification/methods.py            | 307 +++++--
 .../runners/polyglot_quality_runner.py             | 126 +++
 staging/part_01                                    | 550 ------------
 staging/part_02                                    | 536 ------------
 staging/part_03                                    | 476 ----------
 staging/part_04                                    | 559 ------------
 staging/part_05                                    | 698 ---------------
 staging/part_06                                    | 535 ------------
 staging/part_07                                    | 535 ------------
 staging/part_08                                    | 437 ----------
 staging/part_09                                    | 541 ------------
 staging/part_10                                    | 140 ---
 .../test_end_to_end_governance_excellence.py       | 142 +++
 tests/unit/cli/test_install.py                     |   2 +-
 .../test_engineering_governance_edge_branches.py   | 677 +++++++++++++++
 .../test_engineering_governance_upgrades.py        | 921 ++++++++++++++++++++
 59 files changed, 6955 insertions(+), 5564 deletions(-)
[EXIT 0]
```

## 13. Diff-Check Without --allow-protected (Protected File Inventory)
```json
{
  "status": "FAIL",
  "base_ref": "origin/main",
  "head_ref": "HEAD",
  "files_changed": 59,
  "protected_touched": [
    ".github/workflows/recon_full_audit.yml",
    "AGENTS.md",
    "schemas/architecture-contracts.schema.json",
    "schemas/drift-ledger.schema.json",
    "schemas/review-attestation.schema.json"
  ],
  "deleted_tests": [],
  "frozen_api_failures": [],
  "schema_breaking_changes": [],
  "reasons": [
    "protected governance files modified without --allow-protected: ['.github/workflows/recon_full_audit.yml', 'AGENTS.md', 'schemas/architecture-contracts.schema.json', 'schemas/drift-ledger.schema.json', 'schemas/review-attestation.schema.json']"
  ]
}
```

## 14. Diff-Check With --allow-protected (Compatibility & Schema Gate)
```text
{
  "status": "PASS",
  "base_ref": "origin/main",
  "head_ref": "HEAD",
  "files_changed": 59,
  "protected_touched": [
    ".github/workflows/recon_full_audit.yml",
    "AGENTS.md",
    "schemas/architecture-contracts.schema.json",
    "schemas/drift-ledger.schema.json",
    "schemas/review-attestation.schema.json"
  ],
  "deleted_tests": [],
  "frozen_api_failures": [],
  "schema_breaking_changes": [],
  "reasons": []
}
[EXIT 0]
```

## 15. Longitudinal Drift Snapshot (gencode-gov drift . --no-persist --json)
```text
{
  "current": {
    "recorded_at": "2026-11-28T00:24:56Z",
    "commit_sha": "4620052bd4370794a34f683b3ca0c1468191eee8",
    "python_files": 142,
    "max_cyclomatic_complexity": 114,
    "mean_cyclomatic_complexity": 7.02,
    "internal_import_edges": 58,
    "declared_dependencies": 3,
    "active_exceptions": 0
  },
  "prior": null,
  "warnings": []
}
[EXIT 0]
```

## 16. Self-Governance Assessment Summary (gencode-gov assess . --json)
```text
Decision: BLOCKED
Score: {"total": 0.0}
Total rules evaluated: 43
  BLOCKED (27): ['SE-ARC-001', 'SE-DB-001', 'SE-DB-002', 'SE-INF-001', 'SE-OBS-001', 'SE-OBS-002', 'SE-OBS-003', 'SE-PRF-002', 'SE-PRI-001', 'SE-REL-001', 'SE-REL-002', 'SE-REL-004', 'SE-REQ-002', 'SE-REQ-003', 'SE-SEC-001', 'SE-SEC-002', 'SE-SEC-003', 'SE-SEC-004', 'SE-SEC-005', 'SE-SEC-006', 'SE-SEC-007', 'SE-SEC-009', 'SE-SEC-010', 'SE-SEC-011', 'SE-SEC-GOV-001', 'SE-SEC-GOV-002', 'SE-TST-002']
  FAIL (5): ['SE-ARC-002', 'SE-CQ-003', 'SE-DEV-002', 'SE-SEC-008', 'SE-TST-004']
  NOT_APPLICABLE (3): ['SE-API-001', 'SE-PRF-001', 'SE-SCL-001']
  PASS (8): ['SE-API-002', 'SE-CQ-002', 'SE-DB-003', 'SE-DEV-001', 'SE-MNT-001', 'SE-REL-003', 'SE-REL-005', 'SE-TST-003']
    FAIL detail -> SE-ARC-002: architecture-layer-boundary-check: circular package dependencies (2 > 0): ['config <-> core', 'governance <-> policies <-> rules']; module-cycle-detection: circular package dependencies (2 > 0): ['config <-> core', 'governance <-> policies <-> rules']
    FAIL detail -> SE-CQ-003: complexity-budget-check: functions exceeding complexity ceiling (45): ['src/gencode_gov/cli.py:271 _orig_cmd_assess (cc=114)', 'src/gencode_gov/security_audit/validators.py:134 validate_coverage_ledger_data (cc=66)', 'src/gencode_gov/security_audit/validators.py:270 validate_findings_data (cc=49)', 'src/gencode_gov/validation.py:59 validate_repository (cc=48)', 'src/gencode_gov/verification/domain_verifiers.py:507 _verify_sbom_and_security_methods (cc=53)']
    FAIL detail -> SE-DEV-002: dependency-lockfile-determinism-check: no deterministic dependency lockfile found in repository root
    FAIL detail -> SE-SEC-008: lockfile-inventory: no deterministic dependency lockfile found in repository root; software-composition-analysis: missing .gencode-gov/security-controls.yaml verification record for software-composition-analysis; unused-dependency-analysis: missing .gencode-gov/security-controls.yaml verification record for unused-dependency-analysis; vulnerability-triage: missing .gencode-gov/security-controls.yaml verification record for vulnerability-triage; provenance-review: missing .gencode-gov/security-controls.yaml verification record for provenance-review; human-review-approval: authorized human review attestation missing for SE-SEC-008 (record via 'gencode-gov attest --rule SE-SEC-008')
    FAIL detail -> SE-TST-004: zero-test-failures-check: pytest reported 17 failure(s) and 0 error(s); negative-security-scenario-traceability: missing .gencode-gov/security-test-matrix.yaml; generic test counts do not prove negative-security scenario coverage; critical-workflow-test-coverage-review: missing security-test-matrix.yaml or critical-workflows.yaml; human-security-review: authorized human review attestation missing for SE-TST-004 (record via 'gencode-gov attest --rule SE-TST-004')
```

## 17. Wheel Build, Clean Venv Install & Post-Install CLI Smoke Tests
```text
* Creating isolated environment: venv+pip...
* Installing packages in isolated environment:
  - setuptools==84.2.1
  - wheel==0.48.0
* Getting build dependencies for wheel...
running egg_info
creating src/gencode_gov.egg-info
writing src/gencode_gov.egg-info/PKG-INFO
writing dependency_links to src/gencode_gov.egg-info/dependency_links.txt
writing entry points to src/gencode_gov.egg-info/entry_points.txt
writing requirements to src/gencode_gov.egg-info/requires.txt
writing top-level names to src/gencode_gov.egg-info/top_level.txt
writing manifest file 'src/gencode_gov.egg-info/SOURCES.txt'
reading manifest file 'src/gencode_gov.egg-info/SOURCES.txt'
adding license file 'LICENSE'
writing manifest file 'src/gencode_gov.egg-info/SOURCES.txt'
WARNING `project.license` as a TOML table is deprecated
!!

        ********************************************************************************
        Please use a simple string containing a SPDX expression for `project.license`. You can also use `project.license-files`. (Both options available on setuptools>=77.0.0).

        By 2027-Feb-18, you need to update your project and remove deprecated calls
        or your builds will no longer be supported.

        See https://packaging.python.org/en/latest/guides/writing-pyproject-toml/#license for details.
        ********************************************************************************

!!
WARNING License classifiers are deprecated.
!!

        ********************************************************************************
        Please consider removing the following classifiers in favor of a SPDX license expression:

        License :: OSI Approved :: MIT License

        See https://packaging.python.org/en/latest/guides/writing-pyproject-toml/#license for details.
        ********************************************************************************

!!
WARNING License classifiers are deprecated.
!!

        ********************************************************************************
        Please consider removing the following classifiers in favor of a SPDX license expression:

        License :: OSI Approved :: MIT License

        See https://packaging.python.org/en/latest/guides/writing-pyproject-toml/#license for details.
        ********************************************************************************

!!
* Installed build dependency versions:
  - setuptools==84.2.1
  - wheel==0.48.0
* Building wheel...
running bdist_wheel
running build
running build_py
creating build/lib/gencode_gov
copying src/gencode_gov/__init__.py -> build/lib/gencode_gov
copying src/gencode_gov/validation.py -> build/lib/gencode_gov
copying src/gencode_gov/cli.py -> build/lib/gencode_gov
copying src/gencode_gov/cli_extensions.py -> build/lib/gencode_gov
copying src/gencode_gov/config.py -> build/lib/gencode_gov
creating build/lib/gencode_gov/language_support
copying src/gencode_gov/language_support/__init__.py -> build/lib/gencode_gov/language_support
copying src/gencode_gov/language_support/language_profile_loader.py -> build/lib/gencode_gov/language_support
copying src/gencode_gov/language_support/registry.py -> build/lib/gencode_gov/language_support
copying src/gencode_gov/language_support/compatibility.py -> build/lib/gencode_gov/language_support
copying src/gencode_gov/language_support/detector.py -> build/lib/gencode_gov/language_support
copying src/gencode_gov/language_support/tool_resolver.py -> build/lib/gencode_gov/language_support
creating build/lib/gencode_gov/assessment
copying src/gencode_gov/assessment/decision.py -> build/lib/gencode_gov/assessment
copying src/gencode_gov/assessment/__init__.py -> build/lib/gencode_gov/assessment
copying src/gencode_gov/assessment/drift.py -> build/lib/gencode_gov/assessment
copying src/gencode_gov/assessment/gates.py -> build/lib/gencode_gov/assessment
copying src/gencode_gov/assessment/scorer.py -> build/lib/gencode_gov/assessment
creating build/lib/gencode_gov/security_audit
copying src/gencode_gov/security_audit/__init__.py -> build/lib/gencode_gov/security_audit
copying src/gencode_gov/security_audit/reassessment.py -> build/lib/gencode_gov/security_audit
copying src/gencode_gov/security_audit/orchestrator.py -> build/lib/gencode_gov/security_audit
copying src/gencode_gov/security_audit/coverage.py -> build/lib/gencode_gov/security_audit
copying src/gencode_gov/security_audit/sandbox.py -> build/lib/gencode_gov/security_audit
copying src/gencode_gov/security_audit/hunting.py -> build/lib/gencode_gov/security_audit
copying src/gencode_gov/security_audit/cli_dispatch.py -> build/lib/gencode_gov/security_audit
copying src/gencode_gov/security_audit/findings.py -> build/lib/gencode_gov/security_audit
copying src/gencode_gov/security_audit/runtime.py -> build/lib/gencode_gov/security_audit
copying src/gencode_gov/security_audit/verifier.py -> build/lib/gencode_gov/security_audit
copying src/gencode_gov/security_audit/dispatcher.py -> build/lib/gencode_gov/security_audit
copying src/gencode_gov/security_audit/reporting.py -> build/lib/gencode_gov/security_audit
copying src/gencode_gov/security_audit/validators.py -> build/lib/gencode_gov/security_audit
copying src/gencode_gov/security_audit/taxonomy.py -> build/lib/gencode_gov/security_audit
copying src/gencode_gov/security_audit/worker_entry.py -> build/lib/gencode_gov/security_audit
copying src/gencode_gov/security_audit/governance_bridge.py -> build/lib/gencode_gov/security_audit
creating build/lib/gencode_gov/verification
copying src/gencode_gov/verification/__init__.py -> build/lib/gencode_gov/verification
copying src/gencode_gov/verification/profiles.py -> build/lib/gencode_gov/verification
copying src/gencode_gov/verification/engine.py -> build/lib/gencode_gov/verification
copying src/gencode_gov/verification/domain_verifiers.py -> build/lib/gencode_gov/verification
copying src/gencode_gov/verification/architecture_verifier.py -> build/lib/gencode_gov/verification
copying src/gencode_gov/verification/code_and_test_integrity.py -> build/lib/gencode_gov/verification
copying src/gencode_gov/verification/assess_dispatch.py -> build/lib/gencode_gov/verification
copying src/gencode_gov/verification/scenario_verifier.py -> build/lib/gencode_gov/verification
copying src/gencode_gov/verification/methods.py -> build/lib/gencode_gov/verification
copying src/gencode_gov/verification/diff_governance.py -> build/lib/gencode_gov/verification
creating build/lib/gencode_gov/integrations
copying src/gencode_gov/integrations/__init__.py -> build/lib/gencode_gov/integrations
copying src/gencode_gov/integrations/base.py -> build/lib/gencode_gov/integrations
creating build/lib/gencode_gov/policies
copying src/gencode_gov/policies/__init__.py -> build/lib/gencode_gov/policies
copying src/gencode_gov/policies/advisory.py -> build/lib/gencode_gov/policies
copying src/gencode_gov/policies/blocking.py -> build/lib/gencode_gov/policies
copying src/gencode_gov/policies/exceptions.py -> build/lib/gencode_gov/policies
creating build/lib/gencode_gov/orchestrator
copying src/gencode_gov/orchestrator/stage_manager.py -> build/lib/gencode_gov/orchestrator
copying src/gencode_gov/orchestrator/__init__.py -> build/lib/gencode_gov/orchestrator
copying src/gencode_gov/orchestrator/task_dispatcher.py -> build/lib/gencode_gov/orchestrator
copying src/gencode_gov/orchestrator/lifecycle.py -> build/lib/gencode_gov/orchestrator
creating build/lib/gencode_gov/rules
copying src/gencode_gov/rules/__init__.py -> build/lib/gencode_gov/rules
copying src/gencode_gov/rules/registry.py -> build/lib/gencode_gov/rules
copying src/gencode_gov/rules/validator.py -> build/lib/gencode_gov/rules
copying src/gencode_gov/rules/loader.py -> build/lib/gencode_gov/rules
copying src/gencode_gov/rules/evaluator.py -> build/lib/gencode_gov/rules
creating build/lib/gencode_gov/projects
copying src/gencode_gov/projects/__init__.py -> build/lib/gencode_gov/projects
copying src/gencode_gov/projects/loader.py -> build/lib/gencode_gov/projects
copying src/gencode_gov/projects/matcher.py -> build/lib/gencode_gov/projects
creating build/lib/gencode_gov/evidence
copying src/gencode_gov/evidence/__init__.py -> build/lib/gencode_gov/evidence
copying src/gencode_gov/evidence/collector.py -> build/lib/gencode_gov/evidence
copying src/gencode_gov/evidence/attestation.py -> build/lib/gencode_gov/evidence
copying src/gencode_gov/evidence/supply_chain.py -> build/lib/gencode_gov/evidence
copying src/gencode_gov/evidence/store.py -> build/lib/gencode_gov/evidence
copying src/gencode_gov/evidence/integrity.py -> build/lib/gencode_gov/evidence
creating build/lib/gencode_gov/governance
copying src/gencode_gov/governance/__init__.py -> build/lib/gencode_gov/governance
copying src/gencode_gov/governance/charter_loader.py -> build/lib/gencode_gov/governance
copying src/gencode_gov/governance/enforcement.py -> build/lib/gencode_gov/governance
copying src/gencode_gov/governance/policy_loader.py -> build/lib/gencode_gov/governance
creating build/lib/gencode_gov/reporting
copying src/gencode_gov/reporting/__init__.py -> build/lib/gencode_gov/reporting
copying src/gencode_gov/reporting/json_reporter.py -> build/lib/gencode_gov/reporting
copying src/gencode_gov/reporting/sarif_reporter.py -> build/lib/gencode_gov/reporting
copying src/gencode_gov/reporting/markdown_reporter.py -> build/lib/gencode_gov/reporting
copying src/gencode_gov/reporting/html_reporter.py -> build/lib/gencode_gov/reporting
creating build/lib/gencode_gov/core
copying src/gencode_gov/core/constants.py -> build/lib/gencode_gov/core
copying src/gencode_gov/core/__init__.py -> build/lib/gencode_gov/core
copying src/gencode_gov/core/logging.py -> build/lib/gencode_gov/core
copying src/gencode_gov/core/errors.py -> build/lib/gencode_gov/core
creating build/lib/gencode_gov/verification/runners
copying src/gencode_gov/verification/runners/__init__.py -> build/lib/gencode_gov/verification/runners
copying src/gencode_gov/verification/runners/tsar_runner.py -> build/lib/gencode_gov/verification/runners
copying src/gencode_gov/verification/runners/polyglot_quality_runner.py -> build/lib/gencode_gov/verification/runners
copying src/gencode_gov/verification/runners/pytest_runner.py -> build/lib/gencode_gov/verification/runners
copying src/gencode_gov/verification/runners/supply_chain_runner.py -> build/lib/gencode_gov/verification/runners
copying src/gencode_gov/verification/runners/mypy_runner.py -> build/lib/gencode_gov/verification/runners
copying src/gencode_gov/verification/runners/base.py -> build/lib/gencode_gov/verification/runners
copying src/gencode_gov/verification/runners/test_suite_runner.py -> build/lib/gencode_gov/verification/runners
copying src/gencode_gov/verification/runners/ruff_runner.py -> build/lib/gencode_gov/verification/runners
creating build/lib/gencode_gov/integrations/_model_impl
copying src/gencode_gov/integrations/_model_impl/__init__.py -> build/lib/gencode_gov/integrations/_model_impl
creating build/lib/gencode_gov/integrations/agents
copying src/gencode_gov/integrations/agents/__init__.py -> build/lib/gencode_gov/integrations/agents
copying src/gencode_gov/integrations/agents/windsurf.py -> build/lib/gencode_gov/integrations/agents
copying src/gencode_gov/integrations/agents/amazon_q.py -> build/lib/gencode_gov/integrations/agents
copying src/gencode_gov/integrations/agents/gemini_cli.py -> build/lib/gencode_gov/integrations/agents
copying src/gencode_gov/integrations/agents/cursor.py -> build/lib/gencode_gov/integrations/agents
copying src/gencode_gov/integrations/agents/github_copilot.py -> build/lib/gencode_gov/integrations/agents
copying src/gencode_gov/integrations/agents/gemini.py -> build/lib/gencode_gov/integrations/agents
copying src/gencode_gov/integrations/agents/replit_agent.py -> build/lib/gencode_gov/integrations/agents
copying src/gencode_gov/integrations/agents/cline.py -> build/lib/gencode_gov/integrations/agents
copying src/gencode_gov/integrations/agents/claude_code.py -> build/lib/gencode_gov/integrations/agents
copying src/gencode_gov/integrations/agents/devin.py -> build/lib/gencode_gov/integrations/agents
copying src/gencode_gov/integrations/agents/gpt.py -> build/lib/gencode_gov/integrations/agents
copying src/gencode_gov/integrations/agents/continue_agent.py -> build/lib/gencode_gov/integrations/agents
copying src/gencode_gov/integrations/agents/tabnine.py -> build/lib/gencode_gov/integrations/agents
copying src/gencode_gov/integrations/agents/jetbrains_ai.py -> build/lib/gencode_gov/integrations/agents
copying src/gencode_gov/integrations/agents/codex_openai.py -> build/lib/gencode_gov/integrations/agents
copying src/gencode_gov/integrations/agents/sourcegraph_cody.py -> build/lib/gencode_gov/integrations/agents
copying src/gencode_gov/integrations/agents/aider.py -> build/lib/gencode_gov/integrations/agents
creating build/lib/gencode_gov/integrations/platforms
copying src/gencode_gov/integrations/platforms/__init__.py -> build/lib/gencode_gov/integrations/platforms
creating build/lib/gencode_gov/integrations/models
copying src/gencode_gov/integrations/models/__init__.py -> build/lib/gencode_gov/integrations/models
copying src/gencode_gov/integrations/models/_openai_compatible.py -> build/lib/gencode_gov/integrations/models
creating build/lib/gencode_gov/integrations/generic_agents
copying src/gencode_gov/integrations/generic_agents/__init__.py -> build/lib/gencode_gov/integrations/generic_agents
copying src/gencode_gov/integrations/generic_agents/adapter.py -> build/lib/gencode_gov/integrations/generic_agents
creating build/lib/gencode_gov/integrations/tsar
copying src/gencode_gov/integrations/tsar/__init__.py -> build/lib/gencode_gov/integrations/tsar
copying src/gencode_gov/integrations/tsar/adapter.py -> build/lib/gencode_gov/integrations/tsar
copying src/gencode_gov/integrations/tsar/verifier.py -> build/lib/gencode_gov/integrations/tsar
creating build/lib/gencode_gov/integrations/_model_impl/deepseek_coder
copying src/gencode_gov/integrations/_model_impl/deepseek_coder/__init__.py -> build/lib/gencode_gov/integrations/_model_impl/deepseek_coder
copying src/gencode_gov/integrations/_model_impl/deepseek_coder/adapter.py -> build/lib/gencode_gov/integrations/_model_impl/deepseek_coder
creating build/lib/gencode_gov/integrations/_model_impl/openai_o
copying src/gencode_gov/integrations/_model_impl/openai_o/__init__.py -> build/lib/gencode_gov/integrations/_model_impl/openai_o
copying src/gencode_gov/integrations/_model_impl/openai_o/adapter.py -> build/lib/gencode_gov/integrations/_model_impl/openai_o
creating build/lib/gencode_gov/integrations/_model_impl/qwen_coder
copying src/gencode_gov/integrations/_model_impl/qwen_coder/__init__.py -> build/lib/gencode_gov/integrations/_model_impl/qwen_coder
copying src/gencode_gov/integrations/_model_impl/qwen_coder/adapter.py -> build/lib/gencode_gov/integrations/_model_impl/qwen_coder
creating build/lib/gencode_gov/integrations/_model_impl/code_llama
copying src/gencode_gov/integrations/_model_impl/code_llama/__init__.py -> build/lib/gencode_gov/integrations/_model_impl/code_llama
copying src/gencode_gov/integrations/_model_impl/code_llama/adapter.py -> build/lib/gencode_gov/integrations/_model_impl/code_llama
creating build/lib/gencode_gov/integrations/platforms/github_copilot
copying src/gencode_gov/integrations/platforms/github_copilot/__init__.py -> build/lib/gencode_gov/integrations/platforms/github_copilot
copying src/gencode_gov/integrations/platforms/github_copilot/adapter.py -> build/lib/gencode_gov/integrations/platforms/github_copilot
creating build/lib/gencode_gov/integrations/models/openai-o
copying src/gencode_gov/integrations/models/openai-o/__init__.py -> build/lib/gencode_gov/integrations/models/openai-o
copying src/gencode_gov/integrations/models/openai-o/adapter.py -> build/lib/gencode_gov/integrations/models/openai-o
creating build/lib/gencode_gov/integrations/models/code-llama
copying src/gencode_gov/integrations/models/code-llama/__init__.py -> build/lib/gencode_gov/integrations/models/code-llama
copying src/gencode_gov/integrations/models/code-llama/adapter.py -> build/lib/gencode_gov/integrations/models/code-llama
creating build/lib/gencode_gov/integrations/models/deepseek-coder
copying src/gencode_gov/integrations/models/deepseek-coder/__init__.py -> build/lib/gencode_gov/integrations/models/deepseek-coder
copying src/gencode_gov/integrations/models/deepseek-coder/adapter.py -> build/lib/gencode_gov/integrations/models/deepseek-coder
creating build/lib/gencode_gov/integrations/models/qwen-coder
copying src/gencode_gov/integrations/models/qwen-coder/__init__.py -> build/lib/gencode_gov/integrations/models/qwen-coder
copying src/gencode_gov/integrations/models/qwen-coder/adapter.py -> build/lib/gencode_gov/integrations/models/qwen-coder
creating build/lib/gencode_gov/integrations/models/kimi
copying src/gencode_gov/integrations/models/kimi/__init__.py -> build/lib/gencode_gov/integrations/models/kimi
copying src/gencode_gov/integrations/models/kimi/adapter.py -> build/lib/gencode_gov/integrations/models/kimi
creating build/lib/gencode_gov/integrations/models/gpt
copying src/gencode_gov/integrations/models/gpt/__init__.py -> build/lib/gencode_gov/integrations/models/gpt
copying src/gencode_gov/integrations/models/gpt/adapter.py -> build/lib/gencode_gov/integrations/models/gpt
creating build/lib/gencode_gov/integrations/models/gemini
copying src/gencode_gov/integrations/models/gemini/__init__.py -> build/lib/gencode_gov/integrations/models/gemini
copying src/gencode_gov/integrations/models/gemini/adapter.py -> build/lib/gencode_gov/integrations/models/gemini
creating build/lib/gencode_gov/integrations/models/claude
copying src/gencode_gov/integrations/models/claude/__init__.py -> build/lib/gencode_gov/integrations/models/claude
copying src/gencode_gov/integrations/models/claude/adapter.py -> build/lib/gencode_gov/integrations/models/claude
creating build/lib/gencode_gov/reporting/templates
copying src/gencode_gov/reporting/templates/engineering_quality.py -> build/lib/gencode_gov/reporting/templates
running egg_info
writing src/gencode_gov.egg-info/PKG-INFO
writing dependency_links to src/gencode_gov.egg-info/dependency_links.txt
writing entry points to src/gencode_gov.egg-info/entry_points.txt
writing requirements to src/gencode_gov.egg-info/requires.txt
writing top-level names to src/gencode_gov.egg-info/top_level.txt
reading manifest file 'src/gencode_gov.egg-info/SOURCES.txt'
adding license file 'LICENSE'
writing manifest file 'src/gencode_gov.egg-info/SOURCES.txt'
copying src/gencode_gov/py.typed -> build/lib/gencode_gov
creating build/lib/gencode_gov/resources/agent_pack
copying src/gencode_gov/resources/agent_pack/AGENTS.md -> build/lib/gencode_gov/resources/agent_pack
copying src/gencode_gov/resources/agent_pack/README.md -> build/lib/gencode_gov/resources/agent_pack
copying src/gencode_gov/resources/agent_pack/SECURITY_AGENTS.md -> build/lib/gencode_gov/resources/agent_pack
creating build/lib/gencode_gov/resources/agent_pack/agents/code-reviewer
copying src/gencode_gov/resources/agent_pack/agents/code-reviewer/AGENT.md -> build/lib/gencode_gov/resources/agent_pack/agents/code-reviewer
creating build/lib/gencode_gov/resources/agent_pack/agents/developer
copying src/gencode_gov/resources/agent_pack/agents/developer/AGENT.md -> build/lib/gencode_gov/resources/agent_pack/agents/developer
creating build/lib/gencode_gov/resources/agent_pack/agents/performance-engineer
copying src/gencode_gov/resources/agent_pack/agents/performance-engineer/AGENT.md -> build/lib/gencode_gov/resources/agent_pack/agents/performance-engineer
creating build/lib/gencode_gov/resources/agent_pack/agents/release-manager
copying src/gencode_gov/resources/agent_pack/agents/release-manager/AGENT.md -> build/lib/gencode_gov/resources/agent_pack/agents/release-manager
creating build/lib/gencode_gov/resources/agent_pack/agents/requirements-engineer
copying src/gencode_gov/resources/agent_pack/agents/requirements-engineer/AGENT.md -> build/lib/gencode_gov/resources/agent_pack/agents/requirements-engineer
creating build/lib/gencode_gov/resources/agent_pack/agents/test-engineer
copying src/gencode_gov/resources/agent_pack/agents/test-engineer/AGENT.md -> build/lib/gencode_gov/resources/agent_pack/agents/test-engineer
creating build/lib/gencode_gov/resources/agent_pack/agents/security-engineer
copying src/gencode_gov/resources/agent_pack/agents/security-engineer/AGENT.md -> build/lib/gencode_gov/resources/agent_pack/agents/security-engineer
creating build/lib/gencode_gov/resources/agent_pack/agents/software-architect
copying src/gencode_gov/resources/agent_pack/agents/software-architect/AGENT.md -> build/lib/gencode_gov/resources/agent_pack/agents/software-architect
creating build/lib/gencode_gov/resources/agent_pack/agents/reliability-engineer
copying src/gencode_gov/resources/agent_pack/agents/reliability-engineer/AGENT.md -> build/lib/gencode_gov/resources/agent_pack/agents/reliability-engineer
creating build/lib/gencode_gov/resources/agent_pack/skills/performance-engineering
copying src/gencode_gov/resources/agent_pack/skills/performance-engineering/SKILL.md -> build/lib/gencode_gov/resources/agent_pack/skills/performance-engineering
creating build/lib/gencode_gov/resources/agent_pack/skills/reliability-engineering
copying src/gencode_gov/resources/agent_pack/skills/reliability-engineering/SKILL.md -> build/lib/gencode_gov/resources/agent_pack/skills/reliability-engineering
creating build/lib/gencode_gov/resources/agent_pack/skills/architecture-engineering
copying src/gencode_gov/resources/agent_pack/skills/architecture-engineering/SKILL.md -> build/lib/gencode_gov/resources/agent_pack/skills/architecture-engineering
creating build/lib/gencode_gov/resources/agent_pack/skills/gencode-gov
copying src/gencode_gov/resources/agent_pack/skills/gencode-gov/SKILL.md -> build/lib/gencode_gov/resources/agent_pack/skills/gencode-gov
creating build/lib/gencode_gov/resources/agent_pack/skills/gencode-gov/references
copying src/gencode_gov/resources/agent_pack/skills/gencode-gov/references/ENGINEERING_CHARTER_AND_DOMAINS.md -> build/lib/gencode_gov/resources/agent_pack/skills/gencode-gov/references
copying src/gencode_gov/resources/agent_pack/skills/gencode-gov/references/OPERATIONAL_CONTRACT.md -> build/lib/gencode_gov/resources/agent_pack/skills/gencode-gov/references
copying src/gencode_gov/resources/agent_pack/skills/gencode-gov/references/VERIFICATION_AND_ADOPTION.md -> build/lib/gencode_gov/resources/agent_pack/skills/gencode-gov/references
copying src/gencode_gov/resources/agent_pack/skills/gencode-gov/references/SECURITY_POSTURE.md -> build/lib/gencode_gov/resources/agent_pack/skills/gencode-gov/references
copying src/gencode_gov/resources/agent_pack/skills/gencode-gov/references/README.md -> build/lib/gencode_gov/resources/agent_pack/skills/gencode-gov/references
creating build/lib/gencode_gov/resources/agent_pack/skills/software-testing
copying src/gencode_gov/resources/agent_pack/skills/software-testing/SKILL.md -> build/lib/gencode_gov/resources/agent_pack/skills/software-testing
creating build/lib/gencode_gov/resources/agent_pack/skills/security-audit
copying src/gencode_gov/resources/agent_pack/skills/security-audit/SKILL.md -> build/lib/gencode_gov/resources/agent_pack/skills/security-audit
creating build/lib/gencode_gov/resources/agent_pack/skills/application-security
copying src/gencode_gov/resources/agent_pack/skills/application-security/SKILL.md -> build/lib/gencode_gov/resources/agent_pack/skills/application-security
creating build/lib/gencode_gov/resources/agent_pack/skills/release-readiness
copying src/gencode_gov/resources/agent_pack/skills/release-readiness/SKILL.md -> build/lib/gencode_gov/resources/agent_pack/skills/release-readiness
creating build/lib/gencode_gov/resources/agent_pack/skills/requirements-engineering
copying src/gencode_gov/resources/agent_pack/skills/requirements-engineering/SKILL.md -> build/lib/gencode_gov/resources/agent_pack/skills/requirements-engineering
creating build/lib/gencode_gov/resources/agent_pack/skills/secure-software-engineering
copying src/gencode_gov/resources/agent_pack/skills/secure-software-engineering/SKILL.md -> build/lib/gencode_gov/resources/agent_pack/skills/secure-software-engineering
creating build/lib/gencode_gov/resources/project_templates/schemas
copying src/gencode_gov/resources/project_templates/schemas/project.schema.json -> build/lib/gencode_gov/resources/project_templates/schemas
creating build/lib/gencode_gov/resources/project_templates/projects/desktop-application
copying src/gencode_gov/resources/project_templates/projects/desktop-application/profile.yaml -> build/lib/gencode_gov/resources/project_templates/projects/desktop-application
copying src/gencode_gov/resources/project_templates/projects/desktop-application/rules.yaml -> build/lib/gencode_gov/resources/project_templates/projects/desktop-application
copying src/gencode_gov/resources/project_templates/projects/desktop-application/gates.yaml -> build/lib/gencode_gov/resources/project_templates/projects/desktop-application
creating build/lib/gencode_gov/resources/project_templates/projects/mobile-application
copying src/gencode_gov/resources/project_templates/projects/mobile-application/profile.yaml -> build/lib/gencode_gov/resources/project_templates/projects/mobile-application
copying src/gencode_gov/resources/project_templates/projects/mobile-application/rules.yaml -> build/lib/gencode_gov/resources/project_templates/projects/mobile-application
copying src/gencode_gov/resources/project_templates/projects/mobile-application/gates.yaml -> build/lib/gencode_gov/resources/project_templates/projects/mobile-application
creating build/lib/gencode_gov/resources/project_templates/projects/web-application
copying src/gencode_gov/resources/project_templates/projects/web-application/profile.yaml -> build/lib/gencode_gov/resources/project_templates/projects/web-application
copying src/gencode_gov/resources/project_templates/projects/web-application/rules.yaml -> build/lib/gencode_gov/resources/project_templates/projects/web-application
copying src/gencode_gov/resources/project_templates/projects/web-application/gates.yaml -> build/lib/gencode_gov/resources/project_templates/projects/web-application
creating build/lib/gencode_gov/resources/project_templates/projects/safety-critical
copying src/gencode_gov/resources/project_templates/projects/safety-critical/profile.yaml -> build/lib/gencode_gov/resources/project_templates/projects/safety-critical
copying src/gencode_gov/resources/project_templates/projects/safety-critical/rules.yaml -> build/lib/gencode_gov/resources/project_templates/projects/safety-critical
copying src/gencode_gov/resources/project_templates/projects/safety-critical/gates.yaml -> build/lib/gencode_gov/resources/project_templates/projects/safety-critical
creating build/lib/gencode_gov/resources/project_templates/projects/enterprise
copying src/gencode_gov/resources/project_templates/projects/enterprise/profile.yaml -> build/lib/gencode_gov/resources/project_templates/projects/enterprise
copying src/gencode_gov/resources/project_templates/projects/enterprise/rules.yaml -> build/lib/gencode_gov/resources/project_templates/projects/enterprise
copying src/gencode_gov/resources/project_templates/projects/enterprise/gates.yaml -> build/lib/gencode_gov/resources/project_templates/projects/enterprise
creating build/lib/gencode_gov/resources/project_templates/projects/distributed-system
copying src/gencode_gov/resources/project_templates/projects/distributed-system/profile.yaml -> build/lib/gencode_gov/resources/project_templates/projects/distributed-system
copying src/gencode_gov/resources/project_templates/projects/distributed-system/rules.yaml -> build/lib/gencode_gov/resources/project_templates/projects/distributed-system
copying src/gencode_gov/resources/project_templates/projects/distributed-system/gates.yaml -> build/lib/gencode_gov/resources/project_templates/projects/distributed-system
creating build/lib/gencode_gov/resources/project_templates/projects/api-service
copying src/gencode_gov/resources/project_templates/projects/api-service/profile.yaml -> build/lib/gencode_gov/resources/project_templates/projects/api-service
copying src/gencode_gov/resources/project_templates/projects/api-service/rules.yaml -> build/lib/gencode_gov/resources/project_templates/projects/api-service
copying src/gencode_gov/resources/project_templates/projects/api-service/gates.yaml -> build/lib/gencode_gov/resources/project_templates/projects/api-service
creating build/lib/gencode_gov/resources/project_templates/projects/universal
copying src/gencode_gov/resources/project_templates/projects/universal/profile.yaml -> build/lib/gencode_gov/resources/project_templates/projects/universal
copying src/gencode_gov/resources/project_templates/projects/universal/rules.yaml -> build/lib/gencode_gov/resources/project_templates/projects/universal
copying src/gencode_gov/resources/project_templates/projects/universal/gates.yaml -> build/lib/gencode_gov/resources/project_templates/projects/universal
installing to build/bdist.linux-x86_64/wheel
running install
running install_lib
creating build/bdist.linux-x86_64/wheel
creating build/bdist.linux-x86_64/wheel/gencode_gov
copying build/lib/gencode_gov/__init__.py -> build/bdist.linux-x86_64/wheel/./gencode_gov
creating build/bdist.linux-x86_64/wheel/gencode_gov/language_support
copying build/lib/gencode_gov/language_support/__init__.py -> build/bdist.linux-x86_64/wheel/./gencode_gov/language_support
copying build/lib/gencode_gov/language_support/language_profile_loader.py -> build/bdist.linux-x86_64/wheel/./gencode_gov/language_support
copying build/lib/gencode_gov/language_support/registry.py -> build/bdist.linux-x86_64/wheel/./gencode_gov/language_support
copying build/lib/gencode_gov/language_support/compatibility.py -> build/bdist.linux-x86_64/wheel/./gencode_gov/language_support
copying build/lib/gencode_gov/language_support/detector.py -> build/bdist.linux-x86_64/wheel/./gencode_gov/language_support
copying build/lib/gencode_gov/language_support/tool_resolver.py -> build/bdist.linux-x86_64/wheel/./gencode_gov/language_support
copying build/lib/gencode_gov/validation.py -> build/bdist.linux-x86_64/wheel/./gencode_gov
creating build/bdist.linux-x86_64/wheel/gencode_gov/resources
creating build/bdist.linux-x86_64/wheel/gencode_gov/resources/project_templates
creating build/bdist.linux-x86_64/wheel/gencode_gov/resources/project_templates/schemas
copying build/lib/gencode_gov/resources/project_templates/schemas/project.schema.json -> build/bdist.linux-x86_64/wheel/./gencode_gov/resources/project_templates/schemas
creating build/bdist.linux-x86_64/wheel/gencode_gov/resources/project_templates/projects
creating build/bdist.linux-x86_64/wheel/gencode_gov/resources/project_templates/projects/desktop-application
copying build/lib/gencode_gov/resources/project_templates/projects/desktop-application/profile.yaml -> build/bdist.linux-x86_64/wheel/./gencode_gov/resources/project_templates/projects/desktop-application
copying build/lib/gencode_gov/resources/project_templates/projects/desktop-application/rules.yaml -> build/bdist.linux-x86_64/wheel/./gencode_gov/resources/project_templates/projects/desktop-application
copying build/lib/gencode_gov/resources/project_templates/projects/desktop-application/gates.yaml -> build/bdist.linux-x86_64/wheel/./gencode_gov/resources/project_templates/projects/desktop-application
creating build/bdist.linux-x86_64/wheel/gencode_gov/resources/project_templates/projects/mobile-application
copying build/lib/gencode_gov/resources/project_templates/projects/mobile-application/profile.yaml -> build/bdist.linux-x86_64/wheel/./gencode_gov/resources/project_templates/projects/mobile-application
copying build/lib/gencode_gov/resources/project_templates/projects/mobile-application/rules.yaml -> build/bdist.linux-x86_64/wheel/./gencode_gov/resources/project_templates/projects/mobile-application
copying build/lib/gencode_gov/resources/project_templates/projects/mobile-application/gates.yaml -> build/bdist.linux-x86_64/wheel/./gencode_gov/resources/project_templates/projects/mobile-application
creating build/bdist.linux-x86_64/wheel/gencode_gov/resources/project_templates/projects/web-application
copying build/lib/gencode_gov/resources/project_templates/projects/web-application/profile.yaml -> build/bdist.linux-x86_64/wheel/./gencode_gov/resources/project_templates/projects/web-application
copying build/lib/gencode_gov/resources/project_templates/projects/web-application/rules.yaml -> build/bdist.linux-x86_64/wheel/./gencode_gov/resources/project_templates/projects/web-application
copying build/lib/gencode_gov/resources/project_templates/projects/web-application/gates.yaml -> build/bdist.linux-x86_64/wheel/./gencode_gov/resources/project_templates/projects/web-application
creating build/bdist.linux-x86_64/wheel/gencode_gov/resources/project_templates/projects/safety-critical
copying build/lib/gencode_gov/resources/project_templates/projects/safety-critical/profile.yaml -> build/bdist.linux-x86_64/wheel/./gencode_gov/resources/project_templates/projects/safety-critical
copying build/lib/gencode_gov/resources/project_templates/projects/safety-critical/rules.yaml -> build/bdist.linux-x86_64/wheel/./gencode_gov/resources/project_templates/projects/safety-critical
copying build/lib/gencode_gov/resources/project_templates/projects/safety-critical/gates.yaml -> build/bdist.linux-x86_64/wheel/./gencode_gov/resources/project_templates/projects/safety-critical
creating build/bdist.linux-x86_64/wheel/gencode_gov/resources/project_templates/projects/enterprise
copying build/lib/gencode_gov/resources/project_templates/projects/enterprise/profile.yaml -> build/bdist.linux-x86_64/wheel/./gencode_gov/resources/project_templates/projects/enterprise
copying build/lib/gencode_gov/resources/project_templates/projects/enterprise/rules.yaml -> build/bdist.linux-x86_64/wheel/./gencode_gov/resources/project_templates/projects/enterprise
copying build/lib/gencode_gov/resources/project_templates/projects/enterprise/gates.yaml -> build/bdist.linux-x86_64/wheel/./gencode_gov/resources/project_templates/projects/enterprise
creating build/bdist.linux-x86_64/wheel/gencode_gov/resources/project_templates/projects/distributed-system
copying build/lib/gencode_gov/resources/project_templates/projects/distributed-system/profile.yaml -> build/bdist.linux-x86_64/wheel/./gencode_gov/resources/project_templates/projects/distributed-system
copying build/lib/gencode_gov/resources/project_templates/projects/distributed-system/rules.yaml -> build/bdist.linux-x86_64/wheel/./gencode_gov/resources/project_templates/projects/distributed-system
copying build/lib/gencode_gov/resources/project_templates/projects/distributed-system/gates.yaml -> build/bdist.linux-x86_64/wheel/./gencode_gov/resources/project_templates/projects/distributed-system
creating build/bdist.linux-x86_64/wheel/gencode_gov/resources/project_templates/projects/api-service
copying build/lib/gencode_gov/resources/project_templates/projects/api-service/profile.yaml -> build/bdist.linux-x86_64/wheel/./gencode_gov/resources/project_templates/projects/api-service
copying build/lib/gencode_gov/resources/project_templates/projects/api-service/rules.yaml -> build/bdist.linux-x86_64/wheel/./gencode_gov/resources/project_templates/projects/api-service
copying build/lib/gencode_gov/resources/project_templates/projects/api-service/gates.yaml -> build/bdist.linux-x86_64/wheel/./gencode_gov/resources/project_templates/projects/api-service
creating build/bdist.linux-x86_64/wheel/gencode_gov/resources/project_templates/projects/universal
copying build/lib/gencode_gov/resources/project_templates/projects/universal/profile.yaml -> build/bdist.linux-x86_64/wheel/./gencode_gov/resources/project_templates/projects/universal
copying build/lib/gencode_gov/resources/project_templates/projects/universal/rules.yaml -> build/bdist.linux-x86_64/wheel/./gencode_gov/resources/project_templates/projects/universal
copying build/lib/gencode_gov/resources/project_templates/projects/universal/gates.yaml -> build/bdist.linux-x86_64/wheel/./gencode_gov/resources/project_templates/projects/universal
creating build/bdist.linux-x86_64/wheel/gencode_gov/resources/agent_pack
creating build/bdist.linux-x86_64/wheel/gencode_gov/resources/agent_pack/agents
creating build/bdist.linux-x86_64/wheel/gencode_gov/resources/agent_pack/agents/code-reviewer
copying build/lib/gencode_gov/resources/agent_pack/agents/code-reviewer/AGENT.md -> build/bdist.linux-x86_64/wheel/./gencode_gov/resources/agent_pack/agents/code-reviewer
creating build/bdist.linux-x86_64/wheel/gencode_gov/resources/agent_pack/agents/developer
copying build/lib/gencode_gov/resources/agent_pack/agents/developer/AGENT.md -> build/bdist.linux-x86_64/wheel/./gencode_gov/resources/agent_pack/agents/developer
creating build/bdist.linux-x86_64/wheel/gencode_gov/resources/agent_pack/agents/performance-engineer
copying build/lib/gencode_gov/resources/agent_pack/agents/performance-engineer/AGENT.md -> build/bdist.linux-x86_64/wheel/./gencode_gov/resources/agent_pack/agents/performance-engineer
creating build/bdist.linux-x86_64/wheel/gencode_gov/resources/agent_pack/agents/release-manager
copying build/lib/gencode_gov/resources/agent_pack/agents/release-manager/AGENT.md -> build/bdist.linux-x86_64/wheel/./gencode_gov/resources/agent_pack/agents/release-manager
creating build/bdist.linux-x86_64/wheel/gencode_gov/resources/agent_pack/agents/requirements-engineer
copying build/lib/gencode_gov/resources/agent_pack/agents/requirements-engineer/AGENT.md -> build/bdist.linux-x86_64/wheel/./gencode_gov/resources/agent_pack/agents/requirements-engineer
creating build/bdist.linux-x86_64/wheel/gencode_gov/resources/agent_pack/agents/test-engineer
copying build/lib/gencode_gov/resources/agent_pack/agents/test-engineer/AGENT.md -> build/bdist.linux-x86_64/wheel/./gencode_gov/resources/agent_pack/agents/test-engineer
creating build/bdist.linux-x86_64/wheel/gencode_gov/resources/agent_pack/agents/security-engineer
copying build/lib/gencode_gov/resources/agent_pack/agents/security-engineer/AGENT.md -> build/bdist.linux-x86_64/wheel/./gencode_gov/resources/agent_pack/agents/security-engineer
creating build/bdist.linux-x86_64/wheel/gencode_gov/resources/agent_pack/agents/software-architect
copying build/lib/gencode_gov/resources/agent_pack/agents/software-architect/AGENT.md -> build/bdist.linux-x86_64/wheel/./gencode_gov/resources/agent_pack/agents/software-architect
creating build/bdist.linux-x86_64/wheel/gencode_gov/resources/agent_pack/agents/reliability-engineer
copying build/lib/gencode_gov/resources/agent_pack/agents/reliability-engineer/AGENT.md -> build/bdist.linux-x86_64/wheel/./gencode_gov/resources/agent_pack/agents/reliability-engineer
creating build/bdist.linux-x86_64/wheel/gencode_gov/resources/agent_pack/skills
creating build/bdist.linux-x86_64/wheel/gencode_gov/resources/agent_pack/skills/performance-engineering
copying build/lib/gencode_gov/resources/agent_pack/skills/performance-engineering/SKILL.md -> build/bdist.linux-x86_64/wheel/./gencode_gov/resources/agent_pack/skills/performance-engineering
creating build/bdist.linux-x86_64/wheel/gencode_gov/resources/agent_pack/skills/reliability-engineering
copying build/lib/gencode_gov/resources/agent_pack/skills/reliability-engineering/SKILL.md -> build/bdist.linux-x86_64/wheel/./gencode_gov/resources/agent_pack/skills/reliability-engineering
creating build/bdist.linux-x86_64/wheel/gencode_gov/resources/agent_pack/skills/architecture-engineering
copying build/lib/gencode_gov/resources/agent_pack/skills/architecture-engineering/SKILL.md -> build/bdist.linux-x86_64/wheel/./gencode_gov/resources/agent_pack/skills/architecture-engineering
creating build/bdist.linux-x86_64/wheel/gencode_gov/resources/agent_pack/skills/gencode-gov
creating build/bdist.linux-x86_64/wheel/gencode_gov/resources/agent_pack/skills/gencode-gov/references
copying build/lib/gencode_gov/resources/agent_pack/skills/gencode-gov/references/ENGINEERING_CHARTER_AND_DOMAINS.md -> build/bdist.linux-x86_64/wheel/./gencode_gov/resources/agent_pack/skills/gencode-gov/references
copying build/lib/gencode_gov/resources/agent_pack/skills/gencode-gov/references/OPERATIONAL_CONTRACT.md -> build/bdist.linux-x86_64/wheel/./gencode_gov/resources/agent_pack/skills/gencode-gov/references
copying build/lib/gencode_gov/resources/agent_pack/skills/gencode-gov/references/VERIFICATION_AND_ADOPTION.md -> build/bdist.linux-x86_64/wheel/./gencode_gov/resources/agent_pack/skills/gencode-gov/references
copying build/lib/gencode_gov/resources/agent_pack/skills/gencode-gov/references/SECURITY_POSTURE.md -> build/bdist.linux-x86_64/wheel/./gencode_gov/resources/agent_pack/skills/gencode-gov/references
copying build/lib/gencode_gov/resources/agent_pack/skills/gencode-gov/references/README.md -> build/bdist.linux-x86_64/wheel/./gencode_gov/resources/agent_pack/skills/gencode-gov/references
copying build/lib/gencode_gov/resources/agent_pack/skills/gencode-gov/SKILL.md -> build/bdist.linux-x86_64/wheel/./gencode_gov/resources/agent_pack/skills/gencode-gov
creating build/bdist.linux-x86_64/wheel/gencode_gov/resources/agent_pack/skills/software-testing
copying build/lib/gencode_gov/resources/agent_pack/skills/software-testing/SKILL.md -> build/bdist.linux-x86_64/wheel/./gencode_gov/resources/agent_pack/skills/software-testing
creating build/bdist.linux-x86_64/wheel/gencode_gov/resources/agent_pack/skills/security-audit
copying build/lib/gencode_gov/resources/agent_pack/skills/security-audit/SKILL.md -> build/bdist.linux-x86_64/wheel/./gencode_gov/resources/agent_pack/skills/security-audit
creating build/bdist.linux-x86_64/wheel/gencode_gov/resources/agent_pack/skills/application-security
copying build/lib/gencode_gov/resources/agent_pack/skills/application-security/SKILL.md -> build/bdist.linux-x86_64/wheel/./gencode_gov/resources/agent_pack/skills/application-security
creating build/bdist.linux-x86_64/wheel/gencode_gov/resources/agent_pack/skills/release-readiness
copying build/lib/gencode_gov/resources/agent_pack/skills/release-readiness/SKILL.md -> build/bdist.linux-x86_64/wheel/./gencode_gov/resources/agent_pack/skills/release-readiness
creating build/bdist.linux-x86_64/wheel/gencode_gov/resources/agent_pack/skills/requirements-engineering
copying build/lib/gencode_gov/resources/agent_pack/skills/requirements-engineering/SKILL.md -> build/bdist.linux-x86_64/wheel/./gencode_gov/resources/agent_pack/skills/requirements-engineering
creating build/bdist.linux-x86_64/wheel/gencode_gov/resources/agent_pack/skills/secure-software-engineering
copying build/lib/gencode_gov/resources/agent_pack/skills/secure-software-engineering/SKILL.md -> build/bdist.linux-x86_64/wheel/./gencode_gov/resources/agent_pack/skills/secure-software-engineering
copying build/lib/gencode_gov/resources/agent_pack/AGENTS.md -> build/bdist.linux-x86_64/wheel/./gencode_gov/resources/agent_pack
copying build/lib/gencode_gov/resources/agent_pack/README.md -> build/bdist.linux-x86_64/wheel/./gencode_gov/resources/agent_pack
copying build/lib/gencode_gov/resources/agent_pack/SECURITY_AGENTS.md -> build/bdist.linux-x86_64/wheel/./gencode_gov/resources/agent_pack
creating build/bdist.linux-x86_64/wheel/gencode_gov/assessment
copying build/lib/gencode_gov/assessment/decision.py -> build/bdist.linux-x86_64/wheel/./gencode_gov/assessment
copying build/lib/gencode_gov/assessment/__init__.py -> build/bdist.linux-x86_64/wheel/./gencode_gov/assessment
copying build/lib/gencode_gov/assessment/drift.py -> build/bdist.linux-x86_64/wheel/./gencode_gov/assessment
copying build/lib/gencode_gov/assessment/gates.py -> build/bdist.linux-x86_64/wheel/./gencode_gov/assessment
copying build/lib/gencode_gov/assessment/scorer.py -> build/bdist.linux-x86_64/wheel/./gencode_gov/assessment
creating build/bdist.linux-x86_64/wheel/gencode_gov/security_audit
copying build/lib/gencode_gov/security_audit/__init__.py -> build/bdist.linux-x86_64/wheel/./gencode_gov/security_audit
copying build/lib/gencode_gov/security_audit/reassessment.py -> build/bdist.linux-x86_64/wheel/./gencode_gov/security_audit
copying build/lib/gencode_gov/security_audit/orchestrator.py -> build/bdist.linux-x86_64/wheel/./gencode_gov/security_audit
copying build/lib/gencode_gov/security_audit/coverage.py -> build/bdist.linux-x86_64/wheel/./gencode_gov/security_audit
copying build/lib/gencode_gov/security_audit/sandbox.py -> build/bdist.linux-x86_64/wheel/./gencode_gov/security_audit
copying build/lib/gencode_gov/security_audit/hunting.py -> build/bdist.linux-x86_64/wheel/./gencode_gov/security_audit
copying build/lib/gencode_gov/security_audit/cli_dispatch.py -> build/bdist.linux-x86_64/wheel/./gencode_gov/security_audit
copying build/lib/gencode_gov/security_audit/findings.py -> build/bdist.linux-x86_64/wheel/./gencode_gov/security_audit
copying build/lib/gencode_gov/security_audit/runtime.py -> build/bdist.linux-x86_64/wheel/./gencode_gov/security_audit
copying build/lib/gencode_gov/security_audit/verifier.py -> build/bdist.linux-x86_64/wheel/./gencode_gov/security_audit
copying build/lib/gencode_gov/security_audit/dispatcher.py -> build/bdist.linux-x86_64/wheel/./gencode_gov/security_audit
copying build/lib/gencode_gov/security_audit/reporting.py -> build/bdist.linux-x86_64/wheel/./gencode_gov/security_audit
copying build/lib/gencode_gov/security_audit/validators.py -> build/bdist.linux-x86_64/wheel/./gencode_gov/security_audit
copying build/lib/gencode_gov/security_audit/taxonomy.py -> build/bdist.linux-x86_64/wheel/./gencode_gov/security_audit
copying build/lib/gencode_gov/security_audit/worker_entry.py -> build/bdist.linux-x86_64/wheel/./gencode_gov/security_audit
copying build/lib/gencode_gov/security_audit/governance_bridge.py -> build/bdist.linux-x86_64/wheel/./gencode_gov/security_audit
copying build/lib/gencode_gov/cli.py -> build/bdist.linux-x86_64/wheel/./gencode_gov
creating build/bdist.linux-x86_64/wheel/gencode_gov/verification
copying build/lib/gencode_gov/verification/__init__.py -> build/bdist.linux-x86_64/wheel/./gencode_gov/verification
copying build/lib/gencode_gov/verification/profiles.py -> build/bdist.linux-x86_64/wheel/./gencode_gov/verification
copying build/lib/gencode_gov/verification/engine.py -> build/bdist.linux-x86_64/wheel/./gencode_gov/verification
copying build/lib/gencode_gov/verification/domain_verifiers.py -> build/bdist.linux-x86_64/wheel/./gencode_gov/verification
copying build/lib/gencode_gov/verification/architecture_verifier.py -> build/bdist.linux-x86_64/wheel/./gencode_gov/verification
copying build/lib/gencode_gov/verification/code_and_test_integrity.py -> build/bdist.linux-x86_64/wheel/./gencode_gov/verification
copying build/lib/gencode_gov/verification/assess_dispatch.py -> build/bdist.linux-x86_64/wheel/./gencode_gov/verification
creating build/bdist.linux-x86_64/wheel/gencode_gov/verification/runners
copying build/lib/gencode_gov/verification/runners/__init__.py -> build/bdist.linux-x86_64/wheel/./gencode_gov/verification/runners
copying build/lib/gencode_gov/verification/runners/tsar_runner.py -> build/bdist.linux-x86_64/wheel/./gencode_gov/verification/runners
copying build/lib/gencode_gov/verification/runners/polyglot_quality_runner.py -> build/bdist.linux-x86_64/wheel/./gencode_gov/verification/runners
copying build/lib/gencode_gov/verification/runners/pytest_runner.py -> build/bdist.linux-x86_64/wheel/./gencode_gov/verification/runners
copying build/lib/gencode_gov/verification/runners/supply_chain_runner.py -> build/bdist.linux-x86_64/wheel/./gencode_gov/verification/runners
copying build/lib/gencode_gov/verification/runners/mypy_runner.py -> build/bdist.linux-x86_64/wheel/./gencode_gov/verification/runners
copying build/lib/gencode_gov/verification/runners/base.py -> build/bdist.linux-x86_64/wheel/./gencode_gov/verification/runners
copying build/lib/gencode_gov/verification/runners/test_suite_runner.py -> build/bdist.linux-x86_64/wheel/./gencode_gov/verification/runners
copying build/lib/gencode_gov/verification/runners/ruff_runner.py -> build/bdist.linux-x86_64/wheel/./gencode_gov/verification/runners
copying build/lib/gencode_gov/verification/scenario_verifier.py -> build/bdist.linux-x86_64/wheel/./gencode_gov/verification
copying build/lib/gencode_gov/verification/methods.py -> build/bdist.linux-x86_64/wheel/./gencode_gov/verification
copying build/lib/gencode_gov/verification/diff_governance.py -> build/bdist.linux-x86_64/wheel/./gencode_gov/verification
creating build/bdist.linux-x86_64/wheel/gencode_gov/integrations
copying build/lib/gencode_gov/integrations/__init__.py -> build/bdist.linux-x86_64/wheel/./gencode_gov/integrations
creating build/bdist.linux-x86_64/wheel/gencode_gov/integrations/_model_impl
copying build/lib/gencode_gov/integrations/_model_impl/__init__.py -> build/bdist.linux-x86_64/wheel/./gencode_gov/integrations/_model_impl
creating build/bdist.linux-x86_64/wheel/gencode_gov/integrations/_model_impl/deepseek_coder
copying build/lib/gencode_gov/integrations/_model_impl/deepseek_coder/__init__.py -> build/bdist.linux-x86_64/wheel/./gencode_gov/integrations/_model_impl/deepseek_coder
copying build/lib/gencode_gov/integrations/_model_impl/deepseek_coder/adapter.py -> build/bdist.linux-x86_64/wheel/./gencode_gov/integrations/_model_impl/deepseek_coder
creating build/bdist.linux-x86_64/wheel/gencode_gov/integrations/_model_impl/openai_o
copying build/lib/gencode_gov/integrations/_model_impl/openai_o/__init__.py -> build/bdist.linux-x86_64/wheel/./gencode_gov/integrations/_model_impl/openai_o
copying build/lib/gencode_gov/integrations/_model_impl/openai_o/adapter.py -> build/bdist.linux-x86_64/wheel/./gencode_gov/integrations/_model_impl/openai_o
creating build/bdist.linux-x86_64/wheel/gencode_gov/integrations/_model_impl/qwen_coder
copying build/lib/gencode_gov/integrations/_model_impl/qwen_coder/__init__.py -> build/bdist.linux-x86_64/wheel/./gencode_gov/integrations/_model_impl/qwen_coder
copying build/lib/gencode_gov/integrations/_model_impl/qwen_coder/adapter.py -> build/bdist.linux-x86_64/wheel/./gencode_gov/integrations/_model_impl/qwen_coder
creating build/bdist.linux-x86_64/wheel/gencode_gov/integrations/_model_impl/code_llama
copying build/lib/gencode_gov/integrations/_model_impl/code_llama/__init__.py -> build/bdist.linux-x86_64/wheel/./gencode_gov/integrations/_model_impl/code_llama
copying build/lib/gencode_gov/integrations/_model_impl/code_llama/adapter.py -> build/bdist.linux-x86_64/wheel/./gencode_gov/integrations/_model_impl/code_llama
creating build/bdist.linux-x86_64/wheel/gencode_gov/integrations/agents
copying build/lib/gencode_gov/integrations/agents/__init__.py -> build/bdist.linux-x86_64/wheel/./gencode_gov/integrations/agents
copying build/lib/gencode_gov/integrations/agents/windsurf.py -> build/bdist.linux-x86_64/wheel/./gencode_gov/integrations/agents
copying build/lib/gencode_gov/integrations/agents/amazon_q.py -> build/bdist.linux-x86_64/wheel/./gencode_gov/integrations/agents
copying build/lib/gencode_gov/integrations/agents/gemini_cli.py -> build/bdist.linux-x86_64/wheel/./gencode_gov/integrations/agents
copying build/lib/gencode_gov/integrations/agents/cursor.py -> build/bdist.linux-x86_64/wheel/./gencode_gov/integrations/agents
copying build/lib/gencode_gov/integrations/agents/github_copilot.py -> build/bdist.linux-x86_64/wheel/./gencode_gov/integrations/agents
copying build/lib/gencode_gov/integrations/agents/gemini.py -> build/bdist.linux-x86_64/wheel/./gencode_gov/integrations/agents
copying build/lib/gencode_gov/integrations/agents/replit_agent.py -> build/bdist.linux-x86_64/wheel/./gencode_gov/integrations/agents
copying build/lib/gencode_gov/integrations/agents/cline.py -> build/bdist.linux-x86_64/wheel/./gencode_gov/integrations/agents
copying build/lib/gencode_gov/integrations/agents/claude_code.py -> build/bdist.linux-x86_64/wheel/./gencode_gov/integrations/agents
copying build/lib/gencode_gov/integrations/agents/devin.py -> build/bdist.linux-x86_64/wheel/./gencode_gov/integrations/agents
copying build/lib/gencode_gov/integrations/agents/gpt.py -> build/bdist.linux-x86_64/wheel/./gencode_gov/integrations/agents
copying build/lib/gencode_gov/integrations/agents/continue_agent.py -> build/bdist.linux-x86_64/wheel/./gencode_gov/integrations/agents
copying build/lib/gencode_gov/integrations/agents/tabnine.py -> build/bdist.linux-x86_64/wheel/./gencode_gov/integrations/agents
copying build/lib/gencode_gov/integrations/agents/jetbrains_ai.py -> build/bdist.linux-x86_64/wheel/./gencode_gov/integrations/agents
copying build/lib/gencode_gov/integrations/agents/codex_openai.py -> build/bdist.linux-x86_64/wheel/./gencode_gov/integrations/agents
copying build/lib/gencode_gov/integrations/agents/sourcegraph_cody.py -> build/bdist.linux-x86_64/wheel/./gencode_gov/integrations/agents
copying build/lib/gencode_gov/integrations/agents/aider.py -> build/bdist.linux-x86_64/wheel/./gencode_gov/integrations/agents
creating build/bdist.linux-x86_64/wheel/gencode_gov/integrations/platforms
copying build/lib/gencode_gov/integrations/platforms/__init__.py -> build/bdist.linux-x86_64/wheel/./gencode_gov/integrations/platforms
creating build/bdist.linux-x86_64/wheel/gencode_gov/integrations/platforms/github_copilot
copying build/lib/gencode_gov/integrations/platforms/github_copilot/__init__.py -> build/bdist.linux-x86_64/wheel/./gencode_gov/integrations/platforms/github_copilot
copying build/lib/gencode_gov/integrations/platforms/github_copilot/adapter.py -> build/bdist.linux-x86_64/wheel/./gencode_gov/integrations/platforms/github_copilot
creating build/bdist.linux-x86_64/wheel/gencode_gov/integrations/models
copying build/lib/gencode_gov/integrations/models/__init__.py -> build/bdist.linux-x86_64/wheel/./gencode_gov/integrations/models
creating build/bdist.linux-x86_64/wheel/gencode_gov/integrations/models/openai-o
copying build/lib/gencode_gov/integrations/models/openai-o/__init__.py -> build/bdist.linux-x86_64/wheel/./gencode_gov/integrations/models/openai-o
copying build/lib/gencode_gov/integrations/models/openai-o/adapter.py -> build/bdist.linux-x86_64/wheel/./gencode_gov/integrations/models/openai-o
creating build/bdist.linux-x86_64/wheel/gencode_gov/integrations/models/code-llama
copying build/lib/gencode_gov/integrations/models/code-llama/__init__.py -> build/bdist.linux-x86_64/wheel/./gencode_gov/integrations/models/code-llama
copying build/lib/gencode_gov/integrations/models/code-llama/adapter.py -> build/bdist.linux-x86_64/wheel/./gencode_gov/integrations/models/code-llama
creating build/bdist.linux-x86_64/wheel/gencode_gov/integrations/models/deepseek-coder
copying build/lib/gencode_gov/integrations/models/deepseek-coder/__init__.py -> build/bdist.linux-x86_64/wheel/./gencode_gov/integrations/models/deepseek-coder
copying build/lib/gencode_gov/integrations/models/deepseek-coder/adapter.py -> build/bdist.linux-x86_64/wheel/./gencode_gov/integrations/models/deepseek-coder
copying build/lib/gencode_gov/integrations/models/_openai_compatible.py -> build/bdist.linux-x86_64/wheel/./gencode_gov/integrations/models
creating build/bdist.linux-x86_64/wheel/gencode_gov/integrations/models/qwen-coder
copying build/lib/gencode_gov/integrations/models/qwen-coder/__init__.py -> build/bdist.linux-x86_64/wheel/./gencode_gov/integrations/models/qwen-coder
copying build/lib/gencode_gov/integrations/models/qwen-coder/adapter.py -> build/bdist.linux-x86_64/wheel/./gencode_gov/integrations/models/qwen-coder
creating build/bdist.linux-x86_64/wheel/gencode_gov/integrations/models/kimi
copying build/lib/gencode_gov/integrations/models/kimi/__init__.py -> build/bdist.linux-x86_64/wheel/./gencode_gov/integrations/models/kimi
copying build/lib/gencode_gov/integrations/models/kimi/adapter.py -> build/bdist.linux-x86_64/wheel/./gencode_gov/integrations/models/kimi
creating build/bdist.linux-x86_64/wheel/gencode_gov/integrations/models/gpt
copying build/lib/gencode_gov/integrations/models/gpt/__init__.py -> build/bdist.linux-x86_64/wheel/./gencode_gov/integrations/models/gpt
copying build/lib/gencode_gov/integrations/models/gpt/adapter.py -> build/bdist.linux-x86_64/wheel/./gencode_gov/integrations/models/gpt
creating build/bdist.linux-x86_64/wheel/gencode_gov/integrations/models/gemini
copying build/lib/gencode_gov/integrations/models/gemini/__init__.py -> build/bdist.linux-x86_64/wheel/./gencode_gov/integrations/models/gemini
copying build/lib/gencode_gov/integrations/models/gemini/adapter.py -> build/bdist.linux-x86_64/wheel/./gencode_gov/integrations/models/gemini
creating build/bdist.linux-x86_64/wheel/gencode_gov/integrations/models/claude
copying build/lib/gencode_gov/integrations/models/claude/__init__.py -> build/bdist.linux-x86_64/wheel/./gencode_gov/integrations/models/claude
copying build/lib/gencode_gov/integrations/models/claude/adapter.py -> build/bdist.linux-x86_64/wheel/./gencode_gov/integrations/models/claude
creating build/bdist.linux-x86_64/wheel/gencode_gov/integrations/generic_agents
copying build/lib/gencode_gov/integrations/generic_agents/__init__.py -> build/bdist.linux-x86_64/wheel/./gencode_gov/integrations/generic_agents
copying build/lib/gencode_gov/integrations/generic_agents/adapter.py -> build/bdist.linux-x86_64/wheel/./gencode_gov/integrations/generic_agents
creating build/bdist.linux-x86_64/wheel/gencode_gov/integrations/tsar
copying build/lib/gencode_gov/integrations/tsar/__init__.py -> build/bdist.linux-x86_64/wheel/./gencode_gov/integrations/tsar
copying build/lib/gencode_gov/integrations/tsar/adapter.py -> build/bdist.linux-x86_64/wheel/./gencode_gov/integrations/tsar
copying build/lib/gencode_gov/integrations/tsar/verifier.py -> build/bdist.linux-x86_64/wheel/./gencode_gov/integrations/tsar
copying build/lib/gencode_gov/integrations/base.py -> build/bdist.linux-x86_64/wheel/./gencode_gov/integrations
creating build/bdist.linux-x86_64/wheel/gencode_gov/policies
copying build/lib/gencode_gov/policies/__init__.py -> build/bdist.linux-x86_64/wheel/./gencode_gov/policies
copying build/lib/gencode_gov/policies/advisory.py -> build/bdist.linux-x86_64/wheel/./gencode_gov/policies
copying build/lib/gencode_gov/policies/blocking.py -> build/bdist.linux-x86_64/wheel/./gencode_gov/policies
copying build/lib/gencode_gov/policies/exceptions.py -> build/bdist.linux-x86_64/wheel/./gencode_gov/policies
copying build/lib/gencode_gov/cli_extensions.py -> build/bdist.linux-x86_64/wheel/./gencode_gov
creating build/bdist.linux-x86_64/wheel/gencode_gov/orchestrator
copying build/lib/gencode_gov/orchestrator/stage_manager.py -> build/bdist.linux-x86_64/wheel/./gencode_gov/orchestrator
copying build/lib/gencode_gov/orchestrator/__init__.py -> build/bdist.linux-x86_64/wheel/./gencode_gov/orchestrator
copying build/lib/gencode_gov/orchestrator/task_dispatcher.py -> build/bdist.linux-x86_64/wheel/./gencode_gov/orchestrator
copying build/lib/gencode_gov/orchestrator/lifecycle.py -> build/bdist.linux-x86_64/wheel/./gencode_gov/orchestrator
creating build/bdist.linux-x86_64/wheel/gencode_gov/rules
copying build/lib/gencode_gov/rules/__init__.py -> build/bdist.linux-x86_64/wheel/./gencode_gov/rules
copying build/lib/gencode_gov/rules/registry.py -> build/bdist.linux-x86_64/wheel/./gencode_gov/rules
copying build/lib/gencode_gov/rules/validator.py -> build/bdist.linux-x86_64/wheel/./gencode_gov/rules
copying build/lib/gencode_gov/rules/loader.py -> build/bdist.linux-x86_64/wheel/./gencode_gov/rules
copying build/lib/gencode_gov/rules/evaluator.py -> build/bdist.linux-x86_64/wheel/./gencode_gov/rules
creating build/bdist.linux-x86_64/wheel/gencode_gov/projects
copying build/lib/gencode_gov/projects/__init__.py -> build/bdist.linux-x86_64/wheel/./gencode_gov/projects
copying build/lib/gencode_gov/projects/loader.py -> build/bdist.linux-x86_64/wheel/./gencode_gov/projects
copying build/lib/gencode_gov/projects/matcher.py -> build/bdist.linux-x86_64/wheel/./gencode_gov/projects
creating build/bdist.linux-x86_64/wheel/gencode_gov/evidence
copying build/lib/gencode_gov/evidence/__init__.py -> build/bdist.linux-x86_64/wheel/./gencode_gov/evidence
copying build/lib/gencode_gov/evidence/collector.py -> build/bdist.linux-x86_64/wheel/./gencode_gov/evidence
copying build/lib/gencode_gov/evidence/attestation.py -> build/bdist.linux-x86_64/wheel/./gencode_gov/evidence
copying build/lib/gencode_gov/evidence/supply_chain.py -> build/bdist.linux-x86_64/wheel/./gencode_gov/evidence
copying build/lib/gencode_gov/evidence/store.py -> build/bdist.linux-x86_64/wheel/./gencode_gov/evidence
copying build/lib/gencode_gov/evidence/integrity.py -> build/bdist.linux-x86_64/wheel/./gencode_gov/evidence
creating build/bdist.linux-x86_64/wheel/gencode_gov/governance
copying build/lib/gencode_gov/governance/__init__.py -> build/bdist.linux-x86_64/wheel/./gencode_gov/governance
copying build/lib/gencode_gov/governance/charter_loader.py -> build/bdist.linux-x86_64/wheel/./gencode_gov/governance
copying build/lib/gencode_gov/governance/enforcement.py -> build/bdist.linux-x86_64/wheel/./gencode_gov/governance
copying build/lib/gencode_gov/governance/policy_loader.py -> build/bdist.linux-x86_64/wheel/./gencode_gov/governance
creating build/bdist.linux-x86_64/wheel/gencode_gov/reporting
copying build/lib/gencode_gov/reporting/__init__.py -> build/bdist.linux-x86_64/wheel/./gencode_gov/reporting
copying build/lib/gencode_gov/reporting/json_reporter.py -> build/bdist.linux-x86_64/wheel/./gencode_gov/reporting
creating build/bdist.linux-x86_64/wheel/gencode_gov/reporting/templates
copying build/lib/gencode_gov/reporting/templates/engineering_quality.py -> build/bdist.linux-x86_64/wheel/./gencode_gov/reporting/templates
copying build/lib/gencode_gov/reporting/sarif_reporter.py -> build/bdist.linux-x86_64/wheel/./gencode_gov/reporting
copying build/lib/gencode_gov/reporting/markdown_reporter.py -> build/bdist.linux-x86_64/wheel/./gencode_gov/reporting
copying build/lib/gencode_gov/reporting/html_reporter.py -> build/bdist.linux-x86_64/wheel/./gencode_gov/reporting
copying build/lib/gencode_gov/py.typed -> build/bdist.linux-x86_64/wheel/./gencode_gov
copying build/lib/gencode_gov/config.py -> build/bdist.linux-x86_64/wheel/./gencode_gov
creating build/bdist.linux-x86_64/wheel/gencode_gov/core
copying build/lib/gencode_gov/core/constants.py -> build/bdist.linux-x86_64/wheel/./gencode_gov/core
copying build/lib/gencode_gov/core/__init__.py -> build/bdist.linux-x86_64/wheel/./gencode_gov/core
copying build/lib/gencode_gov/core/logging.py -> build/bdist.linux-x86_64/wheel/./gencode_gov/core
copying build/lib/gencode_gov/core/errors.py -> build/bdist.linux-x86_64/wheel/./gencode_gov/core
running install_egg_info
Copying src/gencode_gov.egg-info to build/bdist.linux-x86_64/wheel/./gencode_gov-0.1.0-py3.12.egg-info
running install_scripts
creating build/bdist.linux-x86_64/wheel/gencode_gov-0.1.0.dist-info/WHEEL
creating '/tmp/dist_wheel/.tmp-vct87qbb/gencode_gov-0.1.0-py3-none-any.whl' and adding 'build/bdist.linux-x86_64/wheel' to it
adding 'gencode_gov/__init__.py'
adding 'gencode_gov/cli.py'
adding 'gencode_gov/cli_extensions.py'
adding 'gencode_gov/config.py'
adding 'gencode_gov/py.typed'
adding 'gencode_gov/validation.py'
adding 'gencode_gov/assessment/__init__.py'
adding 'gencode_gov/assessment/decision.py'
adding 'gencode_gov/assessment/drift.py'
adding 'gencode_gov/assessment/gates.py'
adding 'gencode_gov/assessment/scorer.py'
adding 'gencode_gov/core/__init__.py'
adding 'gencode_gov/core/constants.py'
adding 'gencode_gov/core/errors.py'
adding 'gencode_gov/core/logging.py'
adding 'gencode_gov/evidence/__init__.py'
adding 'gencode_gov/evidence/attestation.py'
adding 'gencode_gov/evidence/collector.py'
adding 'gencode_gov/evidence/integrity.py'
adding 'gencode_gov/evidence/store.py'
adding 'gencode_gov/evidence/supply_chain.py'
adding 'gencode_gov/governance/__init__.py'
adding 'gencode_gov/governance/charter_loader.py'
adding 'gencode_gov/governance/enforcement.py'
adding 'gencode_gov/governance/policy_loader.py'
adding 'gencode_gov/integrations/__init__.py'
adding 'gencode_gov/integrations/base.py'
adding 'gencode_gov/integrations/_model_impl/__init__.py'
adding 'gencode_gov/integrations/_model_impl/code_llama/__init__.py'
adding 'gencode_gov/integrations/_model_impl/code_llama/adapter.py'
adding 'gencode_gov/integrations/_model_impl/deepseek_coder/__init__.py'
adding 'gencode_gov/integrations/_model_impl/deepseek_coder/adapter.py'
adding 'gencode_gov/integrations/_model_impl/openai_o/__init__.py'
adding 'gencode_gov/integrations/_model_impl/openai_o/adapter.py'
adding 'gencode_gov/integrations/_model_impl/qwen_coder/__init__.py'
adding 'gencode_gov/integrations/_model_impl/qwen_coder/adapter.py'
adding 'gencode_gov/integrations/agents/__init__.py'
adding 'gencode_gov/integrations/agents/aider.py'
adding 'gencode_gov/integrations/agents/amazon_q.py'
adding 'gencode_gov/integrations/agents/claude_code.py'
adding 'gencode_gov/integrations/agents/cline.py'
adding 'gencode_gov/integrations/agents/codex_openai.py'
adding 'gencode_gov/integrations/agents/continue_agent.py'
adding 'gencode_gov/integrations/agents/cursor.py'
adding 'gencode_gov/integrations/agents/devin.py'
adding 'gencode_gov/integrations/agents/gemini.py'
adding 'gencode_gov/integrations/agents/gemini_cli.py'
adding 'gencode_gov/integrations/agents/github_copilot.py'
adding 'gencode_gov/integrations/agents/gpt.py'
adding 'gencode_gov/integrations/agents/jetbrains_ai.py'
adding 'gencode_gov/integrations/agents/replit_agent.py'
adding 'gencode_gov/integrations/agents/sourcegraph_cody.py'
adding 'gencode_gov/integrations/agents/tabnine.py'
adding 'gencode_gov/integrations/agents/windsurf.py'
adding 'gencode_gov/integrations/generic_agents/__init__.py'
adding 'gencode_gov/integrations/generic_agents/adapter.py'
adding 'gencode_gov/integrations/models/__init__.py'
adding 'gencode_gov/integrations/models/_openai_compatible.py'
adding 'gencode_gov/integrations/models/claude/__init__.py'
adding 'gencode_gov/integrations/models/claude/adapter.py'
adding 'gencode_gov/integrations/models/code-llama/__init__.py'
adding 'gencode_gov/integrations/models/code-llama/adapter.py'
adding 'gencode_gov/integrations/models/deepseek-coder/__init__.py'
adding 'gencode_gov/integrations/models/deepseek-coder/adapter.py'
adding 'gencode_gov/integrations/models/gemini/__init__.py'
adding 'gencode_gov/integrations/models/gemini/adapter.py'
adding 'gencode_gov/integrations/models/gpt/__init__.py'
adding 'gencode_gov/integrations/models/gpt/adapter.py'
adding 'gencode_gov/integrations/models/kimi/__init__.py'
adding 'gencode_gov/integrations/models/kimi/adapter.py'
adding 'gencode_gov/integrations/models/openai-o/__init__.py'
adding 'gencode_gov/integrations/models/openai-o/adapter.py'
adding 'gencode_gov/integrations/models/qwen-coder/__init__.py'
adding 'gencode_gov/integrations/models/qwen-coder/adapter.py'
adding 'gencode_gov/integrations/platforms/__init__.py'
adding 'gencode_gov/integrations/platforms/github_copilot/__init__.py'
adding 'gencode_gov/integrations/platforms/github_copilot/adapter.py'
adding 'gencode_gov/integrations/tsar/__init__.py'
adding 'gencode_gov/integrations/tsar/adapter.py'
adding 'gencode_gov/integrations/tsar/verifier.py'
adding 'gencode_gov/language_support/__init__.py'
adding 'gencode_gov/language_support/compatibility.py'
adding 'gencode_gov/language_support/detector.py'
adding 'gencode_gov/language_support/language_profile_loader.py'
adding 'gencode_gov/language_support/registry.py'
adding 'gencode_gov/language_support/tool_resolver.py'
adding 'gencode_gov/orchestrator/__init__.py'
adding 'gencode_gov/orchestrator/lifecycle.py'
adding 'gencode_gov/orchestrator/stage_manager.py'
adding 'gencode_gov/orchestrator/task_dispatcher.py'
adding 'gencode_gov/policies/__init__.py'
adding 'gencode_gov/policies/advisory.py'
adding 'gencode_gov/policies/blocking.py'
adding 'gencode_gov/policies/exceptions.py'
adding 'gencode_gov/projects/__init__.py'
adding 'gencode_gov/projects/loader.py'
adding 'gencode_gov/projects/matcher.py'
adding 'gencode_gov/reporting/__init__.py'
adding 'gencode_gov/reporting/html_reporter.py'
adding 'gencode_gov/reporting/json_reporter.py'
adding 'gencode_gov/reporting/markdown_reporter.py'
adding 'gencode_gov/reporting/sarif_reporter.py'
adding 'gencode_gov/reporting/templates/engineering_quality.py'
adding 'gencode_gov/resources/agent_pack/AGENTS.md'
adding 'gencode_gov/resources/agent_pack/README.md'
adding 'gencode_gov/resources/agent_pack/SECURITY_AGENTS.md'
adding 'gencode_gov/resources/agent_pack/agents/code-reviewer/AGENT.md'
adding 'gencode_gov/resources/agent_pack/agents/developer/AGENT.md'
adding 'gencode_gov/resources/agent_pack/agents/performance-engineer/AGENT.md'
adding 'gencode_gov/resources/agent_pack/agents/release-manager/AGENT.md'
adding 'gencode_gov/resources/agent_pack/agents/reliability-engineer/AGENT.md'
adding 'gencode_gov/resources/agent_pack/agents/requirements-engineer/AGENT.md'
adding 'gencode_gov/resources/agent_pack/agents/security-engineer/AGENT.md'
adding 'gencode_gov/resources/agent_pack/agents/software-architect/AGENT.md'
adding 'gencode_gov/resources/agent_pack/agents/test-engineer/AGENT.md'
adding 'gencode_gov/resources/agent_pack/skills/application-security/SKILL.md'
adding 'gencode_gov/resources/agent_pack/skills/architecture-engineering/SKILL.md'
adding 'gencode_gov/resources/agent_pack/skills/gencode-gov/SKILL.md'
adding 'gencode_gov/resources/agent_pack/skills/gencode-gov/references/ENGINEERING_CHARTER_AND_DOMAINS.md'
adding 'gencode_gov/resources/agent_pack/skills/gencode-gov/references/OPERATIONAL_CONTRACT.md'
adding 'gencode_gov/resources/agent_pack/skills/gencode-gov/references/README.md'
adding 'gencode_gov/resources/agent_pack/skills/gencode-gov/references/SECURITY_POSTURE.md'
adding 'gencode_gov/resources/agent_pack/skills/gencode-gov/references/VERIFICATION_AND_ADOPTION.md'
adding 'gencode_gov/resources/agent_pack/skills/performance-engineering/SKILL.md'
adding 'gencode_gov/resources/agent_pack/skills/release-readiness/SKILL.md'
adding 'gencode_gov/resources/agent_pack/skills/reliability-engineering/SKILL.md'
adding 'gencode_gov/resources/agent_pack/skills/requirements-engineering/SKILL.md'
adding 'gencode_gov/resources/agent_pack/skills/secure-software-engineering/SKILL.md'
adding 'gencode_gov/resources/agent_pack/skills/security-audit/SKILL.md'
adding 'gencode_gov/resources/agent_pack/skills/software-testing/SKILL.md'
adding 'gencode_gov/resources/project_templates/projects/api-service/gates.yaml'
adding 'gencode_gov/resources/project_templates/projects/api-service/profile.yaml'
adding 'gencode_gov/resources/project_templates/projects/api-service/rules.yaml'
adding 'gencode_gov/resources/project_templates/projects/desktop-application/gates.yaml'
adding 'gencode_gov/resources/project_templates/projects/desktop-application/profile.yaml'
adding 'gencode_gov/resources/project_templates/projects/desktop-application/rules.yaml'
adding 'gencode_gov/resources/project_templates/projects/distributed-system/gates.yaml'
adding 'gencode_gov/resources/project_templates/projects/distributed-system/profile.yaml'
adding 'gencode_gov/resources/project_templates/projects/distributed-system/rules.yaml'
adding 'gencode_gov/resources/project_templates/projects/enterprise/gates.yaml'
adding 'gencode_gov/resources/project_templates/projects/enterprise/profile.yaml'
adding 'gencode_gov/resources/project_templates/projects/enterprise/rules.yaml'
adding 'gencode_gov/resources/project_templates/projects/mobile-application/gates.yaml'
adding 'gencode_gov/resources/project_templates/projects/mobile-application/profile.yaml'
adding 'gencode_gov/resources/project_templates/projects/mobile-application/rules.yaml'
adding 'gencode_gov/resources/project_templates/projects/safety-critical/gates.yaml'
adding 'gencode_gov/resources/project_templates/projects/safety-critical/profile.yaml'
adding 'gencode_gov/resources/project_templates/projects/safety-critical/rules.yaml'
adding 'gencode_gov/resources/project_templates/projects/universal/gates.yaml'
adding 'gencode_gov/resources/project_templates/projects/universal/profile.yaml'
adding 'gencode_gov/resources/project_templates/projects/universal/rules.yaml'
adding 'gencode_gov/resources/project_templates/projects/web-application/gates.yaml'
adding 'gencode_gov/resources/project_templates/projects/web-application/profile.yaml'
adding 'gencode_gov/resources/project_templates/projects/web-application/rules.yaml'
adding 'gencode_gov/resources/project_templates/schemas/project.schema.json'
adding 'gencode_gov/rules/__init__.py'
adding 'gencode_gov/rules/evaluator.py'
adding 'gencode_gov/rules/loader.py'
adding 'gencode_gov/rules/registry.py'
adding 'gencode_gov/rules/validator.py'
adding 'gencode_gov/security_audit/__init__.py'
adding 'gencode_gov/security_audit/cli_dispatch.py'
adding 'gencode_gov/security_audit/coverage.py'
adding 'gencode_gov/security_audit/dispatcher.py'
adding 'gencode_gov/security_audit/findings.py'
adding 'gencode_gov/security_audit/governance_bridge.py'
adding 'gencode_gov/security_audit/hunting.py'
adding 'gencode_gov/security_audit/orchestrator.py'
adding 'gencode_gov/security_audit/reassessment.py'
adding 'gencode_gov/security_audit/reporting.py'
adding 'gencode_gov/security_audit/runtime.py'
adding 'gencode_gov/security_audit/sandbox.py'
adding 'gencode_gov/security_audit/taxonomy.py'
adding 'gencode_gov/security_audit/validators.py'
adding 'gencode_gov/security_audit/verifier.py'
adding 'gencode_gov/security_audit/worker_entry.py'
adding 'gencode_gov/verification/__init__.py'
adding 'gencode_gov/verification/architecture_verifier.py'
adding 'gencode_gov/verification/assess_dispatch.py'
adding 'gencode_gov/verification/code_and_test_integrity.py'
adding 'gencode_gov/verification/diff_governance.py'
adding 'gencode_gov/verification/domain_verifiers.py'
adding 'gencode_gov/verification/engine.py'
adding 'gencode_gov/verification/methods.py'
adding 'gencode_gov/verification/profiles.py'
adding 'gencode_gov/verification/scenario_verifier.py'
adding 'gencode_gov/verification/runners/__init__.py'
adding 'gencode_gov/verification/runners/base.py'
adding 'gencode_gov/verification/runners/mypy_runner.py'
adding 'gencode_gov/verification/runners/polyglot_quality_runner.py'
adding 'gencode_gov/verification/runners/pytest_runner.py'
adding 'gencode_gov/verification/runners/ruff_runner.py'
adding 'gencode_gov/verification/runners/supply_chain_runner.py'
adding 'gencode_gov/verification/runners/test_suite_runner.py'
adding 'gencode_gov/verification/runners/tsar_runner.py'
adding 'gencode_gov-0.1.0.dist-info/licenses/LICENSE'
adding 'gencode_gov-0.1.0.dist-info/METADATA'
adding 'gencode_gov-0.1.0.dist-info/WHEEL'
adding 'gencode_gov-0.1.0.dist-info/entry_points.txt'
adding 'gencode_gov-0.1.0.dist-info/top_level.txt'
adding 'gencode_gov-0.1.0.dist-info/RECORD'
removing build/bdist.linux-x86_64/wheel
WARNING `project.license` as a TOML table is deprecated
!!

        ********************************************************************************
        Please use a simple string containing a SPDX expression for `project.license`. You can also use `project.license-files`. (Both options available on setuptools>=77.0.0).

        By 2027-Feb-18, you need to update your project and remove deprecated calls
        or your builds will no longer be supported.

        See https://packaging.python.org/en/latest/guides/writing-pyproject-toml/#license for details.
        ********************************************************************************

!!
WARNING License classifiers are deprecated.
!!

        ********************************************************************************
        Please consider removing the following classifiers in favor of a SPDX license expression:

        License :: OSI Approved :: MIT License

        See https://packaging.python.org/en/latest/guides/writing-pyproject-toml/#license for details.
        ********************************************************************************

!!
WARNING License classifiers are deprecated.
!!

        ********************************************************************************
        Please consider removing the following classifiers in favor of a SPDX license expression:

        License :: OSI Approved :: MIT License

        See https://packaging.python.org/en/latest/guides/writing-pyproject-toml/#license for details.
        ********************************************************************************

!!
Successfully built gencode_gov-0.1.0-py3-none-any.whl

[notice] A new release of pip is available: 25.0.1 -> 26.3
[notice] To update, run: python3.12 -m pip install --upgrade pip
{
  "name": "GENCODE-GOV",
  "identifier": "gencode-gov",
  "package": "gencode_gov",
  "version": "0.1.0"
}
TSAR binary not found: tsar
GENCODE-GOV doctor — FAILED
  [FAIL] missing required file: VERSION
  [FAIL] missing required file: manifest/index.yaml
  [FAIL] missing required file: README.md
  [FAIL] missing required file: AGENTS.md
  [FAIL] manifest load failed: manifest file missing: /tmp/wheel_venv/lib/python3.12/manifest/index.yaml
  [WARN] TSAR is not available; security verification remains BLOCKED until configured
[EXIT 1]
```

## 17b. Cross-Python Wheel & Test Compatibility (Python 3.11 & 3.13)
```text
=== Verifying on Python 3.11.18 ===

[notice] A new release of pip is available: 24.0 -> 26.3
[notice] To update, run: python3.11 -m pip install --upgrade pip
GENCODE-GOV 0.1.0
usage: gencode-gov [-h]
                   {version,doctor,validate,inspect,audit,assess,install,project,status,exceptions,report,verify,attest,diff-check,drift}
                   ...
gencode-gov: error: unrecognized arguments: .
[EXIT 1]
```

## 18. Agent Skills Discovery (npx skills)
```text

[38;5;250m███████╗██╗  ██╗██╗██╗     ██╗     ███████╗[0m
[38;5;248m██╔════╝██║ ██╔╝██║██║     ██║     ██╔════╝[0m
[38;5;245m███████╗█████╔╝ ██║██║     ██║     ███████╗[0m
[38;5;243m╚════██║██╔═██╗ ██║██║     ██║     ╚════██║[0m
[38;5;240m███████║██║  ██╗██║███████╗███████╗███████║[0m
[38;5;238m╚══════╝╚═╝  ╚═╝╚═╝╚══════╝╚══════╝╚══════╝[0m

┌  [46m[30m skills [39m[49m
│
│  [2mTip: use the --yes (-y) and --global (-g) flags to install without prompts.[22m
[?25l│
◇  Source: /home/runner/work/GENCODE-GOV/GENCODE-GOV
[?25h[?25l│
◇  Local path validated
[?25h[?25l│
◇  Found [32m10[39m skills
[?25h
│
◇  [1mAvailable Skills[22m
│
│    [36mapplication-security[39m
│
│      [2mThreat-model, implement, test, and verify application security controls for AI-generated software using GENCODE-GOV's security rules and evidence requirements.[22m
│
│    [36marchitecture-engineering[39m
│
│      [2mDesign software architecture, document decisions, and produce a threat model. Ensures the architecture satisfies requirements and is defensible.[22m
│
│    [36mgencode-gov[39m
│
│      [2mEnforce GENCODE-GOV software engineering governance, fail-closed verification, security assurance, and evidence-backed reporting on AI-generated or agent-modified code, applications, and systems. Automatically consult and apply whenever planning, designing, implementing, refactoring, reviewing, testing, auditing security, verifying, or releasing software.[22m
│
│    [36mperformance-engineering[39m
│
│      [2mDefine performance budgets, run benchmarks, monitor runtime latency percentiles, and detect/alert on performance degradation with measured evidence.[22m
│
│    [36mrelease-readiness[39m
│
│      [2mConduct evidence-based Production Readiness Review for secure, reliable, observable, and recoverable software before release.[22m
│
│    [36mreliability-engineering[39m
│
│      [2mDefine SLOs, instrument services, test backup restoration and rollback, and prove operational recovery for AI-generated software.[22m
│
│    [36mrequirements-engineering[39m
│
│      [2mExtract, refine, and verify software requirements. Ensures every requirement has a measurable acceptance criterion before implementation.[22m
│
│    [36msecure-software-engineering[39m
│
│      [2mApply GENCODE-GOV application-security rules to software built by AI agents. Produce threat models, security tests, remediation evidence, and honest gate outcomes. TSAR is one delegated scanner, not the complete security program.[22m
│
│    [36msecurity-audit[39m
│
│      [2mConduct coverage-led, independently verified, target-neutral source security audits using GENCODE-GOV's coverage ledger, 19-class taxonomy, sandbox, and artifact validators.[22m
│
│    [36msoftware-testing[39m
│
│      [2mDesign and run cross-language test strategies, critical functional workflows, and scenario-traced negative security tests without false-assurance shortcuts.[22m

│
└  Use --skill <name> to install specific skills

[EXIT 0]
```

## 19. Post-Implementation Diff & Security Audit vs origin/main
```text
  File "<string>", line 28
    print(f"Audited {len(files)}} tracked files: 0 staging residue, 0 legacy tokens." if False else f"Audited {len(files)} tracked files: 0 staging residue, 0 legacy tokens.")
                                ^
SyntaxError: f-string: single '}' is not allowed
[EXIT 1]
```

## 20. Final Integration Commit & Gate Verdict
- Integrated commit on feat/integrate-staged-governance: 4620052bd4370794a34f683b3ca0c1468191eee8
- Overall FAIL flag: 1
- Fast-forward push to origin/feat/integrate-staged-governance: SKIPPED (FAIL=1)
