---
type: concept
domain: github-ecosystem
keywords: [github-actions, ci, cd, automation, workflows, devops]
created: 2026-05-14
---

# GitHub Actions

## Definition

GitHub Actions is a continuous integration and continuous delivery (CI/CD) platform that automates software workflows directly within GitHub repositories. Workflows are triggered by GitHub events — push, pull request, issue creation, schedule, or manual dispatch — and execute in configurable runner environments. Each workflow is a YAML-defined sequence of jobs and steps that can build, test, package, release, and deploy code across any platform.

## Core Concepts

### Workflow Anatomy

- **Event trigger**: The GitHub activity that starts a workflow, e.g., `push`, `pull_request`, `schedule`, `workflow_dispatch`
- **Runner**: The virtual machine or container that executes jobs — GitHub-hosted (Ubuntu, Windows, macOS) or self-hosted
- **Job**: A logical unit of work composed of multiple steps, running on a single runner; jobs can depend on each other via `needs:`
- **Step**: An individual task — run a shell command or invoke an Action (a reusable unit of automation from the Marketplace)
- **Action**: Pre-built automation packages published as Docker containers or JavaScript; actions like `actions/checkout@v4` or `actions/setup-node@v4` handle common setup tasks
- **Matrix strategy**: Run the same job across multiple OS, language versions, or environment configurations in parallel

### Configuration Structure

```yaml
name: CI
on: [push, pull_request]
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: npm ci && npm test
```

### Common Workflow Patterns

| Pattern | Use Case | Key Actions |
|:--------|:---------|:------------|
| **CI** | Run tests on every push/PR | `checkout`, `setup-node`, `npm test` |
| **CD** | Deploy after tests pass | `checkout`, `docker-login`, deploy script |
| **Release** | Tag, build, publish artifact | `semantic-release`, `upload-release-asset` |
| **Scheduled** | Nightly cron jobs | `schedule: cron`, data exports, cleanup |
| **Dependency** | Auto-update dependencies | `dependabot`, `renovate` |

### Best Practices

- Pin Actions to full commit SHA for supply-chain security
- Use OIDC tokens instead of long-lived secrets for cloud authentication
- Cache dependencies (npm, pip, Gradle) with `actions/cache` to speed workflows
- Use concurrency groups to cancel redundant in-progress runs
- Set minimum `permissions:` at the job level — the principle of least privilege

## Relationships

- **Related to**: `git-workflow` (branching model determines trigger strategy), `github-pr-workflow` (PR automation tie-in)
- **Works with**: `actions/checkout`, `actions/setup-*`, `actions/cache`, `docker/login-action`
- **Depends on**: `.github/workflows/` directory conventions, GitHub repository permissions
- **Complemented by**: `github-api` (talking to GitHub programmatically), `github-project-ops` (project management)
