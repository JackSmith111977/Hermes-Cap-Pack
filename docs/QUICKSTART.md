# 🚀 新 Agent 5 步初始化流程 (Quickstart)

> **文档状态**: `v1.0` · **预计耗时**: 10 分钟 · **目标读者**: 首次接入能力包的新 AI Agent  
> **前置条件**: Python ≥ 3.11, Git

---

## 概述

本指南帮助 **新的 AI Agent**（无论你是 Hermes、OpenCode、Claude Code 还是 OpenClaw）在 5 步内完成能力包的安装、验证和使用。

```
第 1 步: 克隆仓库 ────── 获取能力包标准库
第 2 步: 安装依赖 ────── Python 环境准备
第 3 步: 扫描现有包 ──── 了解可用的能力包
第 4 步: 安装目标包 ──── 适配器自动安装
第 5 步: 验证安装 ────── 确认技能生效
```

---

## 第 1 步：克隆仓库

从 GitHub 获取 hermes-cap-pack 仓库：

```bash
# 克隆
git clone https://github.com/JackSmith111977/Hermes-Cap-Pack.git
cd Hermes-Cap-Pack

# 验证克隆成功
ls packs/
# 预期输出: 17 个能力包目录（agent-orchestration, creative-design, ...）
```

**验证**：
```bash
git log --oneline -1
# 预期输出: 最近一次提交记录
```

---

## 第 2 步：安装依赖

```bash
# 安装核心依赖（仅需 pyyaml）
pip install pyyaml>=6.0

# 安装治理引擎包（可选，用于 L0-L4 扫描）
pip install -e packages/skill-governance/

# 验证 Python 版本
python3 --version
# 预期输出: Python 3.11.x 或以上

# 验证依赖
python3 -c "import yaml; print(f'pyyaml: {yaml.__version__}')"
# 预期输出: pyyaml: 6.x
```

**创建 CLI alias**：
```bash
alias cap-pack='python -m skill_governance.cli.main'

# 验证 CLI 可用
cap-pack --help
# 预期输出: cap-pack CLI 帮助信息
```

---

## 第 3 步：扫描现有能力包

### 查看所有可用包

```bash
# 列出所有能力包目录
ls -d packs/*/
# 预期输出: 17 个包目录

# 使用 CLI 搜索特定包
cap-pack search doc
# 预期输出: 📦 doc-engine (2.0.0) — 文档引擎能力包

cap-pack search learning
# 预期输出: 📦 learning-engine, 📦 learning-workflow
```

### 检查包内容（不安装）

```bash
# 查看 doc-engine 包的详细内容
cap-pack inspect packs/doc-engine
# 预期输出:
# 📦 doc-engine (2.0.0)
#   Skills: 12
#   Experiences: 11
#   MCP: 3
#   Skills:
#     📄 pdf-layout — PDF 布局引擎
#     📄 pdf-render — PDF 渲染
#     ...

# 查看状态概览
cap-pack status
# 预期输出: 📊 能力包状态概览（含已安装包数、质量评分等）
```

### 治理扫描（检查包质量）

```bash
# 全量 L0-L4 扫描
python -m skill_governance.cli.main scan packs/doc-engine
# 预期输出:
#   L0 ✅ — Compatibility
#   L1 ✅ — Foundation
#   L2 ✅ — Health
#   L3 ✅ — Ecosystem
#   L4 ✅ — Workflow Orchestration

# JSON 格式输出（AI 友好）
python -m skill_governance.cli.main scan packs/doc-engine --format json
```

---

## 第 4 步：安装目标能力包

### 自动检测安装（推荐）

```bash
# auto 模式：自动检测当前环境（Hermes → OpenCode → ...）
cap-pack install packs/doc-engine
# 预期输出:
# ============================================================
#   📦 安装能力包: doc-engine
# ============================================================
#     名称:    doc-engine
#     版本:    2.0.0
#     Skills:  12
#     经验:    11
#     MCP:     3
#     目标:    auto
#     适配器:  HermesAdapter
#   ✅ 安装完成！共安装 12 个 skill → HermesAdapter
```

### 指定目标 Agent 安装

```bash
# 安装到 Hermes Agent
cap-pack install packs/doc-engine --target hermes

# 安装到 OpenCode CLI
cap-pack install packs/doc-engine --target opencode

# 预览安装（不实际执行）
cap-pack install packs/doc-engine --dry-run
```

### 使用 Python API 安装（编程方式）

```python
from pathlib import Path
from scripts.uca import PackParser
from scripts.adapters.hermes import HermesAdapter

# 解析能力包
parser = PackParser(schema_path=Path("schemas/cap-pack-v0.9.1schema.json"))
pack = parser.parse(Path("packs/doc-engine"))

# 安装
adapter = HermesAdapter()
result = adapter.install(pack)

if result.success:
    print(f"✅ 安装 {len(result.details['installed_skills'])} 个 skill")
else:
    print(f"❌ 失败: {result.errors}")
```

### 同时安装多个包

```bash
# 安装多个感兴趣的能力包
cap-pack install packs/developer-workflow
cap-pack install packs/quality-assurance
cap-pack install packs/security-audit

# 全部升级到最新
cap-pack upgrade --all
```

---

## 第 5 步：验证安装

### 验证已安装的包

```bash
# 列出所有已安装的能力包
cap-pack list
# 预期输出:
#   doc-engine (2.0.0) — 2026-05-16T12:00:00
#   developer-workflow (1.0.0) — 2026-05-16T12:01:00
#   ...

# 验证特定包的安装完整性
cap-pack verify doc-engine
# 预期输出: ✅ 验证通过

# 验证全部状态
cap-pack status
# 预期输出: 📊 能力包状态概览
```

### 确认技能可用

```bash
# 对于 Hermes Agent
ls ~/.hermes/skills/ | head -10
# 预期输出: 已安装的技能目录列表

# 对于 OpenCode CLI
ls ~/.config/opencode/skills/ | head -10
# 预期输出: 已安装的 OpenCode 技能目录列表

# 检查跟踪文件
cat ~/.hermes/installed_packs.json
# 预期输出: JSON 格式的已安装包追踪信息
```

### 运行测试确认

```bash
# 运行全量测试（确保适配器正常工作）
python -m pytest scripts/tests/ -q
# 预期输出: 141 passed

# 运行指定适配器测试
python -m pytest scripts/tests/test_hermes_adapter.py -v
python -m pytest scripts/tests/test_opencode_adapter.py -v
```

---

## 完整初始化脚本

将以上 5 步合并为一个脚本，方便新 Agent 一键初始化：

```bash
#!/usr/bin/env bash
# hermes-cap-pack 新 Agent 初始化脚本
set -e

echo "🚀 初始化 hermes-cap-pack..."

# Step 1: 克隆
if [ ! -d "Hermes-Cap-Pack" ]; then
    git clone https://github.com/JackSmith111977/Hermes-Cap-Pack.git
fi
cd Hermes-Cap-Pack

# Step 2: 依赖
pip install pyyaml>=6.0
pip install -e packages/skill-governance/ 2>/dev/null || true

# Step 3: 扫描
echo "📦 可用能力包:"
ls -d packs/*/ | wc -l | xargs -I{} echo "  {} 个包"

# Step 4: 安装（根据实际需要修改包名）
PACKS_TO_INSTALL=(
    "packs/developer-workflow"
    "packs/quality-assurance"
    "packs/doc-engine"
)
for pack in "${PACKS_TO_INSTALL[@]}"; do
    echo "📦 安装 $pack ..."
    python -m skill_governance.cli.main install "$pack" --dry-run

**查看已安装能力包状态**：
cap-pack status
echo "✅ 初始化完成！"
```

---

## 下一步

| 目标 | 参考文档 |
|:-----|:---------|
| 了解 4 个适配器的详细用法 | `docs/ADAPTER_GUIDE.md` |
| 开发自己的适配器 | `docs/developer-guide-adapter.md` |
| 创建新的能力包 | `README.md` 十二、开发指南 |
| 运行治理扫描 | `README.md` 七、质量治理 |
| 查看项目 Spec | `docs/SPEC-6-3.md` |

---

## 故障排查

| 步骤 | 问题 | 解决方案 |
|:-----|:-----|:---------|
| Step 1 | `git clone` 失败 | 检查网络连接和 GitHub 访问权限 |
| Step 2 | `pip install` 失败 | 检查 Python 版本 ≥ 3.11，或使用 conda venv |
| Step 3 | `cap-pack search` 无结果 | 确认在项目根目录运行，或 `packs/` 目录存在 |
| Step 4 | 安装失败：适配器不可用 | 确认目标 Agent 环境已安装（`is_available` 返回 True） |
| Step 5 | `verify` 不通过 | 检查安装路径和文件权限，参考 `ADAPTER_GUIDE.md` 故障排查 |
| 任何步骤 | 命令找不到 | 执行 `alias cap-pack='python -m skill_governance.cli.main'` |
