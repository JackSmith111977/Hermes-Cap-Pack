---
type: concept
domain: messaging
keywords: [event-driven, pub-sub, webhook, callback, async-communication, event-bus]
created: 2026-05-14
---

# Event-Driven Communication

## Definition

Event-Driven Communication is an architectural pattern where system components react to events rather than polling or direct invocation. In an AI agent context, events include incoming messages, tool execution results, state changes, and system signals (timeouts, errors, lifecycle hooks). An event bus decouples producers from consumers, allowing asynchronous, loosely coupled interactions that improve reliability, scalability, and responsiveness.

## Core Concepts

### Event Types

| Type | Source | Example |
|:-----|:-------|:--------|
| **Message Event** | Platform adapter | User sends a message, reply received |
| **Tool Event** | Tool execution | Code returned output, API call finished |
| **State Event** | Agent runtime | Task started, memory updated, context switched |
| **System Event** | Infrastructure | Rate limit hit, connection lost, heartbeat timeout |

### Pub/Sub Topology

```
Producers → Event Bus → Subscribers (agents, hooks, loggers)
                │
                ├─ Fan-out: all subscribers get a copy (broadcast)
                └─ Queue: one consumer processes each event (work queue)
```

Webhooks extend this pattern outward: external services push events to the agent via HTTP callbacks, enabling integrations like CI/CD notifications, payment confirmations, and third-party API responses without polling.
