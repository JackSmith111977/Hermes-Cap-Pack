# STORY-4-7: 缺失元数据补充（cap-pack.yaml 补齐字段）

> **状态**: `completed` · **Epic**: EPIC-004 · **Spec**: SPEC-4-3
> **SDD 状态**: `completed` · **创建**: 2026-05-14

---

## 用户故事

**As a** 主人
**I want** 全部 16 个能力包的 cap-pack.yaml 包含完整的元数据字段
**So that** 能力包可以被自动化工具正确索引和发现

## 验收标准

- [ ] AC-01: 每个 cap-pack.yaml 至少包含 name/version/description/author/triggers
- [ ] AC-02: YAML 格式合法（yaml.safe_load 通过）
- [ ] AC-03: description 至少 2 句话（功能 + 适用场景）
- [ ] AC-04: project-state.py verify 通过

## 范围

| 包含 | 不包含 |
|:-----|:--------|
| ✅ 16 个包的 `packs/*/cap-pack.yaml` | ❌ SKILL.md 内容修改 |
| ✅ name/version/description/author/triggers | ❌ 非元数据的配置字段 |
| ✅ YAML 语法验证 | |

## 依赖关系

- 前置: STORY-4-6（低分 skill 改进）
