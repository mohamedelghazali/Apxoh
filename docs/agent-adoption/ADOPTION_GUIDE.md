# Apxoh Agent Adoption Guide

**Version:** 1.0  
**Status:** Adoption specification; implementation and integration claims require verification  
**Last updated:** 2026-11-01

---

## 1. What Adoption Means

Adopting Apxoh does **not** mean an agent obeys automatically.

Adoption is a five-level progression. Each level requires evidence:

| Level | Meaning | Evidence required |
| :--- | :--- | :--- |
| 1. Installed | Files present on disk | Filesystem check |
| 2. Discoverable | Agent can locate skill files | Discovery check |
| 3. Activated | Instructions loaded into agent context | Platform-specific activation evidence |
| 4. Configured | Agent settings bind to Apxoh | Configuration inspection |
| 5. Verified | Behavioral verification passed | Repeatable test run and independently validated evidence |

Apxoh must not claim an integration is verified merely because configuration files exist. Level 5 requires an implemented verification procedure, reproducible results, and authenticated evidence. Until those mechanisms are implemented and exercised, the level is **not established**.

## 2. Prerequisites

- Apxoh CLI installed from the repository root.
- A valid `.arkhon/project.yaml` in the governed project.
- TSAR available for security verification where the security gate requires it.

The `doctor` command checks installation prerequisites; a successful doctor run alone does not prove agent adoption or behavioral compliance.

## 3. Adoption by Integration Type

### 3.1 Models

The intended integration layout may provide:

- `integrations/models/<model>/config.yaml` — endpoint, model name, and authentication configuration.
- `integrations/models/<model>/prompts/system.md` — system instructions.
- `integrations/models/<model>/prompts/governance-injection.md` — task-context template.
- `integrations/models/<model>/skill-bindings.yaml` — skill-to-domain bindings.

These paths and capabilities must be checked against the actual repository tree before use. Do not infer that a provider integration exists because it is listed in documentation.

Adoption procedure, where the integration exists:

1. Install the integration directory in the agent platform.
2. Configure the endpoint and credentials using the platform's secret-management mechanism.
3. Load the system instructions according to platform capabilities.
4. Apply the governance context template to tasks.
5. Run the supported Apxoh verification procedure and retain its evidence.

### 3.2 Platforms (GitHub Copilot)

Platform-level configuration does not by itself prove model behavior. Apxoh may report only the highest level supported by an implemented and repeatable check. Do not claim level 4 or level 5 until the corresponding verifier and evidence are present.

### 3.3 Generic Agents

Generic instructions can support installation, discovery, or activation. A generic agent must not be described as behaviorally verified without a platform-independent test harness and independently checked results.

## 4. What the Agent Must Do

When operating under Apxoh, an agent is instructed to:

1. Read the applicable governance files.
2. Never claim verification without evidence.
3. Preserve governance files and protections.
4. Never bypass a mandatory gate.
5. Report failures honestly.
6. Escalate to human review when required.

These are governance requirements. Their presence in a prompt does not prove that a model follows them.

## 5. What Apxoh Is Intended to Do

Apxoh is designed to provide independent verification, structured remediation feedback, evidence records, and human escalation. Each capability must be assessed against the implemented code and operational controls; this guide is not proof that every capability is deployed.

## 6. Adoption Checklist

- [ ] `.arkhon/project.yaml` exists and is valid.
- [ ] Project profile is explicitly chosen or resolved by a verified mechanism.
- [ ] `AGENTS.md` is present where required.
- [ ] `SECURITY_AGENTS.md` is present where required.
- [ ] The relevant integration files exist.
- [ ] Platform instructions are demonstrably loaded.
- [ ] TSAR is available when required.
- [ ] `arkhon doctor` has been run and its result retained.
- [ ] `arkhon inspect` reports expected languages and profile.
- [ ] A supported verification run produced evidence.
- [ ] Evidence authenticity and signatures are verified when required by policy.

## 7. Reference

- `docs/agent-adoption/COMPATIBILITY_MATRIX.md`
- `AGENTS.md`
- `SECURITY_AGENTS.md`
- `integrations/models/<model>/README.md` (if present)
- `integrations/platforms/<platform>/README.md` (if present)

---

**End of Guide**
