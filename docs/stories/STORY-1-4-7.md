# STORY-1-4-7: Hermes 适配器回滚机制

> **story_id**: `STORY-1-4-7`
> **status**: `implemented`
> **priority**: P1
> **epic**: EPIC-001-feasibility
> **spec_ref**: SPEC-1-4
> **created**: 2026-05-13
> **implemented**: 2026-05-13
> **owner**: boku

---

## 用户故事

> **As a** Hermes 适配器用户
> **I want** 安装失败时自动回滚到安装前状态
> **So that** 即使安装出错也不会破坏现有环境

## 验收标准

- [x] AC1: 安装前自动创建快照（skills + MCP 配置 + 跟踪状态）
- [x] AC2: 安装异常时自动从快照恢复
- [x] AC3: 安装成功后自动清理快照
- [x] AC4: `uninstall` 从 `.bak` 备份恢复被替换的 skill

## 引用链

- SPEC-1-4: [docs/SPEC-1-4.md](../SPEC-1-4.md)
- 前序 Story: STORY-020-hermes-adapter
