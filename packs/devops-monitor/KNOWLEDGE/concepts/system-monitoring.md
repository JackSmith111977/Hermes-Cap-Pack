---
type: concept
domain: devops-monitor
keywords: [monitoring, observability, metrics, logging, alerting]
created: 2026-05-14
---

# System Monitoring and Observability

## Definition

System Monitoring and Observability is the practice of collecting, analyzing, and acting upon data about system behavior, performance, and health. Observability goes beyond traditional monitoring by enabling teams to understand internal system states from external outputs (logs, metrics, traces). A robust monitoring strategy provides early warning of issues, aids root cause analysis, and informs capacity planning.

## Core Concepts

### The Three Pillars of Observability

| Pillar | Data Type | Purpose | Tooling |
|:-------|:----------|:--------|:--------|
| **Metrics** | Numerical measurements over time | Trend analysis, alerting thresholds | Prometheus, Grafana, Datadog |
| **Logs** | Discrete event records | Debugging, audit trails, forensics | ELK, Loki, CloudWatch |
| **Traces** | Request flow across services | Distributed system debugging, latency analysis | Jaeger, Zipkin, OpenTelemetry |

### Monitoring Levels

- **Infrastructure**: CPU, memory, disk, network, uptime — the health of underlying resources
- **Application**: Request rate, error rate, latency (the Golden Signals) — user-facing performance
- **Business**: Active users, revenue, conversion rates — outcomes that matter to the organization
- **Dependency**: External API health, database connection pool, cache hit ratio — third-party reliability

### Alerting Strategies

```
# Alert design principles
- Alert on symptoms, not causes (response time > threshold, not CPU > 90%)
- Define severity levels (P0 = service down, P1 = degraded, P2 = warning)
- Set appropriate thresholds (avoid "alert fatigue" from false positives)
- Include runbooks in alert notifications (what to do, not just what's wrong)
```

### Key Patterns

- **USE method**: For every resource, check Utilization, Saturation, and Errors
- **RED method**: For every service, check Rate, Errors, and Duration
- **SLO-based alerting**: Set Service Level Objectives, alert when approaching breach
- **Dashboard composition**: Service overview → component drill-down → log/trace correlation

## Relationships

- **Related to**: `project-startup-workflow` (monitoring setup for new projects)
- **Works with**: `webhook-subscriptions` (event-driven monitoring responses)
- **Depends on**: `linux-ops-guide` for OS-level metric collection (htop, iostat, dmesg)
- **Required by**: `proxy-monitor` for network-level observability
- **Companion to**: `docker-container-management` (monitoring containerized workloads)
