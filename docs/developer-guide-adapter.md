# 🔌 第三方适配器开发指南

> **文档状态**: `completed` · **关联 Spec**: SPEC-1-4-adaptation · **版本**: 1.0.0
> **目标读者**: 想为新的 Agent（Cursor / Windsurf / Continue 等）编写适配器的开发者

---

## 一、架构概览

```
能力包 (cap-pack.yaml)
       │
       ▼
┌───────────────────────────────────┐
│         UCA Core                  │
│  ┌───────────────────────────┐    │
│  │ PackParser                │    │  ← 解析 cap-pack.yaml
│  │ DependencyChecker         │    │  ← 检查 Python 包/前置 skill
│  │ PackVerifier              │    │  ← 验证安装完整性
│  └───────────────────────────┘    │
│              │                    │
│              ▼                    │
│  ┌───────────────────────────┐    │
│  │   AgentAdapter Protocol   │    │  ← 你的适配器实现这个接口
│  └───────────────────────────┘    │
│              │                    │
│              ▼                    │
│  ┌───────────────────────────┐    │
│  │  Hermes / OpenCode / ...  │    │  ← 具体 Agent 适配器
│  └───────────────────────────┘    │
└───────────────────────────────────┘
```

### 核心组件

| 组件 | 路径 | 你的适配器需要关心？ |
|:-----|:------|:-------------------|
| `AgentAdapter` Protocol | `scripts/uca/protocol.py` | ✅ **必须实现** |
| `PackParser` | `scripts/uca/parser.py` | ✅ 直接使用 |
| `DependencyChecker` | `scripts/uca/dependency.py` | ⭕ 按需使用 |
| `PackVerifier` | `scripts/uca/verifier.py` | ⭕ 按需使用 |
| `CapPack` 数据类 | `scripts/uca/protocol.py` | ✅ 你的适配器接收此对象 |

---

## 二、AgentAdapter Protocol 详解

你的适配器必须实现以下 6 个方法：

```python
from scripts.uca.protocol import AgentAdapter, CapPack, AdapterResult

class MyAdapter:
    """我的 Agent 适配器"""

    @property
    def name(self) -> str:
        """适配器名称（唯一标识，用于 CLI --target 参数）"""
        return "my-agent"

    @property
    def is_available(self) -> bool:
        """当前环境是否支持此适配器"""
        return shutil.which("my-agent") is not None

    def install(self, pack: CapPack) -> AdapterResult:
        """安装能力包到目标 Agent"""
        ...

    def uninstall(self, pack_name: str) -> AdapterResult:
        """卸载已安装的能力包"""
        ...

    def update(self, pack: CapPack, old_version: str) -> AdapterResult:
        """更新到新版本"""
        ...

    def list_installed(self) -> list[dict]:
        """列出已安装的能力包"""
        ...

    def verify(self, pack_name: str) -> AdapterResult:
        """验证安装是否完整"""
        ...
```

### 参数与返回值

| 方法 | 输入 | 返回值 | 说明 |
|:-----|:-----|:-------|:------|
| `install` | `CapPack` | `AdapterResult` | skills → Agent skills 目录；MCP → Agent 配置；记录跟踪 |
| `uninstall` | `str (pack_name)` | `AdapterResult` | 删除文件 + 恢复备份（如有） |
| `update` | `CapPack + old_version` | `AdapterResult` | 先卸载旧版 → 再安装新版 |
| `list_installed` | 无 | `list[dict]` | 每个 dict 含 name/version/installed_at/skill_count |
| `verify` | `str (pack_name)` | `AdapterResult` | 检查文件存在性 + 配置完整性 |

### CapPack 对象结构

```python
@dataclass
class CapPack:
    name: str                # 能力包名称 (e.g. "doc-engine")
    version: str             # 版本号 (e.g. "2.0.0")
    pack_dir: Path           # 能力包目录路径
    manifest: dict           # 原始 cap-pack.yaml 内容

    skills: list[CapPackSkill]       # 技能列表
    experiences: list[CapPackExperience]  # 经验列表
    mcp_configs: list[CapPackMCP]    # MCP 配置列表
    dependencies: list[str]          # Python 包依赖
    hooks: list[dict]                # 安装钩子
    compatibility: dict              # 兼容性声明 (agent_types等)
```

### AdapterResult 对象结构

```python
@dataclass
class AdapterResult:
    success: bool            # 是否成功
    pack_name: str           # 能力包名称
    action: str              # install / uninstall / update / verify
    details: dict            # 详细数据（如 installed_skills）
    warnings: list[str]      # 警告
    errors: list[str]        # 错误
    backup_path: str         # 备份路径（如果有）
```

---

## 三、实现步骤

### Step 1: 创建适配器文件

```bash
touch scripts/adapters/my_agent.py
```

### Step 2: 实现骨架

```python
from pathlib import Path
from scripts.uca.protocol import CapPack, AdapterResult

TRACK_FILE = Path.home() / ".hermes" / "installed_myagent_packs.json"

class MyAgentAdapter:
    @property
    def name(self) -> str:
        return "my-agent"

    @property
    def is_available(self) -> bool:
        # 检查目标 Agent 是否已安装
        import shutil
        return shutil.which("my-agent-cli") is not None
```

### Step 3: 安装逻辑

典型安装流程：

```python
def install(self, pack: CapPack, dry_run: bool = False) -> AdapterResult:
    result = AdapterResult(success=True, pack_name=pack.name, action="install")

    # ① 解析 PackParser 已经在 CLI 层完成，这里直接使用 pack
    # ② 复制 skill 文件到目标目录
    installed = []
    for skill in pack.skills:
        src = pack.pack_dir / "SKILLS" / skill.id
        dst = TARGET_SKILLS_DIR / skill.id
        if src.exists() and not dry_run:
            shutil.copytree(src, dst)
        installed.append(skill.id)

    # ③ 注入 MCP 配置
    for mcp in pack.mcp_configs:
        # 写入目标 Agent 的 MCP 配置文件
        ...

    # ④ 记录跟踪（用于卸载）
    if not dry_run:
        tracked = self._load_tracked()
        tracked[pack.name] = {"version": pack.version, "skills": installed}
        self._save_tracked(tracked)

    result.details["installed_skills"] = installed
    return result
```

### Step 4: 注册到 CLI

在 `scripts/cli/commands.py` 中：

```python
from scripts.adapters.my_agent import MyAgentAdapter

def _get_adapter(target: str | None = None):
    if target == "my-agent":
        return MyAgentAdapter()
    # ... 已有逻辑
```

在 `scripts/cli/main.py` 的 `--target` choices 中添加 `"my-agent"`。

### Step 5: 编写测试

在 `scripts/tests/` 下创建 `test_my_agent_adapter.py`：

```python
"""Tests for MyAgentAdapter"""
import pytest
from scripts.adapters.my_agent import MyAgentAdapter

class TestMyAgentAdapter:
    def test_name(self):
        assert MyAgentAdapter().name == "my-agent"

    def test_install_dry_run(self):
        adapter = MyAgentAdapter()
        # 使用 tmp_path 模拟环境
        ...
```

### Step 6: 验证对等性

在 `scripts/tests/test_parity.py` 中添加测试：

```python
def test_my_agent_adapter_parity(self, real_pack):
    adapter = MyAgentAdapter()
    assert hasattr(adapter, 'install')
    assert hasattr(adapter, 'verify')
```

---

## 四、完整示例：Cursor 适配器

以下是一个假设的 Cursor 适配器实现，展示完整模式：

```python
"""
CursorAdapter — 将能力包安装到 Cursor IDE

Cursor 使用 .cursor/rules/ 目录存放 AI 规则文件。
"""

import json, shutil
from pathlib import Path

from scripts.uca.protocol import CapPack, AdapterResult

CURSOR_RULES = Path.home() / ".cursor" / "rules"
TRACK_FILE = Path.home() / ".hermes" / "installed_cursor_packs.json"


class CursorAdapter:
    @property
    def name(self) -> str:
        return "cursor"

    @property
    def is_available(self) -> bool:
        # Cursor 没有 CLI，检查配置目录是否存在
        return Path.home().joinpath(".cursor", "rules").parent.exists()

    def install(self, pack: CapPack, dry_run: bool = False) -> AdapterResult:
        result = AdapterResult(success=True, pack_name=pack.name, action="install")
        installed = []

        for skill in pack.skills:
            src = pack.pack_dir / "SKILLS" / skill.id / "SKILL.md"
            dst = CURSOR_RULES / f"{skill.id}.md"

            if not src.exists():
                continue

            if not dry_run:
                dst.parent.mkdir(parents=True, exist_ok=True)
                # Cursor 使用 Markdown 格式，规则文件可直接复制
                shutil.copy2(src, dst)

            installed.append(skill.id)

        result.details["installed_skills"] = installed

        if not dry_run:
            tracked = self._load_tracked()
            tracked[pack.name] = {
                "version": pack.version,
                "skills": installed,
                "installed_at": __import__("datetime").datetime.now().isoformat()[:19],
            }
            self._save_tracked(tracked)

        return result

    def uninstall(self, pack_name: str) -> AdapterResult:
        result = AdapterResult(success=True, pack_name=pack_name, action="uninstall")
        tracked = self._load_tracked()

        if pack_name not in tracked:
            result.success = False
            result.errors.append(f"'{pack_name}' 未安装")
            return result

        for sid in tracked[pack_name].get("skills", []):
            rule_file = CURSOR_RULES / f"{sid}.md"
            if rule_file.exists():
                rule_file.unlink()

        del tracked[pack_name]
        self._save_tracked(tracked)
        return result

    # --- 其余方法按相同模式实现 ---
    def update(self, pack: CapPack, old_version: str) -> AdapterResult: ...
    def list_installed(self) -> list[dict]: ...
    def verify(self, pack_name: str) -> AdapterResult: ...

    # --- 跟踪文件工具 ---
    def _load_tracked(self) -> dict:
        if TRACK_FILE.exists():
            return json.loads(TRACK_FILE.read_text())
        return {}

    def _save_tracked(self, tracked: dict):
        TRACK_FILE.parent.mkdir(parents=True, exist_ok=True)
        TRACK_FILE.write_text(json.dumps(tracked, indent=2, ensure_ascii=False) + "\n")
```

---

## 五、已知 Agent 的目标路径速查

| Agent | Skills 路径 | MCP 配置路径 | 安装方式 |
|:------|:-----------|:-------------|:---------|
| **Hermes** | `~/.hermes/skills/{id}/SKILL.md` | `~/.hermes/config.yaml mcp_servers` | 文件复制 + YAML 修改 |
| **OpenCode** | `~/.config/opencode/skills/{id}/SKILL.md` | `~/.config/opencode/opencode.json mcp` | SKILL.md 转换 + JSON 修改 |
| **Claude Code** | `~/.claude/skills/{id}/SKILL.md` | `~/.claude/claude.json mcpServers` | 文件复制 + JSON 修改 |
| **Codex CLI** | `~/.codex/skills/{id}/SKILL.md` | `~/.codex/config.toml` | 文件复制 + TOML 修改 |
| **Cursor** | `.cursor/rules/{id}.md` | `.cursor/mcp.json` | Markdown 规则文件 |
| **Windsurf** | `.windsurf/rules/{id}.md` | `.windsurf/global_rules.json` | 规则文件复制 |

> 💡 如果目标 Agent 的路径不在此表中，请参考其官方文档。

---

## 六、最佳实践

### 1. 利用 `~/.claude/skills/` 兼容性

多个 Agent（OpenCode、Continue 等）原生支持 `~/.claude/skills/` 格式。
如果目标 Agent 也支持，最简单的适配器就是直接安装到 `~/.claude/skills/`：

```python
# 如果目标 Agent 兼容 Claude Code 格式...
dst = Path.home() / ".claude" / "skills" / skill.id
shutil.copytree(src, dst)
```

### 2. 跟踪文件命名约定

```python
TRACK_FILE = Path.home() / ".hermes" / "installed_{name}_packs.json"
# 例如: installed_cursor_packs.json, installed_windsurf_packs.json
```

### 3. 统一使用 UCA Core

不要重新实现 YAML 解析或依赖检查。直接使用：

```python
from scripts.uca import PackParser, DependencyChecker, PackVerifier

parser = PackParser()
pack = parser.parse(pack_dir)

checker = DependencyChecker()
dep_result = checker.check(pack)
```

### 4. CLI 适配器注册三步

```
① scripts/adapters/my_agent.py      → 实现适配器类
② scripts/cli/commands.py           → _get_adapter() 添加分支
③ scripts/cli/main.py               → --target choices 添加选项
```

---

## 七、测试指南

### 基本测试结构

```python
import pytest
from pathlib import Path
from scripts.adapters.my_agent import MyAgentAdapter

@pytest.fixture
def adapter():
    return MyAgentAdapter()

class TestMyAdapter:
    def test_name(self, adapter):
        assert adapter.name == "my-agent"

    def test_install_with_mock_env(self, adapter, tmp_path):
        """在临时目录中模拟安装"""
        # 创建模拟的能力包
        pack_dir = tmp_path / "test-pack"
        pack_dir.mkdir()
        (pack_dir / "SKILLS" / "test-skill").mkdir(parents=True)
        (pack_dir / "SKILLS" / "test-skill" / "SKILL.md").write_text("# Test")

        # 创建模拟的 CapPack
        from scripts.uca.protocol import CapPack, CapPackSkill
        pack = CapPack(
            name="test-pack",
            version="1.0.0",
            pack_dir=pack_dir,
            manifest={},
            skills=[CapPackSkill(id="test-skill", path="SKILLS/test-skill/SKILL.md")],
        )

        # 模拟目标目录
        import scripts.adapters.my_agent as mod
        mod.TARGET_DIR = tmp_path / "target"

        result = adapter.install(pack)
        assert result.success is True
```

### 对等性测试

在 `scripts/tests/test_parity.py` 中添加：

```python
def test_my_adapter_parity(self, real_pack):
    """验证与已有适配器的行为一致性"""
    adapter = MyAgentAdapter()
    assert hasattr(adapter, 'name')
    assert hasattr(adapter, 'install')
    assert hasattr(adapter, 'uninstall')
    assert hasattr(adapter, 'verify')
    assert hasattr(adapter, 'list_installed')

def test_my_adapter_parity_skill_count(self, real_pack):
    """解析的技能数应与 Hermes/OpenCode 一致"""
    assert len(real_pack.skills) > 0
```

---

## 八、Adapter 设计决策模板

开发新适配器时，先回答以下问题：

| 问题 | 你的答案 |
|:-----|:---------|
| Agent 名称是什么？ | |
| Skills 放哪里？ | |
| MCP 怎么配置？ | |
| 有原生 skill 机制吗？ | |
| 有 CLI 可以检测是否安装？ | |
| 需要转换 SKILL.md 格式吗？ | |
| 支持卸载/回滚吗？ | |
| 配置文件格式是什么？ (YAML/JSON/TOML) | |

---

## 九、完整适配器清单（项目当前状态）

| ID | 适配器 | 状态 | 实现文件 |
|:---|:-------|:----:|:---------|
| `hermes` | Hermes Agent | ✅ | `scripts/adapters/hermes.py` |
| `opencode` | OpenCode CLI | ✅ | `scripts/adapters/opencode.py` |
| `claude-code` | Claude Code | 🟡 由 OpenCode 兼容覆盖 | 直接写 `~/.claude/skills/` |
| `codex-cli` | Codex CLI | 🟡 由 OpenCode 兼容覆盖 | 直接写 `~/.codex/skills/` |
| `cursor` | Cursor IDE | ⏳ 待实现 | 参考 §4 示例 |
| `windsurf` | Windsurf | ⏳ 待实现 | |
| `continue` | Continue | ⏳ 待实现 | |

---

## 十、参考文献

- [SPEC-1-4: 跨 Agent 适配层方案](../SPEC-1-4.md) — 完整设计文档
- [AgentAdapter Protocol](../uca/protocol.py) — Protocol 接口定义
- [HermesAdapter 实现](../adapters/hermes.py) — 参考实现
- [OpenCodeAdapter 实现](../adapters/opencode.py) — 参考实现
- [OpenCode Agent Skills 文档](https://opencode.ai/docs/skills/) — 第三方 Agent 技能标准
