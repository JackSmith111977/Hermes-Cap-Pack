---
type: concept
domain: developer-workflow
keywords: [code-review, peer-review, quality-assurance, best-practices, linting]
created: 2026-05-14
---

# Code Review

## Definition
Code review is the systematic examination of source code by peers to identify defects, enforce coding standards, share knowledge, and improve overall code quality before merging into the main branch.

## Core Concepts
- **Review Checklist**: A standardized set of criteria covering correctness, readability, performance, security, test coverage, and adherence to project conventions.
- **Diff-Based Review**: Changes are reviewed as a diff against the base branch, with comments attached to specific lines. Tools like GitHub PRs or Gerrit facilitate this workflow.
- **Automated Checks**: Linters, formatters, and static analyzers (ESLint, Ruff, mypy) catch style and correctness issues before human review begins.
- **Knowledge Sharing**: Review is a two-way learning process — reviewers learn from novel approaches, authors benefit from experienced perspectives.
- **Merge Criteria**: Typical gates include approval from at least one reviewer, all automated checks passing, and no unresolved comments.

## Relationships
- Validates code produced through **TDD Cycle** against quality standards
- Ensures implementation matches the design described in **SDD Workflow** specifications
- Triggers **CI/CD Pipeline** re-runs when review feedback generates new commits
