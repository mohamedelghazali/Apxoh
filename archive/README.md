# Apxoh Archive

**Version:** 1.0  
**Status:** Active  
**Last updated:** 2026-11-02

This directory is the repository's navigation point for historical, deprecated, retired, or superseded artifacts. Archiving preserves context; it does not make an artifact active or enforceable.

---

## 1. What Belongs in the Archive

| Artifact | Archival treatment |
| :--- | :--- |
| Rules | After the deprecation/review process, move to the designated rule archive location and preserve the rule ID and history. |
| ADRs | Keep the original ADR in docs/architecture/DECISION_LOG.md and mark it superseded; do not erase its decision history. |
| Policies | Preserve superseded policy revisions in a clearly named historical location when maintainers approve. |
| Standards references | Mark withdrawn or superseded references and retain the source/version context. |
| Other documents | Archive only when replaced or retired and their historical context remains useful. |

The rule lifecycle in docs/rule-authoring/RULE_LIFECYCLE.md is authoritative for rule deprecation and archival.

## 2. What Must Not Be Archived Here

- **Secrets and credentials:** never commit secrets, tokens, private keys, or live credentials.
- **Active evidence:** evidence belongs in the evidence store and must be managed under the applicable evidence-retention policy, not copied into this archive.
- **Unreviewed drafts:** keep drafts in their working location until accepted, rejected, or intentionally retired.
- **Unrelated deleted files:** do not use the archive as a general-purpose dumping ground.

Evidence must not be pruned automatically based on this document. Apply the applicable retention policy and preserve records subject to audit, legal hold, or incident investigation.

## 3. Rule Archiving

Before archiving a rule:

1. Record the reason, date, affected versions, and responsible reviewer.
2. Mark the rule deprecated according to the rule lifecycle.
3. Identify a replacement and migration guidance when applicable.
4. Allow the required deprecation period, except where an approved emergency removal is documented.
5. Move the rule to the designated archive path, preserve its ID, and record the change in the rule changelog.
6. Confirm that archived rules are excluded from active evaluation.

Do not assume that moving a YAML file alone changes runtime behavior. Verify the loader's discovery rules and tests before claiming a rule is no longer enforced.

## 4. ADR Supersession

When an ADR is superseded:

1. Add the replacement decision with a reference to the earlier ADR.
2. Update the earlier ADR's status to identify the superseding ADR.
3. Preserve both decisions and explain the migration or consequences.

The decision history remains in docs/architecture/DECISION_LOG.md. An ADR's status is historical metadata; it does not prove implementation.

## 5. Retention and Integrity

- Do not delete archived artifacts merely because they are old.
- Do not claim permanent retention unless repository backup and retention controls establish it.
- Do not rewrite historical content to make a superseded decision appear never to have existed.
- Record any approved removal or redaction with its rationale and scope.
- Keep secrets and unnecessary personal data out of archived content.

## 6. Archive Index

No archived rule, policy, or superseded ADR inventory is asserted by this README. Add entries here when artifacts are actually archived; do not use placeholder counts as evidence of an empty archive.

## 7. References

- docs/rule-authoring/RULE_LIFECYCLE.md — rule lifecycle.
- docs/architecture/DECISION_LOG.md — architecture decision history.
- CHANGELOG-RULES.md — rule catalog history.
- docs/operations/INCIDENT_RESPONSE.md — incident handling.

---

**End of Archive Guide**
