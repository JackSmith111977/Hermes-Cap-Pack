# 🏗️ EPIC-001: 能力模块化可行性调查

> **状态**: `approved` · **优先级**: P0 · **创建**: 2026-05-12 · **更新**: 2026-05-12
> **SDD 流程**: `CLARIFY ✅ → RESEARCH ✅ → CREATE ✅ → QA_GATE ✅ → REVIEW ✅`
> **负责人**: boku (Emma/小玛) · **到期**: 2026-05-26

---

## 〇、需求澄清记录 (CLARIFY)

### 用户故事

> **As a** AI Agent 开发者和使用者（主人）
> **I want** 将 boku 的各项 Agent 能力拆分为标准化、可移植的「能力包」
> **So that** 在建立其他 Agent 时，可以通过适配器快速还原 boku 的部分能力

### 确认的需求范围

| 维度 | 确认内容 | 
|:-----|:---------|
| **核心目标** | 185 项技能 → 18 个模块 + 3 个扩展槽 |
| **交付物** | EPIC + 4 个 Spec 文档 + YAML Schema 原型 |
| **不做的** | 在线注册中心、自动分割 AI 工具、全平台适配 |
| **验收标准** | 每个 AC 必须可验证（自动化测试优先） |

---

## 一、Epic 概述

### 成功画面

一位开发者在新的机器上启动了一个全新的 Claude Code 实例，运行：

```bash
cap-pack install doc-engine --agent claude-code
```

Claude Code 立即获得了与 boku 相同的文档生成能力（PDF 排版、PPT 生成、HTML 渲染），包括：
- 相同的 SKILL.md 操作指南
- boku 踩过的所有坑（WQY 字体回退、ReportLab 中文编码）
- 相同的 MCP 工具链配置

### 范围矩阵

| 维度 | 包含 | 不包含 |
|:-----|:------|:-------|
| **格式定义** | Capability Pack YAML schema v1 | 注册中心后端 |
| **分割方法论** | 模块边界判断标准、粒度指南 | 自动分割 AI 工具 |
| **生命周期** | CRUD + 版本号 + 依赖管理 | 在线注册中心 |
| **迭代机制** | 基于使用反馈的更新流程 | 自动技能进化（Phase 3+） |
| **适配层** | Hermes + Claude Code + Codex CLI | 所有 20+ 平台适配 |
| **文档范围** | EPIC + SPEC-001~004 | Story 实现文档（Phase 1） |

---

## 二、RESEARCH — 深度调研

### 2.1 boku 现有能力存量

| 能力类别 | 已安装 Skills | 可提取模块 | 数据来源 |
|:---------|:------------:|:----------:|:---------|
| 文档排版 | 5 (pdf-layout, pptx-guide, docx-guide, markdown-guide, html-guide) | 1 个完整模块 | self-capabilities-map |
| 学习体系 | 4 (learning-workflow, learning, skill-creator, knowledge-routing) | 1 个完整模块 | self-capabilities-map |
| 开发流程 | 5 (systematic-debugging, tdd, writing-plans, plan, patch-file-safety) | 1 个完整模块 | self-capabilities-map |
| 安全审计 | 3 (delete-safety, patch-file-safety, commit-quality-check) | 1 个完整模块 | self-capabilities-map |
| 金融分析 | 1 (financial-analyst) + akshare/ta/matplotlib | 1 个模块 | self-capabilities-map |
| 运维监控 | 3 (linux-ops-guide, proxy-monitor, system-health-check) | 1 个模块 | self-capabilities-map |
| 创意设计 | 8+ (architecture-diagram, mermaid-guide, concept-diagrams, 等) | 1-2 个模块 | self-capabilities-map |
| 人格记忆 | SOUL.md + MEMORY.md + SRA 记忆系统 | 1 个复杂模块 | hermes-self-analysis |

### 2.2 业界标准参考

| 标准 | 成熟度 | 与本项目的关系 |
|:-----|:------:|:---------------|
| MCP (Model Context Protocol) | ✅ 97M+ SDK 月下载 | 工具层标准，能力包的 MCP 配置部分直接使用 |
| SKILL.md (agentskills.io) | ✅ 开放标准 | 能力包的技能部分直接使用 |
| AgenticFormat (Auton) | 🟡 研究原型 | 可借鉴的声明式 Agent 蓝图格式 |
| SkillX 三层体系 | 🟡 研究论文 | 可借鉴的 Plan/Functional/Atomic 层级 |
| Profile 导出 (Hermes) | ✅ 生产可用 | 能力包分发的参考实现 |

### 2.3 风险矩阵

| 风险 | 概率 | 影响 | 缓解措施 |
|:-----|:----:|:----:|:---------|
| 格式定义过度设计 | 中 | 高 | 先最小可行（YAML v1），再逐步迭代 |
| 适配层维护负担 | 高 | 中 | 插件化适配器架构，社区可贡献 |
| 跨 Agent 能力不对等 | 中 | 中 | 兼容性矩阵显式标注差异 |
| 技能内容与 Agent 框架耦合 | 低 | 高 | 经验层用自然语言，不依赖特定框架 |
| 模块体积膨胀 | 中 | 低 | 渐进式披露，按需加载 |

---

## 三、四个核心问题 (The Four Pillars)

本 Epic 围绕四个核心问题展开调研，每个问题对应一个 Spec：

```text
┌──────────────────────────────────────────────────────────────────┐
│                   EPIC-001: 能力模块化可行性调查                    │
│                                                                  │
│   ┌──────────────────────────────────────────────────────────┐   │
│   │  ① 如何分割？    → SPEC-001-splitting.md                  │   │
│   │  ② 如何管理？    → SPEC-002-management.md                 │   │
│   │  ③ 如何迭代？    → SPEC-003-iteration.md                 │   │
│   │  ④ 如何适配？    → SPEC-004-adaptation.md                │   │
│   └──────────────────────────────────────────────────────────┘   │
│                                                                  │
│   产出: HTML 全生命周期追踪报告 (reports/lifecycle.html)           │
└──────────────────────────────────────────────────────────────────┘
```

---

## 四、验收标准 (Acceptance Criteria)

### P0（必须完成）
- [ ] `EPIC-001.md` 经主人审阅 **批准**
- [ ] SPEC-001 ~ SPEC-004 均已创建并通过 QA_GATE
- [ ] 至少一个能力包原型格式定义（YAML Schema）完成
- [ ] HTML 生命周期追踪报告可正常生成

### P1（应该完成）
- [ ] 每个 Spec 包含 ≥ 3 个业界参考案例（已验证来源，非 AI 臆造）
- [ ] 每个 Spec 包含 ≥ 2 个候选方案对比矩阵
- [ ] 分割方法论可用决策树形式表达，可执行
- [ ] 适配层架构有清晰的接口定义

### P2（可以完成）
- [ ] 能力的模块依赖关系图
- [ ] 版本兼容性矩阵
- [ ] 第一次迭代回路的真实反馈记录

---

## 五、Stories 列表

| ID | 标题 | 关联 Spec | 优先级 | 状态 |
|:---|:-----|:---------|:------:|:----:|
| STORY-001 | 模块分割维度与粒度分析 | SPEC-001 | P1 | ⏳ 待创建 |
| STORY-002 | 模块边界判断标准决策树 | SPEC-001 | P1 | ⏳ 待创建 |
| STORY-003 | Capability Pack 格式定义 v1 | SPEC-001 | P0 | ⏳ 待创建 |
| STORY-004 | 模块生命周期状态机设计 | SPEC-002 | P1 | ⏳ 待创建 |
| STORY-005 | 版本号与依赖管理规范 | SPEC-002 | P1 | ⏳ 待创建 |
| STORY-006 | 基于使用反馈的迭代流程 | SPEC-003 | P1 | ⏳ 待创建 |
| STORY-007 | 经验与技能的同步更新机制 | SPEC-003 | P2 | ⏳ 待创建 |
| STORY-008 | 适配层接口抽象定义 | SPEC-004 | P1 | ⏳ 待创建 |
| STORY-009 | Hermes 适配器实现 | SPEC-004 | P0 | ⏳ 待创建 |
| STORY-010 | Claude Code 适配器实现 | SPEC-004 | P1 | ⏳ 待创建 |

---

## 六、时间线

| 阶段 | 时间 | 里程碑 | 交付物 |
|:----|:----|:-------|:-------|
| Phase 0: Spec 写作 | 5/12 - 5/16 | 4 个 Spec 获批 | EPIC + SPEC-001~004 |
| Phase 1: 格式设计 | 5/16 - 5/23 | Cap Pack 格式 v1 | YAML Schema + 示例 |
| Phase 2: 分割实施 | 5/23 - 5/30 | 6+ 能力包提取 | 能力包目录 |
| Phase 3: 适配层 | 5/30 - 6/13 | 3 个适配器上线 | Hermes/Claude/Codex 适配 |

---

## 七、决策日志

| 日期 | 决策 | 备选方案 | 理由 |
|:----|:-----|:---------|:-----|
| 2026-05-12 | 采用 YAML 作为能力包格式 | JSON/TOML | YAML 支持注释，对 AI 友好 |
| 2026-05-12 | 按领域（非工具）分类 | 按工具/按功能 | 领域分类更稳定，跨框架通用 |
| 2026-05-12 | 预留 3 个扩展槽 | 不预留/预留 5 个 | 平衡扩展性和简洁性 |

---

## 八、引用与参考

- `self-capabilities-map` skill — boku 能力边界认知地图
- `hermes-agent` skill — Hermes Agent 完整指南
- `sra-dev-workflow` — SRA 项目开发工作流
- `sdd-workflow` — SDD 规范驱动开发工作流
- AgentWiki — 模块化 AI Agent 架构研究
- MCP 规范 — Model Context Protocol
- SkillX 论文 — arXiv:2604.04804
- STEM Agent — arXiv:2603.22359

---

## 九、QA_GATE 检查清单

- [x] Epic ID 格式正确（EPIC-001）
- [x] 状态字段完整（draft/priority/created/updated）
- [x] SDD 流程阶段标注
- [x] 需求澄清记录（CLARIFY 章节）
- [x] 深度调研记录（RESEARCH 章节）
- [x] 用户故事（As a / I want / So that）
- [x] 范围矩阵（包含/不包含）
- [x] AC 可验证（列表形式，每项可独立检验）
- [x] out_of_scope 已明确
- [x] Stories 列表完整
- [x] 主人 REVIEW 批准
