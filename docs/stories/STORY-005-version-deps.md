# Story: 版本号与依赖管理规范

> **story_id**: `STORY-005-version-deps`
> **status**: `draft`
> **priority**: P1
> **epic**: EPIC-001-feasibility
> **spec_ref**: SPEC-002-management
> **created**: 2026-05-13
> **owner**: boku

---

## 用户故事

> **As a** 能力包的消费者
> **I want** 能力包有清晰的版本号和依赖声明
> **So that** 我知道升级是否安全，是否有破坏性变更

## 验收标准

- [ ] AC1: 语义版本号规则 MAJOR.MINOR.PATCH 已文档化，明确每种变更对应的版本号变化
- [ ] AC2: 依赖声明支持 cap_packs / system_packages / python_packages / node_packages 四种类型
- [ ] AC3: 依赖版本约束支持精确版本（==）、范围（>=、<=）和兼容（^、~）
- [ ] AC4: `validate-pack.py` 能检查依赖声明的格式正确性

## 引用链

- EPIC-001: [docs/EPIC-001-feasibility.md](../EPIC-001-feasibility.md)
- SPEC-002: [docs/SPEC-002-management.md](../SPEC-002-management.md)
