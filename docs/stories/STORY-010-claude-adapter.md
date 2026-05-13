# Story: Claude Code 适配器实现

> **story_id**: `STORY-010-claude-adapter`
> **status**: `draft`
> **priority**: P1
> **epic**: EPIC-001-feasibility
> **spec_ref**: SPEC-004-adaptation
> **created**: 2026-05-13
> **owner**: boku

---

## 用户故事

> **As a** Claude Code 用户
> **I want** 将能力包安装到 Claude Code 环境中
> **So that** Claude Code 也能使用 boku 沉淀的文档排版等能力

## 验收标准

- [ ] AC1: 适配器将 SKILLS/ 内容写入 `~/.claude/skills/{pack}/{id}.md`
- [ ] AC2: MCP 配置写入 `claude.json` 的 mcpServers 字段
- [ ] AC3: EXPERIENCES/ 嵌入 CLAUDE.md 或 skills reference
- [ ] AC4: 支持与 Hermes 相同的基本操作（install/remove/status）

## 引用链

- EPIC-001: [docs/EPIC-001-feasibility.md](../EPIC-001-feasibility.md)
- SPEC-004: [docs/SPEC-004-adaptation.md](../SPEC-004-adaptation.md)
- 前序 Story: STORY-008-adapter-interface, STORY-009-hermes-adapter

## 不做的范围

- ❌ Codex CLI 适配器（Phase 3）
- ❌ 全量 20+ Agent 适配
