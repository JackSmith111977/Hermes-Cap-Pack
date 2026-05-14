---
type: concept
domain: metacognition
keywords: [metacognition, reflection, self-assessment, introspection, cognitive-patterns]
created: 2026-05-14
---

# Metacognition Patterns

## Definition

Metacognition Patterns describe structured approaches an AI agent uses to reason about its own reasoning, evaluate its outputs, and adapt its behavior. These patterns go beyond simple tool use — they encompass recursive thinking (planning a plan), confidence calibration (knowing what you don't know), selective attention (choosing which context to focus on), and error recovery (detecting and correcting mistakes). A metacognitive agent can answer "how did I arrive at this conclusion?" and "what should I do differently next time?"

## Core Concepts

### Reflection Loop

The agent processes a task, then reflects on its process using prompt-level introspection. This loop can repeat multiple times — each pass refines the reasoning chain and catches errors before output.

### Confidence Calibration

Agents assign explicit confidence scores (high/medium/low) to their assertions based on evidence strength, source reliability, and knowledge freshness. Low-confidence outputs trigger additional verification steps (search, tool use, deferred response) rather than producing guesswork.

### Selective Context Management

Not all context is equally relevant. Metacognitive agents prune conversation history, prioritize recent evidence, and actively decide what to forget or summarize — preventing context window pollution while preserving critical information.
