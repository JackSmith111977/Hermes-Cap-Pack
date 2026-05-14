---
type: concept
domain: learning-engine
keywords: [skill, precipitation, extraction, procedure, automation, knowledge]
created: 2026-05-14
---

# Skill Precipitation

## Definition

Skill Precipitation is the process of extracting repeatable procedures from hands-on experience and encoding them as reusable, executable skills. Unlike raw knowledge (facts and concepts), a skill is a structured capability that an AI agent can invoke directly to accomplish a task. Precipitation transforms tacit, context-specific know-how into explicit, parameterized, and composable skill modules that form the building blocks of agent autonomy.

## Core Concepts

### The Precipitation Workflow

1. **Recognition**: Identify a task that has been performed successfully multiple times (Rule of 3)
2. **Capture**: Document the steps, inputs, outputs, edge cases, and failure modes as an Experience document
3. **Abstraction**: Generalize the procedure — remove hardcoded values, identify parameters and configuration knobs
4. **Formalization**: Write the skill definition (SKILL.md) with name, description, parameters, prompt template, tool bindings, and validation criteria
5. **Testing**: Execute the skill in varied contexts to confirm robustness
6. **Iteration**: Refine based on failures, new edge cases, and user feedback

### Skill Structure

| Component | Description | Example |
|:----------|:------------|:--------|
| **Name** | Unique identifier for the skill | `financial-analysis` |
| **Trigger** | What activates the skill | User request: "analyze AAPL stock" |
| **Parameters** | Configurable inputs | ticker, time_period, output_format |
| **Prompt** | Instruction template for the agent | System prompt guiding analysis steps |
| **Tools** | Bound capabilities the skill can use | yfinance, matplotlib, pandas |
| **Validation** | Criteria to confirm successful execution | Output contains PE ratio, chart, summary |

### Skill Classification

- **Atomic skills**: Single-purpose, minimal dependencies — e.g., `calculate-moving-average`
- **Composite skills**: Orchestrate multiple atomic skills — e.g., `generate-financial-report`
- **Meta-skills**: Skills that create or modify other skills — e.g., `skill-creator`

### Quality Metrics

- **Reliability**: Success rate across different inputs and environments
- **Composability**: Ease of combining with other skills in a workflow
- **Discoverability**: Clear naming and keyword tagging for retrieval
- **Maintainability**: Clear separation of concerns, versioned changes

## Relationships

- **Phase of**: `learning-cycle` (Phase 3 — Precipitate), complements `knowledge-precipitation` (concept-level extraction)
- **Related to**: `skill-creator` (meta-skill for building skills), `learning-workflow` (operational framework)
- **Works with**: `hermes-knowledge-base` (storage), `skill-dispatcher` (execution)
- **Feeds into**: `capability-pack-design` (skills organized into packs by domain)
