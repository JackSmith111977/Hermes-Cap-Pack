# STORY-3-9: github-ecosystem 能力包提取

> **状态**: `approved` · **优先级**: P1 · **Epic**: EPIC-003 · **Spec**: SPEC-3-3
> **SDD 状态**: `approved` · **创建**: 2026-05-14
> **标签**: `extraction`, `github-ecosystem`

## 用户故事

**As a** 主人
**I want** GitHub 生态相关技能被提取为 `github-ecosystem` 能力包
**So that** 跨 Agent 复用 PR/Issue/Code Review/Repo 管理等 GitHub 操作能力

## 验收标准

- [ ] AC-01: `packs/github-ecosystem/cap-pack.yaml` 创建，通过 v2 schema 验证
- [ ] AC-02: 全部 ~9 个 GitHub 技能提取到 `SKILLS/` 目录
- [ ] AC-03: 每个 skill 通过 SQS 质检
- [ ] AC-04: 覆盖率从 53% (9/17) 提升至 59% (10/17)
- [ ] AC-05: `project-report.json` + `PROJECT-PANORAMA.html` 同步更新
