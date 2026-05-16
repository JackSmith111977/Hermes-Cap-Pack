# EPIC-006: Governance Fix Engine + 跨 Agent Cap-Pack 适配

> **epic_id**: `EPIC-006`
> **status**: `implemented`
> **created**: 2026-05-16
> **updated**: 2026-05-16
> **owner**: boku (Emma)
> **优先级**: P1 — 治理引擎闭环 + 跨 Agent 标准
> **估算**: ~18h（4 Phases · ~12 Stories）
> **前置条件**: EPIC-005 治理引擎全部完成 ✅
> **SDD 流程**: `CLARIFY ✅ → RESEARCH ✅ → SPEC-6-1/6-2/6-3 ✅ → IMPLEMENT ✅ → QA_GATE ✅ → COMMIT ✅`
> **完成情况**: 12/12 Stories ✅ — Phase 0-3 全部交付

---

## 〇、动机与背景

### 为什么要做？

Cap-pack 的目标不是改造某个 Agent 的内部技能库，而是成为 **跨 Agent 的技能包通用标准**。就像 Docker 镜像可以在任何容器运行时上运行一样，cap-pack 技能包应该能在 **Hermes / OpenCode / Claude Code / MCP** 等任意 Agent 上即插即用。

当前存在的两个关键缺口：

#### 缺口 1：检测后无自动修复
EPIC-005 交付的治理引擎能检测问题，但 **不能自动修复**。18 个包的合规分平均仅 79.6，100% 的包存在 F001/F006/F007/E001 问题。

```text
现状:  检测 → 看报告 → 手动修 → 再检测  循环太慢
目标:  检测 → 一键修复 → 确认          秒级闭环
```

#### 缺口 2：跨 Agent 适配过程不透明
EPIC-005 Phase 3 已经交付了 4 个适配器（Hermes / OpenCode / OpenClaw / Claude），但：
- 新 Agent 怎么接入 cap-pack？适配器怎么用？
- Agent 如何挂载/卸载技能包？保留自己独特的技能？
- 整个 cap-pack 的能力范围和管理方式没有清晰的文档

**核心问题**：适配器写得再好，没人知道怎么用就等于白做。

### 目标

| 维度 | 当前 | 目标 |
|:-----|:-----|:------|
| 修复效率 | 手动修，每包 ~30min | `fix --all` 秒级修复 |
| 合规分 | 79.6 | ≥ 90 |
| 跨 Agent 理解 | 适配器存在但不透明 | README 让任意 AI Agent 看 5 分钟就能上手 |
| Agent 独立性 | ❌ 可能误改造用户技能库 | ✅ 保留 Agent 自有技能，cap-pack 是挂载层 |

---

## 一、解决方案全景

### 架构：分层修复 + 跨 Agent 文档

```text
EPIC-006
│
├── Phase 0-1: 修复引擎核心 ──→ 确保所有 cap-pack 合规 → 可靠的基础
│   FixRule ABC → Dispatcher → 5 条确定性规则
│
├── Phase 2: LLM 辅助修复  ──→ 处理语义型问题（classification/SRA）
│   LLM 辅助框架 → F006 增强 → E001/E002 → E005 断链
│
└── Phase 3: 跨 Agent 适配文档 ──→ 让任意 Agent 知道怎么用
    README 重写 → 适配器指南 → 初始化流程 → CLI 参考
                    ↓
          新 Agent 可以 5 分钟上手
```

### 跨 Agent Cap-Pack 的核心模型

```
┌──────────────────────────────────────────┐
│             Agent A 原生技能库              │
│  ~/.hermes/skills/  (Hermes 独有)         │
│  ~/.claude/skills/  (Claude 独有)         │
└──────────────────────────────────────────┘
              ↑ 保留不变，cap-pack 不碰这里
              │
┌──────────────────────────────────────────┐
│         Cap-Pack 挂载层 (新增)              │
│  mounts:                                   │
│    - packs/doc-engine/   → Hermes 可用     │
│    - packs/quality-assurance/ → Hermes 可用│
│    - packs/... (跨 Agent 共享)              │
└──────────────────────────────────────────┘
              ↑ 通过适配器安装/卸载/更新
              │
         skill-governance fix → 确保合规
```

---

## 二、Phase 计划

### Phase 0 — Fix 基础设施（3 Stories · ~4h）

| Story | 内容 | 估算 | 产出物 |
|:------|:-----|:----:|:-------|
| STORY-6-0-1 | **FixRule 抽象层 + Dispatcher** | 2h | `fixer/base.py`, `fixer/dispatcher.py` |
| STORY-6-0-2 | **CLI `fix` 子命令** | 1h | `cli/main.py` 扩展 — fix 命令 |
| STORY-6-0-3 | **dry_run/apply 报告格式 + 备份机制** | 1h | 修复前后对比 + `.bak` 文件 |

### Phase 1 — 确定性修复引擎（4 Stories · ~5h）

| Story | 内容 | 估算 | 产出物 |
|:------|:-----|:----:|:-------|
| STORY-6-1-1 | **F001: 生成缺失 SKILL.md** | 1.5h | `fixer/rules/f001_skill_md.py` |
| STORY-6-1-2 | **F007: 提取 triggers** | 1h | `fixer/rules/f007_triggers.py` |
| STORY-6-1-3 | **H001+H002: 树簇归属+簇大小优化** | 1.5h | `fixer/rules/h001_cluster.py`, `h002_cluster_size.py` |
| STORY-6-1-4 | **F006: 启发式 classification + 测试套件** | 1h | `fixer/rules/f006_classification.py` + `tests/` |

### Phase 2 — LLM 辅助修复（3 Stories · ~4h）

| Story | 内容 | 估算 | 产出物 |
|:------|:-----|:----:|:-------|
| STORY-6-2-1 | **LLM 辅助修复框架 + F006 增强** | 1.5h | `fixer/llm_assist.py` |
| STORY-6-2-2 | **E001 SRA 元数据 + E002 跨平台声明** | 1.5h | `fixer/rules/e001_sra.py`, `e002_cross_platform.py` |
| STORY-6-2-3 | **E005 断裂链接检测与修复** | 1h | `fixer/rules/e005_broken_links.py` |

### Phase 3 — 跨 Agent 适配文档与 README（2 Stories · ~5h）

| Story | 内容 | 估算 | 产出物 |
|:------|:-----|:----:|:-------|
| STORY-6-3-1 | **README 全面重写（AI 友好版）** | 3h | `README.md` v2.0 |
| STORY-6-3-2 | **适配器指南 + 初始化流程 + CLI 速查** | 2h | `docs/ADAPTER_GUIDE.md`, `docs/QUICKSTART.md` |

#### README v2.0 要求

必须让任何 AI Agent **在 5 分钟内理解 cap-pack**：

```markdown
# Hermes Capability Pack

## 🤔 Cap-Pack 是什么？
一句话：就像 Docker 镜像之于容器，Cap-Pack 是跨 Agent 的技能包标准。

## 🎯 核心能力
- 📦 技能打包：将多个 SKILL.md 打包为标准化能力包
- 🔄 跨 Agent：同一套包可在 Hermes / OpenCode / Claude 等任意 Agent 挂载
- 🛡️ 质量治理：L0-L4 四层合规检测 + 自动修复
- 🔌 即插即用：install/uninstall/list 一条命令

## 🧠 对 AI Agent 的意义
- 你不需要改造自己的技能库
- Cap-Pack 是挂载层：安装后你的原生技能 + 包技能同时可用
- 包之间的依赖自动解析，冲突自动检测

## 🚀 快速开始 (5 分钟)
# 1. 安装一个包
python3 -m scripts.cli.main install packs/doc-engine/

# 2. 检查合规
skill-governance scan packs/doc-engine/

# 3. 自动修复问题
skill-governance fix packs/doc-engine/ --apply

## 🔧 适配器体系
| Agent | 适配器 | 状态 |
|-------|--------|------|
| Hermes | HermesAdapter | ✅ 可用 |
| OpenCode | OpenCodeAdapter | ✅ 可用 |
| OpenClaw | OpenClawAdapter | ✅ 可用 |
| Claude Code | ClaudeAdapter | ✅ 可用 |
| MCP 兼容 | MCP Server | ✅ 可用 |

## 📋 CLI 速查
...
```

---

## 三、Phase 验收标准

### Phase 0
- [x] FixRule 抽象基类定义 analyze() + apply() 接口
- [x] Dispatcher 根据规则 ID 路由到具体 FixRule
- [x] CLI `fix` 子命令支持 --dry-run / --apply / --rules / --all
- [x] dry_run 输出：创建/修改文件列表 + unified diff
- [x] apply 前自动备份（.bak 文件）
- [x] 所有 FixRule 幂等（已合规则跳过）

### Phase 1
- [x] F001: 自动生成缺失的 SKILL.md 骨架文件
- [x] F007: 从 tags/description 提取 triggers
- [x] H001: Jaccard 匹配最佳簇归属
- [x] H002: 簇 < 3 时建议合并目标
- [x] F006: 从包名/description 启发式推断 classification
- [x] 包内 `tests/` 测试套件 > 90% 覆盖率

### Phase 2
- [x] LLM 辅助修复框架：给定扫描结果 + SKILL.md → 结构化修复建议
- [x] E001: 生成 SRA triggers 提升可发现性
- [x] E002: 补充 cross-platform agent_types 声明
- [x] E005: 检测内外断裂链接，建议替换或移除

### Phase 3
- [x] README.md 完整重写：AI 友好，5 分钟上手
- [x] README 包含：cap-pack 概念、跨 Agent 模型、CLI 速查、适配器一览
- [x] ADAPTER_GUIDE.md：每个适配器的使用案例 + 配置 + 故障排查
- [x] QUICKSTART.md：新 Agent 初始化接入流程
- [x] 文档让任意 AI Agent 阅读后能独立完成 cap-pack 的安装/卸载/检查

---

## 四、不做的范围

| 项目 | 理由 |
|:-----|:------|
| ❌ 改造任何 Agent 原生技能库 | Cap-pack 是挂载层，不碰 Agent 自有技能 |
| ❌ Web UI 仪表盘 | CLI + README 已满足 |
| ❌ 自动 git commit | 修复由主人确认后手动提交 |
| ❌ 公共注册中心 | 属于 cap-pack 生态后续环节 |
| ❌ 自动修改 SKILL.md 正文内容 | 只改 frontmatter 和缺失文件 |

---

## 五、成功指标

| 指标 | 目标值 | 测量方式 |
|:-----|:------:|:---------|
| 修复覆盖 | ≥ 10 条扫描规则有对应 fix 规则 | `fix --list-rules` |
| 批量速度 | 18 包 < 60s（确定性修复） | `time fix --all --rules F001` |
| 合规分 | 平均分 79.6 → ≥ 90 | 修复前后扫描对比 |
| README 可读性 | 新 AI Agent 5 分钟内理解 | 自行测试 |
| 适配器覆盖 | 4 个适配器均有使用文档 | ADAPTER_GUIDE.md |
