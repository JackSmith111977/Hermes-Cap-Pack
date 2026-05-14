---
type: concept
domain: developer-workflow
keywords: [code-review, pr, collaboration, quality]
created: 2026-05-14
---

# Code Review Patterns

## Definition

Code Review is the systematic examination of software source code by peers before integration into the main codebase. It serves as a quality gate, knowledge sharing mechanism, and collaborative learning opportunity. Effective code review patterns balance thoroughness with speed, providing constructive feedback without creating bottlenecks.

## Core Concepts

### Review Focus Areas

| Dimension | What to Check | Example Concerns |
|:----------|:--------------|:-----------------|
| **Correctness** | Does it work correctly? | Edge cases, error handling, logic errors |
| **Design** | Is the architecture sound? | Separation of concerns, coupling, extensibility |
| **Readability** | Is it easy to understand? | Naming, comments, complexity, consistency |
| **Performance** | Are there efficiency issues? | N+1 queries, memory leaks, unnecessary computation |
| **Security** | Are vulnerabilities introduced? | Input validation, auth bypass, injection |
| **Testing** | Is there adequate test coverage? | Missing test cases, brittle tests, false positives |

### Review Workflows

```
# Synchronous (Pair Review)
Two developers review together in real-time
→ Fast, high-bandwidth, knowledge intensive
→ Good for: Complex changes, security-sensitive code

# Asynchronous (PR-based)
Reviewer examines code independently, comments in PR
→ Flexible, documented, auditable
→ Good for: Most changes, distributed teams

# Lightweight (Pre-commit / Linting)
Automated checks before human review
→ Catches style, formatting, obvious bugs
→ Essential for: All PRs, frees humans for logic review
```

### Effective Review Techniques

- **Read the diff, not the file**: Focus on changes, ignore untouched code
- **Review test coverage first**: Tests reveal the author's understanding of requirements
- **Prioritize by severity**: Blocking issues > design concerns > style suggestions
- **Explain the "why"**: Comments should explain impact, not just "this is wrong"
- **Limit to ~400 LOC per session**: Attention drops after 60-90 minutes

### Code Review Anti-Patterns

| Anti-pattern | Description | Remedy |
|:-------------|:------------|:-------|
| **Nitpicking** | Focusing on trivial style issues | Use auto-formatters, merge quickly |
| **Rubber stamping** | Approving without thorough review | Use checklist, enforce minimum review time |
| **Design by committee** | Endless debate on alternatives | Author decides after collecting opinions |
| **Review gatekeeping** | Blocking for personal preferences | Separate blocking from non-blocking feedback |
| **Drive-by review** | Commenting without ownership | Assign explicit reviewers with responsibility |

## Relationships

- **Works with**: `requesting-code-review` (skill for effective review requests)
- **Related to**: `test-driven-development` (TDD produces reviewable, testable code)
- **Enforced by**: `writing-styles-guide` (consistency in code style)
- **Supported by**: `github-code-review` for GitHub-specific PR workflows
- **Input for**: `github-pr-workflow` (PR management pipeline)
