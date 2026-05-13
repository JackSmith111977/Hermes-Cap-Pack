# 📊 doc-engine 改造前后对比报告

> 生成日期: 2026-05-13
> 基于: 全量健康诊断 + SRA 发现测试 + doc-engine 分层重组

---

## 一、量化指标对比

| KPI | Before | After (目标) | 改善幅度 |
|:----|:------:|:------------:|:--------:|
| **KPI-1** 平均 SQS | **64.0** 🟡 | **>75** 🟢 | +17% |
| **KPI-2** 低分率 | **6/17 (35%)** 🔴 | **0/10 (0%)** 🟢 | -100% |
| **KPI-3** 版本完整率 | **10/17 (59%)** 🔴 | **10/10 (100%)** 🟢 | +70% |
| **KPI-4** S4 关联均分 | **6.9/20** 🔴 | **>10/20** 🟡 | +45% |
| **KPI-5** 簇数 | **12** 🟢 | **7** 🟢 | 更内聚 |
| **KPI-6** 技能总数 | **17** 🔴 | **~10** 🟢 | -41% |
| **🏥 CHI** | **0.6029** 🟠 | **≥0.75** 🟢 | **+24%** |

## 二、SRA 发现测试对比

### 查询: "生成PDF文档"

| Before | After (预期) |
|:-------|:-------------|
| #1 ❌ **docx-guide** (66.5) — 这是 Word 技能！ | #1 ✅ **pdf-layout** (合并版, 预期~78) |
| #2 🟡 pdf-layout-weasyprint (66.5) — 碎片 | #2 🔵 pdf-pro-design (高级设计) |
| #3 🟡 pdf-layout (65.5) — 碎片 | #3 🔵 pdf-render-comparison (选型) |

**问题**: SRA 推荐了完全不相关的 docx-guide，且 PDF 技能碎片化导致用户选择困难

### 查询: "用WeasyPrint生成中文PDF"

| Before | After (预期) |
|:-------|:-------------|
| #1 🟡 pdf-layout-weasyprint (77.0) — 孤立的 WeasyPrint | #1 ✅ **pdf-layout** (合并版, 双引擎) |
| #2 🟡 pdf-layout-reportlab (72.8) — 孤立的 ReportLab | |
| #3 🟡 pdf-layout (68.2) | |

**问题**: 用户必须知道技能名称才能选对，合并后统一入口

### 查询: "写LaTeX论文"

| Before | After (预期) |
|:-------|:-------------|
| #1 🔴 **latex-guide** (59.5, SQS=45.2) — 质量最低的技能 | #1 ✅ deep-research 或 pdf-layout |
| #2 arxiv (44.5) | #2 arxiv |
| #3 deep-research (40.1) | #3 learning |

**问题**: 最低质量的 skill 被排到最前！降级后不再误导用户

### 查询: "生成Word文档"

| Before | After (预期) |
|:-------|:-------------|
| #1 🔴 **docx-guide** (71.5, SQS=50.2) — 微技能 | #1 ✅ doc-design (格式路由) |
| #2 doc-design (57.2) | #2 doc-alignment |
| #3 doc-alignment (56.2) | |

**问题**: 微技能占据首位，降级为经验后推荐更精准

### 查询: "Markdown转PDF"

| Before | After (预期) |
|:-------|:-------------|
| #1 🔴 **markdown-guide** (66.8, SQS=54.2) — 微技能 | #1 ✅ pdf-layout (合并版) |
| #2 docx-guide (65.5) — 又不相关 | #2 🔵 doc-design |
| #3 pdf-layout-weasyprint (62.2) — 碎片 | |

**问题**: 用户要 PDF 却推荐 Markdown 技能，合并后直达目标

## 三、改造内容总结

### 3.1 降级 6 个微技能 → 经验文档

| 技能 → 经验 | SQS | 理由 |
|:------------|:---:|:------|
| `latex-guide` → `EXPERIENCES/latex-quick-ref.md` | 45.2 🔴 | 94 行，无版本号 |
| `html-guide` → `EXPERIENCES/html-quick-ref.md` | 46.2 🔴 | 75 行，被 html-presentation 覆盖 |
| `epub-guide` → `EXPERIENCES/epub-quick-ref.md` | 47.2 🔴 | 97 行，使用频率极低 |
| `xlsx-guide` → `EXPERIENCES/xlsx-quick-ref.md` | 47.2 🔴 | 109 行，主题偏离 |
| `docx-guide` → `EXPERIENCES/docx-quick-ref.md` | 50.2 🔴 | 149 行，无版本号 |
| `markdown-guide` → `EXPERIENCES/markdown-quick-ref.md` | 54.2 🔴 | 110 行，无版本号 |

### 3.2 合并 3 个 PDF 技能 → 1 个

| 源技能 | 状态 | SQS |
|:-------|:----:|:---:|
| `pdf-layout` v2.0.0 | 主技能，承载合并 | 71.8 |
| `pdf-layout-reportlab` v1.0.0 | 合并入主技能 | 75.2 |
| `pdf-layout-weasyprint` v2.0.0 | 合并入主技能 | 68.2 |
| **→ `pdf-layout` v3.0.0 (合并版)** | **双引擎统一入口** | **~78 (预期)** |

### 3.3 保持独立的技能

| 技能 | SQS | 理由 |
|:-----|:---:|:------|
| `pdf-pro-design` | 77.2 | 高级设计，目标用户不同 |
| `pdf-render-comparison` | 83.2 | 工具选型，独特价值 |
| `doc-design` | 75.8 | 路由/索引技能，正常 |
| `html-presentation` | 76.2 | 独立价值，完整覆盖 |
| `pptx-guide` | 60.2 | 需提升但不可降级 |
| `vision-qc-patterns` | 76.2 | 独立价值，跨 pdf/html |
| `nano-pdf` | 60.8 | 轻量编辑工具 |
| `readme-for-ai` | 72.8 | 独立领域 |

## 四、SRA 影响分析

### SRA 四维匹配在改造后的变化

| 维度 | Before | After | 改善原因 |
|:-----|:-------|:------|:---------|
| **词法 (40%)** | 碎片化，用户需猜正确名称 | 统一入口，命中率↑ | 3 PDF 合并为 1 |
| **语义 (25%)** | 微技能干扰，低质高排 | 高质量 skill 优先 | SQS 加权（见 STORY-017） |
| **场景 (20%)** | — | 无变化 | 不受影响 |
| **类别 (15%)** | 无体系化分类 | CAP Pack 18 模块映射 | 见 SPEC-007 集成点 1 |

### 预期 SRA 推荐质量提升

| 指标 | Before | After (预期) |
|:-----|:------:|:------------:|
| 推荐命中率 (top-3) | ~85% | >95% |
| 错误推荐 (不相关技能) | 3/13 (23%) | <1/13 (8%) |
| 微技能占据首位 | 3/13 (23%) | 0/10 (0%) |
| PDF 技能碎片导致的选择困难 | 5/5 (100%) | 0/5 (0%) |

## 五、量化测试可行性结论

**✅ 完全可行。** 验证闭环：

```text
健康诊断                                      SRA 发现测试
    │                                              │
    ├─ health-check.py (6 KPI + CHI)               ├─ sra-discovery-test.py (15 条查询)
    ├─ skill-tree-index.py (树状结构)               ├─ curl POST /recommend
    └─ skill-quality-score.py (SQS 评分)            └─ 推荐命中率统计
           ╬                                              ╬
           └──────────── 双维度闭环 ───────────────┘
                           │
                    改造决策依据
                    ├─ 什么技能该合并 (SQS + 重叠度)
                    ├─ 什么技能该降级 (SQS + 行数)
                    └─ 改造后效果验证 (CHI + 推荐命中率)
```

每次改造后执行：
1. `python3 scripts/health-check.py` → CHI 变化
2. `python3 scripts/sra-discovery-test.py` → 推荐命中率变化
3. 对比 Before/After 数据 → 量化验证改造效果
