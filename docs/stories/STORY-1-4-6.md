# STORY-1-4-6: Hermes Agent 适配器实现

> **story_id**: `STORY-1-4-6`
> **status**: `implemented`
> **priority**: P0
> **epic**: EPIC-001-feasibility
> **spec_ref**: SPEC-1-4
> **created**: 2026-05-13
> **implemented**: 2026-05-13
> **owner**: boku

---

## 用户故事

> **As a** Hermes Agent 用户
> **I want** 通过 `cap-pack install` 一键安装能力包到 Hermes 环境（含 MCP 配置自动注入）
> **So that** 无需手动配置，即装即用

## 验收标准

- [x] AC1: `HermesAdapter` 实现 `AgentAdapter` Protocol 的全部方法
- [x] AC2: `install()` 将 skill 文件复制到 `~/.hermes/skills/`
- [x] AC3: `install()` 将 MCP 配置注入到 `~/.hermes/config.yaml mcp_servers`
- [x] AC4: `uninstall()` 删除 skill 并从备份恢复
- [x] AC5: `verify()` 检查 skill 文件完整性
- [x] AC6: `list_installed()` 返回已安装包列表

## 引用链

- SPEC-1-4: [docs/SPEC-1-4.md](../SPEC-1-4.md)
- 前序 Story: STORY-019-uca-cli
- 后序 Story: STORY-021-hermes-rollback

## 不做的范围

- ❌ Claude Code 适配器
- ❌ Codex CLI 适配器
- ❌ 可视化仪表盘
