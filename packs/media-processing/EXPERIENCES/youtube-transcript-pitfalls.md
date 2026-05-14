---
type: pitfall
skill_ref: youtube-content
keywords: [youtube, transcript, subtitle, language, chunking]
---

# YouTube 字幕获取陷阱

## 语言处理
- 视频可能没有目标语言的字幕
- `--language en,tr` 逗号分隔，按优先级回退
- 如果指定语言找不到 → 自动回退到第一个可用语言
- 用 `--text-only` 不带语言参数获取任何可用字幕

## 视频不可用
| 错误原因 | 处理方法 |
|:---------|:---------|
| 字幕已禁用 | 告知用户检查视频页面是否有 CC |
| 私密/下架视频 | 确认 URL 是否正确 |
| 地区限制 | 无法绕过，建议用户自查 |

## 大篇幅处理
- 50K+ 字符的脚本需要分块
- 推荐：40K 字符块 + 2K 重叠，逐块摘要后合并
- 保持时间戳连续性（分块边界对齐句子）

## 依赖
- `pip install youtube-transcript-api` 必须提前安装
- YouTube API 可能版本更新，接口签名变化 — 用 `pip install -U` 更新
