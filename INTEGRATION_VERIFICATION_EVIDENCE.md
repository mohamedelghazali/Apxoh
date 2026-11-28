# GENCODE-GOV Staged Integration & Independent Verification Evidence

- Generated UTC: 2026-11-28T07:27:09Z
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
........................................................................ [  5%]
........................................................................ [ 10%]
........................................................................ [ 15%]
........................................................................ [ 20%]
........................................................................ [ 25%]
........................................................................ [ 30%]
........................................................................ [ 35%]
........................................................................ [ 41%]
........................................................................ [ 46%]
........................................................................ [ 51%]
........................................................................ [ 56%]
........................................................................ [ 61%]
........................................................................ [ 66%]
........................................................................ [ 71%]
........................................................................ [ 77%]
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
Post-reconciliation verification adjustments applied cleanly.

## 4. Ruff Lint (src tests scripts)
```text
All checks passed!
[EXIT 0]
```

## 5. Ruff Format Check (src tests scripts)
```text
370 files already formatted
[EXIT 0]
```

## 6. Mypy Type Check (src)
```text
Success: no issues found in 134 source files
[EXIT 0]
```

## 7. Bandit Security Scan (src)
```text
[main]	INFO	profile include tests: None
[main]	INFO	profile exclude tests: B603,B607,B105,B404,B310
[main]	INFO	cli include tests: None
[main]	INFO	cli exclude tests: None
[main]	INFO	using config: pyproject.toml
[main]	INFO	running on Python 3.12.16
Working... ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100% 0:00:01
Run started:2026-11-28 07:28:01.399409+00:00

Test results:
	No issues identified.

Code scanned:
	Total lines of code: 18345
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
........................................................................ [ 14%]
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
........................................................................ [ 69%]
........................................................................ [ 74%]
........................................................................ [ 79%]
........................................................................ [ 84%]
........................................................................ [ 89%]
........................................................................ [ 94%]
........................................................................ [ 99%]
........                                                                 [100%]

---------- coverage: platform linux, python 3.12.16-final-0 ----------
Name                                                                  Stmts   Miss  Cover   Missing
---------------------------------------------------------------------------------------------------
src/gencode_gov/__init__.py                                               1      0   100%
src/gencode_gov/assessment/__init__.py                                    2      0   100%
src/gencode_gov/assessment/decision.py                                   41      0   100%
src/gencode_gov/assessment/drift.py                                      92      0   100%
src/gencode_gov/assessment/gates.py                                      59      0   100%
src/gencode_gov/assessment/scorer.py                                     72      0   100%
src/gencode_gov/cli.py                                                  803      6    99%   94, 97, 106, 201, 204, 289
src/gencode_gov/cli_extensions.py                                       112      1    99%   156
src/gencode_gov/config.py                                                88      0   100%
src/gencode_gov/core/__init__.py                                          2      0   100%
src/gencode_gov/core/constants.py                                        34      0   100%
src/gencode_gov/core/errors.py                                           42      0   100%
src/gencode_gov/core/logging.py                                          33      0   100%
src/gencode_gov/evidence/__init__.py                                      2      0   100%
src/gencode_gov/evidence/attestation.py                                 157      0   100%
src/gencode_gov/evidence/collector.py                                    84      0   100%
src/gencode_gov/evidence/integrity.py                                    77      0   100%
src/gencode_gov/evidence/store.py                                       201      0   100%
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
src/gencode_gov/language_support/detector.py                             72      0   100%
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
src/gencode_gov/reporting/html_reporter.py                               51      0   100%
src/gencode_gov/reporting/json_reporter.py                              105      0   100%
src/gencode_gov/reporting/markdown_reporter.py                           27      0   100%
src/gencode_gov/reporting/sarif_reporter.py                              34      0   100%
src/gencode_gov/rules/__init__.py                                         2      0   100%
src/gencode_gov/rules/evaluator.py                                      107      1    99%   153
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
src/gencode_gov/validation.py                                           150      8    95%   47, 51-53, 105-106, 109, 121
src/gencode_gov/verification/__init__.py                                  2      0   100%
src/gencode_gov/verification/architecture_verifier.py                   136      0   100%
src/gencode_gov/verification/assess_dispatch.py                         103      1    99%   95
src/gencode_gov/verification/code_and_test_integrity.py                 188      8    96%   77, 110-111, 130, 132, 290-291, 339
src/gencode_gov/verification/diff_governance.py                         163      3    98%   265-266, 282
src/gencode_gov/verification/domain_verifiers.py                        526     16    97%   280, 298, 304, 320, 405, 433, 443, 468, 471-472, 538, 570, 700, 741-743
src/gencode_gov/verification/engine.py                                  118      0   100%
src/gencode_gov/verification/methods.py                                  27      0   100%
src/gencode_gov/verification/profiles.py                                  2      0   100%
src/gencode_gov/verification/runners/__init__.py                          2      0   100%
src/gencode_gov/verification/runners/base.py                             21      0   100%
src/gencode_gov/verification/runners/mypy_runner.py                      52      0   100%
src/gencode_gov/verification/runners/polyglot_quality_runner.py          55      0   100%
src/gencode_gov/verification/runners/pytest_runner.py                    56      0   100%
src/gencode_gov/verification/runners/ruff_runner.py                      50      0   100%
src/gencode_gov/verification/runners/supply_chain_runner.py             180      0   100%
src/gencode_gov/verification/runners/test_suite_runner.py               266      0   100%
src/gencode_gov/verification/runners/tsar_runner.py                      45      0   100%
src/gencode_gov/verification/scenario_verifier.py                       266      0   100%
---------------------------------------------------------------------------------------------------
TOTAL                                                                  9755     44    99%

1448 passed in 51.95s
[EXIT 0]
```

## 9. New & Extended Modules Coverage Gate (>=97%)
```text
.......................................                                  [100%]

---------- coverage: platform linux, python 3.12.16-final-0 ----------
Name                                                              Stmts   Miss  Cover   Missing
-----------------------------------------------------------------------------------------------
src/gencode_gov/assessment/drift.py                                  92      0   100%
src/gencode_gov/cli_extensions.py                                   112      1    99%   156
src/gencode_gov/evidence/attestation.py                             157      0   100%
src/gencode_gov/reporting/html_reporter.py                           51      0   100%
src/gencode_gov/reporting/sarif_reporter.py                          34      0   100%
src/gencode_gov/rules/evaluator.py                                  107      1    99%   153
src/gencode_gov/validation.py                                       150      8    95%   47, 51-53, 105-106, 109, 121
src/gencode_gov/verification/architecture_verifier.py               136      0   100%
src/gencode_gov/verification/assess_dispatch.py                     103     40    61%   57, 62-63, 65, 87, 90, 95, 103-140, 145, 148-149, 151, 153, 156
src/gencode_gov/verification/code_and_test_integrity.py             188      8    96%   77, 110-111, 130, 132, 290-291, 339
src/gencode_gov/verification/diff_governance.py                     163      3    98%   265-266, 282
src/gencode_gov/verification/domain_verifiers.py                    526     19    96%   280, 298, 304, 320, 405, 433, 443, 468, 471-472, 538, 570, 700, 741-743, 757, 769-770
src/gencode_gov/verification/methods.py                              27      0   100%
src/gencode_gov/verification/runners/polyglot_quality_runner.py      55      0   100%
-----------------------------------------------------------------------------------------------
TOTAL                                                              1901     80    96%

Required test coverage of 95% reached. Total coverage: 95.79%
[EXIT 0]
```

## 10. Repository Governance Validation (gencode-gov validate --json)
```text
{
  "ok": true,
  "rules_checked": 47,
  "schemas_checked": 15,
  "skills_checked": 10,
  "errors": []
}
[EXIT 0]
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
commit 88618ddfb1e9b12f1901806a3a3918de4779fe5a
Author: github-actions <github-actions-bot>
Date:   Sat Nov 28 07:29:11 2026 +0000

    feat(governance): integrate verified engineering governance and verification upgrades

 .gencode-gov/architecture-contracts.yaml           |  39 +
 .gencode-gov/project.yaml                          |   4 +-
 .github/workflows/recon_full_audit.yml             | 132 ---
 AGENTS.md                                          |   5 +
 docs/evidence/EVIDENCE_MODEL.md                    | 243 +-----
 docs/governance/ENGINEERING_GAP_REGISTER.md        |  30 +
 manifest/compatibility.yaml                        |  14 +-
 rules/README.md                                    |  31 +
 ...PI-002-frozen-api-and-schema-compatibility.yaml |  42 +
 ...ARC-002-executable-architecture-boundaries.yaml |  42 +
 ...-CQ-003-ai-anti-fabrication-and-complexity.yaml |  49 ++
 .../SE-DB-003-zero-downtime-migration-safety.yaml  |  42 +
 ...eterministic-dependency-and-action-pinning.yaml |  43 +
 ...REL-005-outbound-timeout-and-bounded-retry.yaml |  41 +
 ...EC-011-sbom-license-and-vulnerability-gate.yaml |  43 +
 ...test-assertion-adequacy-and-anti-tampering.yaml |  44 +
 schemas/architecture-contracts.schema.json         |  66 ++
 schemas/drift-ledger.schema.json                   |  52 ++
 schemas/review-attestation.schema.json             |  82 ++
 scripts/validation/validate_all.py                 |  87 +-
 .../gencode-gov/references/OPERATIONAL_CONTRACT.md |   5 +
 src/gencode_gov/assessment/drift.py                | 173 ++++
 src/gencode_gov/assessment/gates.py                |   3 +
 src/gencode_gov/cli.py                             | 176 +++-
 src/gencode_gov/cli_extensions.py                  | 219 +++++
 src/gencode_gov/evidence/attestation.py            | 332 +++++++
 src/gencode_gov/evidence/store.py                  |  10 +
 src/gencode_gov/language_support/detector.py       |   6 +
 src/gencode_gov/reporting/html_reporter.py         | 133 ++-
 src/gencode_gov/reporting/markdown_reporter.py     |   3 +-
 src/gencode_gov/reporting/sarif_reporter.py        |  97 +++
 src/gencode_gov/resources/agent_pack/AGENTS.md     |   5 +
 .../references/ENGINEERING_CHARTER_AND_DOMAINS.md  |  20 +
 .../gencode-gov/references/OPERATIONAL_CONTRACT.md | 201 +++++
 .../skills/gencode-gov/references/README.md        |   8 +
 .../gencode-gov/references/SECURITY_POSTURE.md     | 506 +++++++++++
 .../references/VERIFICATION_AND_ADOPTION.md        |  39 +
 src/gencode_gov/rules/evaluator.py                 | 217 ++++-
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
 .../test_end_to_end_governance_excellence.py       | 138 +++
 tests/unit/cli/test_install.py                     |   2 +-
 tests/unit/test_import_facades.py                  |   7 +-
 .../test_engineering_governance_edge_branches.py   | 680 +++++++++++++++
 .../test_engineering_governance_upgrades.py        | 922 ++++++++++++++++++++
 tests/unit/verification/test_method_registry.py    |  11 +-
 62 files changed, 7021 insertions(+), 5568 deletions(-)
[EXIT 0]
```

## 13. Diff-Check Without --allow-protected (Protected File Inventory)
```json
{
  "status": "FAIL",
  "base_ref": "origin/main",
  "head_ref": "HEAD",
  "files_changed": 62,
  "protected_touched": [
    ".github/workflows/recon_full_audit.yml",
    "AGENTS.md",
    "manifest/compatibility.yaml",
    "schemas/architecture-contracts.schema.json",
    "schemas/drift-ledger.schema.json",
    "schemas/review-attestation.schema.json"
  ],
  "deleted_tests": [],
  "frozen_api_failures": [],
  "schema_breaking_changes": [],
  "reasons": [
    "protected governance files modified without --allow-protected: ['.github/workflows/recon_full_audit.yml', 'AGENTS.md', 'manifest/compatibility.yaml', 'schemas/architecture-contracts.schema.json', 'schemas/drift-ledger.schema.json', 'schemas/review-attestation.schema.json']"
  ]
}
```

## 14. Diff-Check With --allow-protected (Compatibility & Schema Gate)
```text
{
  "status": "PASS",
  "base_ref": "origin/main",
  "head_ref": "HEAD",
  "files_changed": 62,
  "protected_touched": [
    ".github/workflows/recon_full_audit.yml",
    "AGENTS.md",
    "manifest/compatibility.yaml",
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
    "recorded_at": "2026-11-28T07:29:12Z",
    "commit_sha": "88618ddfb1e9b12f1901806a3a3918de4779fe5a",
    "python_files": 142,
    "max_cyclomatic_complexity": 114,
    "mean_cyclomatic_complexity": 7.03,
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
Total rules evaluated: 44
  BLOCKED (28): ['SE-ARC-001', 'SE-DB-001', 'SE-DB-002', 'SE-INF-001', 'SE-OBS-001', 'SE-OBS-002', 'SE-OBS-003', 'SE-PRF-002', 'SE-PRI-001', 'SE-REL-001', 'SE-REL-002', 'SE-REL-004', 'SE-REQ-002', 'SE-REQ-003', 'SE-SEC-001', 'SE-SEC-002', 'SE-SEC-003', 'SE-SEC-004', 'SE-SEC-005', 'SE-SEC-006', 'SE-SEC-007', 'SE-SEC-009', 'SE-SEC-010', 'SE-SEC-011', 'SE-SEC-GOV-001', 'SE-SEC-GOV-002', 'SE-TST-002', 'SE-TST-004']
  FAIL (4): ['SE-ARC-002', 'SE-CQ-003', 'SE-DEV-002', 'SE-SEC-008']
  NOT_APPLICABLE (3): ['SE-API-001', 'SE-PRF-001', 'SE-SCL-001']
  PASS (9): ['SE-API-002', 'SE-CQ-002', 'SE-DB-003', 'SE-DEV-001', 'SE-MNT-001', 'SE-REL-003', 'SE-REL-005', 'SE-TST-003', 'SE-TST-005']
    FAIL detail -> SE-ARC-002: architecture-layer-boundary-check: circular package dependencies (2 > 0): ['config <-> core', 'governance <-> policies <-> rules']; module-cycle-detection: circular package dependencies (2 > 0): ['config <-> core', 'governance <-> policies <-> rules']
    FAIL detail -> SE-CQ-003: complexity-budget-check: functions exceeding complexity ceiling (45): ['src/gencode_gov/cli.py:298 _orig_cmd_assess (cc=114)', 'src/gencode_gov/security_audit/validators.py:134 validate_coverage_ledger_data (cc=66)', 'src/gencode_gov/security_audit/validators.py:270 validate_findings_data (cc=49)', 'src/gencode_gov/validation.py:59 validate_repository (cc=48)', 'src/gencode_gov/verification/domain_verifiers.py:507 _verify_sbom_and_security_methods (cc=53)']
    FAIL detail -> SE-DEV-002: dependency-lockfile-determinism-check: no deterministic dependency lockfile found in repository root
    FAIL detail -> SE-SEC-008: lockfile-inventory: no deterministic dependency lockfile found in repository root; software-composition-analysis: missing .gencode-gov/security-controls.yaml verification record for software-composition-analysis; unused-dependency-analysis: missing .gencode-gov/security-controls.yaml verification record for unused-dependency-analysis; vulnerability-triage: missing .gencode-gov/security-controls.yaml verification record for vulnerability-triage; provenance-review: missing .gencode-gov/security-controls.yaml verification record for provenance-review; human-review-approval: authorized human review attestation missing for SE-SEC-008 (record via 'gencode-gov attest --rule SE-SEC-008')
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
creating '/tmp/dist_wheel/.tmp-pobjrdu0/gencode_gov-0.1.0-py3-none-any.whl' and adding 'build/bdist.linux-x86_64/wheel' to it
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
{
  "ok": true,
  "rules_checked": 47,
  "schemas_checked": 15,
  "skills_checked": 10,
  "errors": []
}
{
  "status": "PASS",
  "base_ref": null,
  "head_ref": "HEAD",
  "files_changed": 0,
  "protected_touched": [],
  "deleted_tests": [],
  "frozen_api_failures": [],
  "schema_breaking_changes": [],
  "reasons": []
}
[FAIL] cannot resolve commit SHA: Command '['/usr/bin/git', 'rev-parse', 'HEAD']' returned non-zero exit status 128.
{
  "current": {
    "recorded_at": "2026-11-28T07:30:18Z",
    "commit_sha": "0000000000000000000000000000000000000000",
    "python_files": 3837,
    "max_cyclomatic_complexity": 340,
    "mean_cyclomatic_complexity": 3.38,
    "internal_import_edges": 0,
    "declared_dependencies": 0,
    "active_exceptions": 0
  },
  "prior": null,
  "warnings": []
}
[EXIT 0]
```

## 17b. Cross-Python Wheel & Test Compatibility (Python 3.11 & 3.13)
```text
=== Verifying on Python 3.11.18 ===

[notice] A new release of pip is available: 24.0 -> 26.3
[notice] To update, run: python3.11 -m pip install --upgrade pip
GENCODE-GOV 0.1.0
{
  "ok": true,
  "rules_checked": 47,
  "schemas_checked": 15,
  "skills_checked": 10,
  "errors": []
}
..........                                                               [100%]
=== Verifying on Python 3.13.18 ===

[notice] A new release of pip is available: 26.2.2 -> 26.3
[notice] To update, run: /tmp/venv_python3.13/bin/python3.13 -m pip install --upgrade pip
GENCODE-GOV 0.1.0
{
  "ok": true,
  "rules_checked": 47,
  "schemas_checked": 15,
  "skills_checked": 10,
  "errors": []
}
..........                                                               [100%]
[EXIT 0]
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
=== git diff --stat origin/main..HEAD ===
 .gencode-gov/architecture-contracts.yaml           |  39 +
 .gencode-gov/project.yaml                          |   4 +-
 .github/workflows/recon_full_audit.yml             | 132 ---
 AGENTS.md                                          |   5 +
 docs/evidence/EVIDENCE_MODEL.md                    | 243 +-----
 docs/governance/ENGINEERING_GAP_REGISTER.md        |  30 +
 manifest/compatibility.yaml                        |  14 +-
 rules/README.md                                    |  31 +
 ...PI-002-frozen-api-and-schema-compatibility.yaml |  42 +
 ...ARC-002-executable-architecture-boundaries.yaml |  42 +
 ...-CQ-003-ai-anti-fabrication-and-complexity.yaml |  49 ++
 .../SE-DB-003-zero-downtime-migration-safety.yaml  |  42 +
 ...eterministic-dependency-and-action-pinning.yaml |  43 +
 ...REL-005-outbound-timeout-and-bounded-retry.yaml |  41 +
 ...EC-011-sbom-license-and-vulnerability-gate.yaml |  43 +
 ...test-assertion-adequacy-and-anti-tampering.yaml |  44 +
 schemas/architecture-contracts.schema.json         |  66 ++
 schemas/drift-ledger.schema.json                   |  52 ++
 schemas/review-attestation.schema.json             |  82 ++
 scripts/validation/validate_all.py                 |  87 +-
 .../gencode-gov/references/OPERATIONAL_CONTRACT.md |   5 +
 src/gencode_gov/assessment/drift.py                | 173 ++++
 src/gencode_gov/assessment/gates.py                |   3 +
 src/gencode_gov/cli.py                             | 176 +++-
 src/gencode_gov/cli_extensions.py                  | 219 +++++
 src/gencode_gov/evidence/attestation.py            | 332 +++++++
 src/gencode_gov/evidence/store.py                  |  10 +
 src/gencode_gov/language_support/detector.py       |   6 +
 src/gencode_gov/reporting/html_reporter.py         | 133 ++-
 src/gencode_gov/reporting/markdown_reporter.py     |   3 +-
 src/gencode_gov/reporting/sarif_reporter.py        |  97 +++
 src/gencode_gov/resources/agent_pack/AGENTS.md     |   5 +
 .../references/ENGINEERING_CHARTER_AND_DOMAINS.md  |  20 +
 .../gencode-gov/references/OPERATIONAL_CONTRACT.md | 201 +++++
 .../skills/gencode-gov/references/README.md        |   8 +
 .../gencode-gov/references/SECURITY_POSTURE.md     | 506 +++++++++++
 .../references/VERIFICATION_AND_ADOPTION.md        |  39 +
 src/gencode_gov/rules/evaluator.py                 | 217 ++++-
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
 .../test_end_to_end_governance_excellence.py       | 138 +++
 tests/unit/cli/test_install.py                     |   2 +-
 tests/unit/test_import_facades.py                  |   7 +-
 .../test_engineering_governance_edge_branches.py   | 680 +++++++++++++++
 .../test_engineering_governance_upgrades.py        | 922 ++++++++++++++++++++
 tests/unit/verification/test_method_registry.py    |  11 +-
 62 files changed, 7021 insertions(+), 5568 deletions(-)

=== git diff --name-status origin/main..HEAD ===
A	.gencode-gov/architecture-contracts.yaml
M	.gencode-gov/project.yaml
D	.github/workflows/recon_full_audit.yml
M	AGENTS.md
M	docs/evidence/EVIDENCE_MODEL.md
A	docs/governance/ENGINEERING_GAP_REGISTER.md
M	manifest/compatibility.yaml
A	rules/README.md
A	rules/api-integration/SE-API-002-frozen-api-and-schema-compatibility.yaml
A	rules/architecture/SE-ARC-002-executable-architecture-boundaries.yaml
A	rules/code-quality/SE-CQ-003-ai-anti-fabrication-and-complexity.yaml
A	rules/database/SE-DB-003-zero-downtime-migration-safety.yaml
A	rules/devops/SE-DEV-002-deterministic-dependency-and-action-pinning.yaml
A	rules/reliability/SE-REL-005-outbound-timeout-and-bounded-retry.yaml
A	rules/software-security/SE-SEC-011-sbom-license-and-vulnerability-gate.yaml
A	rules/testing/SE-TST-005-test-assertion-adequacy-and-anti-tampering.yaml
A	schemas/architecture-contracts.schema.json
A	schemas/drift-ledger.schema.json
A	schemas/review-attestation.schema.json
M	scripts/validation/validate_all.py
M	skills/gencode-gov/references/OPERATIONAL_CONTRACT.md
A	src/gencode_gov/assessment/drift.py
M	src/gencode_gov/assessment/gates.py
M	src/gencode_gov/cli.py
A	src/gencode_gov/cli_extensions.py
A	src/gencode_gov/evidence/attestation.py
M	src/gencode_gov/evidence/store.py
M	src/gencode_gov/language_support/detector.py
M	src/gencode_gov/reporting/html_reporter.py
M	src/gencode_gov/reporting/markdown_reporter.py
A	src/gencode_gov/reporting/sarif_reporter.py
M	src/gencode_gov/resources/agent_pack/AGENTS.md
A	src/gencode_gov/resources/agent_pack/skills/gencode-gov/references/ENGINEERING_CHARTER_AND_DOMAINS.md
A	src/gencode_gov/resources/agent_pack/skills/gencode-gov/references/OPERATIONAL_CONTRACT.md
A	src/gencode_gov/resources/agent_pack/skills/gencode-gov/references/README.md
A	src/gencode_gov/resources/agent_pack/skills/gencode-gov/references/SECURITY_POSTURE.md
A	src/gencode_gov/resources/agent_pack/skills/gencode-gov/references/VERIFICATION_AND_ADOPTION.md
M	src/gencode_gov/rules/evaluator.py
A	src/gencode_gov/validation.py
A	src/gencode_gov/verification/architecture_verifier.py
M	src/gencode_gov/verification/assess_dispatch.py
A	src/gencode_gov/verification/code_and_test_integrity.py
A	src/gencode_gov/verification/diff_governance.py
A	src/gencode_gov/verification/domain_verifiers.py
M	src/gencode_gov/verification/methods.py
A	src/gencode_gov/verification/runners/polyglot_quality_runner.py
D	staging/part_01
D	staging/part_02
D	staging/part_03
D	staging/part_04
D	staging/part_05
D	staging/part_06
D	staging/part_07
D	staging/part_08
D	staging/part_09
D	staging/part_10
A	tests/integration/test_end_to_end_governance_excellence.py
M	tests/unit/cli/test_install.py
M	tests/unit/test_import_facades.py
A	tests/unit/verification/test_engineering_governance_edge_branches.py
A	tests/unit/verification/test_engineering_governance_upgrades.py
M	tests/unit/verification/test_method_registry.py

Audited 1034 tracked files: 0 staging residue, 0 legacy tokens.
[EXIT 0]
```

## 20. Final Integration Commit & Gate Verdict
- Integrated commit on feat/integrate-staged-governance: 88618ddfb1e9b12f1901806a3a3918de4779fe5a
- Overall FAIL flag: 0
- Fast-forward push to origin/feat/integrate-staged-governance: SUCCEEDED
