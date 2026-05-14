---
type: concept
domain: github-ecosystem
keywords: [git, workflow, branching, merging, collaboration]
created: 2026-05-14
---

# Git Workflow Strategies

## Definition

Git Workflow Strategies are standardized patterns for using Git branching and merging to enable team collaboration. A good workflow defines when to create branches, how to name them, how changes flow between branches, and when to merge or rebase. The choice of workflow impacts code quality, release frequency, conflict resolution, and team coordination overhead.

## Core Concepts

### Branching Models

| Model | Structure | Best For |
|:------|:----------|:---------|
| **GitHub Flow** | `main` → feature branches → PR → `main` | Continuous deployment, small teams |
| **Git Flow** | `main` + `develop` + feature/release/hotfix branches | Scheduled releases, complex projects |
| **Trunk-based** | Short-lived feature branches, frequent merges to `main` | CI/CD, large teams, DevOps culture |
| **GitLab Flow** | Environment branches (`staging`, `production`) + feature branches | Deployment pipeline alignment |

### Key Operations

```
# Merging (preserves history)
git checkout main
git merge feature/foo   # creates merge commit

# Rebasing (linear history)
git checkout feature/foo
git rebase main          # replays commits on top of main
git checkout main
git merge feature/foo    # fast-forward

# Cherry-pick (selective commits)
git cherry-pick <commit-hash>
```

### Best Practices

- **Branch naming**: `type/description` — `feature/add-login`, `fix/null-pointer`, `chore/update-deps`
- **Commit messages**: Conventional Commits format — `feat:`, `fix:`, `chore:`, `docs:`
- **Atomic commits**: Each commit is a single logical change, with passing tests
- **PR size**: Keep under 400 lines changed — large PRs reduce review quality
- **Merge strategy**: Squash merge for feature branches, merge commit for collaborative branches

### Conflict Resolution

1. Pull latest target branch: `git pull origin main`
2. Rebase feature branch: `git rebase main` (conflicts appear here, not at merge)
3. Resolve each conflict in order, using `git mergetool` or manual edit
4. Continue rebase: `git rebase --continue`
5. Force push if branch was previously pushed: `git push --force-with-lease`

## Relationships

- **Related to**: `github-pr-workflow` (PR lifecycle), `github-repo-management` (repo setup)
- **Works with**: `git-advanced-ops` (advanced Git operations), `codebase-inspection`
- **Depends on**: Understanding of Git fundamentals (commit, branch, merge, rebase)
- **Input to**: `github-code-review` (reviewing PRs within the chosen workflow)
