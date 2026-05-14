# STORY-3-1: developer-workflow 模块提取

> **状态**: `implemented` · **优先级**: P0 · **Epic**: EPIC-003 · **Spec**: SPEC-3-1
> **SDD 状态**: `completed` · **创建**: 2026-05-14
> **标签**: `extraction`, `developer-workflow`

## 用户故事

**As a** 主人
**I want** developer-workflow 模块（~16 skills）提取为标准能力包
**So that** 其他 Agent 可通过适配器复用 boku 的开发工作流能力

## 验收标准

- [ ] AC-01: packs/developer-workflow/cap-pack.yaml 创建完成
- [ ] AC-02: 全部 ~16 skills 复制到 SKILLS/ 目录
- [ ] AC-03: 每个 skill 有 SQS 评分记录
- [ ] AC-04: validate-pack.py 验证通过
- [ ] AC-05: 更新分类映射表
- [ ] AC-06: project-state.py verify 通过

## 覆盖的 Hermes skills

software-development/ (13): TDD, debugging, subagent, code-review, patch-file-safety, plan, writing-plans, spike, python-env, python-debugpy, node-inspect, requesting-code-review, hermes-agent-skill-authoring
communication/ (1): 1-3-1 决策框架
developer-workflow/ (1): 开发工作流索引
writing-styles-guide/ (1): 去 AI 味写作指南
