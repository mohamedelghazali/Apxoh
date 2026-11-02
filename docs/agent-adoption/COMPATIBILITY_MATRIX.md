# Apxoh Compatibility Matrix

**Version:** 1.0  
**Status:** Initial inventory; no behavioral verification claims established  
**Last updated:** 2026-11-01

This matrix is a tracking baseline. A provider name or documented integration is not evidence that the integration exists, is configured, or has passed behavioral verification. Levels must be updated only from reproducible evidence.

## 1. Model Integrations

| Model family | Provider | Current evidenced level | Verification status | Notes |
| :--- | :--- | :--- | :--- | :--- |
| Claude | Anthropic | Not established | No evidence supplied in this matrix | Verify exact model, platform, and test procedure |
| GPT / OpenAI reasoning models | OpenAI | Not established | No evidence supplied in this matrix | Do not generalize across model versions |
| Gemini | Google | Not established | No evidence supplied in this matrix | Verify API and prompt behavior |
| Kimi | Moonshot | Not established | No evidence supplied in this matrix | Verify exact model and deployment |
| DeepSeek-Coder | DeepSeek | Not established | No evidence supplied in this matrix | Configuration is not behavioral verification |
| Qwen-Coder | Alibaba | Not established | No evidence supplied in this matrix | Verify exact model and deployment |
| Code Llama | Meta | Not established | No evidence supplied in this matrix | Verify local runtime and model version |

## 2. Platform Integrations

| Platform | Provider | Current evidenced level | Notes |
| :--- | :--- | :--- | :--- |
| GitHub Copilot | GitHub / Microsoft | Not established | Platform configuration cannot prove internal model behavior |

## 3. Security Integrations

| Integration | Intended role | Required? | Evidence condition |
| :--- | :--- | :--- | :--- |
| TSAR | Independent security verification | Required where the applicable security gate says so | Missing or unavailable TSAR must produce BLOCKED, not PASS |

## 4. Generic Agents

| Integration | Current evidenced level | Notes |
| :--- | :--- | :--- |
| Generic agents | Not established | Instructions alone do not prove activation or behavior |

## 5. Adoption Level Definitions

1. **Installed:** integration files are present and their hashes/locations are recorded.
2. **Discoverable:** the platform demonstrably locates the integration instructions.
3. **Activated:** the instructions are shown to be loaded into the active agent context.
4. **Configured:** platform settings are inspected and bound to the intended integration.
5. **Verified:** a repeatable behavioral test suite passes and evidence authenticity is independently checked.

A level is the highest level for which all required evidence is available. Missing evidence means the level is not established.

## 6. Versioning

| Apxoh version | Matrix version | Changes |
| :--- | :--- | :--- |
| 0.1.0-dev.1 | 1.0 | Initial evidence-conscious inventory |

## 7. Reporting Discrepancies

Open an issue with the integration identifier, exact model/platform version, claimed level, verification procedure, raw test results, and evidence references. Maintainers must independently review the evidence before changing the matrix.

## 8. Reference

- `docs/agent-adoption/ADOPTION_GUIDE.md`
- `integrations/models/*/README.md` (where present)
- `integrations/platforms/*/README.md` (where present)
- `manifest/integrations.yaml`

---

**End of Document**
