---
type: concept
domain: developer-workflow
keywords: [debugging, methodology, root-cause, systematic]
created: 2026-05-14
---

# Debugging Methodology

## Definition

Debugging Methodology is a systematic approach to identifying, isolating, and resolving software defects. Unlike ad-hoc debugging (random print statements, guessing), a methodology provides a repeatable process: reproduce the defect, formulate hypotheses, isolate the root cause, implement a fix, and verify the resolution. This transforms debugging from an art into an engineering discipline.

## Core Concepts

### The Debugging Cycle

1. **Reproduce** — Get a reliable, minimal reproduction case
2. **Isolate** — Narrow the scope using binary search, divide-and-conquer
3. **Hypothesize** — Formulate theories about the root cause
4. **Test** — Verify or falsify each hypothesis with experiments
5. **Fix** — Apply the minimal correction needed
6. **Verify** — Confirm the fix works and no regression
7. **Learn** — Document the root cause and prevention strategy

### Isolation Techniques

| Technique | Method | Best For |
|:----------|:-------|:---------|
| **Binary search** | Comment out half the code, check | Large codebases, unknown location |
| **Rubber duck** | Explain problem aloud step by step | Logic errors, assumptions |
| **Diff bisect** | Git bisect on commit history | Regression tracking |
| **Observation** | Logging, tracing, breakpoints | Runtime behavior issues |
| **Comparison** | Compare working vs non-working versions | Environmental/setup issues |

### Root Cause Analysis

- **5 Whys**: Ask "why" 5 times to peel back layers of symptoms
- **Dependency tracing**: Follow the call stack and data dependencies backward
- **Breadth-first**: Check all inputs and preconditions before deep logic analysis
- **Occam's razor**: The simplest explanation (typo, config, race condition) is most likely

### Debugging Mindset

- **Assume nothing**: Verify every assumption with empirical evidence
- **Change one variable**: Multiple simultaneous changes invalidate conclusions
- **Read the error message**: Error messages contain precise location and type information
- **Check the obvious first**: Is it plugged in? Is the service running? Is the API key valid?

## Relationships

- **Companion to**: `test-driven-development` (tests prevent debug cycles)
- **Related to**: `systematic-debugging` skill, `python-debugpy` (tooling)
- **Relies on**: `node-inspect-debugger` for Node.js debugging workflows
- **Supported by**: `one-three-one-rule` (allocating time for debugging within development cycles)
