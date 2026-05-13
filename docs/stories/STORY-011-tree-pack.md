# STORY-011: 树状索引工具纳入 cap-pack 项目

> **状态**: `draft` · **优先级**: P1 · **Epic**: EPIC-002 · **Sprint**: 1
> **SDD 状态**: `draft` · **创建**: 2026-05-13 · **预估**: 1 轮
> **标签**: `tree-index`, `cap-pack-integration`

---

## 用户故事

**As a** 系统维护者
**I want** `skill-tree-index.py` 纳入 cap-pack 项目的 `scripts/` 目录并关联到 SPEC-005
**So that** 树状索引工具与能力包体系绑定发布，而不是孤立地在 Hermes 目录中

## 验收标准

- [ ] AC-01: `skill-tree-index.py` 已在 `~/projects/hermes-cap-pack/scripts/` 下
- [ ] AC-02: 工具运行时从 cap-pack 项目读取 18 模块定义
- [ ] AC-03: `--pack` 参数兼容 cap-pack 的包命名
- [ ] AC-04: 输出格式与 cap-pack 格式 v1 兼容
- [ ] AC-05: 可作为独立脚本运行（不依赖 Hermes 内部路径）

## 技术方案

1. 确认 `scripts/skill-tree-index.py` 已在正确位置 ✅（已完成）
2. 确保它可以独立运行（不依赖 `~/.hermes/` 绝对路径）
3. 添加 cap-pack 目录检测逻辑（`$CAP_PACK_DIR` 环境变量）

## 不做的

- 更改树状索引算法本身（已在 v1.0 稳定）
- 增加新功能（属 STORY-013~015）

## 测试

- 单元: `python3 scripts/skill-tree-index.py --json` 输出结构验证
