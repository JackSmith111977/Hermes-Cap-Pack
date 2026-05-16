# Story: CLI fix 子命令

> **story_id**: `STORY-6-0-2`
> **status**: `completed`
> **priority**: P1
> **epic**: EPIC-006
> **spec_ref**: SPEC-6-1
> **phase**: Phase-0
> **created**: 2026-05-16
> **owner**: boku (Emma)

## 用户故事
**As a** 用户
**I want** `skill-governance fix <path>` CLI 命令
**So that** 可在终端一键触发的检测后的修复

## 验收标准
- [x] CLI 支持 `fix <path>` 命令 <!-- 验证: python3 -m skill_governance.cli.main fix --help -->
- [x] 支持 `--rules F001,F007` 过滤规则 <!-- 验证: grep -q "rules" cli/main.py -->
- [x] 支持 `--dry-run`（默认）/ `--apply` <!-- 验证: grep -q "dry_run\|--apply" cli/main.py -->
- [x] 支持 `--all` 批量处理全部 pack <!-- 验证: grep -q "all_packs\|--all" cli/main.py -->
- [x] 复用 `_load_skills_from_pack()` 和 `_build_report()` <!-- 验证: grep -q "load_skills\|_build_report" cli/main.py -->

## 技术方案
- 在 `packages/skill-governance/skill_governance/cli/main.py` 新增 `@app.command("fix")`
- 复用 scan 命令的包加载和扫描逻辑
- 调用 FixDispatcher.dispatch() 获取修复计划
