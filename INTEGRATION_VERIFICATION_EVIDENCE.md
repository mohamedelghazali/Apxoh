# GENCODE-GOV Staged Integration & Independent Verification Evidence

- Generated UTC: 2026-11-27T23:34:27Z
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

## 3. Per-File Pre-Integration Classification vs origin/main

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
Fixed GAP-03: _working_tree_clean filters runtime .gencode-gov/ outputs
Wired rule & commit_sha into evaluate_extended_method in cmd_assess
agent_pack total files after bundling references/: 27

Frozen API self-check: PASS — verified 4 frozen_apis entrypoint(s) ()

## 4. Ruff Lint (src tests scripts)
```text
F821 Undefined name `true`
  --> src/gencode_gov/evidence/attestation.py:75:32
   |
73 |                 "type": "array",
74 |                 "minItems": 1,
75 |                 "uniqueItems": true,
   |                                ^^^^
76 |                 "items": {"type": "string", "pattern": "^SE-[A-Z]+(-[A-Z]+)?-\\d{3,}$"},
77 |             },
   |

S112 `try`-`except`-`continue` detected, consider logging the exception
  --> src/gencode_gov/rules/evaluator.py:78:17
   |
76 |                           if exc.is_active():
77 |                               mapping[exc.rule_id] = exc.id
78 | /                 except Exception:  # noqa: BLE001
79 | |                     continue
   | |____________________________^
80 |           return mapping
   |

SIM102 Use a single `if` statement instead of nested `if` statements
   --> src/gencode_gov/verification/diff_governance.py:139:13
    |
137 |               old_p = old_props[prop_name]
138 |               new_p = new_props[prop_name]
139 | /             if isinstance(old_p, dict) and isinstance(new_p, dict):
140 | |                 if isinstance(old_p.get("enum"), list) and isinstance(new_p.get("enum"), list):
    | |_______________________________________________________________________________________________^
141 |                       dropped_enum = sorted(set(old_p["enum"]) - set(new_p["enum"]))
142 |                       if dropped_enum:
    |
help: Combine `if` statements using `and`

SIM102 Use a single `if` statement instead of nested `if` statements
   --> src/gencode_gov/verification/domain_verifiers.py:464:13
    |
462 |                       if not has_timeout:
463 |                           missing_timeouts.append(f"{rel}:{node.lineno} ({owner}.{attr})")
464 | /             elif isinstance(node, ast.While):
465 | |                 if isinstance(node.test, ast.Constant) and node.test.value is True:
    | |___________________________________________________________________________________^
466 |                       has_exit = any(
467 |                           isinstance(sub, (ast.Break, ast.Return, ast.Raise))
    |
help: Combine `if` statements using `and`

SIM102 Use a single `if` statement instead of nested `if` statements
   --> src/gencode_gov/verification/domain_verifiers.py:831:13
    |
829 |           if _safe_file(root, ".gencode-gov/observability-verification.yaml") is not None:
830 |               doc = _load_yaml_safe(root / ".gencode-gov" / "observability-verification.yaml")
831 | /             if doc is not None and isinstance(doc.get("verified_methods"), dict):
832 | |                 if doc["verified_methods"].get(method_id) is True:
    | |__________________________________________________________________^
833 |                       return STATUS_PASS, f"verified {method_id} in observability-verification.yaml"
834 |           return _verify_operational_artifact_method(
    |
help: Combine `if` statements using `and`

S607 Starting a process with a partial executable path
  --> tests/integration/test_end_to_end_governance_excellence.py:17:9
   |
15 |     subprocess.run(["git", "init", "-q"], cwd=root, check=True, timeout=10)  # noqa: S603,S607
16 |     subprocess.run(  # noqa: S603,S607
17 |         ["git", "config", "user.email", "lead@example.invalid"], cwd=root, check=True, timeout=10
   |         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
18 |     )
19 |     subprocess.run(  # noqa: S603,S607
   |

S607 Starting a process with a partial executable path
  --> tests/integration/test_end_to_end_governance_excellence.py:20:9
   |
18 |     )
19 |     subprocess.run(  # noqa: S603,S607
20 |         ["git", "config", "user.name", "eng_reviewer_role"], cwd=root, check=True, timeout=10
   |         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
21 |     )
22 |     (root / "pyproject.toml").write_text(
   |

S607 Starting a process with a partial executable path
  --> tests/integration/test_end_to_end_governance_excellence.py:55:9
   |
53 |     subprocess.run(["git", "add", "-A"], cwd=root, check=True, timeout=10)  # noqa: S603,S607
54 |     subprocess.run(  # noqa: S603,S607
55 |         ["git", "commit", "-q", "-m", "feat: initial governed project"],
   |         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
56 |         cwd=root,
57 |         check=True,
   |

S607 Starting a process with a partial executable path
  --> tests/integration/test_end_to_end_governance_excellence.py:61:9
   |
59 |     )
60 |     res = subprocess.run(  # noqa: S603,S607
61 |         ["git", "rev-parse", "HEAD"],
   |         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
62 |         cwd=root,
63 |         capture_output=True,
   |

S607 Starting a process with a partial executable path
   --> tests/unit/verification/test_engineering_governance_edge_branches.py:460:9
    |
458 |     subprocess.run(["git", "init", "-q"], cwd=d_repo, check=True, timeout=10)  # noqa: S603,S607
459 |     subprocess.run(  # noqa: S603,S607
460 |         ["git", "config", "user.email", "a@b.c"], cwd=d_repo, check=True, timeout=10
    |         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
461 |     )
462 |     subprocess.run(  # noqa: S603,S607
    |

S607 Starting a process with a partial executable path
   --> tests/unit/verification/test_engineering_governance_edge_branches.py:463:9
    |
461 |     )
462 |     subprocess.run(  # noqa: S603,S607
463 |         ["git", "config", "user.name", "A"], cwd=d_repo, check=True, timeout=10
    |         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
464 |     )
465 |     subprocess.run(["git", "add", "-A"], cwd=d_repo, check=True, timeout=10)  # noqa: S603,S607
    |

S607 Starting a process with a partial executable path
   --> tests/unit/verification/test_engineering_governance_edge_branches.py:467:9
    |
465 |     subprocess.run(["git", "add", "-A"], cwd=d_repo, check=True, timeout=10)  # noqa: S603,S607
466 |     subprocess.run(  # noqa: S603,S607
467 |         ["git", "commit", "-q", "-m", "c1"], cwd=d_repo, check=True, timeout=10
    |         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
468 |     )
469 |     b_sha = subprocess.run(  # noqa: S603,S607
    |

S607 Starting a process with a partial executable path
   --> tests/unit/verification/test_engineering_governance_edge_branches.py:470:9
    |
468 |     )
469 |     b_sha = subprocess.run(  # noqa: S603,S607
470 |         ["git", "rev-parse", "HEAD"],
    |         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
471 |         cwd=d_repo,
472 |         capture_output=True,
    |

S607 Starting a process with a partial executable path
   --> tests/unit/verification/test_engineering_governance_edge_branches.py:484:9
    |
482 |     subprocess.run(["git", "add", "-A"], cwd=d_repo, check=True, timeout=10)  # noqa: S603,S607
483 |     subprocess.run(  # noqa: S603,S607
484 |         ["git", "commit", "-q", "-m", "del"], cwd=d_repo, check=True, timeout=10
    |         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
485 |     )
486 |     assert evaluate_diff_governance(d_repo, base_ref=b_sha).status == STATUS_FAIL
    |

S607 Starting a process with a partial executable path
  --> tests/unit/verification/test_engineering_governance_upgrades.py:70:9
   |
68 |     subprocess.run(["git", "init", "-q"], cwd=root, check=True, timeout=10)  # noqa: S603,S607
69 |     subprocess.run(  # noqa: S603,S607
70 |         ["git", "config", "user.email", "eng@example.invalid"], cwd=root, check=True, timeout=10
   |         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
71 |     )
72 |     subprocess.run(  # noqa: S603,S607
   |

S607 Starting a process with a partial executable path
  --> tests/unit/verification/test_engineering_governance_upgrades.py:73:9
   |
71 |     )
72 |     subprocess.run(  # noqa: S603,S607
73 |         ["git", "config", "user.name", "ci_committer_role"], cwd=root, check=True, timeout=10
   |         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
74 |     )
75 |     (root / "README.md").write_text("# Test Repo\n", encoding="utf-8")
   |

S607 Starting a process with a partial executable path
  --> tests/unit/verification/test_engineering_governance_upgrades.py:78:9
   |
76 |     subprocess.run(["git", "add", "-A"], cwd=root, check=True, timeout=10)  # noqa: S603,S607
77 |     subprocess.run(  # noqa: S603,S607
78 |         ["git", "commit", "-q", "-m", "init"], cwd=root, check=True, timeout=10
   |         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
79 |     )
80 |     res = subprocess.run(  # noqa: S603,S607
   |

S607 Starting a process with a partial executable path
  --> tests/unit/verification/test_engineering_governance_upgrades.py:81:9
   |
79 |     )
80 |     res = subprocess.run(  # noqa: S603,S607
81 |         ["git", "rev-parse", "HEAD"],
   |         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
82 |         cwd=root,
83 |         capture_output=True,
   |

S607 Starting a process with a partial executable path
   --> tests/unit/verification/test_engineering_governance_upgrades.py:410:9
    |
408 |     subprocess.run(["git", "add", "-A"], cwd=tmp_path, check=True, timeout=10)  # noqa: S603,S607
409 |     subprocess.run(  # noqa: S603,S607
410 |         ["git", "commit", "-q", "-m", "drop test"], cwd=tmp_path, check=True, timeout=10
    |         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
411 |     )
412 |     st_del, _ = verify_test_adequacy_method(
    |

S607 Starting a process with a partial executable path
   --> tests/unit/verification/test_engineering_governance_upgrades.py:473:9
    |
471 |     subprocess.run(["git", "add", "-A"], cwd=tmp_path, check=True, timeout=10)  # noqa: S603,S607
472 |     subprocess.run(  # noqa: S603,S607
473 |         ["git", "commit", "-q", "-m", "breaking"], cwd=tmp_path, check=True, timeout=10
    |         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
474 |     )
    |

Found 20 errors.
[EXIT 1]
```

## 5. Ruff Format Check (src tests scripts)
```text
370 files already formatted
[EXIT 0]
```

## 6. Mypy Type Check (src)
```text
src/gencode_gov/verification/code_and_test_integrity.py:294: error: "AST" has no attribute "name"  [attr-defined]
src/gencode_gov/verification/code_and_test_integrity.py:296: error: "AST" has no attribute "body"  [attr-defined]
src/gencode_gov/verification/code_and_test_integrity.py:298: error: "AST" has no attribute "lineno"  [attr-defined]
src/gencode_gov/verification/code_and_test_integrity.py:298: error: "AST" has no attribute "name"  [attr-defined]
src/gencode_gov/verification/code_and_test_integrity.py:300: error: Argument 1 to "_test_has_real_verification" has incompatible type "AST"; expected "FunctionDef | AsyncFunctionDef"  [arg-type]
src/gencode_gov/verification/code_and_test_integrity.py:302: error: "AST" has no attribute "lineno"  [attr-defined]
src/gencode_gov/verification/code_and_test_integrity.py:302: error: "AST" has no attribute "name"  [attr-defined]
src/gencode_gov/evidence/attestation.py:75: error: Name "true" is not defined  [name-defined]
src/gencode_gov/verification/runners/polyglot_quality_runner.py:12: error: Module "gencode_gov.language_support.language_profile_loader" has no attribute "load_language_profiles"; maybe "load_language_profile"?  [attr-defined]
src/gencode_gov/verification/runners/polyglot_quality_runner.py:13: error: Module "gencode_gov.language_support.tool_resolver" has no attribute "resolve_tool"; maybe "resolve_tools"?  [attr-defined]
src/gencode_gov/verification/runners/polyglot_quality_runner.py:46: error: "DetectionResult" has no attribute "__iter__" (not iterable)  [attr-defined]
src/gencode_gov/verification/runners/polyglot_quality_runner.py:100: error: No overload variant of "list" matches argument type "DetectionResult"  [call-overload]
src/gencode_gov/verification/runners/polyglot_quality_runner.py:100: note: Possible overload variants:
src/gencode_gov/verification/runners/polyglot_quality_runner.py:100: note:     def [_T] list() -> list[_T]
src/gencode_gov/verification/runners/polyglot_quality_runner.py:100: note:     def [_T] list(Iterable[_T], /) -> list[_T]
src/gencode_gov/verification/runners/polyglot_quality_runner.py:129: error: Argument 1 to "len" has incompatible type "DetectionResult"; expected "Sized"  [arg-type]
src/gencode_gov/cli_extensions.py:17: error: Module "gencode_gov.language_support.language_profile_loader" has no attribute "load_language_profiles"; maybe "load_language_profile"?  [attr-defined]
src/gencode_gov/cli_extensions.py:18: error: Module "gencode_gov.language_support.tool_resolver" has no attribute "resolve_tool"; maybe "resolve_tools"?  [attr-defined]
src/gencode_gov/cli_extensions.py:166: error: "DetectionResult" has no attribute "__iter__" (not iterable)  [attr-defined]
src/gencode_gov/rules/evaluator.py:77: error: "Exception" has no attribute "id"  [attr-defined]
Found 17 errors in 5 files (checked 134 source files)
[EXIT 1]
```

## 7. Bandit Security Scan (src)
```text
[main]	INFO	profile include tests: None
[main]	INFO	profile exclude tests: B105,B310,B607,B603,B404
[main]	INFO	cli include tests: None
[main]	INFO	cli exclude tests: None
[main]	INFO	using config: pyproject.toml
[main]	INFO	running on Python 3.12.16
Working... ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100% 0:00:01
Run started:2026-11-27 23:35:12.226048+00:00

Test results:
>> Issue: [B112:try_except_continue] Try, Except, Continue detected.
   Severity: Low   Confidence: High
   CWE: CWE-703 (https://cwe.mitre.org/data/definitions/703.html)
   More Info: https://bandit.readthedocs.io/en/1.9.4/plugins/b112_try_except_continue.html
   Location: src/gencode_gov/rules/evaluator.py:78:16
77	                            mapping[exc.rule_id] = exc.id
78	                except Exception:  # noqa: BLE001
79	                    continue
80	        return mapping

--------------------------------------------------

Code scanned:
	Total lines of code: 18310
	Total lines skipped (#nosec): 0
	Total potential issues skipped due to specifically being disabled (e.g., #nosec BXXX): 0

Run metrics:
	Total issues (by severity):
		Undefined: 0
		Low: 1
		Medium: 0
		High: 0
	Total issues (by confidence):
		Undefined: 0
		Low: 0
		Medium: 0
		High: 1
Files skipped (0):
[EXIT 1]
```

## 8. Full Pytest & Coverage Suite
```text

==================================== ERRORS ====================================
_ ERROR collecting tests/rules/positive/test_consolidated_governance_rules.py __
ImportError while importing test module '/home/runner/work/GENCODE-GOV/GENCODE-GOV/tests/rules/positive/test_consolidated_governance_rules.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
tests/rules/positive/test_consolidated_governance_rules.py:12: in <module>
    import gencode_gov.verification.assess_dispatch as ad_mod
src/gencode_gov/verification/assess_dispatch.py:19: in <module>
    from gencode_gov.verification.runners.polyglot_quality_runner import PolyglotQualityRunner
src/gencode_gov/verification/runners/polyglot_quality_runner.py:12: in <module>
    from gencode_gov.language_support.language_profile_loader import load_language_profiles
E   ImportError: cannot import name 'load_language_profiles' from 'gencode_gov.language_support.language_profile_loader' (/home/runner/work/GENCODE-GOV/GENCODE-GOV/src/gencode_gov/language_support/language_profile_loader.py)
_ ERROR collecting tests/unit/security_audit/test_hunting_reassessment_and_cli.py _
ImportError while importing test module '/home/runner/work/GENCODE-GOV/GENCODE-GOV/tests/unit/security_audit/test_hunting_reassessment_and_cli.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
tests/unit/security_audit/test_hunting_reassessment_and_cli.py:18: in <module>
    from gencode_gov.verification.assess_dispatch import (
src/gencode_gov/verification/assess_dispatch.py:19: in <module>
    from gencode_gov.verification.runners.polyglot_quality_runner import PolyglotQualityRunner
src/gencode_gov/verification/runners/polyglot_quality_runner.py:12: in <module>
    from gencode_gov.language_support.language_profile_loader import load_language_profiles
E   ImportError: cannot import name 'load_language_profiles' from 'gencode_gov.language_support.language_profile_loader' (/home/runner/work/GENCODE-GOV/GENCODE-GOV/src/gencode_gov/language_support/language_profile_loader.py)
_ ERROR collecting tests/unit/verification/test_cross_language_and_security_traceability.py _
ImportError while importing test module '/home/runner/work/GENCODE-GOV/GENCODE-GOV/tests/unit/verification/test_cross_language_and_security_traceability.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
tests/unit/verification/test_cross_language_and_security_traceability.py:19: in <module>
    from gencode_gov.verification.assess_dispatch import (
src/gencode_gov/verification/assess_dispatch.py:19: in <module>
    from gencode_gov.verification.runners.polyglot_quality_runner import PolyglotQualityRunner
src/gencode_gov/verification/runners/polyglot_quality_runner.py:12: in <module>
    from gencode_gov.language_support.language_profile_loader import load_language_profiles
E   ImportError: cannot import name 'load_language_profiles' from 'gencode_gov.language_support.language_profile_loader' (/home/runner/work/GENCODE-GOV/GENCODE-GOV/src/gencode_gov/language_support/language_profile_loader.py)
_ ERROR collecting tests/unit/verification/test_engineering_governance_edge_branches.py _
ImportError while importing test module '/home/runner/work/GENCODE-GOV/GENCODE-GOV/tests/unit/verification/test_engineering_governance_edge_branches.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
tests/unit/verification/test_engineering_governance_edge_branches.py:14: in <module>
    from gencode_gov.cli_extensions import (
src/gencode_gov/cli_extensions.py:17: in <module>
    from gencode_gov.language_support.language_profile_loader import load_language_profiles
E   ImportError: cannot import name 'load_language_profiles' from 'gencode_gov.language_support.language_profile_loader' (/home/runner/work/GENCODE-GOV/GENCODE-GOV/src/gencode_gov/language_support/language_profile_loader.py)
_ ERROR collecting tests/unit/verification/test_engineering_governance_upgrades.py _
ImportError while importing test module '/home/runner/work/GENCODE-GOV/GENCODE-GOV/tests/unit/verification/test_engineering_governance_upgrades.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
tests/unit/verification/test_engineering_governance_upgrades.py:14: in <module>
    from gencode_gov.cli_extensions import (
src/gencode_gov/cli_extensions.py:17: in <module>
    from gencode_gov.language_support.language_profile_loader import load_language_profiles
E   ImportError: cannot import name 'load_language_profiles' from 'gencode_gov.language_support.language_profile_loader' (/home/runner/work/GENCODE-GOV/GENCODE-GOV/src/gencode_gov/language_support/language_profile_loader.py)

---------- coverage: platform linux, python 3.12.16-final-0 ----------
Name                                                                  Stmts   Miss  Cover   Missing
---------------------------------------------------------------------------------------------------
src/gencode_gov/__init__.py                                               1      0   100%
src/gencode_gov/assessment/__init__.py                                    2      0   100%
src/gencode_gov/assessment/decision.py                                   41     24    41%   25, 41-105
src/gencode_gov/assessment/drift.py                                      92     65    29%   35, 49-89, 108-173
src/gencode_gov/assessment/gates.py                                      59     32    46%   58, 62, 65, 75-103, 116-121
src/gencode_gov/assessment/scorer.py                                     72     46    36%   23, 41-44, 57-60, 63, 71-83, 88-95, 100-120
src/gencode_gov/cli.py                                                  778    743     4%   20, 25-30, 34-44, 48-82, 86-101, 105-126, 130-172, 176-194, 198-227, 231-253, 257-277, 282-709, 714-773, 778-819, 823, 828-910, 915-1019, 1023-1040, 1044-1064, 1068-1128, 1132-1267, 1271-1276, 1280
src/gencode_gov/cli_extensions.py                                       118    105    11%   18-214
src/gencode_gov/config.py                                                88     58    34%   31-45, 51-62, 79-82, 86-89, 93-96, 99, 112-131, 137
src/gencode_gov/core/__init__.py                                          2      0   100%
src/gencode_gov/core/constants.py                                        34      4    88%   91, 95, 99, 103
src/gencode_gov/core/errors.py                                           42      2    95%   16-17
src/gencode_gov/core/logging.py                                          33     21    36%   18-29, 36, 41-55
src/gencode_gov/evidence/__init__.py                                      2      0   100%
src/gencode_gov/evidence/attestation.py                                 157    122    22%   56, 101-107, 111-122, 137-215, 237-325
src/gencode_gov/evidence/collector.py                                    84     45    46%   25-29, 33, 44-50, 70-73, 76-101, 108, 112, 122-129
src/gencode_gov/evidence/integrity.py                                    77     64    17%   18-22, 26-32, 45-78, 88-109
src/gencode_gov/evidence/store.py                                       202    156    23%   36, 40, 44, 51-52, 55-60, 64, 67-75, 79-81, 85-179, 182-236, 239-251, 254-256, 259-277, 280-287, 292-294
src/gencode_gov/evidence/supply_chain.py                                113     95    16%   26-28, 35-47, 52-73, 80-98, 109-206
src/gencode_gov/governance/__init__.py                                    2      0   100%
src/gencode_gov/governance/charter_loader.py                             74     47    36%   25-28, 39-42, 46, 50-58, 62-83, 88-100
src/gencode_gov/governance/enforcement.py                                80     51    36%   40-41, 54, 63, 67-103, 113-131
src/gencode_gov/governance/policy_loader.py                             102     60    41%   30, 34, 38, 48, 57-67, 72-75, 78, 81, 84, 87, 90, 93, 97-110, 115-136
src/gencode_gov/integrations/__init__.py                                  2      0   100%
src/gencode_gov/integrations/_model_impl/__init__.py                      0      0   100%
src/gencode_gov/integrations/_model_impl/code_llama/__init__.py           0      0   100%
src/gencode_gov/integrations/_model_impl/code_llama/adapter.py            5      1    80%   13
src/gencode_gov/integrations/_model_impl/deepseek_coder/__init__.py       0      0   100%
src/gencode_gov/integrations/_model_impl/deepseek_coder/adapter.py        5      1    80%   13
src/gencode_gov/integrations/_model_impl/openai_o/__init__.py             0      0   100%
src/gencode_gov/integrations/_model_impl/openai_o/adapter.py              5      1    80%   13
src/gencode_gov/integrations/_model_impl/qwen_coder/__init__.py           0      0   100%
src/gencode_gov/integrations/_model_impl/qwen_coder/adapter.py            5      1    80%   13
src/gencode_gov/integrations/agents/__init__.py                           2      2     0%   3-5
src/gencode_gov/integrations/agents/aider.py                              2      2     0%   3-5
src/gencode_gov/integrations/agents/amazon_q.py                           2      2     0%   3-5
src/gencode_gov/integrations/agents/claude_code.py                        2      2     0%   3-5
src/gencode_gov/integrations/agents/cline.py                              2      2     0%   3-5
src/gencode_gov/integrations/agents/codex_openai.py                       2      2     0%   3-5
src/gencode_gov/integrations/agents/continue_agent.py                     2      2     0%   3-5
src/gencode_gov/integrations/agents/cursor.py                             2      2     0%   3-5
src/gencode_gov/integrations/agents/devin.py                              2      2     0%   3-5
src/gencode_gov/integrations/agents/gemini.py                             2      2     0%   3-5
src/gencode_gov/integrations/agents/gemini_cli.py                         2      2     0%   3-5
src/gencode_gov/integrations/agents/github_copilot.py                     2      2     0%   3-5
src/gencode_gov/integrations/agents/gpt.py                                2      2     0%   3-5
src/gencode_gov/integrations/agents/jetbrains_ai.py                       2      2     0%   3-5
src/gencode_gov/integrations/agents/replit_agent.py                       2      2     0%   3-5
src/gencode_gov/integrations/agents/sourcegraph_cody.py                   2      2     0%   3-5
src/gencode_gov/integrations/agents/tabnine.py                            2      2     0%   3-5
src/gencode_gov/integrations/agents/windsurf.py                           2      2     0%   3-5
src/gencode_gov/integrations/base.py                                     27      2    93%   49-50
src/gencode_gov/integrations/generic_agents/__init__.py                   0      0   100%
src/gencode_gov/integrations/generic_agents/adapter.py                   15      5    67%   29, 38, 41, 45-46
src/gencode_gov/integrations/models/__init__.py                          50     28    44%   59, 64-104
src/gencode_gov/integrations/models/_openai_compatible.py               117     81    31%   39-40, 44-47, 56, 59-62, 65-68, 72-80, 83-101, 108-203
src/gencode_gov/integrations/models/claude/__init__.py                    0      0   100%
src/gencode_gov/integrations/models/claude/adapter.py                    82     51    38%   50-51, 55, 70, 73-76, 79-82, 85-189
src/gencode_gov/integrations/models/code-llama/__init__.py                0      0   100%
src/gencode_gov/integrations/models/code-llama/adapter.py                 2      2     0%   3-5
src/gencode_gov/integrations/models/deepseek-coder/__init__.py            0      0   100%
src/gencode_gov/integrations/models/deepseek-coder/adapter.py             2      2     0%   3-5
src/gencode_gov/integrations/models/gemini/__init__.py                    0      0   100%
src/gencode_gov/integrations/models/gemini/adapter.py                    82     56    32%   29-30, 34, 43, 46-49, 52-55, 58-171
src/gencode_gov/integrations/models/gpt/__init__.py                       0      0   100%
src/gencode_gov/integrations/models/gpt/adapter.py                        5      1    80%   13
src/gencode_gov/integrations/models/kimi/__init__.py                      0      0   100%
src/gencode_gov/integrations/models/kimi/adapter.py                       5      1    80%   13
src/gencode_gov/integrations/models/openai-o/__init__.py                  0      0   100%
src/gencode_gov/integrations/models/openai-o/adapter.py                   2      2     0%   3-5
src/gencode_gov/integrations/models/qwen-coder/__init__.py                0      0   100%
src/gencode_gov/integrations/models/qwen-coder/adapter.py                 2      2     0%   3-5
src/gencode_gov/integrations/platforms/__init__.py                       11      5    55%   14, 19-22
src/gencode_gov/integrations/platforms/github_copilot/__init__.py         2      0   100%
src/gencode_gov/integrations/platforms/github_copilot/adapter.py         62     48    23%   27, 37, 41-47, 50-86, 97-113
src/gencode_gov/integrations/tsar/__init__.py                             2      0   100%
src/gencode_gov/integrations/tsar/adapter.py                            149    114    23%   43-45, 49, 58, 61-89, 92-103, 107-138, 142-248
src/gencode_gov/integrations/tsar/verifier.py                           144    110    24%   48-111, 124-127, 132-146, 150-154, 158-174, 181-184, 191-204, 221-244
src/gencode_gov/language_support/__init__.py                              2      0   100%
src/gencode_gov/language_support/compatibility.py                         2      2     0%   3-5
src/gencode_gov/language_support/detector.py                             88     60    32%   61-63, 67-75, 84-117, 125-129, 149-178
src/gencode_gov/language_support/language_profile_loader.py              75     45    40%   48-51, 55-58, 68-127
src/gencode_gov/language_support/registry.py                            100     60    40%   48-49, 52-55, 58, 61, 64, 67, 70, 74-102, 121-153
src/gencode_gov/language_support/tool_resolver.py                        48     18    62%   37, 41, 44, 70-100, 104-105
src/gencode_gov/orchestrator/__init__.py                                  2      0   100%
src/gencode_gov/orchestrator/lifecycle.py                                55     23    58%   124-128, 132-136, 140, 149-154, 157-162
src/gencode_gov/orchestrator/stage_manager.py                            39     21    46%   28-30, 34, 37-52, 55-58
src/gencode_gov/orchestrator/task_dispatcher.py                           2      2     0%   3-5
src/gencode_gov/policies/__init__.py                                      2      0   100%
src/gencode_gov/policies/advisory.py                                     32     12    62%   31, 38, 41, 49-63
src/gencode_gov/policies/blocking.py                                     49     24    51%   33, 37, 44, 47, 56-90, 95-97
src/gencode_gov/policies/exceptions.py                                  154    120    22%   34-36, 39, 43-48, 56, 59, 63-115, 119-182, 194-258
src/gencode_gov/projects/__init__.py                                      2      0   100%
src/gencode_gov/projects/loader.py                                       82     55    33%   33-34, 38-39, 43-56, 62-75, 80-107, 112-115
src/gencode_gov/projects/matcher.py                                      57     40    30%   25-41, 46-65, 70-79, 83-84
src/gencode_gov/reporting/__init__.py                                     2      0   100%
src/gencode_gov/reporting/html_reporter.py                               50     39    22%   15-40, 47-74, 130-131
src/gencode_gov/reporting/json_reporter.py                              105     83    21%   62-71, 79-204, 212-216
src/gencode_gov/reporting/markdown_reporter.py                           27     14    48%   30-62, 70-74
src/gencode_gov/reporting/sarif_reporter.py                              33     33     0%   3-94
src/gencode_gov/rules/__init__.py                                         2      0   100%
src/gencode_gov/rules/evaluator.py                                      108    108     0%   3-215
src/gencode_gov/rules/loader.py                                          90     53    41%   27-28, 32, 36, 40, 44, 48, 52, 65, 69-78, 83-91, 96-123
src/gencode_gov/rules/registry.py                                        59     38    36%   20-41, 44-47, 50, 53, 56, 59, 62, 65, 68, 71, 74, 79-85
src/gencode_gov/rules/validator.py                                      108     98     9%   23-46, 57-77, 82-193, 198-202
src/gencode_gov/security_audit/__init__.py                               15      0   100%
src/gencode_gov/security_audit/cli_dispatch.py                          180    154    14%   66, 70-71, 75-84, 88-91, 101-444
src/gencode_gov/security_audit/coverage.py                              242    138    43%   51-54, 67-76, 95-109, 113, 144, 158, 196-222, 225-246, 250, 290, 294-308, 322-340, 343-359, 363-376, 380, 397-398, 406-420, 437-440, 444-467, 471-473, 477-478, 482-486, 490-506, 511-523, 527-538
src/gencode_gov/security_audit/dispatcher.py                             89     48    46%   24-26, 75-77, 88-125, 139-141, 159-163, 173-186, 190-194
src/gencode_gov/security_audit/findings.py                              232     89    62%   55-58, 70-79, 84-85, 96-103, 107, 124, 134, 155-168, 172, 201-221, 225, 261-265, 268, 282, 298, 308, 362-379, 390-399, 410-411, 462-463, 543-548, 551-552, 560-573, 577, 585-586
src/gencode_gov/security_audit/governance_bridge.py                     114     94    18%   32-87, 95-126, 135-206, 216-229, 234-239
src/gencode_gov/security_audit/hunting.py                               292    235    20%   69, 94, 113-131, 135-146, 151-199, 204-231, 249-320, 336-442, 446-451, 455, 459, 466, 479-516, 520-522, 538-683, 695-749, 759-778, 792-799
src/gencode_gov/security_audit/orchestrator.py                          356    298    16%   41, 45-57, 73-78, 111-119, 122-130, 150-151, 161-177, 195-236, 244-250, 271-408, 420-559, 568-633, 642-702, 705-715, 722-756, 776-823
src/gencode_gov/security_audit/reassessment.py                          136    107    21%   55, 74-88, 101-304
src/gencode_gov/security_audit/reporting.py                             130    113    13%   23-45, 56-159, 164-259, 264-289, 294-317, 321-333, 345-365
src/gencode_gov/security_audit/runtime.py                               193    113    41%   28, 32-34, 49, 78-81, 84, 102, 139, 180-384, 408, 411-413, 429-448, 479-484, 487-514, 530-550, 566-594, 604-635
src/gencode_gov/security_audit/sandbox.py                               274    212    23%   34-37, 42-54, 70-74, 78, 93-140, 186-193, 197-216, 229-231, 235-244, 252-267, 280-391, 404-421, 433-534
src/gencode_gov/security_audit/taxonomy.py                               43     12    72%   439, 445-447, 450, 453-456, 459, 462, 465
src/gencode_gov/security_audit/validators.py                            349    316     9%   39-42, 47-63, 67-96, 100-116, 120-131, 136-267, 272-366, 371-388, 392-395, 399-402, 406-409, 414-504
src/gencode_gov/security_audit/verifier.py                              164    146    11%   40, 45-77, 96-100, 111-329, 340-371, 384-411, 423-457, 469-498, 510-538
src/gencode_gov/security_audit/worker_entry.py                           86     71    17%   29-169, 174-179, 183-193
src/gencode_gov/validation.py                                           150    150     0%   3-230
src/gencode_gov/verification/__init__.py                                  2      0   100%
src/gencode_gov/verification/architecture_verifier.py                   136    118    13%   34-54, 58-94, 99-236
src/gencode_gov/verification/assess_dispatch.py                         103     93    10%   20-158
src/gencode_gov/verification/code_and_test_integrity.py                 189    164    13%   48-67, 71-78, 85-98, 102-112, 117-178, 190-223, 230-257, 267-340
src/gencode_gov/verification/diff_governance.py                         164    138    16%   33, 47-64, 69-121, 129-144, 156-284
src/gencode_gov/verification/domain_verifiers.py                        520    476     8%   56-64, 77-85, 93-101, 105-109, 113-128, 132-189, 193-217, 221-269, 273-308, 315-383, 387-421, 425-433, 437-480, 484-596, 604-617, 621-676, 687-933
src/gencode_gov/verification/engine.py                                  118     84    29%   38, 47-48, 58-121, 139-176, 184-188, 200-248
src/gencode_gov/verification/methods.py                                  27     10    63%   301-303, 308-314
src/gencode_gov/verification/profiles.py                                  2      2     0%   3-5
src/gencode_gov/verification/runners/__init__.py                          2      0   100%
src/gencode_gov/verification/runners/base.py                             21      0   100%
src/gencode_gov/verification/runners/mypy_runner.py                      52     39    25%   18-20, 24, 27-91
src/gencode_gov/verification/runners/polyglot_quality_runner.py          61     53    13%   13-126
src/gencode_gov/verification/runners/pytest_runner.py                    56     40    29%   22-24, 28, 31-121
src/gencode_gov/verification/runners/ruff_runner.py                      50     36    28%   19-21, 25, 28-93
src/gencode_gov/verification/runners/supply_chain_runner.py             180    151    16%   25-40, 45-62, 66-72, 76-91, 99, 102-182, 196, 199-350
src/gencode_gov/verification/runners/test_suite_runner.py               266    229    14%   38-53, 58-100, 107-119, 123-167, 175-193, 200-202, 206, 209-234, 254-265, 268-310, 323-388, 401-454, 467-569, 594-616
src/gencode_gov/verification/runners/tsar_runner.py                      45     30    33%   20-22, 26, 29-101
src/gencode_gov/verification/scenario_verifier.py                       266    241     9%   56-69, 74-123, 128-171, 180-215, 219-234, 238-250, 255-377, 385-463
---------------------------------------------------------------------------------------------------
TOTAL                                                                  9754   7438    24%

=========================== short test summary info ============================
ERROR tests/rules/positive/test_consolidated_governance_rules.py
ERROR tests/unit/security_audit/test_hunting_reassessment_and_cli.py
ERROR tests/unit/verification/test_cross_language_and_security_traceability.py
ERROR tests/unit/verification/test_engineering_governance_edge_branches.py
ERROR tests/unit/verification/test_engineering_governance_upgrades.py
!!!!!!!!!!!!!!!!!!! Interrupted: 5 errors during collection !!!!!!!!!!!!!!!!!!!!
5 errors in 1.90s
[EXIT 2]
```

## 9. New Modules 100% Coverage Gate
```text
/tmp/gov_venv/lib/python3.12/site-packages/coverage/inorout.py:560: CoverageWarning: Module gencode_gov.reporting.html_reporter was never imported. (module-not-imported); see https://coverage.readthedocs.io/en/7.17.5/messages.html#warning-module-not-imported
  self.warn(f"Module {pkg} was never imported.", slug="module-not-imported")
/tmp/gov_venv/lib/python3.12/site-packages/coverage/inorout.py:560: CoverageWarning: Module gencode_gov.reporting.sarif_reporter was never imported. (module-not-imported); see https://coverage.readthedocs.io/en/7.17.5/messages.html#warning-module-not-imported
  self.warn(f"Module {pkg} was never imported.", slug="module-not-imported")
/tmp/gov_venv/lib/python3.12/site-packages/coverage/inorout.py:560: CoverageWarning: Module gencode_gov.rules.evaluator was never imported. (module-not-imported); see https://coverage.readthedocs.io/en/7.17.5/messages.html#warning-module-not-imported
  self.warn(f"Module {pkg} was never imported.", slug="module-not-imported")
/tmp/gov_venv/lib/python3.12/site-packages/coverage/inorout.py:560: CoverageWarning: Module gencode_gov.validation was never imported. (module-not-imported); see https://coverage.readthedocs.io/en/7.17.5/messages.html#warning-module-not-imported
  self.warn(f"Module {pkg} was never imported.", slug="module-not-imported")
/tmp/gov_venv/lib/python3.12/site-packages/coverage/inorout.py:560: CoverageWarning: Module gencode_gov.verification.assess_dispatch was never imported. (module-not-imported); see https://coverage.readthedocs.io/en/7.17.5/messages.html#warning-module-not-imported
  self.warn(f"Module {pkg} was never imported.", slug="module-not-imported")
/tmp/gov_venv/lib/python3.12/site-packages/coverage/inorout.py:560: CoverageWarning: Module gencode_gov.verification.diff_governance was never imported. (module-not-imported); see https://coverage.readthedocs.io/en/7.17.5/messages.html#warning-module-not-imported
  self.warn(f"Module {pkg} was never imported.", slug="module-not-imported")
/tmp/gov_venv/lib/python3.12/site-packages/coverage/inorout.py:560: CoverageWarning: Module gencode_gov.verification.domain_verifiers was never imported. (module-not-imported); see https://coverage.readthedocs.io/en/7.17.5/messages.html#warning-module-not-imported
  self.warn(f"Module {pkg} was never imported.", slug="module-not-imported")
/tmp/gov_venv/lib/python3.12/site-packages/coverage/inorout.py:560: CoverageWarning: Module gencode_gov.verification.methods was never imported. (module-not-imported); see https://coverage.readthedocs.io/en/7.17.5/messages.html#warning-module-not-imported
  self.warn(f"Module {pkg} was never imported.", slug="module-not-imported")
/tmp/gov_venv/lib/python3.12/site-packages/coverage/inorout.py:560: CoverageWarning: Module gencode_gov.verification.runners.polyglot_quality_runner was never imported. (module-not-imported); see https://coverage.readthedocs.io/en/7.17.5/messages.html#warning-module-not-imported
  self.warn(f"Module {pkg} was never imported.", slug="module-not-imported")

==================================== ERRORS ====================================
_ ERROR collecting tests/unit/verification/test_engineering_governance_upgrades.py _
ImportError while importing test module '/home/runner/work/GENCODE-GOV/GENCODE-GOV/tests/unit/verification/test_engineering_governance_upgrades.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
tests/unit/verification/test_engineering_governance_upgrades.py:14: in <module>
    from gencode_gov.cli_extensions import (
src/gencode_gov/cli_extensions.py:17: in <module>
    from gencode_gov.language_support.language_profile_loader import load_language_profiles
E   ImportError: cannot import name 'load_language_profiles' from 'gencode_gov.language_support.language_profile_loader' (/home/runner/work/GENCODE-GOV/GENCODE-GOV/src/gencode_gov/language_support/language_profile_loader.py)
_ ERROR collecting tests/unit/verification/test_engineering_governance_edge_branches.py _
ImportError while importing test module '/home/runner/work/GENCODE-GOV/GENCODE-GOV/tests/unit/verification/test_engineering_governance_edge_branches.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
tests/unit/verification/test_engineering_governance_edge_branches.py:14: in <module>
    from gencode_gov.cli_extensions import (
src/gencode_gov/cli_extensions.py:17: in <module>
    from gencode_gov.language_support.language_profile_loader import load_language_profiles
E   ImportError: cannot import name 'load_language_profiles' from 'gencode_gov.language_support.language_profile_loader' (/home/runner/work/GENCODE-GOV/GENCODE-GOV/src/gencode_gov/language_support/language_profile_loader.py)

---------- coverage: platform linux, python 3.12.16-final-0 ----------
Name                                                      Stmts   Miss  Cover   Missing
---------------------------------------------------------------------------------------
src/gencode_gov/assessment/drift.py                          92     65    29%   35, 49-89, 108-173
src/gencode_gov/cli_extensions.py                           118    105    11%   18-214
src/gencode_gov/evidence/attestation.py                     157    122    22%   56, 101-107, 111-122, 137-215, 237-325
src/gencode_gov/verification/architecture_verifier.py       136    118    13%   34-54, 58-94, 99-236
src/gencode_gov/verification/code_and_test_integrity.py     189    164    13%   48-67, 71-78, 85-98, 102-112, 117-178, 190-223, 230-257, 267-340
---------------------------------------------------------------------------------------
TOTAL                                                       692    574    17%

FAIL Required test coverage of 100% not reached. Total coverage: 17.05%
=========================== short test summary info ============================
ERROR tests/unit/verification/test_engineering_governance_upgrades.py
ERROR tests/unit/verification/test_engineering_governance_edge_branches.py
!!!!!!!!!!!!!!!!!!! Interrupted: 2 errors during collection !!!!!!!!!!!!!!!!!!!!
[EXIT 2]
```

## 10. Repository Governance Validation (gencode-gov validate --json)
```text
Traceback (most recent call last):
  File "/tmp/gov_venv/bin/gencode-gov", line 6, in <module>
    sys.exit(main())
             ^^^^^^
  File "/home/runner/work/GENCODE-GOV/GENCODE-GOV/src/gencode_gov/cli.py", line 1271, in main
    parser = build_parser()
             ^^^^^^^^^^^^^^
  File "/home/runner/work/GENCODE-GOV/GENCODE-GOV/src/gencode_gov/cli.py", line 1264, in build_parser
    from gencode_gov.cli_extensions import register_extended_subcommands
  File "/home/runner/work/GENCODE-GOV/GENCODE-GOV/src/gencode_gov/cli_extensions.py", line 17, in <module>
    from gencode_gov.language_support.language_profile_loader import load_language_profiles
ImportError: cannot import name 'load_language_profiles' from 'gencode_gov.language_support.language_profile_loader' (/home/runner/work/GENCODE-GOV/GENCODE-GOV/src/gencode_gov/language_support/language_profile_loader.py). Did you mean: 'load_language_profile'?
[EXIT 1]
```

## 11. Polyglot Tool Matrix Inspection (gencode-gov inspect . --tools --json)
```text
Traceback (most recent call last):
  File "/tmp/gov_venv/bin/gencode-gov", line 6, in <module>
    sys.exit(main())
             ^^^^^^
  File "/home/runner/work/GENCODE-GOV/GENCODE-GOV/src/gencode_gov/cli.py", line 1271, in main
    parser = build_parser()
             ^^^^^^^^^^^^^^
  File "/home/runner/work/GENCODE-GOV/GENCODE-GOV/src/gencode_gov/cli.py", line 1264, in build_parser
    from gencode_gov.cli_extensions import register_extended_subcommands
  File "/home/runner/work/GENCODE-GOV/GENCODE-GOV/src/gencode_gov/cli_extensions.py", line 17, in <module>
    from gencode_gov.language_support.language_profile_loader import load_language_profiles
ImportError: cannot import name 'load_language_profiles' from 'gencode_gov.language_support.language_profile_loader' (/home/runner/work/GENCODE-GOV/GENCODE-GOV/src/gencode_gov/language_support/language_profile_loader.py). Did you mean: 'load_language_profile'?
[EXIT 1]
```

## 12. Clean Working Tree Check
```text
commit 125a78359dccf274a2b4ad4c73f032fcc68fd207
Author: github-actions <github-actions-bot>
Date:   Fri Nov 27 23:35:15 2026 +0000

    feat(governance): integrate verified engineering governance and verification upgrades

 .gencode-gov/architecture-contracts.yaml           |  39 +
 .gencode-gov/evidence/.gitkeep                     |   0
 .gencode-gov/project.yaml                          |   4 +-
 .gencode-gov/reports/.gitkeep                      |   0
 .gencode-gov/state/.gitkeep                        |   0
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
 src/gencode_gov/cli.py                             | 104 ++-
 src/gencode_gov/cli_extensions.py                  | 214 +++++
 src/gencode_gov/evidence/attestation.py            | 329 ++++++++
 src/gencode_gov/evidence/store.py                  |   7 +
 src/gencode_gov/language_support/detector.py       |  51 +-
 src/gencode_gov/reporting/html_reporter.py         | 130 ++-
 src/gencode_gov/reporting/markdown_reporter.py     |   3 +-
 src/gencode_gov/reporting/sarif_reporter.py        |  94 +++
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
 .../verification/code_and_test_integrity.py        | 340 ++++++++
 src/gencode_gov/verification/diff_governance.py    | 294 +++++++
 src/gencode_gov/verification/domain_verifiers.py   | 933 +++++++++++++++++++++
 src/gencode_gov/verification/methods.py            | 307 +++++--
 .../runners/polyglot_quality_runner.py             | 131 +++
 staging/part_01                                    | 550 ------------
 staging/part_02                                    | 536 ------------
 staging/part_03                                    | 476 -----------
 staging/part_04                                    | 559 ------------
 staging/part_05                                    | 698 ---------------
 staging/part_06                                    | 535 ------------
 staging/part_07                                    | 535 ------------
 staging/part_08                                    | 437 ----------
 staging/part_09                                    | 541 ------------
 staging/part_10                                    | 140 ----
 .../test_end_to_end_governance_excellence.py       | 139 +++
 tests/unit/cli/test_install.py                     |   2 +-
 .../test_engineering_governance_edge_branches.py   | 674 +++++++++++++++
 .../test_engineering_governance_upgrades.py        | 918 ++++++++++++++++++++
 62 files changed, 6934 insertions(+), 5539 deletions(-)
[EXIT 0]
```

## 13. Diff-Check Without --allow-protected (Protected File Inventory)
```json
Traceback (most recent call last):
  File "/tmp/gov_venv/bin/gencode-gov", line 6, in <module>
    sys.exit(main())
             ^^^^^^
  File "/home/runner/work/GENCODE-GOV/GENCODE-GOV/src/gencode_gov/cli.py", line 1271, in main
    parser = build_parser()
             ^^^^^^^^^^^^^^
  File "/home/runner/work/GENCODE-GOV/GENCODE-GOV/src/gencode_gov/cli.py", line 1264, in build_parser
    from gencode_gov.cli_extensions import register_extended_subcommands
  File "/home/runner/work/GENCODE-GOV/GENCODE-GOV/src/gencode_gov/cli_extensions.py", line 17, in <module>
    from gencode_gov.language_support.language_profile_loader import load_language_profiles
ImportError: cannot import name 'load_language_profiles' from 'gencode_gov.language_support.language_profile_loader' (/home/runner/work/GENCODE-GOV/GENCODE-GOV/src/gencode_gov/language_support/language_profile_loader.py). Did you mean: 'load_language_profile'?
```

## 14. Diff-Check With --allow-protected (Compatibility & Schema Gate)
```text
Traceback (most recent call last):
  File "/tmp/gov_venv/bin/gencode-gov", line 6, in <module>
    sys.exit(main())
             ^^^^^^
  File "/home/runner/work/GENCODE-GOV/GENCODE-GOV/src/gencode_gov/cli.py", line 1271, in main
    parser = build_parser()
             ^^^^^^^^^^^^^^
  File "/home/runner/work/GENCODE-GOV/GENCODE-GOV/src/gencode_gov/cli.py", line 1264, in build_parser
    from gencode_gov.cli_extensions import register_extended_subcommands
  File "/home/runner/work/GENCODE-GOV/GENCODE-GOV/src/gencode_gov/cli_extensions.py", line 17, in <module>
    from gencode_gov.language_support.language_profile_loader import load_language_profiles
ImportError: cannot import name 'load_language_profiles' from 'gencode_gov.language_support.language_profile_loader' (/home/runner/work/GENCODE-GOV/GENCODE-GOV/src/gencode_gov/language_support/language_profile_loader.py). Did you mean: 'load_language_profile'?
[EXIT 1]
```

## 15. Longitudinal Drift Snapshot (gencode-gov drift . --no-persist --json)
```text
Traceback (most recent call last):
  File "/tmp/gov_venv/bin/gencode-gov", line 6, in <module>
    sys.exit(main())
             ^^^^^^
  File "/home/runner/work/GENCODE-GOV/GENCODE-GOV/src/gencode_gov/cli.py", line 1271, in main
    parser = build_parser()
             ^^^^^^^^^^^^^^
  File "/home/runner/work/GENCODE-GOV/GENCODE-GOV/src/gencode_gov/cli.py", line 1264, in build_parser
    from gencode_gov.cli_extensions import register_extended_subcommands
  File "/home/runner/work/GENCODE-GOV/GENCODE-GOV/src/gencode_gov/cli_extensions.py", line 17, in <module>
    from gencode_gov.language_support.language_profile_loader import load_language_profiles
ImportError: cannot import name 'load_language_profiles' from 'gencode_gov.language_support.language_profile_loader' (/home/runner/work/GENCODE-GOV/GENCODE-GOV/src/gencode_gov/language_support/language_profile_loader.py). Did you mean: 'load_language_profile'?
[EXIT 1]
```

## 16. Self-Governance Assessment Summary (gencode-gov assess . --json)
```text
Traceback (most recent call last):
  File "<stdin>", line 4, in <module>
  File "/opt/hostedtoolcache/Python/3.12.16/x64/lib/python3.12/json/__init__.py", line 346, in loads
    return _default_decoder.decode(s)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.12.16/x64/lib/python3.12/json/decoder.py", line 338, in decode
    obj, end = self.raw_decode(s, idx=_w(s, 0).end())
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.12.16/x64/lib/python3.12/json/decoder.py", line 356, in raw_decode
    raise JSONDecodeError("Expecting value", s, err.value) from None
json.decoder.JSONDecodeError: Expecting value: line 1 column 1 (char 0)
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
creating '/tmp/dist_wheel/.tmp-p6enlb2p/gencode_gov-0.1.0-py3-none-any.whl' and adding 'build/bdist.linux-x86_64/wheel' to it
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
Traceback (most recent call last):
  File "/tmp/wheel_venv/bin/gencode-gov", line 8, in <module>
    sys.exit(main())
             ^^^^^^
  File "/tmp/wheel_venv/lib/python3.12/site-packages/gencode_gov/cli.py", line 1271, in main
    parser = build_parser()
             ^^^^^^^^^^^^^^
  File "/tmp/wheel_venv/lib/python3.12/site-packages/gencode_gov/cli.py", line 1264, in build_parser
    from gencode_gov.cli_extensions import register_extended_subcommands
  File "/tmp/wheel_venv/lib/python3.12/site-packages/gencode_gov/cli_extensions.py", line 17, in <module>
    from gencode_gov.language_support.language_profile_loader import load_language_profiles
ImportError: cannot import name 'load_language_profiles' from 'gencode_gov.language_support.language_profile_loader' (/tmp/wheel_venv/lib/python3.12/site-packages/gencode_gov/language_support/language_profile_loader.py). Did you mean: 'load_language_profile'?
[EXIT 1]
```

## 17b. Cross-Python Wheel & Test Compatibility (Python 3.11 & 3.13)
```text
=== Verifying on Python 3.11.18 ===

[notice] A new release of pip is available: 24.0 -> 26.3
[notice] To update, run: python3.11 -m pip install --upgrade pip
Traceback (most recent call last):
  File "/tmp/venv_python3.11/bin/gencode-gov", line 8, in <module>
    sys.exit(main())
             ^^^^^^
  File "/tmp/venv_python3.11/lib/python3.11/site-packages/gencode_gov/cli.py", line 1271, in main
    parser = build_parser()
             ^^^^^^^^^^^^^^
  File "/tmp/venv_python3.11/lib/python3.11/site-packages/gencode_gov/cli.py", line 1264, in build_parser
    from gencode_gov.cli_extensions import register_extended_subcommands
  File "/tmp/venv_python3.11/lib/python3.11/site-packages/gencode_gov/cli_extensions.py", line 17, in <module>
    from gencode_gov.language_support.language_profile_loader import load_language_profiles
ImportError: cannot import name 'load_language_profiles' from 'gencode_gov.language_support.language_profile_loader' (/tmp/venv_python3.11/lib/python3.11/site-packages/gencode_gov/language_support/language_profile_loader.py)
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
=== git diff --stat origin/main..HEAD ===
 .gencode-gov/architecture-contracts.yaml           |  39 +
 .gencode-gov/evidence/.gitkeep                     |   0
 .gencode-gov/project.yaml                          |   4 +-
 .gencode-gov/reports/.gitkeep                      |   0
 .gencode-gov/state/.gitkeep                        |   0
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
 src/gencode_gov/cli.py                             | 104 ++-
 src/gencode_gov/cli_extensions.py                  | 214 +++++
 src/gencode_gov/evidence/attestation.py            | 329 ++++++++
 src/gencode_gov/evidence/store.py                  |   7 +
 src/gencode_gov/language_support/detector.py       |  51 +-
 src/gencode_gov/reporting/html_reporter.py         | 130 ++-
 src/gencode_gov/reporting/markdown_reporter.py     |   3 +-
 src/gencode_gov/reporting/sarif_reporter.py        |  94 +++
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
 .../verification/code_and_test_integrity.py        | 340 ++++++++
 src/gencode_gov/verification/diff_governance.py    | 294 +++++++
 src/gencode_gov/verification/domain_verifiers.py   | 933 +++++++++++++++++++++
 src/gencode_gov/verification/methods.py            | 307 +++++--
 .../runners/polyglot_quality_runner.py             | 131 +++
 staging/part_01                                    | 550 ------------
 staging/part_02                                    | 536 ------------
 staging/part_03                                    | 476 -----------
 staging/part_04                                    | 559 ------------
 staging/part_05                                    | 698 ---------------
 staging/part_06                                    | 535 ------------
 staging/part_07                                    | 535 ------------
 staging/part_08                                    | 437 ----------
 staging/part_09                                    | 541 ------------
 staging/part_10                                    | 140 ----
 .../test_end_to_end_governance_excellence.py       | 139 +++
 tests/unit/cli/test_install.py                     |   2 +-
 .../test_engineering_governance_edge_branches.py   | 674 +++++++++++++++
 .../test_engineering_governance_upgrades.py        | 918 ++++++++++++++++++++
 62 files changed, 6934 insertions(+), 5539 deletions(-)

=== git diff --name-status origin/main..HEAD ===
A	.gencode-gov/architecture-contracts.yaml
D	.gencode-gov/evidence/.gitkeep
M	.gencode-gov/project.yaml
D	.gencode-gov/reports/.gitkeep
D	.gencode-gov/state/.gitkeep
D	.github/workflows/recon_full_audit.yml
M	AGENTS.md
M	docs/evidence/EVIDENCE_MODEL.md
A	docs/governance/ENGINEERING_GAP_REGISTER.md
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
A	tests/unit/verification/test_engineering_governance_edge_branches.py
A	tests/unit/verification/test_engineering_governance_upgrades.py

Audited 1031 tracked files: 0 staging residue, 0 legacy tokens.
[EXIT 0]
```

## 20. Final Integration Commit & Gate Verdict
- Integrated commit on feat/integrate-staged-governance: 125a78359dccf274a2b4ad4c73f032fcc68fd207
- Overall FAIL flag: 1
- Fast-forward push to origin/feat/integrate-staged-governance: SKIPPED (FAIL=1)
