# rules/observability

Agents MUST load applicable SE-OBS-* rules for service health, monitoring, dashboards,
metrics, and alerts. Monitoring must cover availability, latency, errors, saturation, and
critical dependencies. Detailed operational dashboards and diagnostic data are restricted
to authorized operators; public health probes disclose only minimal status. Required
checks that cannot run are BLOCKED, never PASS.
