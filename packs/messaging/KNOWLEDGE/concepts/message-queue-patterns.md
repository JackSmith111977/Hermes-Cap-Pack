---
type: concept
domain: messaging
keywords: [messaging, queue, broadcast, notification, patterns]
created: 2026-05-14
---

# Message Queue and Notification Patterns

## Definition

Message Queue and Notification Patterns describe the strategies for delivering messages from a producer (an AI agent or system) to consumers (users, services, or other agents). These patterns address reliability (message delivery guarantees), scalability (handling many recipients), timing (immediate vs scheduled), and channel selection (where to send). A robust messaging system ensures critical notifications reach their destination without overwhelming recipients.

## Core Concepts

### Delivery Models

| Model | Description | Use Case |
|:------|:------------|:---------|
| **Direct** | One-to-one, immediate | Personal notifications, replies |
| **Broadcast** | One-to-many, all recipients | Announcements, alerts |
| **Multicast** | One-to-selected-group | Team notifications, role-based messages |
| **Fan-out** | One message → multiple channels | Cross-platform notifications |
| **Queue** | Buffered, consumer-controlled | Background processing, load leveling |

### Message Delivery Guarantees

- **At-most-once**: Best effort, can lose messages (fast, no retry) — logging, non-critical updates
- **At-least-once**: Retry on failure, can duplicate — alerts, task assignments
- **Exactly-once**: Deduplication + retry — financial transactions, critical commands

### Routing Patterns

- **Content-based**: Route based on message content (e.g., error severity → urgent channel)
- **Topic-based**: Subscribe to topics/channels (e.g., `deploy.success`, `monitor.critical`)
- **Recipient list**: Explicitly list recipients (e.g., list of user IDs)
- **Dynamic routing**: Route based on runtime conditions (e.g., on-call rotation)

### Notification Fatigue Prevention

- **Aggregation**: Combine multiple notifications into a digest
- **Throttling**: Limit notification frequency per recipient
- **Prioritization**: Critical (immediate) vs informational (digest)
- **Opt-in/opt-out**: Respect user preference for notification channels
- **Silent hours**: Suppress non-critical notifications during defined periods

## Relationships

- **Implemented by**: `smart-broadcast` (intelligent message routing), `feishu-batch-send` (bulk sending)
- **Related to**: `feishu-integration` (primary messaging platform), `agentmail` (email fallback)
- **Used in**: `kanban-orchestrator` (task notifications), `webhook-subscriptions` (event-driven messaging)
- **Depends on**: Message format standards, delivery infrastructure
