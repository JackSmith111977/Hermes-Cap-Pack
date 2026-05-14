---
type: concept
domain: agent-orchestration
keywords: [multi-agent, orchestration, delegation, coordination]
created: 2026-05-14
---

# Multi-Agent Orchestration

## Definition

Multi-Agent Orchestration is the practice of coordinating multiple independent AI agents to work together on complex tasks. It involves task decomposition, agent delegation, context management, and result synthesis. Unlike single-agent systems, orchestrated multi-agent setups can parallelize work, bring diverse perspectives, and handle larger problem spaces.

## Core Concepts

### Orchestration Topologies

| Topology | Description | Use Case |
|:---------|:------------|:---------|
| **Sequential** | Agents execute one after another | Pipeline processing, staged reviews |
| **Parallel (Fan-out)** | Multiple agents work simultaneously | Independent research, parallel code review |
| **Hierarchical** | Orchestrator delegates to sub-agents | Complex project management |
| **Debate/Judge** | Agents argue positions, judge decides | Decision making, quality evaluation |
| **Swarm** | Many agents collaborate without central control | Exploration, creative ideation |

### Delegation Patterns

- **Task delegation**: Orchestrator assigns subtasks with clear scope and context
- **Context compression**: Summarize conversation history to ≤400 words per sub-agent
- **Result collection**: Gather outputs when sub-agents complete or time out
- **Synthesis**: Combine results into coherent final output

### Key Design Decisions

- **Number of agents**: Too few = single point of failure; too many = coordination overhead
- **Agent specialization**: Each agent should have a distinct role/persona
- **Communication model**: Direct message passing vs shared workspace vs blackboard pattern

## Relationships

- **Works with**: `message-injection` for passing context to sub-agents
- **Related to**: Party Mode pattern (parallel spawning of agents)
- **Depends on**: Message routing infrastructure (gateway hooks, SRA)
- **Used by**: Complex problem-solving workflows requiring multiple perspectives
