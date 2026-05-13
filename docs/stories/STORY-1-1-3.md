# STORY-1-1-3: Capability Pack 格式定义 v1

> **story_id**: `STORY-1-1-3`
> **status**: `draft`
> **priority**: P0
> **epic**: EPIC-001-feasibility
> **spec_ref**: SPEC-1-1
> **created**: 2026-05-13
> **owner**: boku

---

## 用户故事

> **As a** 能力包的开发者
> **I want** 定义标准化的 `cap-pack.yaml` 格式规范
> **So that** 所有能力包都遵循统一的 Schema，确保跨 Agent 的可移植性

## 验收标准

- [ ] AC1: cap-pack.yaml 格式规范文档（`schemas/cap-pack-format-v1.md`）已定稿，包含 8 大字段组的完整定义
- [ ] AC2: JSON Schema 验证文件（`schemas/cap-pack-v1.schema.json`）已创建，可通过 `jsonschema.validate()` 验证
- [ ] AC3: 至少 3 个独立的 cap-pack.yaml 示例文件通过了 JSON Schema 验证
- [ ] AC4: 格式规范包含显式的版本号规则（MAJOR.MINOR.PATCH）
- [ ] AC5: 格式规范包含 compatibility（agent_types, requires_mcp, requires_network, requires_env）声明

## 技术方案

### 设计思路

基于四支柱可行性调研的结果，设计一个 YAML 格式的能力包清单文件。格式需要支持技能引用、经验沉淀、MCP 配置、依赖声明和生命周期钩子。参考 MCP 协议规范和 SKILL.md 标准，确保与现有生态兼容。

### 实现步骤

1. 定义顶层字段（name, version, type, classification, display_name, description）
2. 定义 compatibility 和 dependencies 声明
3. 定义 skills 和 experiences 引用格式（含 linked files）
4. 定义 mcp_servers 和 hooks
5. 编写 JSON Schema 用于自动化验证
6. 创建 3 个示例文件验证格式

### 涉及文件

- `schemas/cap-pack-format-v1.md` — 格式规范文档
- `schemas/cap-pack-v1.schema.json` — JSON Schema
- `packs/*/cap-pack.yaml` — 示例

## 测试数据契约

```yaml
test_data:
  source: "packs/doc-engine/cap-pack.yaml"
  ci_independent: true
  pattern_reference: "jsonschema.validate(instance=pack, schema=schema)"
```

## 引用链

- EPIC-001: [docs/EPIC-001-feasibility.md](../EPIC-001-feasibility.md)
- SPEC-1-1: [docs/SPEC-1-1.md](../SPEC-1-1.md)
- 前序 Story: 无（首个实现的 Story）

## 不做的范围

- ❌ 格式的编程语言绑定（JS/Python 等）
- ❌ 在线注册中心的后端服务
- ❌ 自动化格式转换工具
- ❌ 跨 Agent 适配器的实现

---

## 决策日志

| 日期 | 决策 | 理由 |
|:----|:-----|:------|
| 2026-05-13 | 采用 YAML 而非 JSON/TOML | YAML 支持注释，对 AI 友好 |
| 2026-05-13 | `skills[].files` 字段用于声明 linked resources | 解决原格式缺少关联文件信息的问题 |
