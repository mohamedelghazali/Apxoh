# Postmortem: [Incident Title]

**Incident ID:** INC-YYYY-MM-DD-NNN  
**Severity:** Critical / High / Medium / Low (use the repository incident classification)  
**Status:** Draft / Final  
**Author:** [Name or role]  
**Reviewed by:** [Name or role]  
**Date started:** YYYY-MM-DD HH:MM UTC  
**Date resolved:** YYYY-MM-DD HH:MM UTC  
**Time to detect:** [duration or N/A with reason]  
**Time to resolve:** [duration or ongoing]

---

## 1. Summary

Describe what happened, when it happened, the affected system or users, and the outcome in plain language. Distinguish confirmed facts from estimates and hypotheses.

## 2. Impact

- **Users or projects affected:** [count, percentage, or unknown]
- **Services/components affected:** [list]
- **Duration:** [start → end, with timezone]
- **Data loss or corruption:** [yes/no/unknown; details]
- **Security or privacy impact:** [details or none identified]
- **Financial or operational impact:** [if known]
- **Reputation impact:** [if known]

## 3. Timeline

Record all timestamps in UTC. If source timestamps use another timezone, state the original timezone and conversion method.

| Time (UTC) | Event | Evidence/reference |
| :--- | :--- | :--- |
| YYYY-MM-DD HH:MM | [Event] | [Log, issue, workflow, or artifact] |

## 4. Root Cause

State the underlying technical or process condition that allowed the incident to occur. Avoid stopping at labels such as "human error". Separate confirmed root cause from contributing hypotheses.

## 5. Contributing Factors

- [Factor and supporting evidence]
- [Factor and supporting evidence]

Explain how each factor increased likelihood, duration, or impact.

## 6. Detection

- **Detection source:** [alert, user report, monitoring, review, or other]
- **Time to detect:** [duration]
- **Detection gap:** [what was missing or delayed]
- **Evidence:** [references]

If the event was planned or discovered through design review rather than incident detection, say so explicitly.

## 7. Response

- **What went well?** [facts]
- **What went poorly?** [facts]
- **What was lucky?** [facts]
- **Containment actions:** [actions and timestamps]

## 8. Remediation

### Immediate
- [ ] [Action] — Owner: [role/name] — Status/evidence: [reference]

### Short-term (target: within 1 week)
- [ ] [Action] — Owner: [role/name] — Due: YYYY-MM-DD

### Long-term (target: within 1 month or stated milestone)
- [ ] [Action] — Owner: [role/name] — Due: YYYY-MM-DD

Do not mark an action complete without a verifiable result or linked implementation evidence.

## 9. Prevention

Describe changes intended to prevent recurrence:

- **Process:** [change]
- **Technical control:** [change]
- **Tests/monitoring:** [change]
- **Documentation/training:** [change]

## 10. Lessons Learned

Record the assumptions that changed, what was learned, and what should be done differently. Avoid unsupported universal claims.

## 11. Apxoh-Specific Impact

Complete this section when Apxoh governance, rules, evidence, integrations, or release gates were involved.

- **Which gates failed to catch the issue?** [IDs or none; explain]
- **Was evidence fabricated, missing, invalid, or stale?** [details]
- **Was a rule violated or insufficient?** [rule IDs]
- **Was a policy bypassed?** [policy and evidence]
- **Was an agent involved?** [agent/model, adapter, actions, and trace]
- **What was the final gate status?** [PASS / FAIL / BLOCKED / not applicable]

## 12. Blameless Statement

This postmortem aims to improve systems and processes, not assign blame. References to people describe roles and actions for factual traceability, not personal fault.

## 13. Attachments and References

- Logs: [link or artifact ID]
- Metrics: [link or artifact ID]
- Screenshots: [link or artifact ID]
- Incident/issue: [link]
- Related pull requests/commits: [links]
- Evidence bundle: [reference, if safe to share]

Do not include secrets, credentials, or unnecessary personal data.
