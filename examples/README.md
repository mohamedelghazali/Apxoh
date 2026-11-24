# Apxoh Examples

This directory is reserved for small, reviewable projects that demonstrate how Apxoh profiles and governance rules can be applied. Language detection fixtures remain under `tests/languages/fixtures/`; examples are intended to demonstrate project scenarios rather than language detection.

## Planned Example Scenarios

The following are proposed example directories. A row is not evidence that the project currently exists or passes verification; update this table only when the directory and its checks are committed.

| Example directory | Intended profile | Scenario |
| :--- | :--- | :--- |
| `minimal-project/` | `universal` | Smallest governed project |
| `web-application/` | `web-application` | Frontend structure and component tests |
| `api-service/` | `api-service` | HTTP handlers and service tests |
| `enterprise-system/` | `enterprise` | Service layers and broader gate coverage |

## Using an Example

After an example project has been added, run commands supported by the installed Apxoh version. For the current CLI, typical commands include:

```bash
arkhon inspect path/to/example
arkhon verify path/to/example --domain testing
arkhon assess path/to/example
arkhon report path/to/example --format markdown
```

Check `arkhon --help` and the installed release before relying on a command or option. A successful inspection is not the same as a passing verification gate.

## Security Gate Expectations

A required security gate must remain `BLOCKED` when its required security authority or evidence is unavailable. Do not label an example secure because it has no visible findings or because a test runner was not installed.

## What Examples Are Not

- They are not substitutes for language fixtures.
- They are not automatically production-ready reference architectures.
- Their presence does not imply that all gates pass.
- They must not contain real credentials, customer data, or private keys.

## Adding an Example

1. Create `examples/<name>/`.
2. Add `.arkhon/project.yaml` with a profile that exists in the repository.
3. Add the smallest useful source and test files.
4. Add a README describing scope, prerequisites, and limitations.
5. Run inspection and the relevant verification checks.
6. Record actual results; leave unavailable checks BLOCKED.
7. Add the example to the table above through a reviewed pull request.

---

**End of Examples Guide**
