---
type: concept
domain: agent-orchestration
keywords: [agent-orchestration, orchestration, multi-agent, coordination, workflow]
created: 2026-05-14
---

# Agent Orchestration

## Definition
Agent orchestration is the coordination and management of multiple AI agents working together to accomplish complex tasks. It involves defining workflows, assigning responsibilities, managing communication, and handling state across agents.

## Core Concepts
- **Orchestrator Agent**: A central agent that decomposes tasks, delegates subtasks to specialized agents, and aggregates results into a coherent final output.
- **Task Decomposition**: Breaking a high-level user request into discrete, manageable subtasks that can be assigned to different agents based on capability.
- **Agent Registry**: A catalog of available agents with descriptions of their capabilities, tools, and specializations, used by the orchestrator for routing.
- **Inter-Agent Communication**: The protocols and data structures used for passing context, intermediate results, and status updates between agents.
- **State Management**: Maintaining conversation history, task status, and context across multi-turn orchestration sessions.

## Relationships
- Works closely with **Subagent Delegation** for granular task assignment
- Relies on **Tool Selection** mechanisms for agent capabilities
- Feeds into **Workflow Management** systems for structured execution
