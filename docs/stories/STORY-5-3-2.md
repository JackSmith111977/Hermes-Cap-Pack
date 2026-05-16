# Story: MCP Server 治理能力暴露

> **story_id**: `STORY-5-3-2`
> **status**: `completed`
> **priority**: P1
> **epic**: EPIC-005
> **spec_ref**: SPEC-5-3
> **phase**: Phase-3
> **created**: 2026-05-16
> **owner**: boku (Emma)

---

## 用户故事

**As a** 任意 MCP 兼容的 Agent
**I want** 通过 MCP 协议调用治理引擎的扫描、适配和编排能力
**So that** 不依赖特定 Agent 平台，通过标准化 MCP 接口使用治理能力

## 技术方案

### 文件清单

| 操作 | 文件 | 说明 |
|:-----|:-----|:------|
| ✨ 新建 | `packages/skill-governance/skill_governance/mcp/__init__.py` | 包入口 |
| ✨ 新建 | `packages/skill-governance/skill_governance/mcp/skill_governance_server.py` | MCP Server |

### MCP Tools

| Tool | 功能 | 输出 |
|:-----|:------|:------|
| `scan_skill(path)` | 四层检测 | 检测报告 JSON |
| `suggest_pack(path)` | 推荐目标包 | 建议列表 [{pack, confidence, reason}] |
| `apply_adaptation(path, confirm)` | 执行适配 | 成功/失败 + diff |
| `check_compliance(path)` | 合规检查 | pass/fail + 违规列表 |
| `list_workflow_patterns()` | 编排模式列表 | [{name, type, description}] |

### MCP Resources

| URI | 说明 |
|:----|:------|
| `skill-governance://rules` | 规则集 (33 rules, 5 layers) |
| `skill-governance://standards` | 标准文档链接 |
| `skill-governance://patterns` | 编排模式定义 |

### 启动方式

```python
from skill_governance.mcp.skill_governance_server import SkillGovernanceMCPServer

# 方式 1: FastMCP 自动
server = SkillGovernanceMCPServer()
server.run()

# 方式 2: CLI 入口
# python3 -m skill_governance.mcp.skill_governance_server
```

## 验收标准

- [x] 至少暴露 5 个 MCP tools（scan/suggest/apply/check/list） <!-- 验证: grep -c "def scan_skill\|def suggest_pack\|def apply_adaptation\|def check_compliance\|def list_workflow_patterns" packages/skill-governance/skill_governance/mcp/skill_governance_server.py -->
- [x] 至少暴露 3 个 MCP resources（rules/standards/patterns） <!-- 验证: grep -c "skill-governance://" packages/skill-governance/skill_governance/mcp/skill_governance_server.py -->
- [x] 可通过 `python3 -m skill_governance.mcp.skill_governance_server` 启动 <!-- 验证: timeout 3 python3 -m skill_governance.mcp.skill_governance_server 2>&1 || true -->
- [x] 全部 141 测试通过 <!-- 验证: python3 -m pytest scripts/tests/ -q -->

## 边界与不做的范围

- ❌ 不涉及适配器重构（STORY-5-3-1）
- ❌ 不涉及 OpenClaw / Claude Code（STORY-5-3-3）
- ❌ 不提供 Web UI
