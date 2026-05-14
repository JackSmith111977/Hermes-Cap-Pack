---
type: concept
domain: skill-quality
keywords: [skill-quality, scoring, sqs, metrics, evaluation]
created: 2026-05-14
---

# Skill Quality Scoring

## Definition

Skill Quality Scoring (SQS) is a quantitative framework for evaluating the quality of AI agent skills. It measures multiple dimensions — completeness, clarity, testability, dependency integrity, and metadata quality — producing a composite score that determines whether a skill is fit for deployment. The threshold for deployment is SQS ≥ 50, ensuring that only well-structured, documented, and verified skills enter the agent's capability ecosystem.

## Core Concepts

### Quality Dimensions

| Dimension | Weight | What It Measures | Evaluation Method |
|:----------|:-------|:-----------------|:-----------------|
| **Completeness** | High | Are all required sections present? | YAML frontmatter check, section audit |
| **Clarity** | High | Can an agent understand the instructions? | Readability analysis, ambiguity detection |
| **Verifiability** | Medium | Are there validation steps? | Presence of examples, test scenarios |
| **Dependency integrity** | High | Are all referenced skills/assets reachable? | `dependency-scan.py` |
| **Metadata quality** | Medium | Are name/description/tags appropriate? | Length, relevance, uniqueness checks |
| **Up-to-dateness** | Low | Is the skill fresh (<90 days since update)? | Last-modified timestamp check |

### Scoring Computation

```
SQS = (Completeness × 0.25) + (Clarity × 0.25) + 
      (Verifiability × 0.15) + (Dependency × 0.20) + 
      (Metadata × 0.10) + (Freshness × 0.05)
```

Each dimension is scored 0-100. The weighted sum produces the final SQS.

### Common Failures

| Issue | Impact | Remedy |
|:------|:-------|:-------|
| **Missing YAML frontmatter** | SQS = 0 (fatal) | Add required metadata fields |
| **Broken skill references** | -20 points | Fix or remove dangling references |
| **No examples** | -15 points | Add at least 1 positive and 1 negative example |
| **Ambiguous instructions** | -20 points | Rewrite steps to be machine-executable |
| **Outdated (>90 days)** | -10 points | Review and update skill content |

### Quality Gates

```
Raw Skill → Auto-QC → SQS ≥ 50? → QA Review → Deploy
  │          │          │            │           │
 Submit    Validate    Yes/No     Human      skill_manage
 SKILL.md  structure   threshold  check      action=create
```

Skills below the threshold are rejected with specific feedback on which dimensions need improvement.

## Relationships

- **Related to**: `quality-assurance` (broader QA framework)
- **Implemented by**: Scripts in `skill-quality/scripts/` and `skill-quality/cron/`
- **Used by**: `skill-creator` (skill creation), `metacognition` (skill lifecycle audit)
- **Depends on**: YAML frontmatter conventions, dependency scanning utilities
- **Enforced by**: Pre-deployment validation gates in the skill management pipeline
