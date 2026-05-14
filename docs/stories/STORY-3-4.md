# STORY-3-4: cap-pack upgrade + search + status 命令

> **状态**: `draft` · **优先级**: P0 · **Epic**: EPIC-003 · **Spec**: SPEC-3-2
> **SDD 状态**: `draft` · **创建**: 2026-05-14
> **标签**: `cli`, `upgrade`, `search`, `status`

## 用户故事

**As a** 主人
**I want** 通过 `cap-pack upgrade <name>` / `search <term>` / `status` 管理能力包
**So that** 无需手动操作文件

## 验收标准

- [ ] AC-01: upgrade 对比版本号、备份、安装、验证
- [ ] AC-02: upgrade --dry-run 不实际修改
- [ ] AC-03: search 扫描 packs/ 目录并匹配关键词
- [ ] AC-04: status 显示已安装/可用/质量指标
- [ ] AC-05: 101 测试全绿
