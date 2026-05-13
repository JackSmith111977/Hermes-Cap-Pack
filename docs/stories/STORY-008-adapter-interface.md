# Story: 适配层接口抽象定义

> **story_id**: `STORY-008-adapter-interface`
> **status**: `draft`
> **priority**: P1
> **epic**: EPIC-001-feasibility
> **spec_ref**: SPEC-004-adaptation
> **created**: 2026-05-13
> **owner**: boku

---

## 用户故事

> **As a** 适配器开发者
> **I want** 一个清晰的 `AgentAdapter` 抽象接口定义
> **So that** 我可以为 Claude Code、Codex CLI 等 Agent 实现适配器而不需要理解 UCA 全貌

## 验收标准

- [ ] AC1: `AgentAdapter` Protocol 定义（install/uninstall/update/list_installed/verify）
- [ ] AC2: 每个方法的输入输出类型明确定义
- [ ] AC3: 适配器接口与 UCA 架构文档保持一致
- [ ] AC4: 接口定义以 Python Protocol 形式实现

## 引用链

- EPIC-001: [docs/EPIC-001-feasibility.md](../EPIC-001-feasibility.md)
- SPEC-004: [docs/SPEC-004-adaptation.md](../SPEC-004-adaptation.md)
