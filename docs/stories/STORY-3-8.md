# STORY-3-8: creative-design 能力包提取

> **状态**: `completed` · **优先级**: P1 · **Epic**: EPIC-003 · **Spec**: SPEC-3-3
> **SDD 状态**: `approved` · **创建**: 2026-05-14
> **标签**: `extraction`, `creative-design`

## 用户故事

**As a** 主人
**I want** 创意设计领域的技能被提取为 `creative-design` 能力包
**So that** 跨 Agent 复用架构图、图片生成、ASCII 艺术、Mermaid、表情包等创意能力

## 验收标准

- [ ] AC-01: `packs/creative-design/cap-pack.yaml` 创建，通过 v2 schema 验证
- [ ] AC-02: 全部 ~22 个核心 creative skill 提取到 `SKILLS/` 目录
- [ ] AC-03: 每个 skill 通过 SQS 质检（无 < 50 分项）
- [ ] AC-04: 覆盖率从 47% (8/17) 提升至 53% (9/17)
- [ ] AC-05: `project-report.json` + `PROJECT-PANORAMA.html` 同步更新

## 技术方案

1. 盘点 creative-design 域下 ~22 个 skill（architecture-diagram, ascii-art, image-generation, excalidraw 等）
2. 运行 SQS 质检，记录基线
3. 创建 packs/creative-design/ 目录结构
4. 编写 cap-pack.yaml（含所有技能元数据）
5. 复制 skill 到 SKILLS/ 子目录
6. v2 schema 验证
7. 更新 project-report.json 重新生成 HTML 报告

## Out of Scope

- ❌ 修改 skill 原文内容（仅提取，不改）
- ❌ 跨 Agent 适配器修改
- ❌ 非 creative 域的 skill 提取

## 参考

- SPEC-3-3: Phase 2 提取计划
- learning-engine 提取流程（STORY-3-7）作为参考
