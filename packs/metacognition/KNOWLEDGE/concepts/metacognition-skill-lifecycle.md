---
type: concept
domain: metacognition
keywords: [metacognition, self-awareness, skill-lifecycle, capability-mapping]
created: 2026-05-14
---

# Metacognition and Skill Lifecycle

## Definition

Metacognition in an AI agent context is the system's ability to understand, evaluate, and improve its own capabilities. It encompasses skill lifecycle management (create → deploy → maintain → deprecate), capability auditing (knowing what skills exist and their quality), and self-improvement (identifying gaps, updating outdated knowledge, retiring obsolete skills). A metacognitive system can introspect on its own knowledge base and make strategic decisions about what to learn or unlearn.

## Core Concepts

### Skill Lifecycle

```
CREATE → QA GATE → DEPLOY → MAINTAIN → AUDIT → DEPRECATE
  │         │          │         │         │          │
 S1-S9    SQS ≥ 50  skill_    Version  Freshness   Impact
 flow     Check deps manage   tracking   check     analysis
```

Each phase has defined tools and gates. The QA gate prevents low-quality skills from entering the ecosystem. The audit phase periodically reevaluates freshness and relevance.

### Capability Mapping Method

**Inversion principle**: Instead of listing "what tools do I have?", start from "what problems can I solve?" and work backward to capability boundaries.

1. **Enumerate all skills** — scan SKILLS directories for SKILL.md files
2. **Extract name + description + tags** — identify purpose and domain
3. **Cluster by domain** — let skills self-organize into categories
4. **Identify gaps** — compare current capabilities against desired domain coverage
5. **Audit quality** — check SQS scores, freshness, dependency integrity

### Architectural Decision Framework

When deciding whether a component belongs as a runtime, tool, skill, or standalone package:

```markdown
Is it a long-lived daemon?
  ├─ ✅ → Runtime (independent service, HTTP API)
  └─ ❌ → Agent uses on-demand?
      ├─ Atomic operation? → Tool (Hermes built-in)
      └─ Complex procedure? → Skill (SKILL.md knowledge unit)
```

### Self-Improvement Cycle

1. **Audit**: Scan current capabilities, identify weak areas
2. **Research**: Find better patterns, tools, or knowledge
3. **Create/Update**: Write new skills or update existing ones
4. **Verify**: Run quality checks, test in real scenarios
5. **Deploy**: Make the improvement available system-wide

## Relationships

- **Related to**: `self-capabilities-map` (skill for capability auditing)
- **Works with**: `skill-creator` (creating/updating skills), `skill-quality` (scoring)
- **Implemented in**: `architecture-trilemma` (decision framework), `design-philosophy-migration`
- **Supported by**: `skill-to-pypi` (packaging skills as standalone libraries)
