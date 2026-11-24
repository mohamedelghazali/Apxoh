# Internationalization (i18n)

**Version:** 1.0  
**Status:** Active  
**Last updated:** 2026-11-01

---

## 1. Policy

Apxoh's authoritative repository language is English, as declared in `manifest/system.yaml`. Arabic companion documents may be maintained under `docs/i18n/ar/`; they do not replace or silently override the English source.

The policy supports consistent rule interpretation, standards references, and collaboration across contributors. Translations improve accessibility for readers while preserving one authoritative wording for governance requirements.

## 2. Directory Structure

The following is the intended structure. A listed document is not considered published until it exists in the repository.

```text
docs/i18n/
├── README.md
└── ar/
    ├── README.md
    ├── QUICKSTART.md
    ├── GLOSSARY.md
    └── CONTRIBUTING.md
```

## 3. Rules for Translated Documents

1. **Language and source:** identify the translation language and link to the authoritative English document.
2. **Synchronization:** record the date on which the translation was compared with its English source. If the source changes, review the translation; after 90 days without synchronization, label it `OUTDATED`.
3. **Do not translate:** code snippets, rule IDs, file paths, command names, schema keys, and machine-readable status values such as `PASS`, `FAIL`, and `BLOCKED`.
4. **Translate:** explanatory prose, section headings, table headings, and examples' explanations.
5. **Preserve meaning:** do not strengthen, weaken, or add requirements that are absent from the authoritative source.

Use this header:

```markdown
> **Language:** العربية (Arabic)
> **Authoritative version:** [English source](relative/path.md)
> **Last synced:** YYYY-MM-DD
```

## 4. Adding a Language

1. Create `docs/i18n/<lang-code>/` using an ISO 639-1 language code where available.
2. Translate the README and quick-start guide first.
3. Add the language and its maintained documents to this index.
4. Open a pull request and request review from a fluent speaker.
5. Mark documents as `OUTDATED` when the source has materially changed and the translation has not been synchronized.

## 5. Maintenance

- English remains the authoritative source for repository policy.
- Translation updates are maintained on a best-effort basis.
- English documentation changes do not require a simultaneous translation, but the translation status must not imply synchronization when none has occurred.
- If a translated statement conflicts with its English source, follow the English source and open an issue to correct the translation.

---

**End of document**
