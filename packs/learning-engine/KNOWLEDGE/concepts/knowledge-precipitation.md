---
type: concept
domain: learning-engine
keywords: [knowledge, precipitation, extraction, skill-creation]
created: 2026-05-14
---

# Knowledge Precipitation

## Definition

Knowledge Precipitation is the process of transforming tacit knowledge (gained through experience, intuition, and practice) into explicit, structured, and reusable knowledge artifacts. Just as water vapor condenses into liquid, insights and patterns from practical work solidify into documents, skills, and conceptual models that can be shared, reviewed, and applied by others (including AI agents).

## Core Concepts

### The Precipitation Pipeline

```
Experience → Pattern Recognition → Documentation → Abstraction → Skill Creation
    │               │                    │              │              │
 Practice      "I've done this     Write an       Generalize    Encapsulate
               three times"       Experience      to other     as SKILL.md
                                  doc             contexts
```

### Knowledge Artifact Types

| Artifact | Tacit→Explicit | Reusability | Format |
|:---------|:---------------|:------------|:-------|
| **Experience doc** | Low (context-bound) | Medium | EXPERIENCES/*.md |
| **Concept doc** | Medium (generalized) | High | KNOWLEDGE/concepts/*.md |
| **Skill** | High (procedural) | Very high | SKILLS/*/SKILL.md |
| **Checklist** | High (step-by-step) | Very high | Markdown checklist |
| **Template** | High (fill-in-blank) | Very high | Code/Markdown template |
| **Decision tree** | Very high (branching) | Very high | Mermaid/flowchart |

### When to Precipitate

- **Rule of 3**: If you've done something three times the same way, it's ready for precipitation
- **Pain point**: If a task is error-prone or confusing, document the correct procedure
- **Aha moment**: When you finally understand something tricky, capture it immediately
- **Teaching opportunity**: If you need to explain something, formalize it first

### Quality Criteria

- **Completeness**: Does it cover the full workflow? Edge cases?
- **Clarity**: Can someone (or an AI agent) follow it without additional context?
- **Verifiability**: Are there validation steps to confirm correct execution?
- **Connectedness**: Does it link to related concepts and skills?

## Relationships

- **Phase of**: `learning-cycle` (Phase 3: Precipitate)
- **Implemented by**: `skill-creator` (skill extraction), `knowledge-precipitation` (skill)
- **Related to**: `hermes-knowledge-base` (storage and retrieval)
- **Output feeds**: `capability-pack-design` (knowledge organized into packs)
- **Requires**: `learning-workflow` for regular practice
