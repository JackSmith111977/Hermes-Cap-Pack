# Story: 适配器抽象层 + OpenCode 适配器

> **story_id**: `STORY-5-3-1`
> **status**: `completed`
> **priority**: P1
> **epic**: EPIC-005
> **spec_ref**: SPEC-5-3
> **phase**: Phase-3
> **created**: 2026-05-16
> **owner**: boku (Emma)

---

## 用户故事

**As a** Agent 开发者
**I want** 有一个统一的适配器抽象基类，所有 Agent 适配器继承同一接口
**So that** 任意 Agent 都能通过标准化的 scan→suggest→dry_run→apply 四步流程使用治理引擎

## 技术方案

### 文件清单

| 操作 | 文件 | 说明 |
|:-----|:-----|:------|
| ✨ 新建 | `packages/skill-governance/skill_governance/adapter/base.py` | 适配器抽象基类 |
| ✨ 新建 | `packages/skill-governance/skill_governance/adapter/opencode_adapter.py` | OpenCode 适配器 |
| 📦 迁移+重构 | `scripts/adapters/hermes.py` → `skill_governance/adapter/hermes_adapter.py` | 继承基类 |

### base.py 核心接口

```python
class SkillGovernanceAdapter(ABC):
    config: AdapterConfig
    
    @abstractmethod
    def scan(self, path: str) -> dict: ...
    @abstractmethod 
    def suggest(self, path: str) -> list[dict]: ...
    @abstractmethod
    def dry_run(self, path: str) -> str: ...
    @abstractmethod
    def apply(self, path: str) -> bool: ...
    @abstractmethod
    def get_agent_info(self) -> dict: ...
```

### 重构策略

`scripts/adapters/hermes.py`（26K）中的 `HermesAdapter` 类和 `scripts/adapters/opencode.py`（12K）中的逻辑，进行以下变更：
1. 提取共享接口到 `base.py`
2. `HermesAdapter` 继承 `SkillGovernanceAdapter`，保持原有功能
3. 新增 `OpenCodeAdapter` 继承基类，实现 OpenCode CLI 的治理调用
4. `scripts/adapters/` 目录保留为兼容层（委托调用 packages 中的实现）

## 验收标准

- [x] `base.py` 定义完整的抽象基类（5 个抽象方法 + AdapterConfig） <!-- 验证: grep -q "class SkillGovernanceAdapter" packages/skill-governance/skill_governance/adapter/base.py -->
- [x] `OpenCodeAdapter` 继承基类并实现全部方法 <!-- 验证: grep -q "class OpenCodeAdapter.*SkillGovernanceAdapter" packages/skill-governance/skill_governance/adapter/opencode_adapter.py -->
- [x] `scripts/adapters/hermes.py` 中的 `HermesAdapter` 重构为继承基类 <!-- 验证: grep -q "SkillGovernanceAdapter" scripts/adapters/hermes.py -->
- [x] 全部 141 测试通过 <!-- 验证: python3 -m pytest scripts/tests/ -q -->
- [x] 新增适配器测试通过 <!-- 验证: python3 -m pytest scripts/tests/ -k "adapter" -q -->

## 边界与不做的范围

- ❌ 不修改现有 `HermesAdapter` 的对外行为（保持向后兼容）
- ❌ 不涉及 MCP Server（STORY-5-3-2）
- ❌ 不涉及 OpenClaw / Claude Code（STORY-5-3-3）
