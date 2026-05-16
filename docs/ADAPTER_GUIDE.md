# 🔌 适配器使用指南 (Adapter Guide)

> **文档状态**: `v2.0` · **覆盖适配器**: 4 个 · **关联**: `SPEC-6-3`, `developer-guide-adapter.md`  
> **目标读者**: 需要在不同 Agent 环境安装/管理能力包的开发者和 AI Agent

---

## 一、适配器体系概览

hermes-cap-pack 提供 **4 个适配器**，将标准化的能力包安装到不同的 AI Agent 环境。每个适配器实现统一的 `AgentAdapter` Protocol 或 `SkillGovernanceAdapter` ABC，屏蔽底层 Agent 的格式差异。

| 适配器 | 类名 | 位置 | 安装模式 |
|:-------|:-----|:-----|:---------|
| **HermesAdapter** | `HermesAdapter` | `scripts/adapters/hermes.py` | 文件复制 + YAML 配置注入 |
| **OpenCodeAdapter** | `OpenCodeAdapter` | `scripts/adapters/opencode.py` + `packages/.../adapter/opencode_adapter.py` | SKILL.md 格式转换 + JSON 配置 |
| **OpenClawAdapter** | `OpenClawAdapter` | `packages/.../adapter/openclaw_adapter.py` | 直接导入扫描模块 |
| **ClaudeAdapter** | `ClaudeAdapter` | `packages/.../adapter/claude_adapter.py` | 子进程委派模式 |

### UCA → 治理适配器演进

```
v1 (UCA Protocol)                      v2 (SkillGovernanceAdapter)
─────────────────                      ────────────────────────────
scripts/uca/protocol.py                packages/skill-governance/
  AgentAdapter (Protocol)                adapter/base.py
  ├── install(pack)                       SkillGovernanceAdapter (ABC)
  ├── uninstall(name)                     ├── scan(path)
  ├── verify(name)                        ├── suggest(path)
  ├── list_installed()                    ├── dry_run(path)
  └── update(pack, old_ver)               ├── apply(path)
                                          └── get_agent_info()
```

> **兼容性**：两个接口体系并存。`HermesAdapter` 和顶层 `OpenCodeAdapter` 实现 UCA Protocol；`packages/` 下的适配器实现 `SkillGovernanceAdapter` ABC。

---

## 二、HermesAdapter — Hermes Agent

### 使用场景

- **主要场景**：在 Hermes Agent 环境中安装能力包
- **默认模式**：`auto` 检测优先使用 HermesAdapter
- **安装路径**：`~/.hermes/skills/{skill-id}/`
- **MCP 注入**：`~/.hermes/config.yaml` 的 `mcp_servers` 字段

### 配置

```python
from scripts.adapters.hermes import HermesAdapter

# 默认配置（dry_run=True）
adapter = HermesAdapter()

# 自定义配置
from skill_governance.adapter.base import AdapterConfig
adapter = HermesAdapter(
    config=AdapterConfig(
        agent_type="hermes",
        dry_run=False,
        auto_confirm=True,
    )
)
```

### CLI 使用

```bash
# 安装（auto 检测 → Hermes）
cap-pack install packs/doc-engine

# 指定目标
cap-pack install packs/doc-engine --target hermes

# 预览安装
cap-pack install packs/doc-engine --dry-run

# 卸载
cap-pack remove doc-engine --target hermes

# 验证
cap-pack verify doc-engine --target hermes
```

### Python 示例

```python
from pathlib import Path
from scripts.uca import PackParser
from scripts.adapters.hermes import HermesAdapter

# 解析能力包
parser = PackParser(schema_path=Path("schemas/cap-pack-v0.9.1schema.json"))
pack = parser.parse(Path("packs/doc-engine"))
print(f"📦 {pack.name} v{pack.version} — {len(pack.skills)} skills")

# 安装到 Hermes
adapter = HermesAdapter()
result = adapter.install(pack)
if result.success:
    print(f"✅ 安装完成: {len(result.details['installed_skills'])} skills")
    if result.details.get('mcp_injected', 0) > 0:
        print(f"🔌 注入 {result.details['mcp_injected']} 个 MCP 配置")
else:
    print(f"❌ 安装失败: {result.errors}")
```

### 安装流程详解

```
HermesAdapter.install(pack)
 ├── Step 0: 依赖检查（缺失依赖仅警告）
 ├── Step 1: 创建快照（失败时自动回滚）
 ├── Step 2: 安装 skills → ~/.hermes/skills/{id}/
 ├── Step 3: 安装 scripts → ~/.hermes/scripts/
 ├── Step 4: 复制 references
 ├── Step 5: 注入 MCP 配置 → config.yaml
 ├── Step 6: 执行 post_install 脚本
 ├── Step 7: 验证门禁（失败 → 自动回滚）
 ├── Step 8: 记录跟踪到 installed_packs.json
 └── Step 9: 成功 → 清理快照
```

### 故障排查

| 问题 | 可能原因 | 解决方案 |
|:-----|:---------|:---------|
| `Hermes 环境不可用` | 未在 Hermes 环境中 | 检查 `~/.hermes/config.yaml` 是否存在 |
| `验证门禁未通过` | skill 文件损坏或不完整 | 查看日志中具体的 failure 条目 |
| MCP 配置未生效 | config.yaml 格式问题 | 检查 `~/.hermes/config.yaml` 中 `mcp_servers` 格式 |
| `安装异常` | 文件权限不足 | 检查 `~/.hermes/skills/` 目录权限 |

### 验证

```bash
python3 -c "from scripts.adapters.hermes import HermesAdapter; a=HermesAdapter(); print(f'可用: {a.is_available}, 名称: {a.name}')"
# 预期输出: 可用: True, 名称: hermes
```

---

## 三、OpenCodeAdapter — OpenCode CLI Agent

### 使用场景

- **主要场景**：将能力包安装到 OpenCode CLI Agent
- **安装路径**：`~/.config/opencode/skills/{skill-id}/`
- **MCP 注入**：`~/.config/opencode/opencode.json` 的 `mcp` 字段
- **格式转换**：自动将 Hermes 格式的 SKILL.md 转换为 OpenCode 兼容格式

### 配置

```python
from scripts.adapters.opencode import OpenCodeAdapter

# 默认配置
adapter = OpenCodeAdapter()

# Python 调用安装
pack_dir = Path("packs/doc-engine")
from scripts.uca import PackParser
parser = PackParser(schema_path=Path("schemas/cap-pack-v0.9.1schema.json"))
pack = parser.parse(pack_dir)
result = adapter.install(pack)
```

### CLI 使用

```bash
# 安装到 OpenCode
cap-pack install packs/doc-engine --target opencode

# 预览
cap-pack install packs/doc-engine --dry-run --target opencode

# 卸载
cap-pack remove doc-engine --target opencode

# 验证
cap-pack verify doc-engine --target opencode

# 列出 OpenCode 已安装的包
cap-pack list --target opencode
```

### 治理适配器 (packages 版)

OpenCode 在 `packages/skill-governance/` 下还有第二个实现，继承 `SkillGovernanceAdapter`：

```python
from skill_governance.adapter.opencode_adapter import OpenCodeAdapter

adapter = OpenCodeAdapter()

# L0-L4 合规扫描
report = adapter.scan("packs/doc-engine")
print(f"L0 通过: {report.get('layers', {}).get('L0', {}).get('passed')}")

# 推荐匹配包
suggestions = adapter.suggest("path/to/skill-dir")
for s in suggestions:
    print(f"推荐: {s['pack_name']} (匹配度: {s['score']})")

# 预览安装
print(adapter.dry_run("path/to/skill-dir"))

# 安装
success = adapter.apply("path/to/skill-dir")
```

### 格式转换说明

OpenCodeAdapter 在安装时自动执行格式转换：

```python
# 原始 Hermes 格式 SKILL.md
# ---
# name: my-skill
# description: "原始描述"
# tags: [a, b]
# version: 1.0.0
# ---

# 转换后 OpenCode 格式 SKILL.md
# ---
# name: my-skill
# description: "原始描述"
# license: MIT
# compatibility: opencode
# metadata:
#   source: hermes-cap-pack
#   original_name: my-skill
# ---
```

### 故障排查

| 问题 | 可能原因 | 解决方案 |
|:-----|:---------|:---------|
| `OpenCode CLI 未安装` | opencode 不在 PATH 中 | 安装 OpenCode CLI |
| Skill 未被 OpenCode 识别 | 格式转换后 frontmatter 不兼容 | 运行 `opencode debug skill` 检查 |
| MCP 配置未生效 | `opencode.json` 格式错误 | 检查 `~/.config/opencode/opencode.json` |
| 安装后找不到 skill | OpenCode 需要重启 | 重启 OpenCode 终端会话 |

### 验证

```bash
python3 -c "from scripts.adapters.opencode import OpenCodeAdapter; a=OpenCodeAdapter(); print(f'可用: {a.is_available}, 名称: {a.name}')"
# 预期输出: 可用: True/False, 名称: opencode
```

---

## 四、OpenClawAdapter — OpenClaw Agent

### 使用场景

- **主要场景**：在 OpenClaw Agent 环境中进行 L0-L4 合规扫描和技能适配
- **安装模式**：直接导入治理引擎模块（无子进程开销）
- **核心能力**：scan（直接调用 ComplianceChecker、AtomicityScanner、TreeValidator、WorkflowDetector）

### 配置

```python
from skill_governance.adapter.openclaw_adapter import OpenClawAdapter
from skill_governance.adapter.base import AdapterConfig

# 默认配置（dry_run=True）
adapter = OpenClawAdapter()

# 自定义配置
adapter = OpenClawAdapter(
    config=AdapterConfig(
        agent_type="openclaw",
        dry_run=False,
        auto_confirm=True,
    )
)
```

### 使用示例

```python
from skill_governance.adapter.openclaw_adapter import OpenClawAdapter

adapter = OpenClawAdapter()

# 1. L0-L4 合规扫描
report = adapter.scan("packs/doc-engine")
print("扫描报告:")
for layer_id in ["L0", "L1", "L2", "L3", "L4"]:
    layer = report.get("layers", {}).get(layer_id, {})
    print(f"  {layer_id}: {layer.get('layer_name', '?')} — passed={layer.get('passed', '?')}")

# 2. 推荐匹配包
suggestions = adapter.suggest("packs/doc-engine/SKILLS/pdf-layout")
for s in suggestions[:3]:
    print(f"  📦 {s['pack_name']} (得分: {s['score']})")

# 3. 预览适应操作
preview = adapter.dry_run("packs/doc-engine/SKILLS/pdf-layout")
print(f"预览:\n{preview}")

# 4. 执行适应
success = adapter.apply("packs/doc-engine/SKILLS/pdf-layout")
print(f"适应结果: {'✅ 成功' if success else '❌ 失败'}")
```

### 扫描架构

```
OpenClawAdapter.scan(path)
 ├── _load_skills(pack_path)          ← 从 cap-pack.yaml 加载技能列表
 ├── _load_workflows_and_clusters()    ← 加载工作流和簇定义
 │
 ├── Layer 0 (Compatibility)
 │   └── ComplianceChecker(layer_id="L0").scan()
 ├── Layer 1 (Foundation)
 │   └── ComplianceChecker(layer_id="L1").scan()
 ├── Layer 2 (Health)
 │   ├── AtomicityScanner().scan()
 │   └── TreeValidator().scan()
 ├── Layer 3 (Ecosystem)
 │   └── ComplianceChecker(layer_id="L3").scan()
 └── Layer 4 (Workflow)
     └── WorkflowDetector().scan()
```

### 故障排查

| 问题 | 可能原因 | 解决方案 |
|:-----|:---------|:---------|
| `Path does not exist` | 路径无效 | 确认路径指向 pack 或 skill 目录 |
| 扫描返回空报告 | `cap-pack.yaml` 格式问题 | 检查 YAML 语法和必填字段 |
| suggest 返回空列表 | 标签不匹配 | 检查 skill 前言的 tags 字段 |
| apply 失败 | skill 目录缺少 SKILL.md | 确认路径包含 SKILL.md 文件 |

### 验证

```bash
python3 -c "
from skill_governance.adapter.openclaw_adapter import OpenClawAdapter
a = OpenClawAdapter()
info = a.get_agent_info()
print(f'Agent: {info[\"agent_type\"]}')
print(f'可用: {a.scan(\"packs/doc-engine\")[\"layers\"][\"L0\"][\"passed\"] if \"layers\" in a.scan(\"packs/doc-engine\") else \"N/A\"}')
"
# 预期输出: Agent: openclaw, L0 层扫描结果
```

---

## 五、ClaudeAdapter — Claude Code Agent

### 使用场景

- **主要场景**：在 Claude Code 环境中通过子进程委派进行治理操作
- **安装模式**：通过 `subprocess` 调用 Python 代码，适用于隔离环境
- **适用场景**：Claude Code 环境有 Python 包但无法直接导入

### 配置

```python
from skill_governance.adapter.claude_adapter import ClaudeAdapter
from skill_governance.adapter.base import AdapterConfig

# 默认配置（dry_run=True）
adapter = ClaudeAdapter()

# 生产配置（dry_run=False）
adapter = ClaudeAdapter(
    config=AdapterConfig(
        agent_type="claude",
        dry_run=False,
        auto_confirm=True,
    )
)
```

### 使用示例

```python
from skill_governance.adapter.claude_adapter import ClaudeAdapter

adapter = ClaudeAdapter()

# 1. L0-L4 合规扫描（子进程委派）
report = adapter.scan("packs/doc-engine")
print(f"扫描完成: {len(report.get('layers', {}))} 层")

# 2. 推荐匹配包
suggestions = adapter.suggest("packs/doc-engine/SKILLS/pdf-layout")
for s in suggestions[:3]:
    print(f"  推荐: {s['pack_name']} (得分: {s['score']:.2f})")

# 3. 预览
print(adapter.dry_run("packs/doc-engine/SKILLS/pdf-layout"))

# 4. 应用（注意：dry_run=True 时仅预览）
success = adapter.apply("packs/doc-engine/SKILLS/pdf-layout")
print(f"应用结果: {'✅' if success else '❌'}")

# 5. 获取环境信息
info = adapter.get_agent_info()
print(f"Agent: {info['agent_type']}, 版本: {info['version']}")
```

### 子进程委派模式

ClaudeAdapter 通过 `subprocess` 在子进程中执行操作，不直接导入扫描模块：

```python
# 实际执行扫描的子进程调用
# python3 -m skill_governance.cli.main scan <path> --format json

# 实际执行 suggest 的子进程调用
# python3 -c "
#   from skill_governance.adapter.cap_pack_adapter import CapPackAdapter;
#   adapter = CapPackAdapter();
#   result = adapter.suggest('<path>');
#   print(json.dumps([...]))
# "
```

这种设计的目的：
- **环境隔离**：适配器进程与被治理环境解耦
- **错误隔离**：子进程崩溃不影响主进程
- **版本兼容**：可以运行不同版本的治理引擎

### 故障排查

| 问题 | 可能原因 | 解决方案 |
|:-----|:---------|:---------|
| `Governance scan timed out` | 能力包过大或扫描耗时过长 | 增加 `timeout` 参数或分片扫描 |
| `Governance scan failed` | CLI 不可用或语法错误 | 检查 `skill-governance` 包是否安装 |
| `Failed to parse scan output` | JSON 输出格式异常 | 运行 `python -m skill_governance.cli.main scan <path> --format json` 手动检查 |
| suggest 返回空 | 子进程调用失败 | 检查 Python 环境和路径配置 |
| `dry_run` 返回 Error | 路径不存在 | 确认 skill 目录包含 `SKILL.md` |

### 验证

```bash
python3 -c "
from skill_governance.adapter.claude_adapter import ClaudeAdapter
a = ClaudeAdapter()
info = a.get_agent_info()
print(f'Agent: {info[\"agent_type\"]}, 版本: {info[\"version\"]}')
scan_result = a.scan('packs/doc-engine')
if 'error' not in scan_result:
    print(f'L0 扫描: ✅')
else:
    print(f'L0 扫描: ❌ {scan_result[\"error\"]}')
"
# 预期输出: Agent: claude, L0 扫描结果
```

---

## 六、创建新适配器

参考 `docs/developer-guide-adapter.md` 的完整指南。快速步骤：

```bash
# 1. 创建适配器文件
touch scripts/adapters/my_agent.py

# 2. 实现 AgentAdapter Protocol
#    参考 scripts/uca/protocol.py 中的 6 个方法

# 3. 注册到 CLI
#    scripts/cli/commands.py → _get_adapter() 添加分支
#    scripts/cli/main.py → --target choices 添加选项

# 4. 编写测试
#    scripts/tests/test_my_agent_adapter.py

# 5. 验证对等性
#    scripts/tests/test_parity.py
```

### 适配器设计检查清单

| 问题 | 说明 |
|:-----|:------|
| Agent 名称是什么？ | 唯一标识，用于 `--target` 参数 |
| Skills 存放路径？ | 目标 Agent 的 skill 目录 |
| MCP 如何配置？ | 配置文件格式 + 字段名 |
| 需要格式转换？ | SKILL.md 是否需要适配目标 Agent 格式 |
| 有 CLI 可检测？ | `shutil.which()` 或路径检查 |
| 支持回滚？ | 安装前是否需要快照 |

---

## 七、速查：所有 CLI 命令

| 命令 | 用途 | scan/fix 相关 |
|:-----|:-----|:--------------|
| `cap-pack install <dir>` | 安装能力包 | — |
| `cap-pack remove <name>` | 卸载能力包 | — |
| `cap-pack verify <name>` | 验证安装 | — |
| `cap-pack list` | 列出已安装 | — |
| `cap-pack inspect <dir>` | 检查包内容 | — |
| `cap-pack upgrade <name>` | 升级能力包 | — |
| `cap-pack status` | 全局状态 | — |
| `cap-pack search <term>` | 搜索能力包 | — |
| `skill-governance scan <path>` | L0-L4 合规扫描 | ✅ scan |
| `skill-governance fix <path>` | 自动修复问题 | ✅ fix |
| `skill-governance watcher` | 启动监控守护 | ✅ watcher |
| `skill-governance rules` | 查看治理规则 | ✅ rules |

---

## 八、最佳实践

1. **始终先 dry-run**：安装前使用 `--dry-run` 预览变更
2. **确认适配器可用性**：用 `is_available` 检查目标环境
3. **利用 MCP Server**：Agent 可通过 `scan_skill` / `suggest_pack` 工具自动发现能力包
4. **L0-L4 扫描常态化**：每次更新能力包后运行治理扫描
5. **跟踪文件备份**：`~/.hermes/installed_packs.json` 是核心状态文件，建议纳入版本管理
6. **新适配器先看协议**：实现前仔细阅读 `scripts/uca/protocol.py` 和 `packages/.../adapter/base.py`
