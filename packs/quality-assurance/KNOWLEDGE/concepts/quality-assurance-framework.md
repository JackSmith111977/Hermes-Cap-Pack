---
type: concept
domain: quality-assurance
keywords: [qa, testing, quality, validation, verification]
created: 2026-05-14
---

# Quality Assurance Framework

## Definition

Quality Assurance (QA) is a systematic process for ensuring that software, content, and AI agent outputs meet defined quality standards before delivery. Unlike testing (which finds bugs), QA encompasses the entire quality ecosystem — processes, standards, tools, and metrics — that prevent defects and ensure consistency. For AI agent systems, QA extends beyond code quality to include output accuracy, relevance, safety, and adherence to guidelines.

## Core Concepts

### QA Dimensions

| Dimension | What It Covers | Evaluation Method |
|:----------|:---------------|:------------------|
| **Correctness** | Is the output factually accurate? | Fact-checking, cross-referencing |
| **Completeness** | Are all required elements present? | Checklist verification |
| **Consistency** | Does output follow established patterns? | Style guides, formatting checks |
| **Usability** | Is the output clear and actionable? | User feedback, readability scores |
| **Safety** | Does output avoid harmful content? | Content filtering, policy compliance |
| **Performance** | Is the output generated efficiently? | Time/memory benchmarks |

### QA Pipeline

```
Input → Gate Check → Process → Validation → Review → Release
  │         │           │          │          │         │
 Source    Schema     Execute    Verify     Human     Publish
 data      check      workflow   output     review
```

### Automated vs Manual QA

| Aspect | Automated QA | Manual QA |
|:-------|:-------------|:----------|
| **Speed** | Instant feedback | Hours to days |
| **Coverage** | 100% of defined checks | Sample-based |
| **What it catches** | Syntax, schema, regression | Nuance, context, creativity |
| **Best for** | Formatting, linting, validation | UX, tone, appropriateness |
| **Tooling** | CI pipelines, linters, validators | Review checklists, peer review |

### Quality Metrics

- **Defect density**: Issues per unit of output (code: per KLOC, docs: per page)
- **First-pass yield**: Percentage passing QA without rework
- **Mean time to detect**: Average time between defect introduction and discovery
- **Test coverage**: Percentage of code paths or requirements exercised
- **SQS (Skill Quality Score)**: Composite metric for skill quality (50+ threshold)

## Relationships

- **Related to**: `skill-quality` (skill-specific quality scoring)
- **Works with**: `commit-quality-check` (pre-commit quality gates)
- **Implemented by**: QA scripts in `quality-assurance/SCRIPTS/`
- **Used in**: All capability packs for ensuring skill quality standards
