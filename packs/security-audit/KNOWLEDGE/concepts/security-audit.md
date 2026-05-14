---
type: concept
domain: security-audit
keywords: [security-audit, vulnerability, threat-model, access-control, secrets, compliance]
created: 2026-05-14
---

# Security Audit

## Definition

Security Audit refers to the systematic evaluation of an AI agent system's security posture — identifying vulnerabilities, verifying access controls, auditing secrets management, and ensuring compliance with security policies. Audits encompass code-level analysis (SAST/DAST), dependency scanning (CVE detection), configuration review (overly permissive permissions), runtime monitoring (suspicious behavior detection), and secrets hygiene (hardcoded credentials, token rotation). The goal is to surface risks before they become exploits.

## Core Concepts

### Audit Dimensions

| Dimension | Focus | Tools/Methods |
|:----------|:------|:--------------|
| **Code Security** | Injection, XSS, path traversal | SAST scanners, manual review |
| **Dependency Risk** | Known CVEs, outdated libraries | `pip-audit`, dependency-check, SBOM |
| **Secrets Management** | Hardcoded keys, expired tokens | Secrets scanners, vault rotation |
| **Access Control** | RBAC misconfig, over-permission | Policy-as-code, principle of least privilege |
| **Runtime Security** | Anomalous API calls, data exfiltration | Monitoring, audit logs, alerting |

### Secrets Hygiene

All secrets (API tokens, keys, passwords) must be injected via environment variables or a secrets vault at runtime — never committed to version control. Automated scanners prevent secret leaks, and rotation policies enforce periodic key refresh.

### Vulnerability Lifecycle

1. **Discovery** — Scanner or report identifies CVE/misconfig
2. **Triage** — Severity, exploitability, blast radius assessment
3. **Remediation** — Patch, configuration change, or mitigation
4. **Verification** — Confirm fix, rerun scanner
5. **Retrospective** — Process improvement to prevent recurrence
