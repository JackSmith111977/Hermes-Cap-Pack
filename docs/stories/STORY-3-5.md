# STORY-3-5: cap-pack skill 子命令（add/remove/list/update）

> **状态**: `implemented` · **优先级**: P0 · **Epic**: EPIC-003 · **Spec**: SPEC-3-2
> **SDD 状态**: `completed` · **创建**: 2026-05-14
> **标签**: `cli`, `skill-management`

## 用户故事

**As a** 主人
**I want** 通过 `cap-pack skill add/remove/list/update` 管理包内具体技能
**So that** 不需要编辑 YAML 文件就能调整能力包内容

## 验收标准

- [ ] AC-01: skill add 从 Hermes 或路径复制 skill 到包中
- [ ] AC-02: skill remove 安全移除并备份
- [ ] AC-03: skill list 显示包内所有技能详情
- [ ] AC-04: skill update 从 Hermes 同步最新版本
- [ ] AC-05: 101 测试全绿
