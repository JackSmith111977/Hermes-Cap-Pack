---
type: concept
domain: agent-orchestration
keywords: [subagent, delegation, task-routing, agent-specialization, parallel-execution]
created: 2026-05-14
---

# Subagent Delegation

## Definition
Subagent delegation is the mechanism by which a primary agent hands off specific subtasks to subordinate agents. Each subagent operates within a bounded scope with its own tools, system prompt, and execution context, returning results to the delegating agent.

## Core Concepts
- **Delegation Decision**: The orchestrator determines which subagent to invoke based on capability matching, current load, and task complexity.
- **Context Passing**: The parent agent passes relevant context, conversation history, and specific instructions to the subagent at invocation time.
- **Result Aggregation**: The orchestrator collects responses from multiple subagents, resolving conflicts and synthesizing a unified result.
- **Error Handling**: Strategies for subagent failure include retry, fallback to alternative agents, and graceful degradation.
- **Parallel vs Sequential Delegation**: Subagents may run concurrently for independent tasks or sequentially when subtasks have dependencies.

## Relationships
- Enables **Agent Orchestration** by providing the execution primitive for task distribution
- Integrates with **Tool Registry** for discovering subagent capabilities
- Supports **Workflow Automation** patterns like map-reduce and chain-of-thought
