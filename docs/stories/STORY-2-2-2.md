# STORY-2-2-2: 自动健康 cron 定时报告

> **状态**: `implemented` · **优先级**: P2 · **Epic**: EPIC-002 · **Sprint**: 2
> **SDD 状态**: `implemented` · **创建**: 2026-05-13 · **预估**: 1 轮
> **标签**: `cron`, `health-report`, `automation`

---

## 用户故事

**As a** 主人
**I want** 每周自动收到 skill 系统健康度报告
**So that** 不需要手动运行工具就能了解技能库的整体状况，及时发现退化

## 验收标准

- [x] AC-01: cron 每周自动运行 `skill-tree-index.py --json` + 健康度分析
- [x] AC-02: 报告通过飞书发送给主人（`deliver: feishu`）
- [x] AC-03: 报告包含: 全貌摘要（包数/技能数/微小skill/未分类）+ 模块分布 Top 5
- [x] AC-04: 无严重变化时发送精简版，发现退化时发送完整版（智能检测低分技能/总数/未分类变化）
- [x] AC-05: 可手动触发 `cronjob action='run' job_id=<id>`

## 交付物

| 文件 | 说明 |
|:-----|:------|
| `scripts/health-report.py` | 健康度报告生成器 v2（智能简报/完整版切换） |
| `~/.hermes/scripts/health-report.py` | 部署到 cron 脚本目录 |
| Cron job `weekly-health-report` | 每周日 09:00 自动执行 → 飞书 |
