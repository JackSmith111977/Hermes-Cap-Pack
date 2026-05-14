---
type: concept
domain: social-gaming
keywords: [gaming-platforms, minecraft, bangumi, steam, game-apis, multiplayer, game-servers]
created: 2026-05-14
---

# Gaming Platforms

## Definition

Gaming Platforms covers the integration landscape of game-related services and APIs that agents can interact with to enhance gaming experiences. This includes game server orchestration (Minecraft Paper/Spigot), game databases and catalogs (Steam, RAWG, IGDB), anime and media databases (Bangumi, MyAnimeList), and gaming community platforms (Discord game SDK, Xbox Live). Each platform has its own authentication model, rate limits, and data schema, requiring platform-specific adapters within a unified gaming integration layer.

## Core Concepts

### Platform Categories

| Category | Platforms | Agent Role |
|:---------|:----------|:-----------|
| **Game Servers** | Minecraft, Valheim, Terraria | Deployment, backup, mod management |
| **Game Catalogs** | Steam, RAWG, IGDB, Epic | Search, recommendations, sales tracking |
| **Media Databases** | Bangumi, MAL, AniList | Watch history, ratings, episode tracking |
| **Gaming Communities** | Discord, Steam Friends | Party coordination, event scheduling |

### Server Orchestration Pattern

Game servers are managed via Docker containers with volume mounts for world data. The agent handles lifecycle (start/stop/restart), backup scheduling, mod installation, and whitelist management. Health checks monitor server process, player count, and resource usage.

### Data Integration Flow

```
Agent → Query → Platform API Adapter → Rate Limiter → External API
                ↑                                    ↓
           Cache (TTL)                    Normalized Response
```

All external gaming API calls are cached with platform-appropriate TTLs to respect rate limits while maintaining responsive user interactions.
