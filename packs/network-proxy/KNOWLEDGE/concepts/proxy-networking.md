---
type: concept
domain: network-proxy
keywords: [proxy, networking, reverse-proxy, forward-proxy, tunnel, load-balancer, gateway]
created: 2026-05-14
---

# Proxy Networking

## Definition

Proxy Networking encompasses the architectural patterns for routing, filtering, and transforming network traffic between clients and servers. In an AI agent context, proxies manage API access (rate limiting, authentication injection), service discovery (routing to the right backend), security (traffic inspection, DDoS protection), and protocol conversion (HTTP → gRPC, WebSocket upgrades). Proxies operate at different OSI layers — Layer 4 (TCP/UDP) for simple forwarding, Layer 7 (HTTP/HTTPS) for content-aware routing.

## Core Concepts

### Proxy Types

| Type | Direction | Purpose |
|:-----|:----------|:--------|
| **Forward Proxy** | Client → Proxy → Internet | Anonymity, caching, access control |
| **Reverse Proxy** | Internet → Proxy → Backend | Load balancing, TLS termination, shielding |
| **Transparent Proxy** | Intercepts without config | Content filtering, monitoring |
| **SOCKS Proxy** | Generic TCP/UDP tunnel | Bypass restrictions, protocol agnostic |

### Common Proxy Features

- **TLS Termination**: Decrypt incoming HTTPS, forward plain HTTP to internal services
- **Load Balancing**: Distribute requests across backends (round-robin, least-connections, IP hash)
- **Rate Limiting**: Throttle per client, per route, or per backend
- **Request Rewriting**: Modify headers, paths, or query params before forwarding
- **Health Checking**: Remove unhealthy backends from rotation automatically

### Proxy Chains and Transparent Tunneling

Multiple proxies can be chained (forward → reverse → egress) for layered security, and transparent proxies use iptables or eBPF to intercept traffic without client configuration.
