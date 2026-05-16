# Story: OpenClaw / Claude Code 适配器

> **story_id**: `STORY-5-3-3`
> **status**: `completed`
> **priority**: P1
> **epic**: EPIC-005
> **spec_ref**: SPEC-5-3
> **phase**: Phase-3
> **created**: 2026-05-16
> **owner**: boku (Emma)

---

## 用户故事

**As a** OpenClaw / Claude Code 用户
**I want** 通过专用适配器调用治理引擎的扫描和适配能力
**So that** 在使用这些 Agent 时也能享受 cap-pack 质量治理

## 技术方案

### 文件清单

| 操作 | 文件 | 说明 |
|:-----|:-----|:------|
| ✨ 新建 | `packages/skill-governance/skill_governance/adapter/openclaw_adapter.py` | OpenClaw 适配器 |
| ✨ 新建 | `packages/skill-governance/skill_governance/adapter/claude_adapter.py` | Claude Code 适配器 |

### OpenClaw 适配器

```python
class OpenClawAdapter(SkillGovernanceAdapter):
    """
    OpenClaw Agent 适配器。
    
    OpenClaw 是开源 CLI Agent，通过子进程调用治理引擎。
    适配策略：
    1. scan: 直接调用 CLI（共享 Python 环境）
    2. suggest: 调用 suggest 子命令
    3. dry_run/apply: 通过 cap_pack_adapter 执行
    """
    def scan(self, path: str) -> dict:
        # 直接 import skill_governance scanner
        from skill_governance.scanner.compliance import ComplianceScanner
        scanner = ComplianceScanner()
        return scanner.scan(path)
    
    def suggest(self, path: str) -> list[dict]:
        ...
```

### Claude Code 适配器

```python
class ClaudeAdapter(SkillGovernanceAdapter):
    """
    Claude Code CLI Agent 适配器。
    
    Claude Code 使用子进程方式调用：
    1. scan: python3 -m skill_governance.cli.main scan <path> --json
    2. suggest: 同上 suggest 子命令
    3. dry_run/apply: 解析 CLI 输出
    """
    def scan(self, path: str) -> dict:
        import subprocess
        result = subprocess.run(
            ["python3", "-m", "skill_governance.cli.main", "scan", path, "--json"],
            capture_output=True, text=True
        )
        return json.loads(result.stdout)
    ...
```

## 验收标准

- [x] `OpenClawAdapter` 继承 `SkillGovernanceAdapter` 并实现全部方法 <!-- 验证: grep -q "class OpenClawAdapter.*SkillGovernanceAdapter" packages/skill-governance/skill_governance/adapter/openclaw_adapter.py -->
- [x] `ClaudeAdapter` 继承 `SkillGovernanceAdapter` 并实现全部方法 <!-- 验证: grep -q "class ClaudeAdapter.*SkillGovernanceAdapter" packages/skill-governance/skill_governance/adapter/claude_adapter.py -->
- [x] `adapter list` 命令可列出 4 个适配器（hermes/opencode/openclaw/claude） <!-- 验证: python3 -m skill_governance.cli.main adapter list 2>&1 -->
- [x] 全部 141 测试通过 <!-- 验证: python3 -m pytest scripts/tests/ -q -->

## 边界与不做的范围

- ❌ 不修改 base.py（依赖 STORY-5-3-1 先行，不可并行）
- ❌ 不涉及 MCP Server（STORY-5-3-2）
- ❌ 不涉及 LangChain / CrewAI（Out of Scope）
