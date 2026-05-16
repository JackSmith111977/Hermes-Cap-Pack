# RESEARCH: SPEC-6-1 — Fix 基础设施 + 确定性修复

> **调研时间**: 2026-05-16
> **调研范围**: Fix 规则引擎架构、修复模式、README AI 友好化、适配器初始化流程
> **调研深度**: P0（深度）
> **调研方法**: 代码级调研（主要）+ 方法论参考（次要）

---

## 1. 搜索记录

### Round 1: 代码级调研（广度扫描）

| 调研方向 | 方法 | 核心发现 |
|:---------|:-----|:---------|
| 现有 fix 脚本的备份机制 | `grep -rn` 搜索 fix-*.py | 🔴 **无备份机制** — 所有脚本直接修改文件 |
| 现有 fix 脚本的幂等性 | 代码分析 | 🟢 fix-low-score-skills.py 有 `skip if already` 模式可复用 |
| FixRule 的复用来源 | `read_file` + 分析 | 🟢 4 个主要可复用模式：YAML RMW、frontmatter 正则、Jaccard、启发式检测 |
| README 当前状态 | `wc -l` + `head` | 406 行，有基础结构但缺少：跨 Agent 概念、适配器指南、初始化流程 |
| README 优化方法论 | `skill_view(readme-for-ai)` | 11 条原则可用，特别是：CLI 三列表格、编号章节、每节验证命令 |
| 适配器初始化流程 | 代码分析 hermes.py:210 | HermesAdapter.install() 已有 dry_run 模式，入口清晰 |

### Round 2: 深度挖掘

| 调研方向 | 方法 | 核心发现 |
|:---------|:-----|:---------|
| ScanReport → FixRule 数据流 | `read_file` models/result.py | `CheckResult.details` → fix rule 上下文；`CheckResult.suggestions` → fix 建议 |
| CLI 命令注册模式 | 分析 cli/main.py | `@app.command()` 模式，fix 命令可平行于 scan/watcher/rules |
| 包内测试夹具模式 | 分析 test_cli_commands.py | `tmp_path` + `monkeypatch` 模式，可复用 |
| MCP Server 的 cross-agent 价值 | 分析 mcp/ | MCP 协议允许任何 MCP 兼容 Agent 调用治理扫描 |

---

## 2. 来源清单

| 来源 | 等级 | 可信度 | 备注 |
|:-----|:----:|:------:|:-----|
| 项目自身代码 (fix-*.py) | 🥇 | 高 | 直接复用模式 |
| models/result.py | 🥇 | 高 | 数据模型定义 |
| cli/main.py | 🥇 | 高 | CLI 注册入口 |
| scripts/adapters/hermes.py:210 | 🥇 | 高 | install 方法签名 |
| readme-for-ai skill | 🥇 | 高 | 官方方法论 |
| README.md (当前) | 🥇 | 高 | 改造目标 |

---

## 3. 结构化分析

### MECE 分类：FixRule 设计模式

```
所有修复规则 (FixRule)
├── 确定性规则 (Deterministic)
│   ├── 模板生成型: F001 (SKILL.md 骨架)
│   ├── 提取填充型: F007 (triggers from tags)
│   └── 算法匹配型: H001 (Jaccard 簇归属)
├── 启发式规则 (Heuristic)
│   ├── 关键词推断: F006 (classification)
│   └── 统计推断型: H002 (簇 < 3 合并建议)
└── LLM 辅助规则 (LLM-assisted) — Phase 2
    ├── 语义生成型: E001 (SRA triggers), E002 (agent_types)
    └── 外部验证型: E005 (断裂链接)
```

### ADR 记录

#### ADR-6-1: FixRule 的 analyze/apply 双阶段设计

**状态**: accepted
**背景**: FixRule 需要在 dry_run 模式（只预览不修改）和 apply 模式（实际执行）之间切换

**方案对比**:
- 方案 A: 单一方法 + dry_run 参数 → 逻辑耦合，违反单一职责
- 方案 B: `analyze()` 生成计划 + `apply()` 执行计划 → 清晰分离预览和执行
- 方案 C: 策略模式 → 过度设计，fix 规则逻辑简单

**决策**: 方案 B — 双阶段设计
**理由**: 与 CapPackAdapter 已有模式一致，dry_run 和 apply 天然分离
**后果**: 每条 FixRule 需要实现两个方法，但逻辑复用更清晰

#### ADR-6-2: 备份机制采用 `.bak` 文件

**状态**: accepted
**背景**: apply 前需要备份原始文件，便于回滚

**方案对比**:
- 方案 A: `shutil.copy2` 生成 `.bak` 文件 → 简单直观
- 方案 B: git 自动 commit → 过度，修复不总是需要 git
- 方案 C: 临时目录快照 → 复杂，管理成本高

**决策**: 方案 A — `.bak` 文件
**理由**: 简单、零依赖、可独立于 git 使用
**后果**: 同目录下会生成 `.bak` 文件，修复后手动清理

#### ADR-6-3: README 采用编号中文章节 + 三列 CLI 表

**状态**: accepted
**背景**: README 需要让 AI Agent 快速理解 cap-pack 的核心概念和使用方式

**方案对比**:
- 方案 A: 传统 README 风格 → 人类友好但 AI 扫描效率低
- 方案 B: readme-for-ai 方法论 → CLI 三列表格 + 编号章节 + 每节验证命令 + 多路径安装
- 方案 C: 纯 markdown 表格 → 缺少概念解释

**决策**: 方案 B — readme-for-ai 方法论
**理由**: 已验证的方法论，cap-pack 当前 README 已有部分采用此风格
**后果**: README 结构大改，需同步更新 validate-readme.py

#### ADR-6-4: CLI fix 命令放在 cli/main.py

**状态**: accepted
**背景**: fix 命令需要复用 `_load_skills_from_pack()` 和 `_build_report()`

**方案对比**:
- 方案 A: cli/main.py 新增 `@app.command("fix")` → 直接复用现有 CLI 基础设施
- 方案 B: 独立 `fix.py` 脚本 → 需要复制扫描逻辑
- 方案 C: fixer/cli.py 子模块 → 增加模块间调用层级

**决策**: 方案 A
**理由**: 避免代码重复，fix 命令本质是 scan 的互补功能
**后果**: cli/main.py 会增加 ~80 行

---

## 4. 调研结论

### 关键发现

| 发现 | 影响 | 来源 |
|:-----|:-----|:------|
| 现有 fix 脚本无备份机制 | EPIC-006 必须从零构建备份 | 代码调研 Round 1 |
| 幂等性模式可复用 | F001/F006/F007 可快速实现 | fix-low-score-skills.py:49 |
| CapPackAdapter.suggest() 的 Jaccard 可直接复用 H001 | H001 实现成本降低 50% | adapter/cap_pack_adapter.py:105 |
| README 已有 406 行但缺少跨 Agent 概念 | 需要重写而非补丁 | README 分析 |
| readme-for-ai 方法论 11 条原则可用 | README 改造有明确指导 | skill_view() |
| 零新增 pip 依赖 | 所有功能用标准库 + pyyaml/typer/rich | 依赖分析 |

### 建议 Execution 顺序

```text
Phase 0: FixRule ABC + CLI fix  + 报告格式  (准备基础设施)
    ↓
Phase 1: F001 → F007 → H001+H002 → F006    (确定性修复，由易到难)
    ↓
Phase 2: LLM 框架 → E001+E002 → E005       (LLM 辅助，依赖 Phase 1)
    ↓
Phase 3: README 重写 → ADAPTER_GUIDE        (文档，最后做最准确)
```
