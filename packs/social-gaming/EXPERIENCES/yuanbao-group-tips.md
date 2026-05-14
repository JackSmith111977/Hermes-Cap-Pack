---
type: pitfall
skill_ref: yuanbao
keywords: [yuanbao, 元宝, group, mention, 艾特]
---

# 元宝群聊 @ 功能注意

## @ 艾特用户
- 必须先用 `yb_query_group_members(action="find", name="...", mention=true)` 获取准确昵称
- 回复中用 `@nickname` 格式，网关自动转换
- **不要猜测昵称** — 必须调工具查询

## 私信 (DM)
- 使用 `yb_send_dm` 工具，不是 `send_message`
- 支持图片附件
- `group_code` 从 chat_id 提取：`group:328306697` → `328306697`

## 查询
| 操作 | 用途 |
|:-----|:------|
| find | 按名称搜索用户（模糊匹配） |
| list_bots | 列出机器人和 AI 助手 |
| list_all | 列出所有群成员 |
