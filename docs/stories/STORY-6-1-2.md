# Story: F006+F007 — classification + triggers

> **story_id**: `STORY-6-1-2`
> **status**: `completed`
> **priority**: P1
> **epic**: EPIC-006
> **spec_ref**: SPEC-6-1
> **phase**: Phase-1
> **created**: 2026-05-16
> **owner**: boku (Emma)

## 用户故事
**As a** 包维护者
**I want** 自动补全 SKILL.md 的 classification 和 triggers 字段
**So that** 满足 L1 合规标准

## 验收标准
- [x] F007: 从 SKILL.md 的 tags[] 提取 triggers <!-- 验证: grep -q "triggers" fixer/rules/f007_triggers.py -->
- [x] F007: 幂等 — 已有 triggers 的不覆盖 <!-- 验证: grep -q "skip\|_is_already" fixer/rules/f007_triggers.py -->
- [x] F006: 从 SKILL.md name/description 推断 classification <!-- 验证: grep -q "classification\|domain\|toolset\|infrastructure" fixer/rules/f006_classification.py -->
- [x] F006: 启发式规则覆盖 domain/toolset/skill/infrastructure <!-- 验证: python3 -c "import ast; ast.parse(open('fixer/rules/f006_classification.py').read()); print('OK')" -->

## 技术方案
- 模块: `fixer/rules/f006_classification.py`, `fixer/rules/f007_triggers.py`
- F006 启发式: 包名含 skill/quality/engine → infrastructure; 含 workflow/process → toolset; 含 creative/design/analysis → domain; 默认 toolset
- F007 从 tags 数组取前 3 个 + name 关键词扩充
- 复用 `scripts/fix-l2-frontmatter.py` 的 `detect_type()` 模式
