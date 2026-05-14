# 🎨 SPEC-2-4: 项目报告生成器工作流集成规范

> **状态**: `draft` · **优先级**: P1 · **创建**: 2026-05-14 · **更新**: 2026-05-14
> **SDD 流程**: `CLARIFY ✅ → RESEARCH ✅ → CREATE ✅ → QA_GATE ⬜ → REVIEW ⬜`
> **关联 Epic**: EPIC-002-tree-health.md
> **关联 Skill**: `project-report-generator` (Hermes Skill)
> **关联 Skills**: `web-ui-ux-design`, `visual-aesthetics`, `concept-diagrams`

---

## 〇、需求澄清 (CLARIFY)

### 用户故事

> **As a** 主人（项目维护者）
> **I want** 项目的状态报告不再由硬编码脚本生成模板替换，而是由 **LLM 驱动的 Hermes Skill** 通过深度循环学习从零创作
> **So that** 每份报告都是根据项目当前特点定制的，具有独特叙事和设计风格，而非模板填充

### 确认的需求范围

| 维度 | 包含 | 不包含 |
|:-----|:------|:-------|
| **报告生成方式** | ❌ 硬编码脚本（`generate-panorama.py`）已废弃 | 继续使用脚本模板 |
| **新方式** | ✅ Hermes Skill 引导 LLM 五阶段深度创作 | 自动模板化批量生成 |
| **设计系统** | ✅ 每次先定义报告风格/配色/布局再创作 | 使用固定 CSS |
| **数据来源** | ✅ 读取 `project-report.json` + SQS DB + SDD 文档 | 手动填写数据 |
| **工作流融合** | ✅ 作为 Sprint/Phase 完成的正式步骤 | 每次随意触发 |
| **质量门禁** | ✅ R1/R2/R3 三层循环 + QG 最终审查 | 一次性出稿 |

### out_of_scope

- 自动定时生成（报告仍按需触发，主人决定何时生成）
- 多项目统一管理（本 SPEC 针对单一 cap-pack 项目）
- 跨 Agent 报告共享

---

## 一、研究记录 (RESEARCH)

### 1.1 原有方案的问题分析

**旧流程（已被否定）：**
```
generate-panorama.py
    └─ json_report → .replace() 模板 → PROJECT-PANORAMA.html
```

| 问题 | 影响 | 根因 |
|:-----|:-----|:------|
| 模板固定 | 所有报告千篇一律 | `.replace()` 占位替换 |
| LLM 未参与创作 | 无叙事、无设计感 | 脚本只做数据填充 |
| 改设计需改代码 | 迭代成本高 | 样式和数据耦合 |
| 无循环迭代 | 一次成型质量不可控 | 脚本无 Review 门禁 |

### 1.2 新方案设计原则

| 原则 | 说明 |
|:-----|:------|
| **LLM 主导创作** | 报告是「创作」而非「填充」，每次从零设计 |
| **五阶段结构化** | 数据→定义→叙事→创作→Review，不跳步 |
| **深度循环迭代** | R1/R2/R3 三层反思门禁，每次至少一次完整 Review |
| **数据驱动** | 项目状态数据是原料，LLM 决定怎么讲这个故事 |
| **组合 skill** | 配合 `web-ui-ux-design`, `visual-aesthetics` 等设计 skill |

### 1.3 与现有 SDD 工作流的融合点

CAP Pack 项目的每个开发阶段完成后，报告生成成为一个**正式的里程碑步骤**：

```text
┌─ SDD 标准流程 ─────────────────────────────────────┐
│  CLARIFY → RESEARCH → CREATE → QA_GATE → REVIEW     │
│                                                    │
│  Sprint 完成时 ──→ 里程碑检查点 ──→ 报告生成触发     │
│                                                    │
│  Phase/Epic 完成 ──→ 全景报告 ──→ 交付主人审批      │
└────────────────────────────────────────────────────┘
```

**触发时机：**
| 时机 | 报告类型 | 用途 |
|:-----|:---------|:------|
| 每个 Sprint 结束 | Sprint 总结报告 | 回顾迭代成果 |
| Epic/Phase 完成 | 项目全景报告 | 全景式项目健康状态 |
| 主人主动要求 | 定制报告 | 按需分析特定维度 |

### 1.4 与同类工具的对比

| 维度 | 旧方案 (generate-panorama.py) | 通用 Shell 脚本方案 | ✅ 本方案 (Hermes Skill) |
|:-----|:---------------------------|:------------------|:----------------------|
| 报告质量 | 模板填充，固定风格 | 无设计能力 | LLM 从零创作，每份独特 |
| 灵活性 | 改模板=改代码 | 无 | 自然语言修改需求 |
| 复用性 | 仅此项目 | 无 Skill 封装 | Hermes Skill 跨项目复用 |
| 设计能力 | CSS 硬编码 | 无 | 配合视觉/设计 skill 组合 |
| 质量管理 | 无 Review 流程 | 无 | R1/R2/R3 三层门禁 |
| 叙事能力 | 数据堆砌 | 无 | 先定叙事线再布局 |

---

## 二、架构概览

### 2.1 五阶段创作工作流

```text
Phase 0 ── 数据采集
    读取：project-report.json + SQS DB + git log + 文档状态
    输出：数据摘要 JSON
    
Phase 1 ── 设计系统定义
    定义：叙事基调 + 色彩语言 + 布局模式 + 组件风格
    原则：Dieter Rams 好设计十大原则，CRAP 对比/重复/对齐/亲密性
    
Phase 2 ── 叙事架构
    决策：报告结构（章节顺序）、信息层级（主次分明）、数据可视化选型
    输出：叙事大纲 markdown
    
Phase 3 ── HTML 创作
    创作：先 skeleton.html → 再填入内容 → 最后润色设计
    约束：暗色主题、响应式、自包含（单 HTML 文件）
    
Phase 4 ── 三层门禁
    R1 ── Design Review：布局/色彩/字体/视觉一致性
    R2 ── Content Review：数据准确/叙事连贯/信息完整
    R3 ── Technical Review：HTML 闭合/CSS 覆盖/无 js 错误
    QG ── 最终门禁：三维度综合评分 ≥ 7/10 才通过
```

### 2.2 数据流

```text
┌──────────────┐    ┌────────────────────┐    ┌──────────────┐
│ project-     │    │ Hermes Skill       │    │ 最终 HTML     │
│ report.json  │───→│ project-report-    │───→│ 报告文件      │
│              │    │ generator          │    │              │
│ SQS DB       │───→│                    │    │ Fully         │
│ (SQLite)     │    │ 深度循环学习        │    │ Self-Contained│
│              │    │ 五阶段创作流程       │    │ Dark Theme    │
│ SDD 文档     │───→│ 三层门禁            │    │ 独特叙事      │
│ (.md files)  │    │                    │    │              │
│              │    │ ← web-ui-ux-design │    │              │
│ git log      │───→│ ← visual-aesthetics│    │              │
└──────────────┘    └────────────────────┘    └──────────────┘
```

### 2.3 融入 SDD 工作流的触发点

每个 Epic/Phase 完成后，在 QA_GATE 到 REVIEW 之间插入报告生成步骤：

```text
SDD 流程： CLARIFY → RESEARCH → CREATE → QA_GATE → [报告生成] → REVIEW → APPROVED
                                                    │
                                              project-report-
                                              generator skill
                                                    │
                                              1. Load skill
                                              2. 五阶段创作
                                              3. 输出 HTML
                                              4. 交付主人
```

---

## 三、验收标准 (AC)

| AC ID | 描述 | 验证方式 | 优先级 |
|:------|:-----|:---------|:------:|
| AC-01 | project-report-generator skill 已创建并存于 `~/.hermes/skills/documentation/` | `skill_view(name='project-report-generator')` 可加载 | P0 |
| AC-02 | skill 包含完整的五阶段创作工作流（Phase 0 ~ Phase 4） | SKILL.md 中有 Explicit 的阶段定义 | P0 |
| AC-03 | skill 包含三层门禁机制（R1/R2/R3 + QG） | 至少有 3 个 Review 步骤定义 | P0 |
| AC-04 | skill 包含 CSS 模式库引用 | `references/css-patterns.md` 存在 | P1 |
| AC-05 | 可配合 `web-ui-ux-design` + `visual-aesthetics` skill 协同使用 | combo 三步装在 SKILL.md 中说明 | P1 |
| AC-06 | SDD 流程图中标注了报告生成步骤 | EPIC-002 或 README 中有更新 | P1 |
| AC-07 | 使用本 skill 生成的报告符合质量标准（QG 通过） | 生成的 HTML 在浏览器中无报错，视觉一致 | P0 |

---

## 四、初步 Story 分解

| Story | 标题 | AC | 预估 |
|:------|:-----|:---|:----:|
| **STORY-2-4-1** | project-report-generator skill 创建与 SDD 工作流集成 | AC-01~07 | ✅ done |

---

## 五、实施顺序

```
唯一 Story STORY-2-4-1:
  1. 创建 SKILL.md（五阶段 + 三层门禁 + 设计原则）
  2. 创建 references/css-patterns.md（10 个 CSS 模式参考）
  3. 更新 EPIC-002 交付物清单 + 故事列表
  4. 更新 README SDD 流程表
  5. 验证：用 skill 生成一份真实报告
```

---

## 六、决策日志

| 日期 | 决策 | 备选方案 | 理由 |
|:----|:-----|:---------|:-----|
| 2026-05-14 | 采用 Hermes Skill 而非脚本 | Python 脚本 | LLM 创作更灵活，每份报告独特 |
| 2026-05-14 | 五阶段（数据→设计→叙事→创作→Review） | 三阶段（准备→写→发） | 更多反思节点，质量可控 |
| 2026-05-14 | R1/R2/R3 三层门禁 + QG 综合门禁 | 一层 Review | 三层分别覆盖不同维度，不遗漏 |
| 2026-05-14 | 归入 EPIC-002（Tree Health） | 独立 EPIC | EPIC-002 已涵盖健康报告体系 |

---

## 七、引用与参考

- `project-report-generator` skill — 本 SPEC 对应的 Hermes Skill
- `web-ui-ux-design` skill — 网页 UI/UX 设计知识库
- `visual-aesthetics` skill — boku 的视觉审美指南
- `concept-diagrams` skill — SVG 概念图生成
- EPIC-002-tree-health.md — 树状健康度管理 Epic
- [Dieter Rams 10 Principles of Good Design](https://www.vitsoe.com/us/about/good-design)
