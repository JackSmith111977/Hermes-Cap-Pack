# Story: F001 — 生成缺失 SKILL.md

> **story_id**: `STORY-6-1-1`
> **status**: `completed`
> **priority**: P1
> **epic**: EPIC-006
> **spec_ref**: SPEC-6-1
> **phase**: Phase-1
> **created**: 2026-05-16
> **owner**: boku (Emma)

## 用户故事
**As a** 包维护者
**I want** 自动为缺失 SKILL.md 的 skill 生成骨架文件
**So that** 不用手动创建每个文件

## 验收标准
- [x] 从 cap-pack.yaml 条目数据生成 SKILL.md 骨架 <!-- 验证: python3 -m pytest tests/test_fixer_f001.py -q -->
- [x] 骨架包含有效 YAML frontmatter (name/description/version/tags) <!-- 验证: grep -q "name\|description\|version\|tags" fixer/rules/f001_skill_md.py -->
- [x] 幂等：已存在 SKILL.md 不被覆盖 <!-- 验证: grep -q "_is_already_fixed\|skip" fixer/rules/f001_skill_md.py -->
- [x] 依赖: FixRule base + CapPackAdapter._parse_frontmatter <!-- 验证: import check -->

## 技术方案
- 模块: `fixer/rules/f001_skill_md.py`
- 复用 `adapter/cap_pack_adapter.py` 的 `_parse_frontmatter` 和 `_extract_skill_tags_and_desc`
- SKILL.md 模板包含基本 frontmatter + 章节骨架
