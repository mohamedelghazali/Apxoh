---
name: New Model Integration
about: Propose support for a new AI model or coding platform
title: "[INTEGRATION] "
labels: integration, enhancement
---

## Integration ID

<!-- Example: mistral-codestral. Use lowercase, hyphenated identifiers. -->

## Provider

<!-- Example: Mistral AI. -->

## Type

- [ ] Model
- [ ] Platform

## API endpoint or platform hook

<!-- Do not include credentials or private tokens. -->

## Capabilities

- [ ] Code generation
- [ ] Code review
- [ ] Long context
- [ ] Multimodal
- [ ] Instruction following
- [ ] Other:

## Verification level requested

- [ ] Installed (1)
- [ ] Discoverable (2)
- [ ] Activated (3)
- [ ] Configured (4)
- [ ] Verified (5)

## Verification evidence

<!-- Explain how the integration can be tested reproducibly. -->

## Proposed implementation checklist

- [ ] `config.yaml`
- [ ] `adapter.py` (no eval/exec/shell=True)
- [ ] `README.md`
- [ ] `prompts/system.md`
- [ ] `prompts/governance-injection.md`
- [ ] `skill-bindings.yaml`, if required by the integration type
- [ ] Tests under `tests/integration/models/` or `tests/integration/platforms/`
- [ ] `manifest/integrations.yaml` updated
- [ ] `docs/agent-adoption/COMPATIBILITY_MATRIX.md` updated
