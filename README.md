# Hermes Capability Pack (hermes-cap-pack)

> **boku 能力模块化与跨 Agent 可复用性项目**
> 将 boku（艾玛/小玛）的全部 Agent 能力拆分为标准化的「能力包」，让其他 Agent 通过适配器快速复用。

## 项目定位

```text
┌─────────────────────────────────────────────────────────┐
│  目标：建立 Agent 能力模块化标准                           │
│  ───────────────────────────────────────────────         │
│  每个模块 = 技能 (Skills) + 经验 (Experiences)            │
│            + MCP 配置 + 知识库引用                        │
│  └─ 通过统一的适配层，部署到不同的 Agent 框架               │
|  └─ 预留扩展槽，Hermes 框架成长时自动吸纳新能力             │
|  └─ 随 boku 的进化不断迭代模块内容                         │
└─────────────────────────────────────────────────────────┘
```

## 🤝 最佳拍档：SRA (Skill Runtime Advisor)

> **CAP Pack = 技能的结构管理，SRA = 技能的运行时发现。两者互补，缺一不可。**

| | CAP Pack | SRA |
|:--|:----------|:-----|
| **解决什么问题** | 技能怎么分类、评分、合并、退役 | 用户发消息时该用什么技能 |
| **核心能力** | 树状索引 + SQS 质量分 + 生命周期 | 语义匹配 + 上下文注入 + 场景记忆 |
| **输出** | `cap-pack.yaml`, `skill-tree-index.py` | `POST /recommend` → rag_context |
| **消费方** | 开发者/维护者 | Agent 运行时 |
| **项目地址** | 你现在就在看 ✨ | [Hermes-Skill-View → SRA](https://github.com/JackSmith111977/Hermes-Skill-View) |

SRA 每次用户消息前自动推荐最匹配的技能，**CAP Pack 的分类体系和 SQS 质量分能让 SRA 推荐更精准**。详见 [SPEC-007: SRA-CAP Pack 适配方案](./docs/SPEC-007-sra-adaptation.md)。

## 核心概念

| 术语 | 定义 | 示例 |
|:-----|:-----|:------|
| **能力包 (Capability Pack)** | 一组可移植的 Agent 能力单元 | 文档生成包、安全审计包 |
| **技能 (Skill)** | 如何完成某事的步骤化指令 | pdf-layout/SKILL.md |
| **经验 (Experience)** | 什么场景用什么、已知陷阱 | WQY 字体回退经验、ReportLab 中文编码 |
| **MCP 配置** | 外部工具服务的连接定义 | OCR 服务、翻译 API、RAG 引擎 |
| **知识库引用** | 三层知识库的关联路径 | L3 Brain 概念页、L2 经验索引 |
| **适配器 (Adapter)** | 将能力包映射到特定 Agent 格式 | Hermes 适配器、Claude Code 适配器 |

---

## 📊 完整能力分类体系（v2.0 — 覆盖全部 185 项技能）

boku 的 185 个技能按领域分为 **18 个大类 + 3 个预留扩展槽**：

### 🟢 已定义的 18 个能力领域

| # | 模块 ID | 名称 | 技能数 | 核心能力 |
|:--|:--------|:-----|:------:|:---------|
| 1 | `knowledge-base` | 📚 知识库系统 | ~6 | 三层知识沉淀/索引/路由/维护 |
| 2 | `learning-engine` | 🧠 学习引擎 | ~7 | 深度调研/学习方法/技能创作/夜间自习 |
| 3 | `doc-engine` | 📄 文档生成 | ~12 | PDF/PPT/DOCX/HTML/LaTeX/EPUB/排版 |
| 4 | `developer-workflow` | 💻 开发工作流 | ~16 | SDD/计划/TDD/调试/子代理/Spike/环境 |
| 5 | `security-audit` | 🔒 安全审计 | ~5 | 删除安全/提交检查/秘密扫描/OSINT |
| 6 | `quality-assurance` | ✅ 质量保障 | ~10 | QA 门禁/测试框架/代码审查/文档对齐/对抗测试/SQS评分/生命周期审计 |
| 7 | `devops-monitor` | 🔧 运维监控 | ~8 | 系统健康/代理监控/Docker/进程/Webhook |
| 8 | `network-proxy` | 🌐 网络代理 | ~5 | Clash 配置/代理发现/浏览器自动化/网络访问 |
| 9 | `messaging` | 💬 消息平台 | ~8 | 飞书/微信/Email/短信/20+ 平台适配 |
| 10 | `agent-orchestration` | 🤖 Agent 协作 | ~12 | 子代理/多Agent/BMAD/Kanban/Advisor模式 |
| 11 | `mcp-integration` | 🔌 MCP 集成 | ~5 | 原生MCP/FastMCP/MCPorter/SRA消息注入 |
| 12 | `financial-analysis` | 📊 金融分析 | ~2 | akshare/ta/matplotlib/研报生成 |
| 13 | `creative-design` | 🎨 创意设计 | ~18 | 架构图/Mermaid/手绘/动画/像素画/表情包 |
| 14 | `media-processing` | 🎵 音视频媒体 | ~8 | TTS/音乐生成/频谱/GIF/图像生成/Prompt设计 |
| 15 | `github-ecosystem` | 🐙 GitHub 生态 | ~10 | PR/代码审查/Issues/Actions/Release/高级Git |
| 16 | `news-research` | 📰 新闻研究 | ~5 | 新闻简报/Arxiv/AI趋势/RSS/预测市场 |
| 17 | `metacognition` | 🪞 元认知系统 | ~6 | 自我分析/自我审查/防重复/能力地图/记忆管理 |
| 18 | `social-gaming` | 🎮 社交娱乐 | ~6 | MC服务器/宝可梦/健身/Xuite/元宝/Bangumi |

### 🟡 预留扩展槽（框架成长性）

| 槽位 | 用途 | 预期来源 |
|:-----|:------|:---------|
| `hermes-new-features` | Hermes 框架新增的未分类能力 | `hermes update` 新功能 |
| `custom-plugin` | 第三方 Plugin 生态 | `hermes plugin install` |
| `future-domain` | 尚未出现的全新领域 | AI Agent 技术演进 |

### 扩展性机制

```text
成长场景                              应对机制
─────────────────────────────────────────────────────
Hermes v2026.6 推出新工具集    →   智能路由到现有模块或创建新槽
boku 创建新 skill              →   skill 标签自动匹配模块分类
安装社区 MCP Server           →   按 domain/tags 归入对应模块
第三方 Plugin 安装            →   注册为 custom-plugin 模块
新消息平台适配                 →   messaging 模块自动扩展
Hermes 大版本升级              →   hermes-new-features 模块吸纳
```

---

## ⚙️ 分类原则（指导模块的持续扩展）

### 三个不变原则

| 原则 | 说明 | 实践 |
|:-----|:------|:------|
| **按领域不按工具** | 按「解决什么问题」而非「用什么工具」 | 一个模块含 Skills + Experiences + MCP |
| **模块内完整闭环** | 模块内容纳该领域的完整知识链 | 包含怎么做 + 何时做 + 踩过什么坑 |
| **扩展优先于重构** | 新能力先入槽，不完美也比丢失好 | 预留 3 个扩展槽，新技能自动匹配 |

### 分类决策树（新能力归属判断）

```
新能力诞生（新 skill / 新工具 / 新 MCP）
    ↓
① 属于已有领域？ → 是 → 归入对应模块
    ↓ 否
② 与多个领域交叉？ → 是 → 主模块 + 模块间交叉引用
    ↓ 否
③ 是全新的领域且有 ≥3 个技能？ → 是 → 创建新模块
    ↓ 否
④ 暂存到 hermes-new-features 待观察 → 满 3 技能后升级为独立模块
```

---

## 项目结构

```
~/projects/hermes-cap-pack/
├── README.md                         # ← 你正在看的
├── constraints.md                    # 项目约束与边界
├── docs/
│   ├── EPIC-001-feasibility.md       # Epic: 前期可行性调查
│   ├── SPEC-001-splitting.md         # Spec: 模块分割方案
│   ├── SPEC-002-management.md        # Spec: 模块生命周期管理
│   ├── SPEC-003-iteration.md         # Spec: 模块迭代与进化
│   ├── SPEC-004-adaptation.md        # Spec: 跨 Agent 适配层
│   └── STORY-TEMPLATE.md             # Story 模板（SDD 标准）
└── reports/
    └── lifecycle.html                # HTML 全生命周期追踪报告
```

## SDD 流程状态（v2.0 — CLARIFY → RESEARCH → CREATE → QA_GATE → REVIEW）

| Spec | SDD 进度 | CLARIFY | RESEARCH | CREATE | QA_GATE | REVIEW | 优先级 |
|:-----|:--------:|:-------:|:--------:|:------:|:-------:|:------:|:-----:|
| EPIC-001 | ✅ 完成 | ✅ | ✅ | ✅ | ✅ | ✅ 已批准 | P0 |
| SPEC-001 | ✅ 完成 | ✅ | ✅ | ✅ | ✅ | ✅ 已批准 | P1 |
| SPEC-002 | ✅ 完成 | ✅ | ✅ | ✅ | ✅ | ✅ 已批准 | P1 |
| SPEC-003 | ✅ 完成 | ✅ | ✅ | ✅ | ✅ | ✅ 已批准 | P1 |
| SPEC-004 | ✅ 完成 | ✅ | ✅ | ✅ | ✅ | ✅ 已批准 | P2 |
| **EPIC-002** | ⬜ draft | ✅ | ✅ | ✅ 部分 | ⬜ | ⬜ | **P1** |
| **SPEC-005** | ⬜ draft | ✅ | ✅ | ⬜ | ⬜ | ⬜ | **P1** |
| **SPEC-006** | ⬜ draft | ✅ | ✅ | ⬜ | ⬜ | ⬜ | **P1** |
| **SPEC-007** | ⬜ draft | ✅ | ✅ | ⬜ | ⬜ | ⬜ | **P1** |

### EPIC-002: Skill 树状层次管理与健康度优化（新建 — P1）

> 将 302 个扁平 skill 组织为三层树状索引，建立 SQS 质量评分与生命周期审计体系。

| 交付物 | 状态 | 说明 |
|:-------|:----:|:------|
| `docs/EPIC-002-tree-health.md` | ✅ 完成 | EPIC 文档 |
| `docs/SPEC-005-tree-index.md` | ✅ 完成 | 树状索引系统规范 |
| `docs/SPEC-006-quality-health.md` | ✅ 完成 | SQS 质量评分系统规范 |
| `docs/stories/STORY-011~015` | ✅ 完成 | 5 个 Story 文档（draft） |
| `scripts/skill-tree-index.py` | ✅ 完成 | 三层树状索引生成器 |
| `scripts/skill-quality-score.py` | ✅ 已纳入 | SQS 五维评分引擎 |
| `scripts/skill-lifecycle-audit.py` | ✅ 已纳入 | 生命周期审计与退役管理 |
| `packs/quality-assurance/` | ✅ 已创建 | 质量保障能力包 |
| `reports/skill-tree-architecture-research.html` | ✅ 已更新 | 研究报告（来源可点击） |
| `docs/SPEC-007-sra-adaptation.md` | ✅ 完成 | SRA 运行时发现层适配方案 |
| `docs/stories/STORY-016~017` | ✅ 完成 | SRA 分类映射 + SQS 质量加权 |
| `scripts/skill-tree-index.py` | ✅ SRA 模式 | `--sra` 输出簇/包/同类技能格式 |

## Phase 1 进展（格式设计 + 原型 — 进行中）

| 产出物 | 状态 | 说明 |
|:-------|:----:|:------|
| `schemas/cap-pack-format-v1.md` | ✅ 完成 | YAML 格式规范 v1（含完整字段定义） |
| `schemas/cap-pack-v1.schema.json` | ✅ 完成 | JSON Schema（可验证所有 cap-pack.yaml） |
| `packs/doc-engine/cap-pack.yaml` | ✅ 完成 | 文档生成能力包（9 skills + 11 experiences + linked files） |
| `packs/doc-engine/SKILLS/` | ✅ 完成 | 9 个技能（含 scripts/references/checklists） |
| `packs/doc-engine/EXPERIENCES/` | ✅ 完成 | 11 个实战经验文档 |
| `packs/quality-assurance/cap-pack.yaml` | ✅ 完成 | 质量保障能力包（SQS + 审计 + 树索引） |
| `scripts/skill-tree-index.py` | ✅ 完成 | 三层树状索引生成器 + 合并潜力分析 |
| `scripts/skill-quality-score.py` | ✅ 已纳入 | SQS 五维质量评分引擎 |
| `scripts/skill-lifecycle-audit.py` | ✅ 已纳入 | 生命周期审计 + deprecate/revive 管理 |
| `scripts/extract-pack.py` | ✅ 完成 | 从 Hermes 提取真实 skill 内容到能力包 |
| `scripts/validate-pack.py` | ✅ 完成 | 能力包完整性验证（JSON Schema + 文件检查） |
| `scripts/install-pack.py` | ✅ 完成 | 安装能力包到 Hermes（备份还原 + hooks） |
| `reports/skill-tree-architecture-research.html` | ✅ 完成 | 树状层次可行性研究报告（来源可点击） |
|| `pyproject.toml` | ✅ 完成 | 项目元数据 + 版本管理（version: 0.3.0） |
|| `scripts/bump-version.py` | ✅ 完成 | 版本号自动递增（patch/minor/major + git tag） |
|| `.github/workflows/ci.yml` | ✅ 完成 | GitHub Actions CI（4 job 并行质量门禁） |
|| `scripts/ci-check-yaml.py` | ✅ 完成 | YAML 语法验证 |
|| `scripts/ci-check-cross-refs.py` | ✅ 完成 | 跨包引用完整性检查 |
|| Hermes 适配器 | ⏳ 下一轮 | 将能力包安装到 Hermes 的适配器脚本 |
| 更多模块提取 | ⏳ Phase 1.2 | learning-engine, developer-workflow 等 |

### 项目结构

```
~/projects/hermes-cap-pack/
├── README.md                         # 项目说明
├── CHANGELOG.md                      # 版本日志
├── constraints.md                    # 项目约束与边界
├── pyproject.toml                     # 项目元数据 + 版本管理（0.3.0）
├── .gitignore
├── docs/
│   ├── EPIC-001-feasibility.md       # Epic: 前期可行性调查
│   ├── SPEC-001-splitting.md         # Spec: 模块分割方案
│   ├── SPEC-002-management.md        # Spec: 模块生命周期管理
│   ├── SPEC-003-iteration.md         # Spec: 模块迭代与进化
│   ├── SPEC-004-adaptation.md        # Spec: 跨 Agent 适配层
│   └── STORY-TEMPLATE.md             # Story 模板（SDD 标准）
├── schemas/
│   ├── cap-pack-format-v1.md         # 能力包格式规范 v1
│   └── cap-pack-v1.schema.json       # JSON Schema 验证
├── packs/
│   └── doc-engine/                   # 第一个原型能力包
│       ├── cap-pack.yaml             # 模块清单（9 skills + 11 experiences）
│       ├── SKILLS/                   # 技能引用（9个）
│       ├── EXPERIENCES/              # 实战经验（11个）
│       └── MCP/                      # MCP 配置（当前空）
├── .github/workflows/
│   └── ci.yml                        # GitHub Actions CI 工作流
├── scripts/
│   ├── bump-version.py               # 版本号自动递增
│   ├── ci-check-yaml.py              # YAML 语法验证（CI）
│   ├── ci-check-cross-refs.py        # 跨包引用检查（CI）
│   ├── validate-pack.py              # 能力包完整性验证
│   ├── health-check.py               # 健康检查 + 量化测试
│   ├── install-pack.py               # 安装能力包到 Hermes
│   ├── extract-pack.py               # 从 Hermes 提取 skill 内容
│   ├── skill-tree-index.py           # 三层树状索引生成器
│   ├── skill-quality-score.py        # SQS 五维质量评分引擎
│   ├── skill-lifecycle-audit.py      # 生命周期审计
│   └── sra-discovery-test.py         # SRA 发现测试
└── reports/
    └── lifecycle.html                # HTML 全生命周期追踪报告
```

## 四个核心问题

本项目的可行性调查围绕四个核心问题展开：

1. **如何分割 (Splitting)** — 按什么粒度、什么维度将 185 个技能拆分为 ~18 个独立模块？
2. **如何管理 (Management)** — 模块的生命周期、版本、依赖如何管理？
3. **如何迭代 (Iteration)** — 模块如何随 boku 的进化不断更新？
4. **如何适配 (Adaptation)** — 跨 Agent 的适配层如何设计？
