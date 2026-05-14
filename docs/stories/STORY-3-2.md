# STORY-3-2: agent-orchestration 模块提取

> **状态**: `draft` · **优先级**: P0 · **Epic**: EPIC-003 · **Spec**: SPEC-3-1
> **SDD 状态**: `draft` · **创建**: 2026-05-14
> **标签**: `extraction`, `agent-orchestration`

## 用户故事

**As a** 主人
**I want** agent-orchestration 模块（~8 skills）提取为标准能力包
**So that** 其他 Agent 可通过适配器复用 boku 的多 Agent 协作能力

## 验收标准

- [ ] AC-01: packs/agent-orchestration/cap-pack.yaml 创建完成
- [ ] AC-02: 全部 ~8 skills 复制到 SKILLS/ 目录
- [ ] AC-03: 每个 skill 有 SQS 评分记录
- [ ] AC-04: validate-pack.py 验证通过
- [ ] AC-05: MCP 配置调研并注入
- [ ] AC-06: project-state.py verify 通过

## 覆盖的 Hermes skills

autonomous-ai-agents/ (7): hermes-agent, claude-code, codex, opencode, blackbox, honcho, hermes-message-injection
bmad-party-mode-orchestration/ (1): 多智能体编排
