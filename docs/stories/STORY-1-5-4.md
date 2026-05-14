# STORY-1-5-4: 多 Agent 安装与自动检测

> **story_id**: `STORY-1-5-4`
> **status**: `implemented`
> **priority**: P1
> **epic**: EPIC-001-feasibility
> **spec_ref**: SPEC-1-5
> **created**: 2026-05-14
> **owner**: boku

## 用户故事

> **As a** 系统维护者
> **I want** 通过 `--target` 指定目标 Agent 安装能力包
> **So that** 一键安装到 Hermes/OpenCode 或自动检测可用环境

## 验收标准

### AC-5: 多 Agent 适配
- [x] `--target hermes` 安装到 Hermes（HermesAdapter）
- [x] `--target opencode` 安装到 OpenCode（OpenCodeAdapter，含格式转换）
- [x] `--target auto` 自动检测可用环境

## 代码变更

| 文件 | 变更 |
|:-----|:------|
| `scripts/install-pack.py` | 重构 v2.0：argparse 子命令 + `--target` 支持 + auto 检测 + verify 命令 |
| `scripts/adapters/opencode.py` | `install()` 新增 `skip_deps` 参数（与 HermesAdapter API 统一） |
| `scripts/tests/test_hermes_adapter.py` | 新增 `TestMultiAgentInstall` 类（4 个测试） |
