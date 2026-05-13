# STORY-1-4-8: OpenCode CLI 适配器实现

> **story_id**: `STORY-1-4-8`
> **status**: `implemented`
> **priority**: P1
> **epic**: EPIC-001-feasibility
> **spec_ref**: SPEC-1-4
> **created**: 2026-05-13
> **implemented**: 2026-05-13
> **owner**: boku

---

## 用户故事

> **As a** OpenCode CLI 用户
> **I want** 通过 `cap-pack install` 将能力包安装到 OpenCode 环境
> **So that** OpenCode 也能使用 boku 沉淀的能力

## 验收标准

- [x] AC1: `OpenCodeAdapter` 实现 `AgentAdapter` Protocol 全部方法
- [x] AC2: skill 安装到 `~/.config/opencode/skills/{id}/SKILL.md`，frontmatter 转换为 OpenCode 兼容格式
- [x] AC3: MCP 配置写入 `~/.config/opencode/opencode.json` 的 `mcp` 字段
- [x] AC4: `uninstall()` 删除对应 skill 目录
- [x] AC5: `verify()` 检查 skill 文件完整性
- [x] AC6: 利用 OpenCode 对 `~/.claude/skills/` 的原生兼容性

## 引用链

- SPEC-1-4: [docs/SPEC-1-4.md](../SPEC-1-4.md)
- 前序 Story: STORY-020-hermes-adapter
- 参考: https://opencode.ai/docs/skills/

## 不做的范围

- ❌ Claude Code 适配器
- ❌ 在线注册中心集成
