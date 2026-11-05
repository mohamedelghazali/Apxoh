# Apxoh Versioning Policy

**Version:** 1.0
**Status:** Active
**Last updated:** 2026-11-04

---

## 1. Scope

This document defines how Apxoh versions:

- The engine and CLI (`arkhon` Python package)
- The rule catalog (`rules/`, `languages/*/rules/`)
- The schemas (`schemas/`)
- The manifest (`manifest/`)
- The integrations (`integrations/`)
- The report templates (`reports/templates/`)

Each artifact has its own version, following the same principles, but with its own cadence.

---

## 2. Semantic Versioning

Apxoh uses **Semantic Versioning 2.0.0** for all artifacts:

```
MAJOR.MINOR.PATCH[-pre-release][+build]
```

### 2.1 Meaning

| Component | Meaning | Example |
| :--- | :--- | :--- |
| MAJOR | Breaking change to public API | `1.0.0` → `2.0.0` |
| MINOR | New feature, backward compatible | `1.0.0` → `1.1.0` |
| PATCH | Bug fix, no API change | `1.0.0` → `1.0.1` |
| pre-release | Unstable, may change | `1.0.0-alpha.1` |
| build | Build metadata, ignored for ordering | `1.0.0+build.42` |

### 2.2 Pre-1.0 Versions

Before `1.0.0`, Apxoh uses **development-stage pre-release versions**:

```
0.1.0-dev.1
0.1.0-dev.2
0.1.0-rc.1
0.1.0     ← current official release
```

Breaking changes are allowed at any pre-1.0 version. A published `0.1.0` is an official package release, but it does not declare the public API stable. The project remains in the 0.x development stage; `1.0.0` is the first stable API release.

---

## 3. Version Format per Artifact

### 3.1 Engine (`arkhon` package)

- **File:** `VERSION` (plain text, canonical PEP 440 form, e.g., `0.1.0`)
- **File:** `pyproject.toml` (`version = "0.1.0"`, PEP 440)
- **File:** `src/arkhon/__init__.py` (`__version__ = "0.1.0"`)
- **Rule:** `VERSION`, `pyproject.toml`, and `__version__` use the same canonical PEP 440 value. The manifest keeps its SemVer-style display version. Enforced by release checks.

### 3.2 Manifest

- **File:** `manifest/index.yaml` → `manifest_version`
- **Rule:** bumped when the manifest schema or top-level structure changes.
- **Current:** `1.0.0`

### 3.3 Schemas

- Each schema file has `$id` with a version, e.g., `https://apxoh.dev/schemas/rule/1.0.0`
- The version is bumped when the schema is broken (major) or extended (minor).
- **Rule:** a schema bump requires a migration in `migrations/schemas/`.

### 3.4 Rules

- Each rule file has `metadata.version`, e.g., `1.0.0`
- **Rule:** a rule bump requires a `CHANGELOG-RULES.md` entry.
- A rule can be `deprecated` (still active, scheduled for removal) or `archived` (moved to `rules/_archived/`).

### 3.5 Integrations

- Each integration has its own version in `config.yaml`
- **Rule:** integration version is independent of Apxoh version.
- Compatibility matrix is in `manifest/compatibility.yaml`.

### 3.6 Report Templates

- Each template has an implicit version, tracked in `reports/templates/CHANGELOG.md`
- **Rule:** template changes that alter the report structure are minor bumps.

---

## 4. Release Cadence

| Artifact | Cadence | Trigger |
| :--- | :--- | :--- |
| Engine | Monthly, or on security fix | Maintainer decision |
| Manifest | Quarterly, or when needed | Structure change |
| Schemas | Quarterly, or when needed | Contract change |
| Rules | Continuous (PR-based) | New rule approved |
| Integrations | Per-provider | Provider API change |
| Report templates | Quarterly | Format change |

Security fixes override the cadence and can ship at any time (patch version).

---

## 5. Release Process

### 5.1 Release Checklist

Before tagging a release:

- [ ] `VERSION` matches `pyproject.toml` matches `__version__`
- [ ] `CHANGELOG.md` updated with the release entry
- [ ] All tests pass (`make ci`)
- [ ] Security gate passes (`security.yml`)
- [ ] SBOM generated
- [ ] SLSA provenance generated
- [ ] Documentation updated
- [ ] Migration notes written (if breaking)

### 5.2 Release Steps

```bash
# 1. Bump version
echo "0.1.0" > VERSION
# (also update pyproject.toml and __init__.py)

# 2. Update CHANGELOG.md

# 3. Run release-check
make release-check

# 4. Commit
git add VERSION pyproject.toml src/arkhon/__init__.py CHANGELOG.md
git commit -m "release: v0.1.0"

# 5. Tag
git tag -s v0.1.0 -m "Apxoh v0.1.0"

# 6. Push tag (triggers slsa-release.yml)
git push origin v0.1.0

# 7. Verify provenance
slsa-verifier verify-artifact ...
```

### 5.3 Post-Release

- [ ] GitHub release published
- [ ] SBOM attached
- [ ] SLSA provenance attached
- [ ] Security advisory check (any CVEs fixed?)
- [ ] Social announcement (optional)

---

## 6. Deprecation Policy

### 6.1 Announcing Deprecation

A feature, rule, schema, or integration can be **deprecated** at any time:

1. Mark it `deprecated` in its metadata
2. Add a deprecation notice to `CHANGELOG.md`
3. Document the replacement
4. Set a removal target (at least one minor version ahead)

### 6.2 Removal

A deprecated item can be removed in a **major version** bump (or any pre-1.0 bump with a clear notice).

Removal requires:

- Migration guide
- Automated migration tool (if possible)
- Announcement at least 30 days before removal

---

## 7. Compatibility Promises

### 7.1 Public API

From `1.0.0` onward, Apxoh guarantees:

- **CLI:** command names and arguments are stable within a major version
- **Python API:** `arkhon.*` public functions are stable within a major version
- **Schemas:** schema `$id` versions are immutable; breaking changes require a new `$id`
- **Rules:** rule IDs are permanent; a rule can be deprecated but never reused for a different meaning

### 7.2 File Formats

- Rule files (`YAML`): backward compatible within a major schema version
- Evidence files (`JSON`): backward compatible within a major schema version
- Report files (`Markdown`/`HTML`): structure may change within a minor version, content stays

### 7.3 Configuration

- `.arkhon/config.yaml`: unknown keys are ignored with a warning, never fatal
- `manifest/*.yaml`: unknown keys are fatal (strict)

---

## 8. Hotfix Policy

A hotfix is a **patch release** that fixes a critical vulnerability or bug.

- Fixed on a branch off the release tag
- Tested against the existing test suite
- Released as `X.Y.(Z+1)`
- Cherry-picked to `main`

Hotfixes are the only case where the cadence is overridden.

---

## 9. Version Discovery

At any time, versions can be discovered:

```bash
# Engine
arkhon version
cat VERSION
python -c "import arkhon; print(arkhon.__version__)"

# Manifest
grep manifest_version manifest/index.yaml

# Schemas
grep '"$id"' schemas/*.json

# Rules
grep -r "version:" rules/*/*.yaml | head

# Integrations
grep -r "version:" integrations/*/*/config.yaml
```

All versions are also recorded in the SBOM of every release.

---

## 10. Reference

- SemVer 2.0.0: https://semver.org/
- PEP 440: https://peps.python.org/pep-0440/
- `docs/SUPPLY_CHAIN.md` — release integrity
- `CHANGELOG.md` — release history
- `CHANGELOG-RULES.md` — rule history
- `manifest/compatibility.yaml` — compatibility matrix

---

**Release-stage policy:** `0.x` means pre-1.0 development, regardless of whether a particular package version has been published. Use the Beta development-status classifier and `pre-release` project channel until the explicit 1.0.0 stability milestone.\n\n**End of Document**
