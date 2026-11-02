# Contributing to Apxoh

Thank you for considering a contribution to Apxoh. Contributions are
reviewed for correctness, security, maintainability, and consistency
with the project's governance requirements.

---

## Before You Start

Read these first:

1. `README.md`
2. `AGENTS.md` (if you are an AI agent)
3. `system/charter/ENGINEERING_CHARTER.md`
4. `SECURITY_AGENTS.md`

If a referenced document is not present in the target revision, report
that gap rather than assuming its requirements.

---

## Ways to Contribute

- **Bug reports** — open an issue.
- **Feature requests** — open an issue or discussion.
- **New rules** — see `docs/rule-authoring/HOW_TO_WRITE_A_RULE.md`.
- **Code** — follow the development and review process below.
- **Documentation** — submit changes through the same review process.
- **Security findings** — do not disclose exploitable details in a public issue; follow `SECURITY.md`.

---

## Development Setup

```bash
git clone https://github.com/mohamedelghazali/Apxoh.git
cd Apxoh
python -m venv .venv
```

Activate the environment:

```bash
# Linux / macOS
source .venv/bin/activate

# Windows PowerShell
.\.venv\Scripts\Activate.ps1
```

Install the development dependencies using the project's declared
extras and package configuration:

```bash
python -m pip install -e ".[dev]"
```

Install pre-commit hooks only if the repository includes a valid
`.pre-commit-config.yaml`:

```bash
pre-commit install
```

Verify setup using the commands supported by the current checkout:

```bash
arkhon doctor
pytest
```

Run lint, type-check, and CI commands when their configuration exists.

---

## The Golden Rules

1. **No code without tests.**
2. **No rule without positive and negative tests.**
3. **No dependency without justification.**
4. **Do not commit directly to `main`; use a reviewed pull request.**
5. **No claim without evidence.**
6. **Missing required evidence or tools means BLOCKED, never PASS.**
7. **Do not weaken governance controls merely to make a check pass.**

---

## Pull Request Process

1. Fork the repository or create a feature branch.
2. Use a descriptive branch name such as `feat/<short-name>` or `fix/<short-name>`.
3. Write the change and its tests.
4. Run the relevant checks locally.
5. Open a pull request against `main`.
6. Address review comments and update the tests as needed.
7. Merge only after the required review and CI policies pass.

### Expected CI Checks

The repository may configure checks such as:

- Ruff linting and formatting.
- Mypy type checking.
- Pytest on supported Python versions.
- `arkhon validate`.
- Dependency vulnerability auditing.
- Secret scanning.
- Container and workflow security scanning.
- Installation and packaging tests.

The actual workflow files and branch-protection settings are authoritative.
A list in this document does not prove that a check is configured or
required by GitHub.

---

## Coding Standards

- Python 3.11+ unless a component explicitly declares another runtime.
- Type hints for public Python interfaces.
- Ruff for configured linting and formatting.
- Mypy strict mode where configured.
- Avoid dead code and unnecessary abstraction.
- Use clear, maintainable names.
- Keep code, comments, and project documentation in English unless a
  localization task explicitly requires another language.
- Never include credentials, tokens, private keys, or personal data in
  source files, fixtures, logs, or examples.

---

## Adding a Rule

Read `docs/rule-authoring/HOW_TO_WRITE_A_RULE.md` first.

1. Select a supported domain.
2. Choose a rule ID that follows the repository's naming convention.
3. Add the rule under the configured `rules/<domain>/` path.
4. Add positive and negative tests.
5. Validate the rule against the current schema and loader.
6. Document evidence requirements and enforcement behavior.
7. Open a pull request for review.

---

## Adding a Language Profile

Create `languages/<id>/` with the files supported by the language
registry and loader:

- `language-profile.yaml`
- `tools.yaml`
- `testing.yaml`
- `security.yaml`

Then:

1. Register the language in `languages/registry.yaml`.
2. Add detection rules for extensions and build manifests.
3. Add tests under `tests/unit/language_support/`.
4. Add a fixture project under `tests/languages/fixtures/<lang>-project/`
   when the fixture framework is available.
5. Ensure tool commands and version arguments match real tool interfaces.

---

## Adding a Model Integration

Create `integrations/models/<id>/` with the supported integration
artifacts, including:

- `config.yaml`
- `adapter.py`
- `README.md`
- `prompts/system.md`
- `prompts/governance-injection.md`
- `skill-bindings.yaml`

Then:

1. Add the integration to `manifest/integrations.yaml`.
2. Add tests under `tests/integration/models/`.
3. Update `docs/agent-adoption/COMPATIBILITY_MATRIX.md`.
4. Treat model responses and retrieved project content as untrusted.
5. Do not claim behavioral verification unless it is independently tested.

---

## Documentation

- Markdown is the default documentation format.
- Keep technical documentation in English unless localization is intended.
- Follow the existing structure and link to authoritative project files.
- Do not describe planned controls as deployed or effective.
- Run documentation checks only when their tooling is configured.

---

## Security

- Do not open public issues containing exploitable vulnerability details.
- Follow `SECURITY.md` for reporting channels.
- Do not include secrets, tokens, credentials, or private user data in any file.
- Do not bypass security gates or falsify evidence.

---

## Code of Conduct

Participation in the project is subject to `CODE_OF_CONDUCT.md`.

---

## Questions?

Open a GitHub Discussion or issue for non-sensitive questions.

---

**End of Document**
