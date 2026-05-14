# 🔧 SPEC-4-2: L2/L3 逐层升级 — Phase 1

> **状态**: `approved` · **优先级**: P0 · **创建**: 2026-05-14
> **SDD 流程**: `CLARIFY ✅ → RESEARCH ✅ → CREATE ✅ → REVIEW ✅ → APPROVED ✅`
> **关联 Epic**: EPIC-004-quality-upgrade.md

---

## 〇、需求澄清 (CLARIFY)

### 用户故事

> **As a** 主人
> **I want** 为全部 16 个能力包补充 L2 Experiences + L3 Knowledge
> **So that** 能力包不再是「SKILL 拷贝集合」，而是真正的三层知识体系

### 范围

| 包含 | 不包含 |
|:-----|:--------|
| ✅ L2 空包补充 Experiences（~10 个包） | ❌ 重写已有 L2（只补充缺失） |
| ✅ 全部 16 包补充 L3 Knowledge | ❌ 修改 skill 内容本身 |
| ✅ L2/L3 模板标准化 | ❌ 低分 skill 修复（Phase 2） |
| ✅ `validate-layers.py` 质量检查脚本 | ❌ CI 门禁集成（Phase 2） |

---

## 一、技术方案 (RESEARCH)

### 现有 L2 分析

| 包 | L2 数量 | 格式 | 质量评估 |
|:---|:-------:|:-----|:---------|
| doc-engine | 11 | 纯 Markdown + `>` frontmatter | 内容丰富 |
| social-gaming | 5 | YAML frontmatter + Markdown | 标准格式 |
| media-processing | 4 | YAML frontmatter + Markdown | 标准格式 |
| financial-analysis | 2 | YAML frontmatter + Markdown | 标准格式 |
| agent-orchestration | 1 | YAML frontmatter + Markdown | 标准格式 |
| developer-workflow | 1 | YAML frontmatter + Markdown | 标准格式 |
| metacognition | 1 | YAML frontmatter + Markdown | 标准格式 |

**选择**：统一使用 **YAML frontmatter 格式**（与 media-processing 一致）

### L2 Experience 模板

```markdown
---
type: <best-practice|lesson-learned|tutorial|case-study>
skill_ref: <关联 skill 名称>
keywords: [关键词1, 关键词2]
created: 2026-05-14
---

# <标题>

## 背景

## 核心内容

## 为什么有效

## 陷阱/注意事项
```

### L3 Knowledge 模板

```markdown
---
type: <concept|entity|summary>
domain: <所属领域>
keywords: [关键词]
created: 2026-05-14
---

# <标题>

## 定义/描述

## 核心要点

## 关联
```

### 执行计划

```
STORY-4-3 (L2 补充) → 4 个 L1-only 包，每个 1-2 篇
  ├── creative-design   (25 skills) → 2 篇
  ├── devops-monitor    (10 skills) → 1 篇
  ├── github-ecosystem  ( 9 skills) → 1 篇
  └── learning-engine   (11 skills) → 2 篇

STORY-4-4 (L3 填充) → 全部 16 包，每包至少 1 篇
  ├── 大型包 (creative-design, developer-workflow) → 3 篇
  ├── 中型包 (8-13 skills) → 2 篇
  └── 小型包 (<8 skills) → 1 篇

STORY-4-5 (模板 + 检查) → 标准化 + validate-layers.py
```

---

## 二、Stories

### STORY-4-3: L2 Experiences 补充（前 4 个空包）

**目标包**：creative-design, devops-monitor, github-ecosystem, learning-engine

**内容**：编写 6 篇 L2 Experience 文档，覆盖每个包的典型使用场景

**产出**：
- `packs/creative-design/EXPERIENCES/` — 2 篇
- `packs/devops-monitor/EXPERIENCES/` — 1 篇
- `packs/github-ecosystem/EXPERIENCES/` — 1 篇
- `packs/learning-engine/EXPERIENCES/` — 2 篇

**估算**: 2h

### STORY-4-4: L3 Knowledge 首次填充

**目标**：全部 16 包，每包至少 1 篇 L3 Knowledge

**内容**：按 concepts/entities/summaries 三类模板编写

**产出**：每包 `KNOWLEDGE/` 目录 + 知识文档

**估算**: 3h

### STORY-4-5: L2/L3 模板标准化 + validate-layers.py

**内容**：
1. 定义标准模板（YAML frontmatter + sections）
2. 编写 `scripts/validate-layers.py` — 检查每个包的 L2/L3 完整性
3. 将 doc-engine 的旧格式 L2（11 篇）迁移到 YAML frontmatter 格式

**产出**：
- `scripts/validate-layers.py` — 层完整性检查脚本
- doc-engine EXPERIENCES 格式迁移完成

**估算**: 1h

---

## 三、验收标准

| AC ID | 描述 | 验证方式 | 优先级 |
|:------|:-----|:---------|:------:|
| AC-01 | 每个 pack 至少 1 篇 L2 Experience | `validate-layers.py` 全部通过 | P0 |
| AC-02 | 每个 pack 至少 1 篇 L3 Knowledge | `validate-layers.py` 全部通过 | P0 |
| AC-03 | `scripts/validate-layers.py` 存在且可运行 | `--help` 有输出 | P0 |
| AC-04 | doc-engine 旧格式 L2 已迁移到新模板 | 抽查 2 篇验证 frontmatter | P1 |
| AC-05 | 全部 141 测试仍然绿 | `pytest scripts/tests/ -q` | P0 |
| AC-06 | project-state.py verify 通过 | exit code 0 | P0 |

---

## 四、依赖

| # | 依赖 | 类型 | 说明 |
|:-:|:-----|:----:|:------|
| 1 | Phase 0 基线数据 | 数据 | 已完成，知道最低分包 |
| 2 | YAML frontmatter 标准 | 规范 | 与 media-processing 现有格式对齐 |
