# STORY-1-2-1: 模块生命周期状态机设计

> **story_id**: `STORY-1-2-1`
> **status**: `draft`
> **priority**: P1
> **epic**: EPIC-001-feasibility
> **spec_ref**: SPEC-1-2
> **created**: 2026-05-13
> **owner**: boku

---

## 用户故事

> **As a** 能力包的管理者
> **I want** 每个能力包有一个明确的生命周期状态机
> **So that** 我知道哪些包是稳定的、哪些是实验性的、哪些该退休了

## 验收标准

- [ ] AC1: 六阶段生命周期定义（DRAFT → ACTIVE → MATURING → STABLE → DEPRECATED → ARCHIVED）
- [ ] AC2: 每个阶段有明确的进入条件和退出条件
- [ ] AC3: 状态机实现为 Python 类，支持状态查询和转换
- [ ] AC4: 状态转换自动记录到生命周期日志

## 引用链

- EPIC-001: [docs/EPIC-001-feasibility.md](../EPIC-001-feasibility.md)
- SPEC-1-2: [docs/SPEC-1-2.md](../SPEC-1-2.md)
