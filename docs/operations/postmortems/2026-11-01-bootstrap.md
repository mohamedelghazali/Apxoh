# Postmortem: Apxoh Bootstrap — Founding Scope Expanded to Three Products

**Incident ID:** INC-2026-11-01-001  
**Severity:** Medium (process/design retrospective)  
**Status:** Final  
**Author:** Maintainer  
**Reviewed by:** Maintainer  
**Date started:** 2026-11-01  
**Date resolved:** 2026-11-01  
**Time to detect:** N/A — planned scope decision, not an operational failure  
**Time to resolve:** Approximately 1 day

---

## 1. Summary

During Apxoh's founding, the scope expanded from a single CLI focused on enforcing rules to three related products: Core, Agent Governance, and Assurance. This was a planned design expansion, not an operational incident. It is recorded because it changed the repository structure, manifest, milestones, and intended users, and therefore required explicit architectural documentation.

The founding discussion identified AI coding agents as direct participants in software production and governance, alongside developers and reviewers.

## 2. Impact

- **Products:** expanded from one initial CLI concept to three product areas.
- **Files:** the founding estimate described growth from approximately 80 to approximately 180 files; this is a historical estimate, not a verified current file count.
- **Directories:** the founding estimate described growth from approximately 15 to approximately 25 directories; this is a historical estimate.
- **Milestones:** Agent Governance became a distinct roadmap milestone.
- **Target users:** expanded beyond developers operating a CLI to include AI coding agents, reviewers, and engineering/release decision-makers.

## 3. Timeline

The times below are transcribed from the founding notes. Their timezone was not specified in the source record.

| Time (2026-11-01) | Event |
| :--- | :--- |
| 09:00 | Initial scope: a CLI that enforces rules |
| 10:30 | Recognition that AI agents are direct code producers and need explicit governance guidance |
| 11:00 | Decision to organize the scope into Core, Agent Governance, and Assurance |
| 12:00 | Repository structure expanded with skills, agent roles, and integration material |
| 14:00 | Manifest separated into an index and referenced registry files |
| 16:00 | Initial project documents updated to describe the three-product model |
| 18:00 | Architectural decisions recorded in docs/architecture/DECISION_LOG.md |

## 4. Root Cause

The initial scope centered on developers using a command-line tool and did not explicitly model AI coding agents as users/participants in the software development workflow.

That framing was too narrow for the intended governance problem: instructions and integration guidance for agents, independent verification, evidence handling, and release decisions needed to be represented as distinct but related product capabilities.

## 5. Contributing Factors

- Founding discussions initially emphasized what Apxoh should do more than which actors and workflows it should govern.
- The initial specification did not contain explicit user personas.
- The first manifest design preceded the three-product model.

## 6. Detection

This was a deliberate founding decision, not a failure discovered through monitoring or incident detection. The scope gap was identified during design discussion.

## 7. Response

- **What went well:** the product split was made early and recorded in the architecture decision log.
- **What went poorly:** the initial developer-first framing required restructuring and rework during the founding period.
- **What was lucky:** the decision log and manifest were still being shaped, so the revised model could be recorded without changing a released product.

## 8. Remediation

### Immediate (founding work)

- [x] Record the three-product model and separation of security authority in the architecture decision log. The TSAR separation is covered by ADR-002; ADR-001 records the product/technical identifier distinction.
- [x] Split manifest data into an index and referenced registry files.
- [x] Add repository structures for skills, agent roles, and integrations.

### Short-term

- [x] Add working user personas to docs/architecture/SYSTEM_OVERVIEW.md.
- [x] Add the actual repository structure and navigation guidance to docs/architecture/REPO_MAP.md.
- [x] Document the three products and their component boundaries in manifest/products.yaml.
- [ ] Assign named accountable owners to each product; the current registry describes roles and components but does not identify individual owners.

### Long-term

- [ ] Review the persona definitions at each major release and revise them using user feedback.
- [x] Add a **Target user(s)** field to the ADR template in docs/architecture/DECISION_LOG.md.

## 9. Prevention

- Every significant feature proposal should identify its target persona, workflow, and accountable product area before implementation.
- Architecture decisions should record the target user(s), constraints, alternatives, consequences, and implementation status.
- The roadmap should keep the working personas visible and distinguish assumptions from validated user research.

## 10. Lessons Learned

1. **Founding scope has high leverage.** Early assumptions influence architecture, repository structure, and roadmap sequencing.
2. **User personas should be explicit.** "Developers" alone does not describe the different needs of developers, AI agents, reviewers, and release decision-makers.
3. **Decision logs preserve reasoning.** Recording the rationale makes later changes reviewable and reduces ambiguity about why the architecture exists.

## 11. Apxoh-Specific Impact

- **Which gates failed to catch it?** None. This was a design-scope decision, not a gate failure.
- **Was evidence fabricated, missing, or stale?** Not applicable to the founding decision. Implementation claims still require independent evidence.
- **Was a rule violated?** No rule violation was identified in the source retrospective.
- **Was a policy bypassed?** No.
- **Was an agent involved?** No agent was identified as participating in this founding decision.

## 12. Blameless Statement

This postmortem is blameless. The initial developer-first framing was a reasonable starting point for a CLI concept. The scope was broadened during founding and documented before a product release. The purpose of this record is to preserve the reasoning and improve future planning, not assign fault.

## 13. Attachments

- docs/architecture/DECISION_LOG.md — ADR-002 (Apxoh and TSAR have separate responsibilities)
- docs/architecture/SYSTEM_OVERVIEW.md — product model and working personas
- ROADMAP.md — product milestones and target personas
