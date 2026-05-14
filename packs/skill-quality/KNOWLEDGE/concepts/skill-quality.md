---
type: concept
domain: skill-quality
keywords: [skill-quality, scoring, metrics, maintainability, readability, documentation, sqs]
created: 2026-05-14
---

# Skill Quality

## Definition

Skill Quality defines the measurable attributes that determine whether a skill (a packaged agent capability) is fit for production use. Quality is assessed across multiple dimensions — correctness, maintainability, documentation completeness, test coverage, error handling, and performance. The Skill Quality Score (SQS) aggregates these dimensions into a single numeric threshold that gates deployment. A high-quality skill is reliable, well-documented, gracefully handles edge cases, and is easy for other agents (or humans) to understand and modify.

## Core Concepts

### Quality Dimensions

| Dimension | Metric | Weight |
|:----------|:-------|:-------|
| **Correctness** | Tests pass, outputs match spec | High |
| **Maintainability** | Code complexity, modularity | Medium |
| **Documentation** | README completeness, inline comments | Medium |
| **Error Handling** | Graceful failure, clear error messages | Medium |
| **Performance** | Latency, token efficiency | Low |
| **Security** | Input sanitization, no hardcoded secrets | High |

### Scoring Formula (SQS)

SQS is a weighted composite score (0-100). Skills scoring below the threshold (e.g., < 50) are rejected at the QA gate. Scores decay over time if a skill isn't maintained — freshness checks trigger re-evaluation.

### Continuous Quality

Quality isn't a one-time gate. Skills are re-scored periodically, on dependency updates, and when issues are reported. A quality dashboard tracks trends, highlighting skills that need attention before they break.
