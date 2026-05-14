---
type: concept
domain: network-proxy
keywords: [proxy, network, configuration, clash, routing]
created: 2026-05-14
---

# Network Proxy Configuration

## Definition

Network Proxy Configuration involves setting up and managing intermediary servers that route, filter, or modify network traffic between clients and destinations. For AI agents operating in restricted network environments (corporate firewalls, geo-restricted services, rate-limited APIs), proper proxy configuration is essential for reliable internet access. The domain covers proxy protocols (HTTP, SOCKS), subscription management (proxy lists), routing rules (domains, IP ranges), and authentication.

## Core Concepts

### Proxy Protocols and Types

| Type | Protocol | Use Case |
|:-----|:---------|:---------|
| **HTTP proxy** | HTTP CONNECT | Web browsing, API access |
| **SOCKS5 proxy** | TCP/UDP tunneling | General traffic, P2P |
| **Transparent proxy** | No client config | Network-level redirection |
| **Reverse proxy** | Server-side | Load balancing, caching |
| **VPN** | TUN interface | Full system routing |

### Clash Configuration

Clash is a rule-based proxy client that supports subscription-based proxy lists and fine-grained routing rules.

```yaml
# Core Clash concepts
proxies:         # List of proxy servers (from subscription or manual)
proxy-groups:    # Logical groups with selection strategies (url-test, fallback, select)
rules:           # Domain/IP matching to direct or proxy through specific groups
  - DOMAIN-SUFFIX,google.com,Proxy
  - GEOIP,CN,DIRECT
  - MATCH,Proxy
```

### Routing Strategies

| Strategy | Behavior | Best For |
|:---------|:---------|:---------|
| **Direct** | Bypass proxy entirely | Local network, trusted sites |
| **Global** | Route all traffic through proxy | Strong privacy requirements |
| **Rule-based** | Route by domain/geo/IP | Balancing speed vs privacy |
| **Auto (latency)** | Select fastest proxy dynamically | Performance optimization |
| **Fallback** | Try primary, fail to secondary | Reliability |

### Key Considerations

- **Authentication**: Some proxies require username/password or token-based auth
- **DNS leakage**: Ensure DNS queries also go through proxy (not direct)
- **Protocol filtering**: Some proxies block certain protocols (WebSocket, UDP)
- **Rotation**: Proxy pools need health checking and rotation to avoid rate limits
- **Subscription updates**: Proxy lists change; implement periodic refresh

## Relationships

- **Implemented by**: `clash-config` (Clash configuration skill), `proxy-finder` (proxy discovery)
- **Depends on**: `web-access` (skill for agent web requests through proxy)
- **Related to**: Network infrastructure monitoring, geo-restriction bypass
- **Used in**: Scenarios requiring IP rotation, regional access, or corporate network compliance
