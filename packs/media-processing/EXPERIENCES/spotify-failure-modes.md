---
type: pitfall
skill_ref: spotify
keywords: [spotify, music, playback, error, device, premium]
---

# Spotify 集成陷阱与恢复策略

## 常见错误码

| HTTP | 错误 | 原因 | 处理方式 |
|:----:|:-----|:-----|:---------|
| 403 | No active device | Spotify 未在任何设备运行 | 告知用户先打开 Spotify 播放一首歌 |
| 403 | Premium required | 免费账号尝试修改播放 | 只读操作可用，写操作需要 Premium |
| 204 | (empty) | 没有正在播放的内容 | 不是错误，直接报告 |
| 429 | Too Many Requests | 限流 | 等待后重试一次，如果还不行通知用户 |
| 401 | Unauthorized | token 过期 | 告知用户重新 `hermes auth spotify` |

## 最佳实践

### 不要做的事
- ❌ 每次操作前调 `get_state` — 直接 play/pause/skip 即可
- ❌ 对 403 Premium/no device 盲目重试 — 永久性错误
- ❌ 用 `spotify_search` 搜索用户歌单 — 搜的是公开目录
- ❌ 混用 `kind: "tracks"` 和 album URI — API 端点是分开的

### 推荐的 URI 格式
优先使用完整 URI：`spotify:track:0DiWol3AO6WpXZgp0goxAV`
