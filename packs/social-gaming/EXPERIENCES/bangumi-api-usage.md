---
type: pitfall
skill_ref: bangumi-recommender
keywords: [bangumi, anime, api, query, search]
---

# Bangumi API 使用陷阱

## User-Agent 要求
Bangumi API 强制要求 User-Agent 头。脚本已内置。严禁移除或修改。

## 接口说明
| 功能 | 脚本命令 | 说明 |
|:-----|:---------|:------|
| 新番表 | `calendar` | 本周所有在播番剧 |
| 排行榜 | `rank` | 历史高分番剧排名 |
| 搜索 | `search <keyword>` | 按名称/标签搜索 |

## ID 类型注意
- `subject_id` = 条目 ID（番剧、电影、书籍）
- `person_id` = 人物 ID（声优、制作人员）
- 不要混淆两者

## 数据更新
- 番组表每周更新（日本动画季）
- 排行榜每日更新
- 脚本缓存约 1 小时
