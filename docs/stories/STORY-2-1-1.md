# STORY-2-1-1: 树状索引工具纳入 cap-pack 项目

> **状态**: `implemented` · **优先级**: P1 · **Epic**: EPIC-002 · **Sprint**: 1
> **SDD 状态**: `implemented` · **创建**: 2026-05-13 · **预估**: 1 轮
> **标签**: `tree-index`, `cap-pack-integration`

---

## 用户故事

**As a** 系统维护者
**I want** `skill-tree-index.py` 纳入 cap-pack 项目的 `scripts/` 目录并关联到 SPEC-2-1
**So that** 树状索引工具与能力包体系绑定发布，而不是孤立地在 Hermes 目录中

## 验收标准

- [x] AC-01: `skill-tree-index.py` 已在 `~/projects/hermes-cap-pack/scripts/` 下
- [x] AC-02: 工具运行时从 cap-pack 项目读取 18 模块定义（模块映射已在脚本中）
- [x] AC-03: `--pack` 参数兼容 cap-pack 的包命名
- [x] AC-04: 输出格式与 cap-pack 格式 v1 兼容
- [x] AC-05: 可作为独立脚本运行（不依赖 Hermes 内部路径）

## 交付

| 项目 | 内容 |
|:-----|:------|
| Bug 修复 | `build_tree()` 未分类 cluster 缺少 `count` 字段 → 已修复 |
| 测试 | `test_epic002_tools.py::TestSkillTreeIndex` — 6 个测试全部通过 |
| 独立运行验证 | ✅ 可在任意目录下运行（依赖 `~/.hermes/skills/` 但这是设计） |
