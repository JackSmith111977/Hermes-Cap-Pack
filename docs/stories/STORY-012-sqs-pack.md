# STORY-012: SQS/审计工具嵌入 cap-pack 项目

> **状态**: `draft` · **优先级**: P1 · **Epic**: EPIC-002 · **Sprint**: 1
> **SDD 状态**: `draft` · **创建**: 2026-05-13 · **预估**: 1 轮
> **标签**: `sqs`, `audit`, `cap-pack-integration`

---

## 用户故事

**As a** 系统维护者
**I want** `skill-quality-score.py` 和 `skill-lifecycle-audit.py` 被正式纳入 cap-pack 项目结构
**So that** 质量系统是能力包的一部分，而非孤立在 `~/.hermes/skills/skill-creator/` 中

## 验收标准

- [ ] AC-01: 两个脚本已复制/链接到 `cap-pack/scripts/` 下
- [ ] AC-02: 可在 cap-pack 路径下独立执行评分
- [ ] AC-03: cap-pack.yaml 中有对应工具声明
- [ ] AC-04: 安装脚本 (install-pack.py) 在部署时建立符号链接回到 `~/.hermes/scripts/`

## 技术方案

1. 从 `~/.hermes/skills/skill-creator/scripts/` 复制两个 `.py` 文件到 `cap-pack/scripts/`
2. 在 cap-pack 中创建 `packs/quality-assurance/` 包
3. install-pack.py 支持将脚本符号链接到 `~/.hermes/scripts/`

## 不做的

- 更改评分/审计算法
- 重构脚本的内部逻辑

## 测试

- 集成: `python3 scripts/skill-quality-score.py --audit` 在 cap-pack 目录下运行
