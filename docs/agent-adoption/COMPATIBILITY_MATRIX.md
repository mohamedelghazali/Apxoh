# Apxoh Agent Compatibility Matrix

**Version:** 1.1  
**Status:** Evidence-conscious inventory; no provider-wide behavioral verification is claimed  
**Last updated:** 2026-11-02

This matrix records the integrations declared by the repository. A registry entry, adapter file, prompt, or provider name is not proof that an external model is reachable, correctly configured, or behaviorally verified. Evidence must identify the exact model/platform version and reproducible test.

## 1. Model Integrations

| Model family | Provider | Declared in manifest | Evidence-backed adoption level | Notes |
| :--- | :--- | :---: | :--- | :--- |
| Claude | Anthropic | Yes | Not established here | Verify exact model and API configuration |
| OpenAI o | OpenAI | Yes | Not established here | Do not generalize across model versions |
| DeepSeek-Coder | DeepSeek | Yes | Not established here | Configuration is not behavioral verification |
| GPT | OpenAI | Yes | Not established here | Keep distinct from reasoning-model aliases |
| Gemini | Google | Yes | Not established here | Verify API and prompt behavior |
| Code Llama | Meta | Yes | Not established here | Verify local runtime and exact model |
| Qwen-Coder | Alibaba | Yes | Not established here | Verify exact model and deployment |
| Kimi | Moonshot | Yes | Not established here | Verify exact model and deployment |

The repository's structural contract tests are under `tests/integration/models/`. Passing them establishes only the structural properties asserted by those tests, not end-to-end provider behavior.

## 2. Platform Integrations

| Platform | Provider | Declared in manifest | Evidence-backed adoption level | Notes |
| :--- | :--- | :---: | :--- | :--- |
| GitHub Copilot | GitHub / Microsoft | Yes | Not established here | Apxoh cannot pin or observe the model selected internally by the platform |

## 3. Security Integration

| Integration | Intended role | Declared | Evidence condition |
| :--- | :--- | :---: | :--- |
| TSAR | Independent security verification | Yes | A required security check remains BLOCKED unless configured TSAR execution and evidence are validated for the target commit |

The TSAR contract is marked proposed in `integrations/tsar/contract.yaml`. Contract tests do not prove that a TSAR binary is installed or that a production audit has run.

## 4. Generic Agents

Generic-agent guidance is a fallback for unlisted platforms. Manual instruction application does not establish activation or behavioral verification.

## 5. Adoption Levels

1. **Installed:** required integration files are present at the declared path.
2. **Discoverable:** the target agent/platform demonstrably locates the relevant instructions.
3. **Activated:** evidence shows that the instructions were loaded into the active agent context.
4. **Configured:** platform settings are inspected and bound to the intended integration.
5. **Verified:** repeatable behavioral tests pass for the exact model/platform version and evidence is independently checked.

A level is the highest level for which all required evidence is available. Missing evidence means the level is not established. Level 5 is not inferred from a provider's marketing claims or a successful API connection.

## 6. Evidence Required for an Update

A proposed matrix update should include exact provider/model/platform versions, configuration and commit SHA, test procedure and inputs, raw results and timestamps, integrity checks actually performed, and known limitations.

## 7. Reporting Discrepancies

Open an issue with the integration identifier, exact version, claimed level, verification procedure, raw test results, and evidence references. Maintainers should independently review the evidence before changing the matrix.

## 8. References

- `docs/agent-adoption/ADOPTION_GUIDE.md`
- `integrations/models/*/README.md` where present
- `integrations/platforms/*/README.md` where present
- `manifest/integrations.yaml`
- `tests/integration/models/`

---

**End of Compatibility Matrix**
