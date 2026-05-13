# STORY-016: SRA 分类映射表 + 树状索引 SRA 感知

> **状态**: `draft` · **优先级**: P1 · **Epic**: EPIC-002 · **Sprint**: 2
> **SDD 状态**: `draft` · **创建**: 2026-05-13 · **预估**: 1 轮
> **标签**: `sra`, `category-mapping`, `tree-index`

---

## 用户故事

**As a** 系统架构师
**I want** CAP Pack 的 18 模块分类体系可以被 SRA 消费，且树状索引输出 SRA 友好的格式
**So that** SRA 的类别维度（15%权重）不再靠猜标签，而是直接使用经过验证的分类体系

## 验收标准

- [ ] AC-01: `packs/categories/cap-pack-categories.yaml` 包含 18 模块别名映射表
- [ ] AC-02: skill-tree-index 新增 `--sra` 模式，输出含 `cluster` + `pack` + `siblings`
- [ ] AC-03: SRA 加载分类映射表后 30 条测试查询的类别匹配精度提升 >15%
- [ ] AC-04: 分类映射表格式兼容 SRA indexer 的 `extract_keywords` 流程
- [ ] AC-05: 映射表文档说明如何扩展（新增模块时同步更新）

## 技术方案

1. 创建 `packs/categories/cap-pack-categories.yaml`（18 模块别名 + 权重）
2. 修改 `scripts/skill-tree-index.py` 新增 `--sra` 标志：
   - 输出每个 skill 的 `pack`, `cluster`, `siblings` 字段
   - 输出簇级摘要（簇内技能数和平均 SQS）
3. SRA 侧配置：设置 `categories_file` 指向 CAP Pack 的映射表
4. 测试方法论：选 30 个典型用户查询，对比 Before/After 类别匹配精度

## 不做的

- 修改 SRA 核心匹配算法
- 实时同步（周期性刷新即可）

## 测试

- 精度测试: `python3 scripts/skill-tree-index.py --sra --pack doc-engine --json` 验证输出格式
