# hermes-cap-pack

> Agent 能力包标准化格式 + CLI 管理工具  
> **版本**：`0.9.1` · **测试**：`141 ✅` · **许可**：MIT  
> **能力包**：17 个 · **适配器**：4 个 · **CHI**：`67.92` 🟡  
> **跨 Agent 就绪**：✅ Hermes · ✅ OpenCode · ✅ Claude · ✅ OpenClaw

---

## 一、项目身份

| | 属性 | 值 |
|:-----|:----|
| **目的** | 将 AI Agent 的技能拆分为可移植的「能力包 (Capability Pack)」，实现跨 Agent 复用与质量治理 |
| **CLI 入口** | `python -m scripts.cli.main`（或创建 alias `cap-pack`） |
| **Schema 版本** | `schemas/cap-pack-v0.9.1schema.json` |
| **最小 Python** | ≥ 3.11 |
| **唯一依赖** | `pyyaml>=6.0` |
| **仓库** | `https://github.com/JackSmith111977/Hermes-Cap-Pack.git` |
| **作者** | boku (Emma) |

**验证版本**：
```bash
python3 --version
# 预期输出: Python 3.11.x 或以上

python -m scripts.cli.main --help
# 预期输出: 显示 cap-pack CLI 帮助信息
```

---

## 二、快速安装

### 前置条件

```bash
python3 --version
# 预期输出: Python 3.11.x 或以上

git --version
# 预期输出: git 2.x
```

### 安装

```bash
# 1. 克隆
git clone https://github.com/JackSmith111977/Hermes-Cap-Pack.git
cd Hermes-Cap-Pack

# 2. 安装 Python 依赖
pip install pyyaml>=6.0

# 3. 验证
python -m scripts.cli.main --help

# 4. （可选）创建 alias
alias cap-pack='python -m scripts.cli.main'
```

**验证安装成功**：
```bash
python -m scripts.cli.main list
# 预期输出: 📭 (无已安装的能力包)
```

---

## 三、跨 Agent 核心概念

### 什么是 Capability Pack？

**能力包 (Cap-Pack)** 是将 AI Agent 的技能（Skills）、实战经验（Experiences）、
MCP 工具配置封装为一个标准化目录结构。一个能力包可以在 **不同 Agent 之间移植安装**
——从 Hermes Agent 安装到 OpenCode CLI、Claude Code、或 OpenClaw，无需手动转换格式。

### 架构总览

```
┌────────────────────────────────────┐
│     Agent A 原生技能库              │
│  (Hermes Agent 已有 351+ 技能)     │
└───────────────┬────────────────────┘
                │ 技能提取 → 标准化打包
                ▼
┌────────────────────────────────────┐
│      Cap-Pack 标准化层              │
│  ┌──────────┐┌──────────┐┌───────┐ │
│  │PackParser││Dependency││Verifier│ │
│  │(YAML解析) ││(依赖检查) ││(验证)  │ │
│  └──────────┘└──────────┘└───────┘ │
│  ┌──────────────────────────────┐  │
│  │   AgentAdapter Protocol 层    │  │
│  │ ┌──────┐┌────────┐┌───────┐  │  │
│  │ │Hermes││OpenCode││Claude │  │  │
│  │ │Adapt ││Adapter ││Adapter│  │  │
│  │ └──────┘└────────┘└───────┘  │  │
│  │ ┌────────┐                    │  │
│  │ │OpenClaw│ ← 相同 Protocol    │  │
│  │ │Adapter │   各适配器格式转换   │  │
│  │ └────────┘                    │  │
│  └──────────────────────────────┘  │
└───────────────┬────────────────────┘
                │ 安装 → 格式转换 → 注入
                ▼
┌────────────────────────────────────┐
│     Agent B 原生技能库              │
│  (OpenCode/Claude/OpenClaw 各格式)  │
└────────────────────────────────────┘

┌────────────────────────────────────┐
│     skill-governance 治理引擎       │
│  ┌──────┐┌──────┐┌──────┐┌─────┐  │
│  │L0兼容 ││L1基础││L2健康││L3+L4│  │
│  │性检查 ││结构查││原子性││生态/ │  │
│  │      ││     ││检查 ││工作流│  │
│  └──────┘└──────┘└──────┘└─────┘  │
│  MCP Server: scan/suggest/apply    │
└────────────────────────────────────┘
```

### 核心流程

```
原始技能 (SKILL.md)     Cap-Pack 目录         目标 Agent
     │                       │                     │
     ▼                       ▼                     ▼
┌─────────┐         ┌──────────────┐      ┌──────────────┐
│ Hermes  │─提取→    │ packs/doc-   │─安装→│ Hermes:      │
│ 351+    │          │ engine/      │      │ ~/.hermes/   │
│ 技能    │          │ ├ cap-pack.  │      │   skills/    │
│         │          │ │ yaml       │      │              │
└─────────┘          │ ├ SKILLS/    │─安装→│ OpenCode:    │
                     │ ├ EXPERIENCI │      │ ~/.config/   │
Agent 原生 ←─────────│ │ ES/        │      │   opencode/  │
 复用已有能力         │ ├ MCP/       │─安装→│ Claude:      │
                     │ └ SCRIPTS/   │      │ ~/.claude/   │
                     └──────────────┘      │   skills/    │
                                           └──────────────┘
```

### 治理循环

```
scan ──→ 发现 L0-L4 问题 ──→ suggest ──→ 推荐修复方案
  ↑                                      │
  │                                      ▼
  └──── verify ←──── apply ←─── dry_run (预览)
```

**验证核心概念**：
```bash
python -m scripts.cli.main list
# 预期输出: 📭 (无已安装的能力包) 或列出已安装包

python -m scripts.cli.main status
# 预期输出: 📊 能力包状态概览 (含包数量、质量评分等)
```

---

## 四、CLI 完整参考

### 完整命令速查（三列参考表）

| 命令 | 作用 | 关键参数 |
|:-----|:-----|:---------|
| `install <dir>` | 安装能力包到目标 Agent | `--dry-run`, `--target hermes\|opencode\|auto` |
| `remove <name>` | 卸载已安装的能力包 | `--target hermes\|opencode` |
| `verify <name>` | 验证安装完整性 | `--target hermes\|opencode` |
| `list` | 列出已安装包 | `--target hermes\|opencode` |
| `inspect <dir>` | 查看包内容（不安装） | — |
| `upgrade <name>` | 升级已安装的包 | `--all`, `--dry-run` |
| `status` | 全局状态概览 | — |
| `search <term>` | 搜索可用包 | — |
| `skill add <p> <src>` | 向包添加 skill | — |
| `skill remove <p> <id>` | 从包移除 skill | `--dry-run` |
| `skill list <p>` | 列出包内 skill | — |
| `skill update <p> <id> [src]` | 更新包内 skill | — |

### 典型使用场景

```bash
# 安装能力包（含 MCP 配置注入）
cap-pack install packs/doc-engine
# 预期输出:
# ============================================================
#   📦 安装能力包: doc-engine
# ============================================================
#     名称:    doc-engine
#     版本:    2.0.0
#     Skills:  9
#     经验:    11
#     MCP:     3
#     目标:    auto
#     适配器:  HermesAdapter
#   ✅ 安装完成！共安装 9 个 skill → HermesAdapter

# 安装到 OpenCode
cap-pack install packs/doc-engine --target opencode
# 预期输出:
#   ✅ 安装完成！共安装 9 个 skill → OpenCodeAdapter

# 预览安装（不实际执行）
cap-pack install packs/doc-engine --dry-run
# 预期输出:
#   🔍 [DRY RUN] 将安装以下 skill:
#     📄 pdf-layout  —  PDF 布局引擎

# 卸载
cap-pack remove doc-engine
# 预期输出: ✅ 卸载完成

# 验证安装
cap-pack verify doc-engine
# 预期输出: ✅ 验证通过

# 搜索
cap-pack search doc
# 预期输出: 📦 doc-engine (2.0.0) — 文档引擎能力包
```

**验证 CLI 功能**：
```bash
cap-pack status
# 预期输出包含: 📊 能力包状态概览
```

---

## 五、能力包列表

当前 **17 个能力包**（全部在 `packs/` 目录下）：

| 包名 | 目录 | Skills | 版本 | 状态 |
|:-----|:-----|:------:|:----:|:----:|
| **agent-orchestration** | `packs/agent-orchestration/` | 8 | 1.0.0 | ✅ 完整 |
| **creative-design** | `packs/creative-design/` | 26 | 1.0.0 | ✅ 完整 |
| **developer-workflow** | `packs/developer-workflow/` | 16 | 1.0.0 | ✅ 完整 |
| **devops-monitor** | `packs/devops-monitor/` | 10 | 1.0.0 | ✅ 完整 |
| **doc-engine** | `packs/doc-engine/` | 12 | 2.0.0 | ✅ 完整 |
| **financial-analysis** | `packs/financial-analysis/` | 1 | 1.0.0 | ✅ 完整 |
| **github-ecosystem** | `packs/github-ecosystem/` | 9 | 1.0.0 | ✅ 完整 |
| **learning-engine** | `packs/learning-engine/` | 11 | 1.0.0 | ✅ 完整（含知识库） |
| **learning-workflow** | `packs/learning-workflow/` | 4 | 5.5.0 | ✅ 完整 |
| **media-processing** | `packs/media-processing/` | 5 | 1.0.0 | ✅ 完整 |
| **messaging** | `packs/messaging/` | 8 | 1.0.0 | ✅ 完整 |
| **metacognition** | `packs/metacognition/` | 6 | 1.0.0 | ✅ 完整 |
| **network-proxy** | `packs/network-proxy/` | 3 | 1.0.0 | ✅ 完整 |
| **quality-assurance** | `packs/quality-assurance/` | — | 1.0.0 | ✅ 完整（基础设施型） |
| **security-audit** | `packs/security-audit/` | 5 | 1.0.0 | ✅ 完整 |
| **skill-quality** | `packs/skill-quality/` | — | 1.0.0 | ✅ 完整（基础设施型） |
| **social-gaming** | `packs/social-gaming/` | 4 | 1.0.0 | ✅ 完整 |

> **已覆盖：17/17 模块（100%）** — 全部模块三层结构完整 📦
> 质量基线：**CHI 67.92** · **SQS 均分 67.9** · 详见 `docs/EPIC-004-quality-upgrade.md`

**验证能力包列表**：
```bash
ls -d packs/*/
# 预期输出: 17 个能力包目录

python -m scripts.cli.main search doc
# 预期输出: 📦 doc-engine (2.0.0) — 文档引擎能力包
```

---

## 六、适配器体系

### 适配器一览表（4 个适配器）

| 适配器 | 类 | 文件路径 | 状态 | 目标 Agent | 安装路径 |
|:-------|:---|:---------|:----:|:-----------|:---------|
| **Hermes** | `HermesAdapter` | `scripts/adapters/hermes.py` | ✅ 稳定 | Hermes Agent | `~/.hermes/skills/{id}/` |
| **OpenCode** | `OpenCodeAdapter` | `scripts/adapters/opencode.py` | ✅ 稳定 | OpenCode | `~/.config/opencode/skills/` |
| **OpenClaw** | `OpenClawAdapter` | `packages/.../adapter/openclaw_adapter.py` | ✅ 稳定 | OpenClaw Agent | 直接导入扫描模块 |
| **Claude** | `ClaudeAdapter` | `packages/.../adapter/claude_adapter.py` | ✅ 稳定 | Claude Code | 子进程委派模式 |

### UCA Protocol 接口

所有适配器遵循 `AgentAdapter` Protocol（`scripts/uca/protocol.py`）
或 `SkillGovernanceAdapter` ABC（`packages/.../adapter/base.py`）：

```
AgentAdapter / SkillGovernanceAdapter
 ├── name                 # 适配器名称（唯一标识）
 ├── is_available         # 检测目标 Agent 是否可访问
 ├── install(pack)        # 安装能力包到目标 Agent
 ├── uninstall(name)      # 卸载已安装的能力包
 ├── verify(name)         # 验证安装完整性
 ├── list_installed()     # 列出已安装的能力包
 ├── update(pack, old)    # 升级已安装的能力包
 ├── scan(path)           # L0-L4 合规扫描（治理层）
 ├── suggest(path)        # 推荐最佳匹配能力包
 ├── dry_run(path)        # 预览适应操作
 └── apply(path)          # 执行适应操作
```

### 适配器选择策略

| 条件 | 使用适配器 |
|:-----|:-----------|
| 在 Hermes 环境中运行 | `HermesAdapter`（auto 检测优先） |
| 使用 OpenCode CLI | `OpenCodeAdapter`（`--target opencode`） |
| 使用 Claude Code | `ClaudeAdapter`（子进程委派） |
| 使用 OpenClaw | `OpenClawAdapter`（直接导入扫描模块） |
| 不确定目标 | `auto` 模式（自动检测 Hermes → OpenCode） |

**验证适配器可用性**：
```bash
python3 -c "from scripts.adapters.hermes import HermesAdapter; \
  a=HermesAdapter(); print(f'Hermes: {a.is_available}')"
# 预期输出: Hermes: True (在 Hermes 环境中)

python3 -c "from scripts.adapters.opencode import OpenCodeAdapter; \
  a=OpenCodeAdapter(); print(f'OpenCode: {a.is_available}')"
# 预期输出: OpenCode: True (当 opencode CLI 已安装)
```

---

## 七、质量治理（L0-L4）

`skill-governance` 是项目的质量治理引擎，定义四层质量门禁。
每个能力包在发布前必须通过 L0-L4 扫描。

### L0-L4 治理层级

| 层级 | 名称 | 目标 | 阻塞？ | 检测内容 |
|:-----|:-----|:-----|:------:|:---------|
| **L0** | 兼容性 (Compatibility) | L0 pass | ✅ 是 | 格式合规、frontmatter、兼容性声明 |
| **L1** | 基础 (Foundation) | L1 pass | ✅ 是 | YAML 结构、必填字段、路径可访问 |
| **L2** | 健康 (Health) | L2 pass | ❌ 否 | 原子性检查、依赖树、循环引用 |
| **L3** | 生态 (Ecosystem) | L3 pass | ❌ 否 | 跨包交互、命名空间、分类一致性 |
| **L4** | 工作流 (Workflow) | L4 pass | ❌ 否 | DAG 有效性、技能编排完整性 |

### 治理工具

```bash
# 扫描能力包（L0-L4 全量检查）
python -m skill_governance.cli.main scan packs/doc-engine
# 预期输出: L0 ✅ L1 ✅ L2 ✅ L3 ✅ L4 ✅

# JSON 格式输出（AI 友好）
python -m skill_governance.cli.main scan packs/doc-engine --format json

# 自动修复已知问题
python -m skill_governance.cli.main fix packs/doc-engine
# 预期输出: 已修复 N 个问题

# 启动 MCP Server（供 Agent 调用）
python -m skill_governance.mcp.skill_governance_server
# 预期输出: MCP server started on stdio

# 查看治理规则列表
python -m skill_governance.cli.main rules
# 预期输出: 各层级规则清单
```

### MCP Server 暴露的工具

| 工具 | 说明 |
|:-----|:------|
| `scan_skill(path)` | L0-L4 合规扫描 |
| `suggest_pack(path)` | 推荐匹配的能力包 |
| `apply_adaptation(path, confirm)` | 自动适配到最佳包 |
| `check_compliance(path)` | 详细合规报告 |
| `list_workflow_patterns()` | 可用 DAG 工作流模式 |

**验证治理引擎**：
```bash
python -m skill_governance.cli.main scan packs/doc-engine \
  --format json 2>/dev/null | python3 -c \
  "import sys,json; d=json.load(sys.stdin); \
  print('Layers:', list(d.get('layers',{}).keys()))"
# 预期输出: Layers: ['L0', 'L1', 'L2', 'L3', 'L4']
```

---

## 八、运行测试

```bash
# 全量 141 个测试
python -m pytest scripts/tests/ -q

# 按类别
python -m pytest scripts/tests/test_uca_parser.py -v       # 解析器
python -m pytest scripts/tests/test_uca_verifier.py -v     # 验证器
python -m pytest scripts/tests/test_hermes_adapter.py -v    # Hermes 适配器
python -m pytest scripts/tests/test_opencode_adapter.py -v  # OpenCode 适配器
python -m pytest scripts/tests/test_cli_commands.py -v      # CLI 命令
python -m pytest scripts/tests/test_parity.py -v            # 跨适配器一致性
```

**验证测试覆盖**：
```bash
python -m pytest scripts/tests/ --collect-only -q | tail -5
# 预期输出: 141 tests collected
```

---

## 九、目录结构

```
hermes-cap-pack/
├── README.md               # ← 你现在看的（v2.0 AI 友好版）
├── CHANGELOG.md            # 版本日志
├── constraints.md          # 项目约束
├── pyproject.toml          # Python 包元数据 (v0.9.1)
│
├── docs/                   # 设计文档
│   ├── EPIC-*.md           # Epic 文档
│   ├── SPEC-*.md           # Spec 规范
│   ├── stories/            # Story 文档（22+ 个）
│   ├── ADAPTER_GUIDE.md    # 适配器使用指南
│   ├── QUICKSTART.md       # 新 Agent 5 步初始化流程
│   ├── developer-guide-adapter.md  # 第三方适配器开发指南
│   └── project-state.yaml  # 统一状态机
│
├── schemas/                # 格式规范
│   └── cap-pack-v0.9.1schema.json
│
├── packs/                  # 能力包仓库（17 个）
│   ├── doc-engine/         # 📄 文档生成 (12 skills)
│   ├── quality-assurance/  # ✅ 质量保障
│   ├── learning-workflow/  # 🧠 学习工作流
│   ├── developer-workflow/ # 💻 开发工作流
│   ├── agent-orchestration/# 🤖 Agent 协作
│   ├── creative-design/    # 🎨 创意设计
│   ├── devops-monitor/     # 📊 DevOps 监控
│   ├── financial-analysis/ # 💰 财务分析
│   ├── github-ecosystem/   # 🐙 GitHub 生态
│   ├── learning-engine/    # 🧠 学习引擎
│   ├── media-processing/   # 🎬 媒体处理
│   ├── messaging/          # 💬 消息
│   ├── metacognition/      # 🪞 元认知
│   ├── network-proxy/      # 🌐 网络代理
│   ├── security-audit/     # 🔒 安全审计
│   ├── skill-quality/      # 🛡️ 质量门禁
│   └── social-gaming/      # 🎮 社交游戏
│
├── packages/               # Python 包
│   └── skill-governance/   # 治理引擎
│       └── skill_governance/
│           ├── adapter/    # Hermes/OpenCode/Claude/OpenClaw
│           ├── scanner/    # L0-L4 扫描器
│           ├── fixer/      # 自动修复
│           ├── mcp/        # FastMCP Server
│           └── cli/        # 治理 CLI
│
├── scripts/
│   ├── cli/main.py         # CLI 入口（12+ 命令）
│   ├── cli/commands.py     # 命令实现
│   ├── adapters/           # Agent 适配器（顶层）
│   │   ├── hermes.py
│   │   └── opencode.py
│   ├── uca/                # UCA Core 框架
│   │   ├── protocol.py     # AgentAdapter Protocol
│   │   ├── parser.py       # cap-pack.yaml 解析器
│   │   ├── dependency.py   # 依赖检查
│   │   └── verifier.py     # 安装验证
│   ├── tests/              # 141 个测试
│   └── ... (bump-version, validate-pack, health-check)
│
├── reports/                # HTML 质量报告
└── .github/workflows/      # CI (4 job 并行)
```

**验证目录结构**：
```bash
ls -d packs/*/
# 预期输出: 17 个能力包目录

ls scripts/adapters/
# 预期输出: hermes.py  opencode.py
```

---

## 十、FAQ / 排错指南

| 问题 | 排查步骤 | 恢复命令 |
|:-----|:---------|:---------|
| `cap-pack: command not found` | 未创建 alias，或 Python 环境未激活 | `alias cap-pack='python -m scripts.cli.main'` |
| pip install 失败 | 检查 Python 版本 ≥ 3.11，或使用 conda | `python3 --version && pip install pyyaml>=6.0` |
| 安装后 skill 不生效 | Hermes 需要重启才能识别新 skill | `systemctl --user restart hermes-gateway` |
| 升级后版本不对 | 检查 `installed_packs.json` 是否更新 | `cap-pack list` 确认版本号 |
| 适配器不可用 | 目标 Agent 未安装或路径不对 | 运行 `python3 -c "import HermesAdapter; print(HermesAdapter().is_available)"` |
| 治理扫描失败 | 检查 cap-pack.yaml 格式 | `python -m skill_governance.cli.main scan <path> --format json` |
| MCP Server 启动失败 | 检查 Python 环境和 MCP 依赖 | `pip install mcp` 然后重试 |
| 安装回滚 | 自动回滚或手动恢复快照 | `ls ~/.hermes/.uca-snapshots/` |

**验证章节完整性**：
```bash
python3 scripts/validate-readme.py
# 预期输出: 结果: N/N 通过  🔴 阻塞: 0  |  🟡 警告: 0
```

---

## 十一、相关项目

| 项目 | 关系 |
|:-----|:------|
| [SRA](https://github.com/JackSmith111977/Hermes-Skill-View) | CAP Pack 的运行时推荐搭档 |
| [Hermes Agent](https://hermes-agent.nousresearch.com) | 上层 Agent 框架，能力包的消费者 |
| [OpenCode](https://opencode.ai) | 第三方 Agent，兼容 SKILL.md 标准 |
| [Claude Code](https://claude.ai) | Anthropic 的 Agent 框架 |

---

## 十二、开发指南

### 创建新能力包

```bash
# 1. 创建包目录
mkdir -p packs/my-pack/{SKILLS,EXPERIENCES,MCP,SCRIPTS}

# 2. 创建 cap-pack.yaml
cat > packs/my-pack/cap-pack.yaml << 'EOF'
name: my-pack
version: 1.0.0
type: capability-pack
description: "我的第一个能力包"
skills:
  - id: my-skill
    path: SKILLS/my-skill/SKILL.md
    description: "我的第一个技能"
EOF

# 3. 创建技能文件
mkdir -p packs/my-pack/SKILLS/my-skill
cat > packs/my-pack/SKILLS/my-skill/SKILL.md << 'EOF'
---
name: my-skill
description: "我的第一个技能"
tags:
  - example
---

# My Skill

这是一个示例技能。
EOF

# 4. 验证包格式
python -m scripts.cli.main inspect packs/my-pack
# 预期输出: 包名、版本、skills 列表

# 5. 治理扫描
python -m skill_governance.cli.main scan packs/my-pack
# 预期输出: L0-L4 扫描结果
```

### 开发新适配器

参考 `docs/developer-guide-adapter.md` 和 `docs/ADAPTER_GUIDE.md`：

1. 在 `scripts/adapters/` 下创建适配器文件
2. 实现 `AgentAdapter` Protocol（6 个方法）
3. 注册到 CLI（`scripts/cli/commands.py` + `scripts/cli/main.py`）
4. 编写测试（`scripts/tests/test_xxx_adapter.py`）
5. 验证对等性（`scripts/tests/test_parity.py`）
