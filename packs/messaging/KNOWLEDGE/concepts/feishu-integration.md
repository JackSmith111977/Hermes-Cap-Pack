---
type: concept
domain: messaging
keywords: [feishu, lark, bot, integration, messaging]
created: 2026-05-14
---

# Feishu (Lark) Integration

## Definition

Feishu (Lark outside China) is an all-in-one collaboration platform combining messaging, document editing, calendar, and workflow automation. Its bot API enables AI agents to interact within Feishu workspaces — sending messages, creating documents, updating calendars, and responding to user commands. Integration patterns range from simple notification bots to complex interactive assistants with rich card messages.

## Core Concepts

### Feishu API Architecture

```
Agent → Feishu Bot API → Feishu Platform → User
  │          │                │              │
  │    Send message     Message queue   Receive in
  │    Create doc       Event hooks     chat/doc
  │    Update calendar  Card rendering  Interactive
```

### Message Types

| Type | Description | Use Case |
|:-----|:------------|:---------|
| **Text** | Plain text message | Quick notifications |
| **Rich text** | Markdown-formatted content | Formatted updates with links |
| **Card** | Interactive JSON card | Buttons, forms, data display |
| **Image** | Inline image display | Charts, screenshots, diagrams |
| **File** | File attachment | Reports, documents, assets |
| **Voice** | Audio message | Voice notes, recordings |

### Card Message Design

```json
{
  "config": { "wide_screen_mode": true },
  "header": { "title": { "tag": "plain_text", "content": "Title" } },
  "elements": [
    { "tag": "markdown", "content": "**Bold text** with [link](url)" },
    { "tag": "hr" },
    { "tag": "button", "text": { "tag": "plain_text", "content": "Click me" } }
  ]
}
```

### Key Integration Patterns

- **Streaming responses**: Use card message merging to stream token-by-token responses
- **Batch sending**: Send to multiple chats/users efficiently via batch API
- **Event subscription**: Listen for `im.message.receive_v1` to build interactive bots
- **Card callback**: Handle button clicks for interactive workflows
- **File upload**: Attach images and documents with upload-then-send pattern

## Relationships

- **Related to**: `feishu-send-file` (file attachment), `feishu-batch-send` (bulk messaging)
- **Works with**: `feishu-card-merge-streaming` (streaming card updates)
- **Depends on**: Feishu app credentials (App ID, App Secret), tenant access token
- **Companion to**: `agentmail` (email alternative), `smart-broadcast` (targeted messaging)
