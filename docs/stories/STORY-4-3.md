# STORY-4-3: L2 Experiences 补充（前 4 个空包）

> **状态**: `completed` · **Epic**: EPIC-004 · **Spec**: SPEC-4-2
> **SDD 状态**: `completed` · **创建**: 2026-05-14

---

## 用户故事

**As a** 主人
**I want** 为 4 个 L1-only 包补充 L2 Experiences
**So that** 它们不再仅仅是 SKILL 拷贝集合

## 验收标准

- [ ] AC-01: `packs/creative-design/EXPERIENCES/` 至少 2 篇
- [ ] AC-02: `packs/devops-monitor/EXPERIENCES/` 至少 1 篇
- [ ] AC-03: `packs/github-ecosystem/EXPERIENCES/` 至少 1 篇
- [ ] AC-04: `packs/learning-engine/EXPERIENCES/` 至少 2 篇
- [ ] AC-05: 全部使用 YAML frontmatter 标准模板
- [ ] AC-06: project-state.py verify 通过

## 执行步骤

1. 为每个包创建 `EXPERIENCES/` 目录（若不存在）
2. 编写 Experience 文档（按模板：type/skill_ref/keywords + 背景/核心/有效原因/陷阱）
3. 内容来自实际使用经验

## 涉及包

| 包 | Skills | 计划篇数 | 内容方向 |
|:---|:------:|:--------:|:---------|
| creative-design | 25 | 2 | AI 图像生成最佳实践、ComfyUI 工作流经验 |
| devops-monitor | 10 | 1 | Docker 运维陷阱 |
| github-ecosystem | 9 | 1 | GitHub Actions CI 配置经验 |
| learning-engine | 11 | 2 | 学习循环最佳实践、技能提取经验 |

## 估算：2h
