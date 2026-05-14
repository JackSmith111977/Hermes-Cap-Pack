# STORY-3-3: metacognition 模块提取

> **状态**: `draft` · **优先级**: P0 · **Epic**: EPIC-003 · **Spec**: SPEC-3-1
> **SDD 状态**: `draft` · **创建**: 2026-05-14
> **标签**: `extraction`, `metacognition`

## 用户故事

**As a** 主人
**I want** metacognition 模块（~6 skills）提取为标准能力包
**So that** 其他 Agent 可通过适配器复用 boku 的元认知和自我管理能力

## 验收标准

- [ ] AC-01: packs/metacognition/cap-pack.yaml 创建完成
- [ ] AC-02: 全部 ~6 skills 复制到 SKILLS/ 目录
- [ ] AC-03: 每个 skill 有 SQS 评分记录
- [ ] AC-04: validate-pack.py 验证通过
- [ ] AC-05: 交叉引用补全（与 learning-engine 关联）
- [ ] AC-06: project-state.py verify 通过

## 覆盖的 Hermes skills

meta/ (2): self-capabilities-map, architecture-trilemma
self-capabilities-map/ (1): 能力认知地图
skill-creator/ (1): 技能创作工作流
skill-to-pypi/ (1): skill 转 PyPI 包
hermes-ops-tips/ (1): Hermes 运维最佳实践

## 备注

dogfood 中的 self-review、memory-management 等归入后续 Phase。
