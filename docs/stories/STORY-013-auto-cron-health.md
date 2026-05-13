# STORY-013: 自动健康 cron 定时报告

> **状态**: `draft` · **优先级**: P2 · **Epic**: EPIC-002 · **Sprint**: 2
> **SDD 状态**: `draft` · **创建**: 2026-05-13 · **预估**: 1 轮
> **标签**: `cron`, `health-report`, `automation`

---

## 用户故事

**As a** 主人
**I want** 每周自动收到 skill 系统健康度报告
**So that** 不需要手动运行工具就能了解技能库的整体状况，及时发现退化

## 验收标准

- [ ] AC-01: cron 每周自动运行 `skill-tree-index.py --health` + `skill-lifecycle-audit.py --audit`
- [ ] AC-02: 报告通过飞书发送给主人
- [ ] AC-03: 报告包含: 全貌摘要、低分技能列表、变化趋势
- [ ] AC-04: 无严重变化时发送精简版，发现退化时发送完整版
- [ ] AC-05: 可手动触发 `cronjob action='run' job_id=<id>`

## 技术方案

1. 使用 Hermes cronjob 系统创建每周任务
2. 脚本组合 `skill-tree-index.py --json` + `skill-lifecycle-audit.py --audit --json`
3. 输出格式化后发送到飞书 home channel
4. 设置交付目标为 `"origin"`（当前对话）

## 不做的

- 实时告警（只做定期报告）
- 自动修复退化

## 测试

- 手动触发一次 cron 确认报告格式和送达
