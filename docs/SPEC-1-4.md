# 🔌 SPEC-1-4: 适配层方案

> **状态**: `approved` · **优先级**: P2 · **创建**: 2026-05-12 · **更新**: 2026-05-12
> **SDD 流程**: `CLARIFY ✅ → RESEARCH ✅ → CREATE ✅ → QA_GATE ✅ → REVIEW ✅`
> **关联 Epic**: EPIC-001-feasibility.md
> **审查人**: 主人

---

## 〇、需求澄清记录 (CLARIFY)

### 要解决的核心问题

> 如何让标准化的能力包能在不同 Agent 框架（Hermes / Claude Code / Codex CLI）上以各自的原生方式运行？

### 确认的范围

| 包含 | 不包含 |
|:-----|:--------|
| ✅ 适配层的抽象接口定义 (UCA Core) | ❌ 所有 Agent 适配器实现 |
| ✅ Hermes 适配器实现 | ❌ 非 MCP/无 Skills 的 Agent 适配 |
| ✅ Claude Code 适配器设计 | ❌ 适配器的性能基准测试 |
| ✅ Codex CLI 适配器设计 | ❌ IDE Agent (Cursor/Windsurf) 适配 |
| ✅ 跨 Agent 能力一致性保障 | ❌ 适配器市场/商店 |

---

## 一、RESEARCH — 深度调研

### 1.1 业界参考

| 来源 | 要点 | 可借鉴 |
|:-----|:------|:-------|
| **MCP 协议** | 标准化工具发现和调用 | 能力包的工具层协议标准 |
| **Hermes MCP Serve** | Hermes 可作 MCP Server 供给其他 Agent | 双向适配模式 |
| **AgenticFormat** (Auton) | 声明式 Agent 蓝图 + 运行时引擎分离 | 适配层的蓝图设计哲学 |
| **ALTK** | 框架无关的中间件钩子 | 适配器的 hook 机制 |
| **LangChain → CrewAI Adapter** | Tool 兼容性问题的典型案例 | 提前设计适配层接口 |

### 1.2 适配器设计原则

1. **接口统一** — 所有适配器实现相同的 `AgentAdapter` Protocol
2. **渐进适配** — 不要求 100% 能力对等，显式标注差异
3. **可插拔** — 第三方可通过继承 Protocol 贡献新适配器
4. **安装可验证** — 每个适配器提供 `verify()` 方法确认安装正确

---

## 二、适配层架构 (UCA)

### 统一能力适配器 (Unified Capability Adapter)

```text
                        ┌─────────────────┐
                        │  Capability Pack │
                        │  (cap-pack.yaml) │
                        └────────┬────────┘
                                 │
                                 ▼
                     ┌───────────────────────┐
                     │   UCA Core (核心层)    │
                     │                       │
                     │  ├─ 解析 cap-pack.yaml │
                     │  ├─ 验证完整性          │
                     │  ├─ 检查依赖            │
                     │  └─ 路由到适配器         │
                     └───────────┬───────────┘
                                 │
                 ┌───────────────┼───────────────┐
                 ▼               ▼               ▼
        ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
        │ Hermes       │ │ Claude Code  │ │ Codex CLI    │
        │ Adapter      │ │ Adapter      │ │ Adapter      │
        ├──────────────┤ ├──────────────┤ ├──────────────┤
        │ Skills →     │ │ Skills →     │ │ Skills →     │
        │ SKILL.md dir │ │ ~/.claude/   │ │ .codex/rules │
        │              │ │ skills/      │ │              │
        │ MCP →        │ │ MCP →        │ │ MCP →        │
        │ config.yaml  │ │ claude.json  │ │ tools.json   │
        │              │ │              │ │              │
        │ Exp →        │ │ Exp →        │ │ Exp →        │
        │ knowledge-   │ │ 注入         │ │ 注入         │
        │ ingest L2    │ │ CLAUDE.md    │ │ .md 参考     │
        └──────────────┘ └──────────────┘ └──────────────┘
```

### 适配器接口定义

```python
from typing import Protocol

class AgentAdapter(Protocol):
    """Agent 适配器必须实现的方法"""

    @property
    def name(self) -> str: ...

    @property
    def is_available(self) -> bool: ...

    def install(self, pack: 'CapPack') -> 'AdapterResult': ...
    def uninstall(self, pack_name: str) -> 'AdapterResult': ...
    def update(self, pack: 'CapPack', old_version: str) -> 'AdapterResult': ...
    def list_installed(self) -> list[str]: ...
    def verify(self, pack_name: str) -> bool: ...

class AdapterResult:
    success: bool
    details: dict
    warnings: list[str]
    backup_path: str
```

---

## 三、各 Agent 适配器

### Hermes 适配器（P0）

| 能力包组件 | Hermes 目标 | 实现方式 |
|:-----------|:------------|:---------|
| SKILLS/*.md | `~/.hermes/skills/{category}/{skill}/SKILL.md` | 文件写入 |
| EXPERIENCES/*.md | 技能引用目录 | 文件复制 |
| MCP/*.yaml | `config.yaml mcpServers` | `hermes config set` |
| hooks.on_activate | 安装后执行 | terminal 工具 |

**优势**: 原生 Profile/SRA/Curator 集成

### Claude Code 适配器（P1）

| 能力包组件 | Claude Code 目标 | 实现方式 |
|:-----------|:----------------|:---------|
| SKILLS/*.md | `~/.claude/skills/{pack}/{id}/SKILL.md` | 文件写入 |
| EXPERIENCES/*.md | `CLAUDE.md` | 追加注入 |
| MCP/*.yaml | `claude.json mcpServers` | 配置修改 |

**挑战**: ❌ 无 skill_manage ❌ 无 Curator ❌ 无 Profile 隔离

### Codex CLI 适配器（P1）

| 能力包组件 | Codex CLI 目标 | 实现方式 |
|:-----------|:---------------|:---------|
| SKILLS/*.md | `.codex/rules/{pack}-{id}.md` | 写入规则目录 |
| EXPERIENCES/*.md | `.codex/rules/{pack}-exp.md` | 合并为规则文件 |
| MCP/*.yaml | `.codex/mcp.json` | 写入 MCP 配置 |

---

## 四、适配器优先级矩阵

| Agent 类型 | 优先级 | 难度 | Skills | MCP | 经验 | 回滚 |
|:-----------|:------:|:----:|:------:|:---:|:----:|:----:|
| **Hermes** | P0 🥇 | ⭐⭐ | ✅ 原生 | ✅ 原生 | ✅ 原生 | ✅ 原生 |
| **Claude Code** | P1 🥈 | ⭐⭐⭐ | ✅ Skills | ✅ MCP | ⚠️ CLAUDE.md | ❌ 手动 |
| **Codex CLI** | P1 🥈 | ⭐⭐ | ✅ Rules | ✅ MCP | ✅ Rules | ❌ 手动 |
| **OpenCode** | P2 🥉 | ⭐⭐ | ✅ Skills | ✅ MCP | ⚠️ | ❌ |
| **Cursor** | P2 🥉 | ⭐⭐⭐ | ❌ 无 | ✅ MCP | ⚠️ rules | ❌ |

---

## 五、适配器插件化架构

```text
UCA Core
├── adapters/
│   ├── base.py           ← AgentAdapter Protocol
│   ├── hermes.py
│   ├── claude_code.py
│   ├── codex_cli.py
│   └── ... (第三方贡献)
├── core/
│   ├── pack_parser.py    ← cap-pack.yaml 解析
│   ├── dependency.py     ← 依赖检查
│   └── verifier.py       ← 安装验证
└── cli/
    └── main.py           ← cap-pack 命令
```

---

## 六、跨 Agent 能力一致性保障

### 能力对等性测试

```python
def test_doc_engine_consistency():
    for agent in ["hermes", "claude-code", "codex-cli"]:
        result = cap_pack.test("doc-engine", agent=agent)
        assert result.skills_installed >= 3
        assert result.mcp_configured >= 1
```

### 兼容性声明

```yaml
compatibility:
  hermes:
    skills: full
    mcp: full
    experiences: full
  claude-code:
    skills: full
    mcp: full
    experiences: limited   # 仅注入 CLAUDE.md
  codex-cli:
    skills: full           # 以 rules 形式
    mcp: full
    experiences: partial
```

---

## 七、验收标准 (AC)

- [x] AgentAdapter Protocol 可被 3 个适配器实现（Phase 0: Protocol 定义完成 ✅）
- [x] Hermes 适配器可完整安装/卸载/更新能力包（Phase 1: HermesAdapter 实现完成 ✅）
- [x] Claude Code 适配器可安装技能和 MCP 配置（Phase 2: OpenCode 适配器 + Claude 兼容完成 ✅）
- [x] Codex CLI 适配器可使用 rules 系统加载技能（Phase 2: OpenCode 适配器 + Codex 兼容完成 ✅）
- [x] 能力对等性测试可至少覆盖 Hermes 和 OpenCode（Phase 2: parity 测试完成 ✅）
- [x] 第三方适配器集成文档可指引新适配器开发（Phase 2.5: developer-guide-adapter.md 完成 ✅）

---

## 八、开放问题

- [ ] Q1: 是否允许一个 Agent 安装多个版本的能力包？
- [ ] Q2: 适配器插件化是否采用与 Hermes Plugin 相同的注册机制？

---

## 九、QA_GATE 检查清单

- [x] Spec ID 格式正确（SPEC-1-4）
- [x] 关联 Epic 引用完整
- [x] CLARIFY 章节记录了需求澄清
- [x] RESEARCH 章节有 5 个业界参考
- [x] 适配器接口定义有 Python Protocol 示例
- [x] 3 个 Agent 适配器有具体设计
- [x] 优先级矩阵覆盖了 5 种 Agent
- [x] 插件化架构有目录结构
- [x] 能力一致性保障有测试示例
- [x] AC 每项可独立验证
- [x] 主人 REVIEW 批准
