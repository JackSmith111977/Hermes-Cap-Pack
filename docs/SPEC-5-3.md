# 🔌 SPEC-5-3: 多 Agent 适配层 — Phase 3

> **spec_id**: `SPEC-5-3`
> **status**: `completed`
> **epic**: `EPIC-005`
> **phase**: `Phase-3`
> **created**: 2026-05-16
> **updated**: 2026-05-16
> **owner**: boku (Emma)
> **优先级**: P1
> **估算**: ~6h（3 Stories）
> **前置**: Phase 0（标准就绪）✅ + Phase 1（引擎 MVP）✅ + Phase 2（Hermes 集成）✅

---

## 〇、需求澄清 (CLARIFY)

### 用户故事

> **As a** 主人
> **I want** Skill 治理引擎的能力通过适配器抽象层暴露给多种 Agent（OpenCode / OpenClaw / Claude Code）以及 MCP 协议
> **So that** 不拘泥于 Hermes 平台，任何 Agent 都能调用治理扫描和自动适配能力

### 范围

| 包含 (In Scope) | 不包含 (Out of Scope) |
|:----------------|:---------------------|
| 适配器抽象基类（Adapter Base Class） | Web UI 仪表盘 |
| OpenCode 适配器（继承基类） | 与其他 Agent 生态的 skill marketplace 集成 |
| MCP Server 暴露治理 + 编排能力 | 自动修改 skill 内容（仅通过 cap-pack.yaml） |
| OpenClaw / Claude Code 适配器 | 公共注册中心 |

---

## 一、技术方案

### 1.1 包结构

```
packages/skill-governance/skill_governance/
├── __init__.py
├── models/                  ← 已有 (Phase 1)
│   ├── result.py
│   └── rules.py
├── scanner/                 ← 已有 (Phase 1)
│   ├── base.py
│   ├── atomicity.py
│   ├── tree_validator.py
│   ├── workflow_detector.py
│   └── compliance.py
├── reporter/                ← 已有 (Phase 1)
│   └── html_reporter.py
├── integration/             ← 已有 (Phase 2)
│   ├── pre_flight_gate.py
│   ├── sra_quality_injector.py
│   └── cron_reporter.py
├── adapter/                 ← 已有 + 扩展
│   ├── __init__.py
│   ├── cap_pack_adapter.py ← 已有 (Phase 2 自动适配)
│   ├── base.py             ← ✨ 新增: 适配器抽象基类
│   ├── hermes_adapter.py   ← 📦 已有: scripts/adapters/hermes.py 迁移+重构
│   ├── opencode_adapter.py ← ✨ 新增: OpenCode 适配器
│   ├── openclaw_adapter.py ← ✨ 新增
│   └── claude_adapter.py   ← ✨ 新增
└── mcp/                     ← ✨ 新增
    ├── __init__.py
    └── skill_governance_server.py ← MCP Server
```

### 1.2 适配器抽象基类

```python
# adapter/base.py

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional

@dataclass
class AdapterConfig:
    """适配器通用配置"""
    agent_type: str          # hermes / opencode / openclaw / claude
    working_dir: str         # 工作目录
    dry_run: bool = True     # 默认 dry-run 模式
    auto_confirm: bool = False  # 自动确认（仅非 dry-run 时生效）

class SkillGovernanceAdapter(ABC):
    """
    治理引擎适配器抽象基类。
    
    所有 Agent 适配器必须实现此接口，确保跨平台一致的治理能力。
    四步流程: scan → suggest → dry_run → apply
    """
    
    def __init__(self, config: AdapterConfig):
        self.config = config
    
    @abstractmethod
    def scan(self, path: str) -> dict:
        """对 skill 运行四层扫描，返回检测结果"""
        ...
    
    @abstractmethod
    def suggest(self, path: str) -> list[dict]:
        """推荐目标包 + 建议的 cap-pack.yaml 修改"""
        ...
    
    @abstractmethod
    def dry_run(self, path: str) -> str:
        """预览修改（不实际写入），返回 diff 文本"""
        ...
    
    @abstractmethod
    def apply(self, path: str) -> bool:
        """执行修改（需确认或 auto_confirm），返回成功/失败"""
        ...
    
    @abstractmethod
    def get_agent_info(self) -> dict:
        """返回 Agent 自身信息（类型/版本/能力）"""
        ...
```

### 1.3 OpenCode 适配器

```python
# adapter/opencode_adapter.py

class OpenCodeAdapter(SkillGovernanceAdapter):
    """
    OpenCode CLI Agent 适配器。
    
    通过 opencode run 命令委托治理扫描任务。
    使用 `opencode run 'scan <path>' --dir <dir>` 模式。
    """
    
    def scan(self, path: str) -> dict:
        # 调用 OpenCode 执行 skill-governance scan
        # 解析 CLI JSON 输出
        ...
    
    def suggest(self, path: str) -> list[dict]:
        # 调用 skill-governance suggest 命令
        ...
```

### 1.4 MCP Server

```python
# mcp/skill_governance_server.py

class SkillGovernanceMCPServer:
    """
    MCP Server 暴露治理引擎能力。
    
    Tools:
      - scan_skill(path) → 四层检测结果
      - suggest_pack(path) → 推荐目标包
      - apply_adaptation(path, confirm) → 执行适配
      - check_compliance(path) → 合规检查
      - list_workflow_patterns() → 编排模式列表
    
    Resources:
      - skill-governance://rules → 规则集
      - skill-governance://standards → 标准文档
      - skill-governance://patterns → 编排模式
    """
    ...
```

### 1.5 重构现有适配器

`scripts/adapters/hermes.py`（26K）和 `scripts/adapters/opencode.py`（12K）重构为继承 `base.py`：

```python
class HermesAdapter(SkillGovernanceAdapter):
    """已有 HermesAdapter，重构为继承基类"""
    ...

class OpenCodeAdapter(SkillGovernanceAdapter):
    """已有 OpenCodeAdapter，重构为继承基类 + 新增 Phase 2 能力"""
    ...
```

### 1.6 CLI 扩展

新增适配器相关子命令：

```bash
skill-governance adapter list            # 列出可用适配器
skill-governance adapter info <type>     # 查看适配器信息
skill-governance adapter scan <type> <path>   # 通过指定适配器扫描
skill-governance adapter apply <type> <path>  # 通过指定适配器执行适配
```

---

## 二、Story 分解

| ID | 标题 | 内容 | 估算 | 产出物 |
|:---|:-----|:-----|:----:|:-------|
| STORY-5-3-1 | **适配器抽象层 + OpenCode 适配器** | 创建 Adapter Base Class，重构已有 hermes.py，新建 opencode_adapter.py | 2h | `adapter/base.py`, `adapter/opencode_adapter.py`, 重构 `scripts/adapters/hermes.py` |
| STORY-5-3-2 | **MCP Server 暴露治理 + 编排能力** | 创建 MCP Server，暴露 scan/suggest/apply tools + rules/patterns resources | 2h | `mcp/skill_governance_server.py` |
| STORY-5-3-3 | **OpenClaw / Claude Code 适配器** | 实现两套适配器，继承 base.py，支持 scan→suggest→dry_run→apply | 2h | `adapter/openclaw_adapter.py`, `adapter/claude_adapter.py` |

---

## 三、验收标准

### STORY-5-3-1
- [x] `adapter/base.py` 定义 `SkillGovernanceAdapter` 抽象基类，包含 scan/suggest/dry_run/apply/get_agent_info 五个抽象方法 <!-- 验证: grep -q "abstractmethod\|@abstractmethod" adapter/base.py -->
- [x] `adapter/opencode_adapter.py` 继承基类并实现全部方法 <!-- 验证: python3 -c "from skill_governance.adapter.opencode_adapter import OpenCodeAdapter; print('OK')" -->
- [x] 已有 `scripts/adapters/hermes.py` 重构为继承 `SkillGovernanceAdapter` <!-- 验证: grep -q "SkillGovernanceAdapter" scripts/adapters/hermes.py -->

### STORY-5-3-2
- [x] MCP Server 至少暴露 3 个 tools（scan/suggest/apply） <!-- 验证: grep -q "def scan_skill\|def suggest_pack\|def apply_adaptation" mcp/skill_governance_server.py -->
- [x] MCP Server 至少暴露 2 个 resources（rules/patterns） <!-- 验证: grep -q "skill-governance://" mcp/skill_governance_server.py -->
- [x] MCP Server 可通过 FastMCP 或 stdio 模式启动 <!-- 验证: python3 -c "from skill_governance.mcp.skill_governance_server import SkillGovernanceMCPServer; print('OK')" -->

### STORY-5-3-3
- [x] `adapter/openclaw_adapter.py` 继承基类并实现全部方法 <!-- 验证: grep -q "SkillGovernanceAdapter" adapter/openclaw_adapter.py -->
- [x] `adapter/claude_adapter.py` 继承基类并实现全部方法 <!-- 验证: grep -q "SkillGovernanceAdapter" adapter/claude_adapter.py -->
- [x] 全部 141 测试通过（+ 新增适配器测试） <!-- 验证: python3 -m pytest scripts/tests/ -q -->

---

## 四、依赖关系

| 依赖 | 类型 | 说明 |
|:-----|:-----|:------|
| Phase 0 标准 | 前置 | ✅ CAP-PACK-STANDARD.md v1.0 |
| Phase 1 引擎 | 前置 | ✅ skill-governance 引擎已实现 |
| Phase 2 自动适配 | 前置 | ✅ cap_pack_adapter.py 已实现 |
| `scripts/adapters/hermes.py` | 重构目标 | 需迁移到 packages 目录并继承基类 |
| `scripts/adapters/opencode.py` | 参考实现 | 为新适配器提供模式参考 |

---

## 五、不做的范围

| 项目 | 理由 |
|:-----|:------|
| ❌ Web UI 仪表盘 | CLI + MCP 已满足需求 |
| ❌ 公共注册中心 | 属于 cap-pack 生态的其他环节 |
| ❌ 自动修改 skill 内容 | 适配只改 cap-pack.yaml 和归类 |
| ❌ LangChain / CrewAI 适配器 | 超出 Phase 3 scope，留待后续 |
