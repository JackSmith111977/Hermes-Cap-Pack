---
type: pitfall
skill_ref: gif-search
keywords: [tenor, gif, api-key, rate-limit, format]
---

# GIF 搜索陷阱 (Tenor API)

## API Key 配置
- 必须设置 `TENOR_API_KEY` 环境变量
- 获取方式：Google Cloud Console → 启用 Tenor API → 免费 key
- 未设置时 curl 报 403 或 key missing 错误
- 建议加入 `~/.hermes/.env`

## Rate Limit
- 免费配额：每天约 100-200 次请求
- 超出后返回 429 Too Many Requests
- 缓解：缓存常用 GIF 搜索结果，用 local 文件避免重复请求

## 格式选择
| 场景 | 推荐格式 | 理由 |
|:-----|:---------|:------|
| Telegram/Discord 发送 | `tinygif` | 体积小，加载快 |
| 网页嵌入 | `gif` (原始) | 质量最高 |
| 预览/缩略图 | `nanogif` | 极小体积 |
| 视频格式 | `mp4`/`tinymp4` | GIF 的替代，文件更小 |

## Search Query 技巧
- 空格编码用 `+` 而非 `%20`
- 支持 `contentfilter` 参数：`off`/`low`/`medium`/`high`
- `locale` 参数可影响搜索结果排序
