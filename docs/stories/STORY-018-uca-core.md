# Story: UCA Core 适配器核心框架

> **story_id**: `STORY-018-uca-core`
> **status**: `implemented`
> **priority**: P0
> **epic**: EPIC-001-feasibility
> **spec_ref**: SPEC-004-adaptation
> **created**: 2026-05-13
> **implemented**: 2026-05-13
> **owner**: boku

---

## 用户故事

> **As a** 适配器开发者
> **I want** 一个统一的 UCA Core 核心框架（AgentAdapter Protocol + 包解析 + 依赖检查 + 验证器）
> **So that** 我可以为不同 Agent 实现适配器，而无需重复实现包解析和验证逻辑

## 验收标准

- [ ] AC1: `AgentAdapter` Protocol 定义了 install/uninstall/update/list/verify 5 个方法
- [ ] AC2: `PackParser` 能解析 cap-pack.yaml 并返回 `CapPack` 对象（含 skills/experiences/mcp/hooks）
- [ ] AC3: `PackParser` 在 YAML 格式错误时抛出明确异常
- [ ] AC4: `DependencyChecker` 能检查 Python 包依赖、前置 skill 是否存在
- [ ] AC5: `PackVerifier` 能验证 skill 文件完整性、MCP 配置语法
- [ ] AC6: 所有组件有单元测试覆盖（≥80% line coverage）

## 技术方案

### 设计思路

将适配器的公共基础设施抽取为 `uca/` 包：
- **Protocol**: 定义适配器契约，所有适配器实现同一接口
- **Parser**: 解析 cap-pack.yaml → `CapPack` 数据类，含 JSON Schema 校验
- **Dependency**: 检查安装前置条件（Python 包 / 系统工具 / 前置 skill）
- **Verifier**: 安装后验证完整性（文件存在 / MCP 可达 / skill 可加载）

### 涉及文件

| 文件 | 操作 | 说明 |
|:-----|:-----|:------|
| `scripts/uca/__init__.py` | 新建 | 包导出 |
| `scripts/uca/protocol.py` | 新建 | AgentAdapter Protocol + AdapterResult + CapPack |
| `scripts/uca/parser.py` | 新建 | cap-pack.yaml 解析器 |
| `scripts/uca/dependency.py` | 新建 | 依赖检查器 |
| `scripts/uca/verifier.py` | 新建 | 安装后验证器 |
| `scripts/tests/test_uca_parser.py` | 新建 | 解析器测试 |
| `scripts/tests/test_uca_dependency.py` | 新建 | 依赖检查测试 |
| `scripts/tests/test_uca_verifier.py` | 新建 | 验证器测试 |

## 测试数据契约

```yaml
test_data:
  source: "packs/doc-engine/cap-pack.yaml"
  ci_independent: true
  pattern_reference: "python3 -m pytest scripts/tests/ -q"
```

## 引用链

- SPEC-004: [docs/SPEC-004-adaptation.md](../SPEC-004-adaptation.md)
- 后序 Story: STORY-019-uca-cli, STORY-020-hermes-adapter

## 不做的范围

- ❌ CLI 命令（STORY-019 覆盖）
- ❌ Hermes 适配器（STORY-020 覆盖）
- ❌ 跨 Agent 适配器（STORY-022/023 覆盖）
- ❌ 回滚/快照机制（STORY-021 覆盖）

---

## 决策日志

| 日期 | 决策 | 理由 |
|:----|:-----|:------|
| 2026-05-13 | Protocol 用 `typing.Protocol` 而非 ABC | Protocol 更轻量、鸭子类型友好 |
| 2026-05-13 | `CapPack` 用 dataclass 而非 dict | 类型安全、IDE 友好、可序列化 |
| 2026-05-13 | verifier 返回结构化报告而非 bool | 便于 CLI 展示详细验证结果 |
