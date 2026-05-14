---
type: concept
domain: messaging
keywords: [messaging-platforms, feishu, discord, telegram, slack, channel-adapter, protocol]
created: 2026-05-14
---

# Messaging Platforms

## Definition

Messaging Platforms covers the integration patterns and adapters for connecting AI agents to various chat and collaboration platforms. Each platform (Feishu/Lark, Discord, Telegram, Slack, WeChat) has unique API semantics, rate limits, message formatting, authentication flows, and real-time capabilities. A platform-agnostic agent architecture abstracts these differences behind a unified messaging interface while preserving platform-specific features like rich embeds, interactive components, and voice channels.

## Core Concepts

### Platform Abstraction Layer

| Platform | Transport | Auth Model | Key Features |
|:---------|:----------|:-----------|:-------------|
| **Feishu/Lark** | Webhook + WebSocket | App ID/Secret + Tenant Token | Rich cards, doc integration, calendar |
| **Discord** | WebSocket Gateway | Bot Token | Slash commands, embeds, voice, threads |
| **Telegram** | Long Polling / Webhook | Bot Token | Inline keyboards, file upload, polls |
| **Slack** | RTM / Socket Mode | Bot Token + Signing Secret | Blocks, modals, workflows, channels |

### Adapter Pattern

Each platform implements a `MessagingAdapter` interface with common methods (`send_message`, `edit_message`, `react`, `upload_file`) plus optional platform-specific extensions. Adapters handle token refresh, reconnection, rate-limit backoff, and message formatting conversion.
