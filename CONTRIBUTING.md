# Contributing to Apxoh

---

## Before You Start

Read these first:

1. `README.md`
2. `AGENTS.md` (if you are an AI agent)
3. `system/charter/ENGINEERING_CHARTER.md`
4. `SECURITY_AGENTS.md`

---

## Ways to Contribute

- **Bug reports** — open an issue
- **Feature requests** — open an issue
- **New rules** — see `docs/rule-authoring/HOW_TO_WRITE_A_RULE.md`
- **Code** — see below
- **Documentation** — same review process
- **Security findings** — do NOT open a public issue; see `SECURITY.md`

---

## Development Setup

```bash
git clone https://github.com/mohamedelghazali/Apxoh.git
cd Apxoh
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pre-commit install
```

Verify setup:

```bash
arkhon doctor
pytest
make lint
```

---

## The Golden Rules

1. **No code without tests.**
2. **No rule without positive and negative tests.**
3. **No dependency without justification.**
4. **No direct commits to `main`.**
5. **No claim without evidence.**

---

## Pull Request Process

1. Fork the repository.
2. Create a branch: `feat/<short-name>` or `fix/<short-name>`.
3. Write the change and its tests.
4. Run `make ci` locally.
5. Open a PR against `main`.
6. Address review comments.
7. After approval and CI pass, a maintainer merges.

### What CI Checks

- `ruff check`
- `mypy --strict`
- `pytest` on Python 3.11, 3.12, 3.13
- `arkhon validate`
- `pip-audit`
- `gitleaks`
- `trivy`
- `zizmor`
- Installation test

Any failure blocks merge.

---

## Coding Standards

- Python 3.11+.
- Type hints required.
- `ruff` for linting and formatting.
- `mypy --strict` must pass.
- No dead code.
- No premature abstraction.
- English-only in code, comments, and documentation.

---

## Adding a Rule

Read `docs/rule-authoring/HOW_TO_WRITE_A_RULE.md` first.

Summary:

1. Pick a domain.
2. Choose a rule ID matching the domain prefix.
3. Write the YAML file in `rules/<domain>/`.
4. Write positive and negative tests in `tests/rules/`.
5. Run `arkhon validate`.
6. Open a PR.

---

## Adding a Language Profile

1. Create `languages/<id>/` with:
   - `language-profile.yaml`
   - `tools.yaml`
   - `testing.yaml`
   - `security.yaml`
2. Register the language in `languages/registry.yaml`.
3. Add detection rules (extensions, build files).
4. Add tests in `tests/unit/language_support/`.
5. Add a fixture project in `tests/languages/fixtures/<lang>-project/`.

---

## Adding a Model Integration

1. Create `integrations/models/<id>/` with:
   - `config.yaml`
   - `adapter.py`
   - `README.md`
   - `prompts/system.md`
   - `prompts/governance-injection.md`
   - `skill-bindings.yaml`
2. Add to `manifest/integrations.yaml`.
3. Add tests in `tests/integration/models/`.
4. Update `docs/agent-adoption/COMPATIBILITY_MATRIX.md`.

---

## Documentation

- Markdown only.
- English only.
- Follow the existing structure.
- Run `make docs` if available (currently a placeholder).

---

## Security

- Do not open public issues for vulnerabilities.
- See `SECURITY.md` for reporting channels.
- Do not include secrets, tokens, or credentials in any file.

---

## Code of Conduct

See `CODE_OF_CONDUCT.md`.

---

## Questions?

Open a discussion on GitHub.

---

**End of Document**
