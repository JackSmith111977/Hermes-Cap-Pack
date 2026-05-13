# Story: 模块边界判断标准决策树

> **story_id**: `STORY-002-boundary-tree`
> **status**: `draft`
> **priority**: P1
> **epic**: EPIC-001-feasibility
> **spec_ref**: SPEC-001-splitting
> **created**: 2026-05-13
> **owner**: boku

---

## 用户故事

> **As a** 能力包的维护者
> **I want** 一个可执行的决策树来判断新能力属于哪个模块
> **So that** 新增 skill 时无需人工判断分类

## 验收标准

- [ ] AC1: 决策树以可执行形式存在（Python 函数或 YAML 规则）
- [ ] AC2: 决策树覆盖 4 种场景（已有领域/多领域交叉/全新领域/暂存观察）
- [ ] AC3: 至少 10 个测试用例验证决策树输出正确
- [ ] AC4: 决策树与 SPEC-001 的 18 模块分类保持一致

## 引用链

- EPIC-001: [docs/EPIC-001-feasibility.md](../EPIC-001-feasibility.md)
- SPEC-001: [docs/SPEC-001-splitting.md](../SPEC-001-splitting.md)
- 前序 Story: STORY-001-splitting-analysis

## 不做的范围

- ❌ 自动分类 AI 模型（仅规则引擎）
