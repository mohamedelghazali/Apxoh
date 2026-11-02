# Postmortem: [Incident Title]

**Incident ID:** INC-YYYY-MM-DD-NNN  
**Severity:** Critical / High / Medium / Low  
**Status:** Draft / Final  
**Author:** [Name]  
**Reviewed by:** [Name]  
**Date started:** YYYY-MM-DD  
**Date resolved:** YYYY-MM-DD  
**Timezone:** UTC

---

## 1. Summary

Write one concise paragraph describing what happened in plain language, what was affected, and how the incident was resolved. Distinguish confirmed facts from assumptions.

---

## 2. Impact

- **Users affected:** [count or percentage; state estimation method]
- **Services affected:** [list]
- **Duration:** [start → end, in minutes]
- **Data loss or corruption:** [yes/no/unknown; details]
- **Security or privacy impact:** [yes/no/under investigation; details]
- **Financial impact:** [if applicable]
- **Geographic or regulatory scope:** [if applicable]

---

## 3. Timeline

All timestamps in UTC. Include the source for significant timestamps where possible.

| Time (UTC) | Event | Source / Evidence |
| :--- | :--- | :--- |
| 14:00 | First known symptom | [monitoring / log / report] |
| 14:03 | Alert fired | [alert reference] |
| 14:05 | On-call acknowledged | [incident record] |
| 14:12 | Root cause identified | [investigation reference] |
| 14:20 | Mitigation deployed | [change / deployment reference] |
| 14:30 | Service restored | [health check / monitoring] |

---

## 4. Root Cause

Describe the technical and organizational conditions that directly caused the incident. Avoid stopping at labels such as “human error.” Explain why the action or failure was possible and which system conditions allowed it to occur.

Separate:

- **Confirmed root cause:** [evidence-backed explanation]
- **Contributing technical conditions:** [details]
- **Unresolved questions:** [details]

---

## 5. Contributing Factors

List conditions that increased the likelihood, impact, or duration of the incident.

- [Factor 1]
- [Factor 2]
- [Factor 3]

For each factor, cite the relevant log, metric, change, configuration, or interview record.

---

## 6. Detection

- **How was it detected?** [alert, user report, monitoring, external notification]
- **Time to detect:** [first symptom to detection]
- **Detection gap:** [why it took that long]
- **Missing or ineffective signals:** [details]
- **Evidence references:** [links or identifiers]

---

## 7. Response

- **What went well?** [specific actions and conditions]
- **What went poorly?** [specific delays or failures]
- **What was uncertain?** [unknowns during response]
- **What was lucky?** [conditions that limited impact]
- **Communication:** [internal and external communication summary]

---

## 8. Remediation

### Immediate — completed during the incident

- [ ] [Action] — Owner: [Name] — Completed: YYYY-MM-DD HH:MM UTC — Evidence: [reference]

### Short-term — within 1 week

- [ ] [Action] — Owner: [Name] — Due: YYYY-MM-DD — Tracking issue: [link]

### Long-term — within 1 month

- [ ] [Action] — Owner: [Name] — Due: YYYY-MM-DD — Tracking issue: [link]

Each action must have a clear owner, measurable completion criteria, and a tracking reference. Do not mark an action complete without evidence.

---

## 9. Prevention

Describe the changes intended to prevent recurrence or reduce impact:

- **Process change:** [description]
- **Technical control:** [description]
- **Test coverage:** [description]
- **Monitoring and alerting:** [description]
- **Documentation and training:** [description]

Explain how the effectiveness of each change will be measured.

---

## 10. Lessons Learned

- **What did we learn?** [new information]
- **Which assumption was wrong?** [details]
- **What remains uncertain?** [details]
- **What should change in our operating model?** [details]

---

## 11. Apxoh-Specific Impact

Complete this section when the incident involves Apxoh governance or a governed project.

- **Which gates should have detected or blocked the issue?**
- **Did any gate incorrectly close?**
- **Was evidence fabricated, missing, malformed, tampered with, or stale?**
- **Was evidence bound to the wrong commit?**
- **Was a rule violated or incorrectly evaluated?**
- **Was a policy bypassed or an exception misused?**
- **Did a runner fail, crash, skip, or return an inconclusive result?**
- **Was an AI agent involved?** If so, record the model/provider, integration, relevant request or run identifiers, actions taken, and independently verifiable outputs.
- **Were audit logs and evidence preserved?**
- **What governance changes are required?**

Do not include secrets, access tokens, personal data, or sensitive exploit details in this document. Store restricted forensic material in the approved secure location and reference it by identifier.

---

## 12. Blameless Statement

This postmortem is blameless. Its purpose is to improve systems, controls, and processes, not to assign personal blame. References to individuals describe roles and actions needed to reconstruct events; they are not accusations.

---

## 13. Attachments and References

- Logs: [link / evidence ID]
- Metrics: [link / evidence ID]
- Traces: [link / evidence ID]
- Screenshots: [link; supplementary only]
- Incident channel or thread: [link]
- Related pull requests: [links]
- Related issues: [links]
- Evidence bundles: [IDs and commit SHAs]
- Forensic archive: [restricted location / reference]

---

## 14. Review and Closure

- **Incident commander:** [Name]
- **Service owner:** [Name]
- **Security review required:** [yes/no; reviewer]
- **Privacy/legal review required:** [yes/no; reviewer]
- **All remediation actions tracked:** [yes/no]
- **Residual risk accepted by:** [authorized owner or N/A]
- **Closure date:** YYYY-MM-DD
- **Next review date:** YYYY-MM-DD

---

**End of Postmortem**
