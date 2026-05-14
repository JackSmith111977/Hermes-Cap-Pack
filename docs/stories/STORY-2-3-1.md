# STORY-2-3-1: SRA 分类映射表 + 树状索引 SRA 感知

> **状态**: `implemented` · **优先级**: P1 · **Epic**: EPIC-002 · **Sprint**: 2
> **SDD 状态**: `implemented` · **创建**: 2026-05-13 · **预估**: 1 轮
> **标签**: `sra`, `category-mapping`, `tree-index`

---

## 用户故事

**As a** 系统架构师
**I want** CAP Pack 的 18 模块分类体系可以被 SRA 消费，且树状索引输出 SRA 友好的格式
**So that** SRA 的类别维度（15%权重）不再靠猜标签，而是直接使用经过验证的分类体系

## 验收标准

- [x] AC-01: `packs/categories/cap-pack-categories.yaml` 包含 18 模块别名映射表
- [x] AC-02: skill-tree-index 已有 `--sra` 模式，输出含 `cluster` + `pack` + `siblings` + `avg_sqs`
- [ ] AC-03: SRA 加载分类映射表后 30 条测试查询类别匹配精度提升 >15%（需 SRA 侧集成验证）
- [x] AC-04: 分类映射表格式兼容 SRA indexer 的 `extract_keywords` 流程
- [x] AC-05: 映射表文档说明如何扩展（含新增模块步骤 + SRA 集成说明）

## 交付物

| 文件 | 说明 |
|:-----|:------|
| `packs/categories/cap-pack-categories.yaml` | 18 模块分类映射表（含别名/权重/模式/扩展指南） |
| `scripts/skill-tree-index.py --sra` | 已验证输出完整的 `pack`/`cluster`/`siblings`/`avg_sqs` 字段 |
