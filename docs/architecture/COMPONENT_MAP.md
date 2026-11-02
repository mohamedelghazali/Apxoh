# Apxoh Component Map

**Version:** 1.0
**Status:** Active
**Last updated:** 2026-11-01

---

## 1. The Full Picture

```
┌─────────────────────────────────────────────────────────────────┐
│                         CLI (argparse)                          │
│   version · doctor · validate · inspect · audit · assess       │
│   report · verify                                               │
└─────────────────────────────────────────────────────────────────┘
                                 │
        ┌────────────────────────┼──────────────────────────┐
        ▼                        ▼                          ▼
┌───────────────┐       ┌────────────────┐       ┌────────────────┐
│  Governance   │       │   Rules        │       │  Verification  │
│  · charter    │       │   · loader     │       │  · engine      │
│  · policy     │       │   · validator  │       │  · runners     │
│  · enforcement│       │   · registry   │       │  · base        │
└───────────────┘       └────────────────┘       └────────────────┘
        │                        │                          │
        └────────────┬───────────┴──────────┬───────────────┘
                     ▼                      ▼
              ┌─────────────┐        ┌─────────────┐
              │  Evidence   │        │ Assessment  │
              │  · collector│        │ · scorer    │
              │  · integrity│        │ · gates     │
              │  · store    │        │ · decision  │
              └─────────────┘        └─────────────┘
                     │                      │
                     └──────────┬───────────┘
                                ▼
                       ┌─────────────────┐
                       │  Reporting      │
                       │  · json         │
                       │  · markdown     │
                       │  · templates    │
                       └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │  Orchestrator   │
                       │  · lifecycle    │
                       │  · stage mgr    │
                       └─────────────────┘
```

---

## 2. Core Modules

### 2.1 `src/arkhon/config.py`

- Loads `manifest/index.yaml` and all referenced manifest files.
- Exposes a single `Manifest` dataclass.
- Cached via `get_manifest()`.

### 2.2 `src/arkhon/core/`

- `constants.py` — status enums, domain prefixes.
- `errors.py` — exception hierarchy with stable codes.
- `logging.py` — structured logging (JSON or text).

### 2.3 `src/arkhon/governance/`

- `charter_loader.py` — loads the 12 principles.
- `policy_loader.py` — loads blocking/advisory/exception policies.
- `enforcement.py` — evaluates rules into outcomes.

### 2.4 `src/arkhon/rules/`

- `loader.py` — reads YAML rule files, deduplicates IDs.
- `validator.py` — schema + semantic validation.
- `registry.py` — indexed lookup by id, domain, severity, status.

### 2.5 `src/arkhon/verification/`

- `engine.py` — runs a sequence of runners, produces evidence.
- `runners/base.py` — abstract Runner.
- `runners/pytest_runner.py` — JUnit XML.
- `runners/ruff_runner.py` — ruff JSON.
- `runners/mypy_runner.py` — mypy text.
- `runners/tsar_runner.py` — TSAR delegation.

### 2.6 `src/arkhon/evidence/`

- `collector.py` — builds evidence drafts, computes SHA-256.
- `integrity.py` — verifies hashes, freshness, commit binding.
- `store.py` — append-only storage under `.arkhon/evidence/`.

### 2.7 `src/arkhon/assessment/`

- `scorer.py` — weighted 100-point score.
- `gates.py` — aggregate outcomes into gate verdicts.
- `decision.py` — final release decision.

### 2.8 `src/arkhon/projects/`

- `loader.py` — loads `projects/<name>/*.yaml`.
- `matcher.py` — explicit or inferred profile matching.

### 2.9 `src/arkhon/language_support/`

- `registry.py` — loads `languages/registry.yaml`.
- `detector.py` — walks a project, counts files by extension.
- `tool_resolver.py` — checks tool availability.

### 2.10 `src/arkhon/integrations/`

- `base.py` — Integration ABC.
- `tsar/adapter.py` — calls TSAR CLI.
- `tsar/verifier.py` — verifies TSAR evidence.

### 2.11 `src/arkhon/reporting/`

- `json_reporter.py` — produces `report.json`.
- `markdown_reporter.py` — produces `report.md`.
- `templates/engineering_quality.py` — 16 standard documents.

### 2.12 `src/arkhon/orchestrator/`

- `lifecycle.py` — 10 stages, forward/backward.
- `stage_manager.py` — checks exit criteria before advancing.

### 2.13 `src/arkhon/policies/`

- `blocking.py` — blocking policy evaluation.
- `advisory.py` — advisory notes.
- `exceptions.py` — exception registry (add, expire, active).

---

## 3. Data Files

### 3.1 `manifest/`

- Split into 7 files, indexed by `index.yaml`.
- The single source of truth for system identity.

### 3.2 `system/`

- Charter (Markdown + YAML).
- Policies (blocking / advisory / exceptions).
- Lifecycle, enforcement model, risk classification.

### 3.3 `rules/`

- 16 domains (one directory each).
- YAML files, one rule per file.
- `_deprecated/` and `_archived/` for lifecycle.

### 3.4 `languages/`

- `registry.yaml` — 9 languages.
- `python/`, `javascript/`, `typescript/`, `go/`, `rust/`, etc.
- Each language: `language-profile.yaml`, `tools.yaml`, `testing.yaml`, `security.yaml`.

### 3.5 `projects/`

- 8 profiles (universal, web-application, api-service, …).
- Each profile: `profile.yaml`, `rules.yaml`, `gates.yaml`.

### 3.6 `schemas/`

- 9 JSON Schemas (rule, evidence, finding, assessment, exception, report, project, state, integration-contract).

### 3.7 `integrations/`

- `models/` — 8 model directories.
- `platforms/` — 1 platform (github-copilot).
- `tsar/` — contract, evidence-mapping, adapter.
- `generic-agents/` — fallback.

### 3.8 `.arkhon/`

- `project.yaml` — Apxoh's own project declaration (self-governance).
- `config.yaml` — Apxoh's own runtime config.
- `evidence/` — where Apxoh's own evidence goes.
- `state/` — append-only state log.

---

## 4. Cross-References

| Question | File |
| :--- | :--- |
| What are the 12 principles? | `system/charter/ENGINEERING_CHARTER.md` |
| What are the 9 languages? | `languages/registry.yaml` |
| What are the 8 models? | `manifest/integrations.yaml` |
| What are the 10 stages? | `src/arkhon/orchestrator/lifecycle.py` |
| What are the 16 quality documents? | `reports/templates/engineering-quality/` |
| What are the 9 schemas? | `schemas/*.json` |
| What is the TSAR contract? | `integrations/tsar/contract.yaml` |
| What is the threat model? | `docs/threat-model/ARKHON_THREAT_MODEL.md` |
| What is the score model? | `src/arkhon/assessment/scorer.py` |

---

## 5. Dependency Order

Bottom to top — nothing depends on something above it:

```
core/  →  config  →  governance  →  rules
                         │
                         ▼
                    policies
                         │
                         ▼
                  verification  →  evidence
                         │              │
                         └──────┬───────┘
                                ▼
                           assessment
                                │
                    ┌───────────┼───────────┐
                    ▼           ▼           ▼
                 projects   language_support  integrations
                    └───────────┼───────────┘
                                ▼
                           reporting
                                │
                                ▼
                          orchestrator
                                │
                                ▼
                              cli
```

No layer may import from a layer above it. This is enforced by mypy and by review.

---

**End of Document**
