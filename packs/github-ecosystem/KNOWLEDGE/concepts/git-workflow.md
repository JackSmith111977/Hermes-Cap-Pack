---
type: concept
domain: github-ecosystem
keywords: [git, workflow, branching, merging, collaboration, version-control]
created: 2026-05-14
---

# Git Workflow

## Definition

Git Workflow is a standardized branch management strategy that governs how developers collaborate on a shared codebase. It defines conventions for branch creation, naming, merging, and release management. A well-chosen workflow minimizes merge conflicts, enforces code review gates, aligns with CI/CD pipelines, and ensures that the main branch remains deployable at all times.

## Core Concepts

### Popular Branching Models

| Model | Branches | Best For |
|:------|:---------|:---------|
| **GitHub Flow** | `main` + short-lived feature branches | Continuous deployment, simple projects |
| **Git Flow** | `main`, `develop`, `feature/*`, `release/*`, `hotfix/*` | Scheduled releases, complex products |
| **Trunk-Based** | `main` (trunk) + very short feature branches | CI/CD at scale, large engineering orgs |
| **GitLab Flow** | `main`, `pre-production`, `production` | Environment-aligned deployments |

### Key Operations

- **Pull request (PR)**: The primary mechanism for code review and merge gating; branches are merged via squash, merge commit, or rebase
- **Squash merge**: Condenses all feature branch commits into one commit on the target branch — clean history for linear stories
- **Merge commit**: Preserves full branch topology with a merge commit — useful for collaborative feature branches
- **Rebase**: Rewrites commit history to appear as if work started from the latest target branch tip — produces linear history but requires force push
- **Cherry-pick**: Selectively applies individual commits from one branch to another — used for hotfixes and backports

### Branch Naming Convention

```
type/description        e.g., feat/user-auth, fix/null-pointer
types: feat, fix, chore, docs, refactor, test, hotfix
```

### Conflict Resolution Strategy

1. Pull target: `git pull origin main`
2. Rebase feature branch: `git rebase main`
3. Resolve each conflicted file — accept, edit, or use `git mergetool`
4. Continue: `git rebase --continue`
5. Force push: `git push --force-with-lease`

### Integration with CI/CD

Git workflow directly affects CI/CD efficiency: trunk-based workflows deploy continuously on every merge; Git Flow staggers releases through release branches; GitHub Flow uses PR-triggered CI checks as quality gates before allowing a merge.

## Relationships

- **Related to**: `github-actions` (CI/CD triggers depend on branching model), `github-pr-workflow` (PR lifecycle)
- **Works with**: `git-advanced-ops` (rebase, bisect, submodules), `codebase-inspection` (code review)
- **Depends on**: Git fundamentals (commit, branch, merge, rebase), team conventions
- **Input to**: `github-code-review` (reviewing PRs within the chosen workflow model)
