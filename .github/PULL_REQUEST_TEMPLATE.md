# Pull Request

## Summary

<!-- What changes, why, and what is deliberately out of scope? -->

## Type of change

- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] New rule or policy
- [ ] New integration
- [ ] New language profile
- [ ] Documentation
- [ ] CI / infrastructure
- [ ] Security

## Related issue

Closes #

## General checklist

- [ ] I have read `CONTRIBUTING.md`.
- [ ] I have read `AGENTS.md` if this change is AI-assisted.
- [ ] Existing files and protections are preserved.
- [ ] The change is scoped and commits are understandable.
- [ ] No secrets, tokens, credentials, or private data are included.

## Tests and verification

- [ ] Tests cover new behavior.
- [ ] Regression tests cover the reported defect, where applicable.
- [ ] Relevant tests were run locally.
- [ ] CI results were reviewed.
- [ ] I have not claimed checks that were not run.

Commands and results:

```text
<!-- Paste commands and concise, sanitized results. -->
```

## Rules and governance (if applicable)

- [ ] Rule ID follows the current naming convention.
- [ ] Rule validates against `schemas/rule.schema.json`.
- [ ] Positive, negative, and regression tests are included.
- [ ] Policy and evidence requirements are documented.
- [ ] Governance changes have the required independent review.

## Integrations (if applicable)

- [ ] Integration contract and adapter are documented.
- [ ] Adapter input is treated as untrusted.
- [ ] Adapter contains no unsafe eval/exec or shell=True use.
- [ ] `manifest/integrations.yaml` is updated.
- [ ] Compatibility matrix reflects only evidence-backed levels.

## Documentation and risk

- [ ] Documentation reflects actual behavior and limitations.
- [ ] Significant decisions are recorded in `docs/architecture/DECISION_LOG.md`.
- [ ] Risks, rollback considerations, and migration steps are described.

## Screenshots / Evidence

<!-- Include only sanitized evidence. Do not upload secrets or customer data. -->

## Additional notes
