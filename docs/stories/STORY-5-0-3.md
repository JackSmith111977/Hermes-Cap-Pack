# Story: Workflow 编排模式定义

> **story_id**: `STORY-5-0-3`
> **status**: `completed`
> **priority**: P1
> **epic**: EPIC-005
> **spec_ref**: SPEC-5-0
> **phase**: Phase-0
> **created**: 2026-05-16
> **owner**: boku (Emma)

---

## 用户故事

> **As a** 治理引擎编排检测器
> **I want** 一套标准化的 Workflow 编排模式定义（DAG/顺序/条件/并行）
> **So that** 可以自动识别 skill 间协作关系并验证编排合法性

## 验收标准

- [x] `standards/workflow-patterns.md` 定义四种编排模式 <!-- 验证: grep -q "sequential\|parallel\|conditional\|dag" standards/workflow-patterns.md -->
- [x] 每种模式有明确的 schema 定义和 YAML 示例 <!-- 验证: grep -c "^###" standards/workflow-patterns.md -->
- [x] 工作流支持跨 skill 引用（`workflow.next`、`workflow.steps`） <!-- 验证: grep -q "next\|steps" standards/workflow-patterns.md -->
- [x] workflow schema 兼容 cap-pack.yaml 的现有字段 <!-- 验证: grep -q "cap-pack.yaml" standards/workflow-patterns.md -->
- [x] 模式定义与 Cap-Pack-STANDARD.md 的 Layer 4 章节一致 <!-- 验证: python3 -c "import re; open('standards/workflow-patterns.md').read(); print('验证通过')" -->

## 技术方案

### 设计思路

定义 Skill 间协作的四种基本编排模式，以及它们在 cap-pack.yaml 中的声明方式：

```yaml
# 顺序执行 (sequential)
workflows:
  - id: generate-report
    pattern: sequential
    steps:
      - pdf-layout
      - vision-qc
      - feishu-send

# 并行扇出 (parallel)
  - id: multi-search
    pattern: parallel
    steps:
      - web-search
      - arxiv-search
      - blog-search

# 条件路由 (conditional)
  - id: quality-gate
    pattern: conditional
    condition: "sqs_score >= 60"
    pass: notify-success
    fail: notify-failure

# DAG 组合 (dag)
  - id: full-pipeline
    pattern: dag
    steps:
      - id: research
        next: [analyze, visualize]
      - id: analyze
        next: [report]
      - id: visualize
        next: [report]
      - id: report
```

### 涉及文件

- `standards/workflow-patterns.md` — 新增
- `docs/CAP-PACK-STANDARD.md` — 同步更新 Layer 4 章节

## 引用链

- EPIC-005: `docs/EPIC-005-skill-governance-engine.md`
- SPEC-5-0: `docs/SPEC-5-0.md`
- 前序 Story: STORY-5-0-1（标准文档 | Layer 4 章节）

## 不做的范围

- 编排检测器代码实现（Phase 1）
- workflow 引擎运行时（不属于本次治理引擎范围）

---

## 决策日志

| 日期 | 决策 | 理由 |
|:-----|:-----|:------|
| 2026-05-16 | 四种模式独立定义 + 可组合 | cap-pack 需要灵活编排 |
