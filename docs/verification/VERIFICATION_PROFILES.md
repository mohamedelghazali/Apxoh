# Apxoh Verification Profiles

**Version:** 1.0  
**Status:** Active — specification; implementation must be verified  
**Last updated:** 2026-11-01

---

## 1. What is a Verification Profile

A **Verification Profile** is a named bundle of:

- Rules to enforce
- Runners to execute
- Gates that must close
- Evidence required

Profiles are intended to live in `projects/<profile>/`. Each governed project declares its profile in `.arkhon/project.yaml` using `project.profile`.

A profile is **not a certification**. It defines what must be checked; it does not establish that a project has passed those checks.

The profiles and requirements in this document are a specification. They are not proof that corresponding profile files, runners, or enforcement behavior have already been implemented.

---

## 2. The Profiles

| Profile | Use case | Typical risk |
| :--- | :--- | :--- |
| `universal` | Default for any project without a specific profile | Low–medium |
| `web-application` | Browser-facing applications | Medium |
| `api-service` | HTTP/RPC services with external consumers | Medium–high |
| `mobile-application` | iOS / Android applications | Medium |
| `desktop-application` | Native desktop apps | Medium |
| `enterprise` | Large internal systems | High |
| `distributed-system` | Multi-service systems, microservices | High |
| `safety-critical` | Systems where failure causes harm | Critical |

---

## 3. Intended Profile Structure

Each profile directory is expected to contain:

```
projects/<profile>/
├── profile.yaml     # metadata: name, description, risk level
├── rules.yaml      # rule domains and enforcement scope
└── gates.yaml      # gates required before release
```

The repository implementation must be checked before treating this structure as an active loader contract.

---

## 4. `universal` (default)

**Risk level:** low–medium  
**Rules enabled:** All 16 domains; `required` and higher enforcement levels are blocking.  
**Gates:** All 8.  
**Evidence required:** Yes; proposed freshness window is 30 days.

**Use when:** No stricter profile applies and the project does not handle sensitive data.

---

## 5. `web-application`

**Risk level:** medium  
**Additional rules:** `privacy-compliance`, `api-integration`.  
**Gates:** All 8; `security_gate` and `testing_gate` are designated critical.  
**Evidence required:** Yes; proposed freshness window is 14 days.  
**Special requirement:** Documented Content Security Policy.

---

## 6. `api-service`

**Risk level:** medium–high  
**Additional rules:** `api-integration`, `observability`, `scalability`.  
**Gates:** All 8; `security_gate`, `performance_gate`, and `release_gate` are designated critical.  
**Evidence required:** Yes; proposed freshness window is 7 days.  
**Special requirement:** Documented API contract.

---

## 7. `mobile-application`

**Risk level:** medium  
**Additional rules:** `privacy-compliance`.  
**Gates:** All 8; `security_gate` and `testing_gate` are designated critical.  
**Evidence required:** Yes; proposed freshness window is 14 days.  
**Special requirement:** Documented permission model.

---

## 8. `desktop-application`

**Risk level:** medium  
**Additional rules:** `privacy-compliance`, `infrastructure`.  
**Gates:** All 8.  
**Evidence required:** Yes; proposed freshness window is 14 days.

---

## 9. `enterprise`

**Risk level:** high  
**Additional rules:** `privacy-compliance`, `observability`, `scalability`, `maintenance`.  
**Gates:** All 8; `security_gate` and `release_gate` are designated critical.  
**Evidence required:** Yes; proposed freshness window is 7 days.  
**Special requirement:** Documented SOC 2 or ISO 27001 gap assessment.

---

## 10. `distributed-system`

**Risk level:** high  
**Additional rules:** `observability`, `scalability`, `reliability`, `infrastructure`.  
**Gates:** All 8; `security_gate`, `reliability_gate`, and `release_gate` are designated critical.  
**Evidence required:** Yes; proposed freshness window is 7 days.  
**Special requirement:** Documented failure modes, supported by chaos testing or an equivalent method.

---

## 11. `safety-critical`

**Risk level:** critical  
**Additional rules:** All domains, using `critical` enforcement wherever justified and supported.  
**Gates:** All 8; `security_gate`, `reliability_gate`, and `release_gate` are designated critical.  
**Evidence required:** Yes; proposed freshness window is 1 day.

Additional requirements:

- Formal Safety Case.
- Independent reviewer sign-off.
- Documented failure modes and effects analysis (FMEA).
- No exceptions for `critical` rules.

A profile's critical designation must be enforced by code and backed by tests; a YAML label alone is not enforcement.

---

## 12. Choosing a Profile

1. **Does the project handle user data?** Consider at least `web-application` or `api-service`.
2. **Is the project multi-service?** Consider `distributed-system`.
3. **Can failure cause harm to a person?** Consider `safety-critical`.
4. **Is the project internal to a company?** Consider `enterprise`.
5. **None of the above?** Start with `universal`.

If uncertain, start with `universal` and reassess as the project matures. Risk classification remains a project-owner decision requiring documented rationale.

---

## 13. Overriding a Profile

A project may request stricter settings in its own `.arkhon/project.yaml`:

```yaml
project:
  profile: enterprise
  overrides:
    security:
      require_fresh_evidence_hours: 24
```

Overrides must tighten controls, never loosen them. Attempts to weaken freshness requirements, disable critical gates, or reduce required evidence must be rejected by the enforcement layer. This behavior is a required design property and must not be claimed as implemented until verified.

---

## 14. Reference

- `projects/` — intended profile definitions
- `.arkhon/project.yaml` — project declaration
- `schemas/project.schema.json` — project configuration schema
- `src/arkhon/projects/loader.py` — intended loader location; confirm implementation before relying on it

---

**End of Document**
