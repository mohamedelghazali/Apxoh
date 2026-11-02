# Apxoh Repository Map

**Version:** 1.1  
**Status:** Active  
**Last updated:** 2026-11-02

This map describes repository paths present in the current source tree. It is a navigation guide, not a claim that every listed integration or tool has been deployed, enabled, or independently verified.

---

## 1. Top-Level Structure

~~~text
Apxoh/
├── .arkhon/                 # Repository self-governance configuration/state
├── .devcontainer/           # Development-container configuration
├── .github/                 # Workflows, templates, CODEOWNERS and automation
├── agents/                  # Agent role definitions and bindings
├── archive/                 # Historical and superseded material
├── benchmarks/              # Benchmark plans and supporting material
├── docs/                    # Technical and governance documentation
├── examples/                # Example projects
├── integrations/            # Agent/editor/platform integration packages
├── languages/               # Language registry, profiles, tools and rules
├── manifest/                # Split system and product registries
├── migrations/              # Schema migration guidance and artifacts
├── projects/                # Project-type profiles
├── reports/                 # Report examples and templates
├── rules/                   # Global engineering rule catalog
├── schemas/                 # JSON Schema contracts
├── scripts/                 # Validation and maintenance automation
├── skills/                  # Reusable agent-consumed skills
├── src/arkhon/              # Python package and CLI implementation
├── standards/               # Standards references
├── system/                  # Charter, governance, lifecycle and policies
├── tests/                   # Unit, integration, security and language tests
└── tools/                   # External-tool notes, generators, scanners, validators
~~~

Root-level files include the project README, installation and contribution guides, governance and security policies, version/changelog files, packaging metadata, and the Makefile.

## 2. Manifest

manifest/index.yaml is the entry point. It references these split registries:

| File | Purpose |
| :--- | :--- |
| system.yaml | System identity, runtime range, and founding decisions |
| products.yaml | Core, Agent Governance, and Assurance product definitions |
| integrations.yaml | Declared model, platform, security, and generic integrations |
| languages.yaml | Supported-language declarations |
| standards.yaml | External standards references |
| compatibility.yaml | Runtime, schema, and integration compatibility declarations |

The index is the navigation authority for the manifest. A registry declaration does not prove that an integration or language has passed runtime verification.

## 3. System Governance

system/ contains the engineering charter and governance documents:

- charter/ — founding engineering principles.
- governance/ — governance model, risk classification, and exception policy.
- lifecycle/ — software lifecycle definition.
- enforcement/ — enforcement model.
- policies/ — blocking, advisory, and exception policy files.
- risk-model/ — risk classification and criteria.

## 4. Rules

Global rules are stored one YAML file per rule under rules/<domain>/. The current catalog contains 20 global rules across these 16 domains:

api-integration, architecture, code-quality, database, devops, infrastructure, maintenance, observability, performance, privacy-compliance, release, reliability, requirements, scalability, software-security, and testing.

Python-specific rules are under languages/python/rules/. At the time of this update, the combined catalog contains 23 rules (20 global + 3 Python).

The repository's rule test currently discovers rules under rules/; do not infer that it also validates language-specific rule files or this map.

## 5. Languages and Project Profiles

- languages/registry.yaml declares Python, JavaScript, TypeScript, Java, C#, C++, Go, Rust, and Ruby.
- languages/<language>/ contains language-specific material. Registry maturity and actual tool availability must be checked before claiming complete language support.
- projects/<project-type>/ contains profile.yaml, rules.yaml, and gates.yaml for the current profiles: API service, desktop application, distributed system, enterprise, mobile application, safety-critical, universal, and web application.

## 6. Python Implementation

The package is under src/arkhon/:

| Package | Responsibility |
| :--- | :--- |
| core/ | Constants, errors, and logging |
| governance/ | Charter and policy loading/enforcement |
| rules/ | Rule loading, validation, registry, and evaluation |
| policies/ | Blocking, advisory, and exception handling |
| evidence/ | Evidence collection, integrity checks, and storage |
| assessment/ | Scoring, gate aggregation, and decisions |
| verification/ | Verification engine, profiles, and tool runners |
| orchestrator/ | Lifecycle and stage management |
| projects/ | Project profile loading and matching |
| language_support/ | Language registry, detection, and tool resolution |
| integrations/ | Agent/model adapters and TSAR adapter/verifier |
| reporting/ | JSON, Markdown, HTML reporting and templates |

The package exposes the arkhon command through pyproject.toml. Apxoh is the product name; arkhon is the Python package and CLI identifier.

## 7. Agent Skills, Roles, and Integrations

- skills/ contains eight skill directories covering governance, requirements, architecture, secure engineering, testing, performance, reliability, and release readiness.
- agents/ contains nine role directories, plus the role registry.
- integrations/models/ contains model-provider integration packages, including Gemini and GPT; the eight-model implementation registry is maintained separately in src/arkhon/integrations/models/.
- integrations/platforms/ contains platform integrations such as GitHub Copilot.
- integrations/generic-agents/ contains generic-agent guidance and the provider/tool adapters grouped by agent: Aider, Amazon Q, Claude Code, Cline, Codex OpenAI, Continue, Cursor, Devin, Gemini CLI, JetBrains AI, Replit Agent, Sourcegraph Cody, Tabnine, and Windsurf.
- integrations/tsar/ contains the separately versioned TSAR security-authority contract, adapter, verifier, and integration tests.

These directories document and implement integration surfaces at different levels. Their presence is not proof that every provider account, external service, or behavioral integration test is operational.

## 8. Schemas, Tools, and Standards

- schemas/ contains JSON Schema contracts for rules, evidence, findings, assessments, exceptions, reports, projects, state, and integration contracts.
- tools/external/ contains documentation for external tools.
- tools/generators/, tools/scanners/, and tools/validators/ contain supporting tool packages and documentation.
- tools/signing/ contains signing-related scripts; presence alone does not prove a configured signing identity or a verified release signature.
- standards/ holds standards references.
- migrations/ contains schema migration material.

## 9. Tests, Examples, and Reports

- tests/unit/ — unit tests.
- tests/integration/ — CLI, agent, model, platform, TSAR, orchestrator, and verification integration tests.
- tests/security/ — security-focused tests.
- tests/languages/ — language detection/profile tests and language fixtures.
- tests/fixtures/ — minimal and web-application fixtures.
- tests/installation/ — installation guidance and tests.
- examples/ — minimal, web-application, API-service, and enterprise examples.
- benchmarks/ — CLI startup, load, rule-evaluation, soak, and stress material.
- reports/templates/ — engineering-quality report templates.

A test file or fixture is not evidence that the corresponding test has been executed successfully. Refer to CI run records for execution status.

## 10. Documentation

Key documentation areas include:

- docs/architecture/ — system overview, component map, data flow, decision log, and glossary.
- docs/agent-adoption/ — adoption and compatibility guidance.
- docs/operations/ — incident response, runbook, and postmortem guidance.
- docs/rule-authoring/ — authoring guide, lifecycle, and examples.
- docs/threat-model/ — threat-model documents.
- docs/verification/ and docs/evidence/ — verification and evidence guidance.
- docs/i18n/ — internationalization policy and Arabic companion documents.

## 11. Navigation Rules

1. Use manifest/index.yaml to locate authoritative manifest data.
2. Use the rule YAML as the source of truth for rule behavior and metadata.
3. Treat documentation as design or usage guidance unless implementation and execution evidence establish the claimed behavior.
4. Treat agent instructions as guidance, not as a technical security boundary.
5. Update this map when top-level architecture or maintained directory responsibilities change.

---

**End of Repository Map**
