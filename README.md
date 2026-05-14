# hermes-cap-pack

> Agent 能力包标准化格式 + CLI 管理工具  
> 版本：**0.8.0** | 测试：**141 ✅** | 能力包：**6 个** | 覆盖：**32% 模块**

---

## 一、项目身份

| 属性 | 值 |
|:-----|:----|
| **目的** | 将 Hermes Agent 的 351+ 个技能拆分为可移植的「能力包」，跨 Agent 复用 |
| **CLI 入口** | `python -m scripts.cli.main`（或创建 alias `cap-pack`） |
| **Schema** | `schemas/cap-pack-v1.schema.json` |
| **最小 Python** | ≥ 3.11 |
| **唯一依赖** | `pyyaml>=6.0` |
| **仓库** | `https://github.com/JackSmith111977/Hermes-Cap-Pack.git` |
| **作者** | boku (Emma) |

---

## 二、快速安装

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
# → 📭 (无已安装的能力包) [首次安装时]
```

---

## 三、能力包列表

当前 **6 个已提取的能力包**（全部在 `packs/` 目录下）：

| 包名 | 目录 | Skills | 版本 | 状态 |
|:-----|:-----|:------:|:----:|:----:|
| **doc-engine** | `packs/doc-engine/` | 9 | 2.0.0 | ✅ 完整 |
| **quality-assurance** | `packs/quality-assurance/` | 7 | 1.0.0 | ✅ 完整 |
| **learning-workflow** | `packs/learning-workflow/` | 4 | 5.5.0 | ⚠️ 骨架 |
| **developer-workflow** | `packs/developer-workflow/` | 16 | 1.0.0 | ✅ 完整 |
| **agent-orchestration** | `packs/agent-orchestration/` | 8 | 1.0.0 | ✅ 完整 |
| **metacognition** | `packs/metacognition/` | 6 | 1.0.0 | ✅ 完整 |

> **已覆盖：6/19 模块（32%）** — 剩余 13 个模块待提取（learning-engine, creative-design, github, devops 等）

---

## 四、CLI 完整参考

### 4.1 安装能力包

```bash
cap-pack install packs/doc-engine              # 安装到 Hermes（auto 检测）
cap-pack install packs/doc-engine --dry-run     # 预览（不实际执行）
cap-pack install packs/doc-engine --target hermes   # 强制安装到 Hermes
cap-pack install packs/doc-engine --target opencode # 安装到 OpenCode
```

**输出示例**：
```
============================================================
  📦 安装能力包: doc-engine
============================================================
     名称:    doc-engine
     版本:    2.0.0
     Skills:  9
     经验:    11
     MCP:     3
     目标:    auto
     适配器:  HermesAdapter

  ✅ 安装完成！共安装 9 个 skill → HermesAdapter
```

### 4.2 卸载能力包

```bash
cap-pack remove doc-engine                  # 从 Hermes 卸载
cap-pack remove doc-engine --target hermes  # 指定 Agent
cap-pack remove doc-engine --target opencode
```

### 4.3 验证安装

```bash
cap-pack verify doc-engine
cap-pack verify doc-engine --target hermes
cap-pack verify doc-engine --target opencode
```

### 4.4 列表已安装

```bash
cap-pack list
```

### 4.5 检查包内容

```bash
cap-pack inspect packs/doc-engine
```

### 4.6 升级能力包

```bash
cap-pack upgrade doc-engine          # 升级指定包
cap-pack upgrade --all               # 全部升级
cap-pack upgrade doc-engine --dry-run # 预览升级
```

**行为**：
1. 读取 `~/.hermes/installed_packs.json` 当前版本
2. 比较 `packs/<name>/cap-pack.yaml` 新版本
3. 备份后执行安装
4. 验证完整性

### 4.7 搜索可用包

```bash
cap-pack search doc       # 搜索名称/描述包含 "doc"
cap-pack search pdf       
cap-pack search learning
```

**匹配范围**：包名、描述、技能名、技能描述

### 4.8 全局状态概览

```bash
cap-pack status
```

**输出包含**：
- 已提取 Skills 总数
- 已安装能力包列表（名称 + 版本 + 时间）
- 可用但未安装的包
- SQS 质量评分均分

### 4.9 包内 Skill 管理

```bash
# 添加 skill
cap-pack skill add doc-engine ~/.hermes/skills/web-ui-ux-design
cap-pack skill add doc-engine /absolute/path/to/skill

# 移除 skill
cap-pack skill remove doc-engine vision-qc-patterns
cap-pack skill remove doc-engine vision-qc-patterns --dry-run

# 列出 pack 内技能
cap-pack skill list doc-engine

# 更新某 skill
cap-pack skill update doc-engine pdf-layout                    # 从 Hermes 同步
cap-pack skill update doc-engine pdf-layout ~/new-version/     # 从指定路径
```

**版本变更规则**：
- `skill add` → minor bump（1.0.0 → 1.1.0）
- `skill remove` → patch bump（1.0.0 → 1.0.1）
- `skill update` → patch bump

---

## 五、作为 Python 模块使用

```python
from scripts.uca import PackParser
from scripts.adapters.hermes import HermesAdapter
from pathlib import Path

# 解析能力包
parser = PackParser(schema_path=Path("schemas/cap-pack-v1.schema.json"))
pack = parser.parse(Path("packs/doc-engine"))
print(f"📦 {pack.name} v{pack.version} — {len(pack.skills)} skills")

# 安装到 Hermes
adapter = HermesAdapter()
result = adapter.install(pack)
print(f"✅ 安装: {len(result.details['installed_skills'])} skills")

# 卸载
result = adapter.uninstall("doc-engine")

# 验证
result = adapter.verify("doc-engine")

# 更新（升级）
result = adapter.update(pack, "1.0.0")  # 从 1.0.0 升级到 pack.version
```

---

## 六、适配器系统

| 适配器 | 类 | 文件 | 状态 | 目标 Agent |
|:-------|:---|:-----|:----:|:-----------|
| **Hermes** | `HermesAdapter` | `scripts/adapters/hermes.py` | ✅ | Hermes Agent |
| **OpenCode** | `OpenCodeAdapter` | `scripts/adapters/opencode.py` | ✅ | OpenCode CLI |

**所有适配器遵循 UCA Protocol**（`scripts/uca/protocol.py`）：

```
AgentAdapter              # Protocol（抽象基类）
 ├── name                 # 适配器名称
 ├── is_available         # 检测目标 Agent 是否存在
 ├── install(pack)        # 安装能力包
 ├── uninstall(name)      # 卸载
 ├── verify(name)         # 验证安装完整性
 ├── list_installed()     # 列出已安装
 └── update(pack, old_ver) # 升级
```

**创建新适配器**：实现 `AgentAdapter` Protocol 即可，参考 `docs/developer-guide-adapter.md`

---

## 七、能力包格式规范

每个能力包是一个目录，包含：

```
packs/<name>/
├── cap-pack.yaml        # 📋 包清单（必需）
├── SKILLS/              # 📄 技能文件
│   ├── <skill-id>/
│   │   └── SKILL.md
│   └── ...
├── EXPERIENCES/         # 📝 实战经验
│   ├── <exp-id>.md
│   └── ...
├── MCP/                 # 🔌 MCP 配置（可选）
└── SCRIPTS/             # ⚙️ 辅助脚本（可选）
```

**cap-pack.yaml 最小示例**：
```yaml
name: my-pack
version: 1.0.0
type: capability-pack
description: "我的第一个能力包"
skills:
  - id: my-skill
    path: SKILLS/my-skill/SKILL.md
    description: "我的第一个技能"
```

**完整格式规范**：`schemas/cap-pack-format-v1.md`  
**JSON Schema**：`schemas/cap-pack-v1.schema.json`

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

---

## 九、目录结构

```
hermes-cap-pack/
├── README.md               # ← 你现在看的
├── CHANGELOG.md            # 版本日志
├── constraints.md          # 项目约束
├── pyproject.toml          # Python 包元数据 (v0.8.0)
│
├── docs/                   # 设计文档
│   ├── EPIC-*.md           # Epic 文档
│   ├── SPEC-*.md           # Spec 规范
│   ├── stories/            # Story 文档（22 个）
│   ├── project-state.yaml  # 统一状态机
│   └── developer-guide-adapter.md
│
├── schemas/                # 格式规范
│   ├── cap-pack-format-v1.md
│   └── cap-pack-v1.schema.json
│
├── packs/                  # 能力包仓库
│   ├── doc-engine/         # 📄 文档生成 (9 skills)
│   ├── quality-assurance/  # ✅ 质量保障 (7 skills)
│   ├── learning-workflow/  # 🧠 学习工作流 (4 skills)
│   ├── developer-workflow/ # 💻 开发工作流 (16 skills)
│   ├── agent-orchestration/# 🤖 Agent 协作 (8 skills)
│   └── metacognition/      # 🪞 元认知 (6 skills)
│
├── scripts/
│   ├── cli/main.py         # CLI 入口
│   ├── cli/commands.py     # 命令实现（13 个命令）
│   ├── adapters/           # Agent 适配器
│   │   ├── hermes.py
│   │   └── opencode.py
│   ├── uca/                # UCA Core 框架
│   │   ├── protocol.py     # AgentAdapter Protocol
│   │   ├── parser.py       # cap-pack.yaml 解析器
│   │   ├── dependency.py   # 依赖检查
│   │   └── verifier.py     # 安装验证
│   ├── tests/              # 141 个测试
│   └── ... (bump-version, validate-pack, health-check, etc.)
│
├── reports/                # HTML 报告
└── .github/workflows/      # CI (4 job 并行)
```

---

## 十、完整命令速查表

| 命令 | 作用 | 关键参数 |
|:-----|:-----|:---------|
| `install <dir>` | 从目录安装能力包 | `--dry-run`, `--target hermes\|opencode` |
| `remove <name>` | 卸载已安装的包 | `--target` |
| `verify <name>` | 验证安装完整性 | `--target` |
| `list` | 列出已安装包 | `--target` |
| `inspect <dir>` | 查看包内容（不安装） | — |
| `upgrade <name>` | 升级已安装的包 | `--all`, `--dry-run` |
| `status` | 全局状态概览 | — |
| `search <term>` | 搜索可用包 | — |
| `skill add <p> <src>` | 向包添加 skill | — |
| `skill remove <p> <id>` | 从包移除 skill | `--dry-run` |
| `skill list <p>` | 列出包内 skill | — |
| `skill update <p> <id> [src]` | 更新包内 skill | — |

---

## 十一、相关项目

| 项目 | 关系 |
|:-----|:------|
| [SRA (Skill Runtime Advisor)](https://github.com/JackSmith111977/Hermes-Skill-View) | CAP Pack 的运行时推荐搭档。CAP Pack 管理「有什么技能」，SRA 管理「该用什么技能」 |
| [Hermes Agent](https://hermes-agent.nousresearch.com) | 上层 Agent 框架，能力包的消费者 |
