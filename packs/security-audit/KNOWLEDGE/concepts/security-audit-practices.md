---
type: concept
domain: security-audit
keywords: [security, audit, vulnerability, scanning, compliance]
created: 2026-05-14
---

# Security Audit Practices

## Definition

Security Audit is the systematic evaluation of a system, codebase, or workflow against security best practices, vulnerability databases, and compliance requirements. For AI agents, this involves scanning for common vulnerabilities (injection, XSS, exposed secrets), verifying authentication and authorization patterns, checking commit hygiene (signed commits, secret leakage), and ensuring safe deletion operations. The goal is to identify and remediate security risks before they can be exploited.

## Core Concepts

### Audit Domains

| Domain | What is Checked | Tools/Skills |
|:-------|:----------------|:-------------|
| **Code security** | Injection, XSS, path traversal, dependency vulns | Static analysis, SCA tools |
| **Secret management** | Hardcoded API keys, tokens, passwords | `delete-safety`, `gitleaks`, `trufflehog` |
| **Access control** | Auth bypass, privilege escalation | `1password`, RBAC review |
| **Commit integrity** | Signed commits, commit authorship | `commit-quality-check` |
| **Operational safety** | Safe file deletion, rollback capability | `delete-safety`, `godmode` safeguards |

### Vulnerability Classification

```markdown
# Common vulnerability severity levels
CRITICAL: Remote code execution, authentication bypass, data exposure
  → Immediate fix, service may be taken offline

HIGH: Privilege escalation, sensitive data access
  → Fix within SLA (typically 24-72h)

MEDIUM: Information disclosure, misconfiguration
  → Fix within regular sprint cycle

LOW: Best practice violations, hardening opportunities
  → Track in backlog, address opportunistically
```

### Audit Process

1. **Scoping**: Define what systems/assets are in scope for the audit
2. **Reconnaissance**: Gather information about targets (open ports, endpoints, dependencies)
3. **Vulnerability scanning**: Automated scanning with tools (Trivy, Semgrep, Snyk)
4. **Manual verification**: Confirm findings, eliminate false positives
5. **Risk assessment**: Rate each finding by impact × likelihood
6. **Remediation planning**: Prioritize fixes, assign ownership
7. **Verification**: Re-scan after fixes to confirm closure
8. **Reporting**: Document findings, evidence, and remediation status

### Defensive Practices

- **Defense in depth**: Multiple security layers (network → app → data)
- **Least privilege**: Minimum necessary permissions for each component
- **Secret rotation**: Regularly rotate API keys, tokens, certificates
- **Audit logging**: Log security-relevant events with integrity protection
- **Incident response**: Predefined playbooks for common security events

## Relationships

- **Related to**: `commit-quality-check` (pre-commit security gates)
- **Works with**: `1password` (secret management), `delete-safety` (safe deletion)
- **Used in**: `godmode` (elevated privilege operations with safeguards)
- **Depends on**: Understanding of OWASP Top 10, CVE databases, security scanning tools
