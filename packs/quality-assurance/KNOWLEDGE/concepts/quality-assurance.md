---
type: concept
domain: quality-assurance
keywords: [qa, testing, validation, quality-gate, regression, coverage, smoke-test]
created: 2026-05-14
---

# Quality Assurance

## Definition

Quality Assurance (QA) in AI agent systems encompasses the processes, tools, and criteria used to validate that skills, tools, and agent behaviors meet defined quality standards before deployment. QA spans automated testing (unit tests, integration tests, smoke tests), manual review gates (peer review, style checks), metric-driven validation (skill quality scores ≥ threshold), and regression prevention (comparing outputs against baselines). A robust QA pipeline catches failures early, enforces consistency, and maintains trust in agent outputs.

## Core Concepts

### QA Pipeline Stages

```yaml
stages:
  - lint:         syntax, style, naming conventions
  - unit:         individual function/tool correctness
  - integration:  cross-tool workflows, API contracts
  - smoke:        critical path walks, happy-path validation
  - regression:   baseline comparison, output diffing
  - gate:         quality score threshold check (SQS ≥ 50)
```

### Quality Gates

A quality gate is a hard checkpoint that blocks promotion. Common gates include: test coverage minimum, linting zero-warnings, skill scoring above floor, documentation completeness, and backwards-compatibility verification.

### Regression Testing Strategy

For AI agents, regression means verifying that new code doesn't break existing conversation patterns. This is done by replaying previous successful interactions and comparing outputs for semantic equivalence, not just exact string matching.
