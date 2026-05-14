---
type: concept
domain: github-ecosystem
keywords: [github-actions, ci, cd, automation, workflows]
created: 2026-05-14
---

# GitHub Actions CI/CD

## Definition

GitHub Actions is a CI/CD and automation platform integrated into GitHub repositories. It enables defining automated workflows triggered by GitHub events (push, PR, issue, schedule) that run in configurable compute environments. Workflows are defined as YAML files in the `.github/workflows/` directory and can build, test, deploy, and orchestrate virtually any software lifecycle task.

## Core Concepts

### Workflow Architecture

```
Event → Trigger → Workflow → Job → Step → Action
  │         │         │        │      │       │
 Push   on:push   .yml file  build  Node      actions/
 PR     schedule   name:test  test   Run      checkout@v4
 Issue  workflow_  needs:     deploy Shell     setup-node
        dispatch  [build]     Run              cache
```

### Core Components

| Component | Description | Example |
|:----------|:------------|:--------|
| **Workflow** | Configurable automated process | `ci.yml`, `deploy.yml` |
| **Event** | Trigger that starts the workflow | `push`, `pull_request`, `schedule` |
| **Job** | Set of steps on a single runner | `build`, `test`, `lint` |
| **Step** | Individual task within a job | `actions/checkout@v4`, `npm test` |
| **Action** | Reusable unit of automation | Community actions, Docker containers |
| **Runner** | Compute environment executing jobs | GitHub-hosted, self-hosted |

### Key Features

- **Matrix builds**: Run jobs across multiple OS/version combinations in parallel
- **Dependency caching**: Cache `node_modules`, `~/.cache/pip`, Gradle caches for speed
- **Secrets management**: Encrypted environment variables per repo/environment
- **OIDC integration**: Use short-lived tokens instead of long-lived cloud credentials
- **Concurrency control**: Cancel in-progress runs, serialize deployment jobs
- **Artifacts**: Share files between jobs, download from completed runs

### Security Best Practices

- Use `pull_request_target` carefully (runs with base branch secrets)
- Pin action versions to full commit SHA for supply chain security
- Limit permissions with `permissions:` block at workflow or job level
- Never log secrets or pass them to untrusted actions

## Relationships

- **Works with**: `github-pr-workflow` (PR automation), `github-deploy-upload` (deployment)
- **Related to**: `github-project-ops` (project management automation), `git-advanced-ops`
- **Depends on**: Repository structure, `.github/workflows/` directory conventions
- **Companion to**: `github-auth` (authentication for actions), `github-api` usage
