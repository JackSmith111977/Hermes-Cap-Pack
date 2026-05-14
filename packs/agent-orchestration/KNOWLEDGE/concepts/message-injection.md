---
type: concept
domain: agent-orchestration
keywords: [message-injection, context, sra, prefix]
created: 2026-05-14
---

# Message Injection

## Definition

Message Injection is a mechanism for inserting contextual information into an AI agent's message stream at runtime. Unlike system prompt modification (which affects caching and may be ignored), message injection appends or prepends content directly to user messages, ensuring the agent sees the injected context in its most recent input.

## Core Concepts

### Injection Points

| Mechanism | Timing | Blocking? | Can Modify? |
|-----------|--------|-----------|-------------|
| **`agent:start` hooks** | Before LLM call | Async non-blocking | No (side effects only) |
| **`run_conversation()` prefix** | Before message queued | Sync blocking | Yes |
| **System prompt injection** | At conversation start | Sync | Yes (but cache-unfriendly) |
| **Tool response injection** | After tool execution | Sync | Yes |

### SRA (Skill Runtime Advisor) Pattern

- SRA daemon runs as an HTTP service, listening for skill recommendations
- At message time, Hermes queries SRA for context relevant to the current conversation
- The recommended context is injected as a prefix to the user message
- Design preserves LLM prompt caching (system prompt unchanged)
- Fast-fail with 2-second timeout — never blocks message delivery

### Design Principles

1. **Cache-friendly**: Modify user message prefix, not system prompt
2. **Graceful degradation**: On failure, pass empty context (no user-visible error)
3. **Deduplication**: Cache MD5 hashes to avoid redundant HTTP calls
4. **Minimal latency**: Sub-second timeout, keep-alive connections

## Relationships

- **Depends on**: SRA daemon (runtime service), gateway hooks infrastructure
- **Used by**: `agent-orchestration` patterns for context passing
- **Related to**: `hermes-agent` configuration for enabling/disabling injection
- **Alternative to**: System prompt engineering (different caching properties)
