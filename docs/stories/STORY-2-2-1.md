# STORY-2-2-1: SQS/审计工具嵌入 cap-pack 项目

> **状态**: `implemented` · **优先级**: P1 · **Epic**: EPIC-002 · **Sprint**: 1
> **SDD 状态**: `implemented` · **创建**: 2026-05-13 · **预估**: 1 轮
> **标签**: `sqs`, `audit`, `cap-pack-integration`

---

## 用户故事

**As a** 系统维护者
**I want** `skill-quality-score.py` 和 `skill-lifecycle-audit.py` 被正式纳入 cap-pack 项目结构
**So that** 质量系统是能力包的一部分，而非孤立在 `~/.hermes/skills/skill-creator/` 中

## 验收标准

- [x] AC-01: 两个脚本已复制/链接到 `cap-pack/scripts/` 下
- [x] AC-02: 可在 cap-pack 路径下独立执行评分
- [x] AC-03: cap-pack.yaml 中有对应工具声明（已纳入 quality-assurance 包）
- [x] AC-04: 安装脚本 (install-pack.py) 在部署时可通过 `install.scripts` 配置建立链接

## 交付

| 项目 | 内容 |
|:-----|:------|
| 测试 | `test_epic002_tools.py::TestSkillQualityScore` — 5 个测试全部通过 |
| 测试 | `test_epic002_tools.py::TestSkillLifecycleAudit` — 6 个测试全部通过 |
| 独立运行 | 两个工具均可在 cap-pack 项目 `scripts/` 下直接运行 |
