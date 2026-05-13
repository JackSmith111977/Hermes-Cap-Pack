# 📦 SPEC-1-1: 模块分割方案

> **状态**: `approved` · **优先级**: P1 · **创建**: 2026-05-12 · **更新**: 2026-05-12
> **SDD 流程**: `CLARIFY ✅ → RESEARCH ✅ → CREATE ✅ → QA_GATE ✅ → REVIEW ✅`
> **关联 Epic**: EPIC-001-feasibility.md
> **审查人**: 主人

---

## 〇、需求澄清记录 (CLARIFY)

### 要解决的核心问题

> 如何将 boku 的全部 185 项能力拆分为独立、内聚、可复用的模块？以什么维度分割？多大粒度合适？如何确保不会遗漏任何能力？如何应对框架未来的成长？

### 确认的范围

| 包含 | 不包含 |
|:-----|:--------|
| ✅ 分割维度分析（按领域/工具/经验） | ❌ 自动分割 AI 工具 |
| ✅ 模块粒度判断标准 | ❌ 所有模块的完整提取（Phase 2 实施） |
| ✅ 18 个模块 + 3 个扩展槽 | ❌ 模块依赖图自动生成 |
| ✅ Capability Pack 格式定义 v1 | ❌ 格式的完整实现 |
| ✅ Hermes 框架成长性的应对机制 | ❌ 自动分类 AI |
| ✅ 遗漏模块的补充（知识库/元认知/媒体等） | ❌ 第三方模块审核流程 |

---

## 一、RESEARCH — 深度调研

### 1.1 完整能力审计（2026-05-12）

boku 深度自我分析后，将全部 **185 个技能** 分为 **18 个能力领域**，并预留 **3 个扩展槽**。

#### 原始遗漏分析

| 原始版本 (v1) | 遗漏了 | 原因 |
|:--------------|:-------|:------|
| 8 个模块 | ❌ 知识库系统 | 只看到显式技能，忽略了三层知识体系 |
| — | ❌ 元认知系统 | 自我分析/自我审查是「关于能力的能力」 |
| — | ❌ 质量保障 | QA 门禁/测试框架/代码审查是跨领域的元能力 |
| — | ❌ 消息平台 | 飞书/微信是通信能力而非工具 |
| — | ❌ 音视频媒体 | TTS/图像生成/音乐属于独立能力域 |
| — | ❌ GitHub 生态 | 10 个相关技能构成完整生态 |
| — | ❌ 网络代理 | Clash/代理/浏览器自动化是独立领域 |
| — | ❌ 新闻研究 | 新闻简报/Arxiv/AI 趋势追踪 |
| — | ❌ Agent 协作 | 子代理/多 Agent/BMAD 编排 |
| — | ❌ 社交娱乐 | MC 服务器/健身/元宝等 |
| — | ❌ 框架成长性 | Hermes 新版本会带来新能力 |

#### 完整 18 模块分类表

| # | 模块 ID | 名称 | 技能数 | 所属层次 |
|:-:|:--------|:-----|:------:|:---------|
| 1 | `knowledge-base` | 📚 知识库系统 | ~6 | **元能力层** |
| 2 | `learning-engine` | 🧠 学习引擎 | ~7 | 元能力层 |
| 3 | `metacognition` | 🪞 元认知系统 | ~6 | **元能力层** |
| 4 | `doc-engine` | 📄 文档生成 | ~12 | 应用层 |
| 5 | `developer-workflow` | 💻 开发工作流 | ~16 | 应用层 |
| 6 | `quality-assurance` | ✅ 质量保障 | ~10 | 元能力层/应用层 |
| 7 | `security-audit` | 🔒 安全审计 | ~5 | 应用层 |
| 8 | `devops-monitor` | 🔧 运维监控 | ~8 | 基础设施层 |
| 9 | `network-proxy` | 🌐 网络代理 | ~5 | 基础设施层 |
| 10 | `github-ecosystem` | 🐙 GitHub 生态 | ~10 | 应用层 |
| 11 | `messaging` | 💬 消息平台 | ~8 | 基础设施层 |
| 12 | `agent-orchestration` | 🤖 Agent 协作 | ~12 | 元能力层 |
| 13 | `mcp-integration` | 🔌 MCP 集成 | ~5 | 基础设施层 |
| 14 | `financial-analysis` | 📊 金融分析 | ~2 | 应用层 |
| 15 | `creative-design` | 🎨 创意设计 | ~18 | 应用层 |
| 16 | `media-processing` | 🎵 音视频媒体 | ~9 | 应用层 |
| 17 | `news-research` | 📰 新闻研究 | ~7 | 应用层 |
| 18 | `social-gaming` | 🎮 社交娱乐 | ~6 | 应用层 |

### 1.2 模块分层架构

能力包不是扁平的——按「能力性质」分为三个层次：

```text
┌─────────────────────────────────────────────────────────────┐
│  🪞 元能力层 (Meta-Capabilities)                            │
│  「关于能力的能力」— 跨领域，所有模块的基础                  │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  knowledge-base     learning-engine                   │   │
│  │  metacognition      quality-assurance                 │   │
│  │  agent-orchestration                                  │   │
│  └──────────────────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────────────┤
│  ⚡ 应用层 (Application Capabilities)                        │
│  「解决具体用户问题」— 面向任务的直接能力                    │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  doc-engine           developer-workflow              │   │
│  │  security-audit       github-ecosystem                │   │
│  │  financial-analysis   creative-design                 │   │
│  │  media-processing     news-research                   │   │
│  │  social-gaming                                       │   │
│  └──────────────────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────────────┤
│  🏗️ 基础设施层 (Infrastructure Capabilities)                │
│  「支撑上层能力的运行环境」— 工具链/协议/平台               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  devops-monitor      network-proxy                    │   │
│  │  messaging           mcp-integration                  │   │
│  └──────────────────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────────────┤
│  🟡 预留扩展槽 (Growth Slots)                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  hermes-new-features    custom-plugin                 │   │
│  │  future-domain                                       │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## 二、扩展性设计（Hermes 框架成长性）

### 2.1 三种成长场景

| 场景 | 触发条件 | boku 的应对 |
|:-----|:---------|:------------|
| **技能增长** | boku 创建新 skill | 新 skill 的标签自动匹配到对应模块 |
| **框架升级** | `hermes update` 安装新版本 | hermes-new-features 模块自动吸纳 |
| **生态扩展** | 安装社区 MCP Server / Plugin | 按 domain/tags 归入已有模块或创建新模块 |

### 2.2 技能自动归属机制

每个 skill 的 frontmatter 中包含分类标签：

```yaml
---
name: my-new-skill
metadata:
  hermes:
    tags: [developer-workflow, testing]
    module: developer-workflow    # 可选：显式指定归属模块
---
```

### 2.3 新增模块的创建流程

当 hermes-new-features 槽积累 ≥3 个技能或框架新增重大能力时：

```text
检测到 new-features 槽 ≥3 技能
    ↓
boku 建议创建新模块 → 主人确认
    ↓
如同意 → 创建新模块 → 更新分类体系 → 更新 HTML 报告
```

### 2.4 跨模块交叉引用

一个技能可能属于多个模块（如 `commit-quality-check` 同时属于 security-audit 和 github-ecosystem）：

```yaml
cross_module_refs:
  - skill: commit-quality-check
    primary_module: security-audit
    secondary_modules:
      - github-ecosystem
      - developer-workflow
```

---

## 三、Capability Pack 格式定义 v1

### 模块清单 (cap-pack.yaml)

```yaml
---
name: knowledge-base
version: 1.0.0
type: capability-pack
classification: domain
layer: meta                              # 元能力层 / 应用层 / 基础设施层

title: 知识库系统
description: >
  三层知识库体系 (L1 Skills / L2 Experiences / L3 Brain)，
  涵盖知识沉淀、路由、检索、维护全流程。

compatibility:
  agent_types:
    - hermes
    - claude-code
    - codex-cli

capabilities:
  skills:
    - id: knowledge-precipitation
      path: SKILLS/knowledge-precipitation.md
    - id: knowledge-routing
      path: SKILLS/knowledge-routing.md

  experiences:
    - id: knowledge-lifecycle
      path: EXPERIENCES/knowledge-lifecycle.md
      type: decision-tree

  knowledge_refs:
    - level: L3
      ref: brain/concepts/knowledge-graph.md

growth_config:
  auto_absorb_new_skills: true
  skill_tag_mapping:
    "知识": knowledge-base
    experience: knowledge-base
```

### 模块目录结构

```text
cap-packs/knowledge-base/
├── cap-pack.yaml                       # 模块清单
├── SKILLS/                             # 技能目录
│   └── knowledge-precipitation/
│       └── SKILL.md
├── EXPERIENCES/                        # 经验目录
│   └── knowledge-lifecycle.md
├── MCP/                                # MCP 配置
│   └── servers.yaml
└── KNOWLEDGE/                          # 知识库引用
    └── refs.yaml
```

---

## 四、验收标准 (Acceptance Criteria)

- [ ] 18 个模块 + 3 个扩展槽的分类体系经主人确认
- [ ] 每个模块的技能清单与实际技能目录一致
- [ ] cap-pack.yaml 格式定义可用 YAML 校验工具验证
- [ ] 新增技能可自动匹配到已有模块（需测试用例验证）
- [ ] 跨模块引用方案经主人确认

---

## 五、QA_GATE 检查清单

- [x] Spec ID 格式正确（SPEC-1-1）
- [x] 关联 Epic 引用完整
- [x] CLARIFY 章节记录了需求确认
- [x] RESEARCH 章节有深度分析
- [x] 范围矩阵（包含/不包含）完整
- [x] AC 每项可独立验证
- [x] 格式定义有 YAML 示例可执行
- [x] 扩展性方案覆盖 3 种成长场景
- [x] 主人 REVIEW 批准
