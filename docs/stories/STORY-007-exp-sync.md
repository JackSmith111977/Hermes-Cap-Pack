# Story: 经验与技能的同步更新机制

> **story_id**: `STORY-007-exp-sync`
> **status**: `draft`
> **priority**: P2
> **epic**: EPIC-001-feasibility
> **spec_ref**: SPEC-003-iteration
> **created**: 2026-05-13
> **owner**: boku

---

## 用户故事

> **As a** boku 的使用者
> **I want** 当我更新一个 skill 时，相关的经验文档也同步更新
> **So that** 经验和技能不会脱节——经验说 A 但技能步骤已是 B

## 验收标准

- [ ] AC1: 经验-技能关联检测机制（在 skill 更新时自动检查关联经验）
- [ ] AC2: 至少 3 种经验类型（pitfall/decision-tree/comparison/lesson）的更新模板
- [ ] AC3: 更新通知机制——当经验与技能脱节时发出警告

## 引用链

- EPIC-001: [docs/EPIC-001-feasibility.md](../EPIC-001-feasibility.md)
- SPEC-003: [docs/SPEC-003-iteration.md](../SPEC-003-iteration.md)
- 前序 Story: STORY-006-feedback-loop

## 不做的范围

- ❌ 自动修复（仅检测和通知）
