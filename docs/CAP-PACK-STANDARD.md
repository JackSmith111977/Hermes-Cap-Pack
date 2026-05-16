# cap-pack 统一管理标准 v1（含编排调度层提案）

> **基于深度研究：** Agent Skills Spec + skill-tree + USK + Perplexity 实践 + SkillRouter 学术研究
> **2026-05-16 · 初稿**

---

## 一、四层架构

按主人的建议，在 skill 结构之上加 **工作流编排层**，形成四层体系：

```
┌─────────────────────────────────────────────────────────────┐
│  Layer 4: Workflow Orchestration  ← 新增：编排调度层        │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  DAG Pipeline · 顺序链 · 条件路由 · 并行扇出          │   │
│  │  调度原子 skill 完成特定工作任务                       │   │
│  │  例: "生成PDF报告" = pdf-layout + html-presentation    │   │
│  │       + vision-qc-patterns + feishu-send             │   │
│  └──────────────────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────────────┤
│  Layer 3: Ecosystem (生态层)                                │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  SRA 可发现性 · 跨平台兼容 · 跨包无冗余               │   │
│  │  MCP 集成 · 多 Agent 适配                             │   │
│  └──────────────────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────────────┤
│  Layer 2: Health & Organization (健康组织层)                │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  树状簇归属 · 簇大小 3-15 · 内聚性 < 60% 重叠        │   │
│  │  原子性 < 500行 · 编排声明 · 版本规范                 │   │
│  └──────────────────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────────────┤
│  Layer 1: Foundation (基础合规层)                           │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  SKILL.md 存在 · frontmatter 合法 · SQS ≥ 60        │   │
│  │  version/tags/classification 必填                    │   │
│  └──────────────────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────────────┤
│  Layer 0: Compatibility (兼容层)                            │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  100% 兼容 Agent Skills Spec (Agentskills.io)        │   │
│  │  不 fork 标准，只扩展 metadata                        │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## 二、Layer 4 详解：工作流编排调度层

### 为什么需要？

当前 cap-pack 的 skill 是原子化的——每个 skill 做一件事。但**真实任务需要多个 skill 协作**：

| 场景 | 涉及的 skill | 
|:-----|:-------------|
| 「生成 PDF 报告并发到飞书」 | pdf-layout → doc-design → vision-qc → feishu-send |
| 「分析股票数据生成研报」 | financial-analyst → html-presentation → feishu-send |
| 「Git 提交前全量检查」 | commit-quality → generic-qa → doc-alignment |

### 编排定义方式

在每个 skill 的 cap-pack.yaml 中声明编排关系：

```yaml
# 方式 1: skill 内声明（轻量）
skills:
  - id: pdf-layout
    workflow:
      pattern: sequential       # sequential | parallel | conditional | dag
      next: [feishu-send]       # 下游 skill
      condition: "生成成功"      # 条件触发

# 方式 2: 独立 workflow 定义（重量，推荐）
workflows:
  - id: generate-report-workflow
    description: 生成 PDF 报告并分发到飞书
    pattern: dag
    steps:
      - id: step-1
        skill: pdf-layout
        input: "{report_data}"
        output: "{pdf_path}"
      - id: step-2
        skill: doc-design
        input: "{pdf_path}"
        depends_on: [step-1]
      - id: step-3
        skill: vision-qc-patterns
        input: "{pdf_path}"
        depends_on: [step-2]
        condition: "quality_check == pass"  # 条件分支
      - id: step-4
        skill: feishu-send
        input: "{pdf_path}"
        depends_on: [step-3]
```

### 编排模式库

| 模式 | 说明 | 适用场景 |
|:-----|:------|:---------|
| **sequential** | 顺序执行链 | 流水线式处理（生成→检查→发送） |
| **parallel** | 并行扇出扇入 | 独立任务并行（同时搜索多个源） |
| **conditional** | 条件分支路由 | 质量门禁（pass→发送, fail→重试） |
| **dag** | 有向无环图 | 复杂编排（上述三种的组合） |
| **map-reduce** | 分治聚合 | 批量处理（分片处理→合并结果） |

---

## 三、统一标准的 Machine-Checkable 规则集

每层对应一组可自动检查的规则：

```python
# Layer 1: Foundation — 基础门槛
RULES_L1 = {
    "skill_md_exists": {"type": "file", "path": "SKILL.md", "severity": "blocking"},
    "frontmatter_valid": {"type": "yaml", "required_fields": ["name", "description"], "severity": "blocking"},
    "sqs_minimum": {"type": "metric", "name": "sqs_total", "min": 60, "severity": "blocking"},
    "version_present": {"type": "field", "field": "version", "severity": "blocking"},
}

# Layer 2: Health — 健康标准
RULES_L2 = {
    "cluster_membership": {"type": "tree", "check": "has_cluster", "severity": "warning"},
    "cluster_size": {"type": "tree", "check": "cluster_size", "min": 3, "max": 15, "severity": "warning"},
    "atomicity_lines": {"type": "metric", "name": "line_count", "max": 500, "severity": "warning"},
    "overlap_ratio": {"type": "metric", "name": "semantic_overlap", "max": 0.6, "severity": "warning"},
    "workflow_declared": {"type": "field", "field": "workflow.pattern", "severity": "info"},
}

# Layer 3: Ecosystem — 生态标准
RULES_L3 = {
    "sra_discoverable": {"type": "metric", "name": "sra_hit_rate", "min": 0.5, "severity": "info"},
    "multi_agent": {"type": "field", "field": "compatibility.agent_types", "min_items": 2, "severity": "info"},
    "cross_pack_overlap": {"type": "metric", "name": "cross_pack_overlap", "max": 0.6, "severity": "info"},
}

# Layer 4: Workflow — 编排标准
RULES_L4 = {
    "workflow_valid": {"type": "workflow", "check": "dag_valid", "severity": "blocking"},
    "workflow_no_circular": {"type": "workflow", "check": "no_cycles", "severity": "blocking"},
    "workflow_skills_exist": {"type": "workflow", "check": "skills_referenced_exist", "severity": "blocking"},
    "workflow_deadlock_free": {"type": "workflow", "check": "no_deadlocks", "severity": "warning"},
}
```

---

## 四、合规判定矩阵

| 层级 | 所有规则通过 | 部分规则通过 | 关键规则失败 |
|:-----|:-----------|:------------|:------------|
| L0 兼容层 | 兼容 | — | 不兼容 |
| L1 基础层 | ✅ **合规** | ⚠️ 部分合规 | ❌ **不合规** |
| L2 健康层 | 🟢 健康 | 🟡 需改进 | 🔴 不健康 |
| L3 生态层 | 🏆 优秀 | 🟢 良好 | 🟡 一般 |
| L4 编排层 | 🔄 可编排 | ⚙️ 部分可编排 | 📄 单 skill（无编排） |

**最终合规等级**：
```
Compliant   = L0 pass + L1 all pass
Healthy     = Compliant + L2 all pass
Excellent   = Healthy + L3 all pass
Orchestrated= Excellent + L4 有 workflow 声明
```
