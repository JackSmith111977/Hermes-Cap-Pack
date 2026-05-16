# Story: FixRule 抽象层 + Dispatcher

> **story_id**: `STORY-6-0-1`
> **status**: `completed`
> **priority**: P1
> **epic**: EPIC-006
> **spec_ref**: SPEC-6-1
> **phase**: Phase-0
> **created**: 2026-05-16
> **owner**: boku (Emma)

## 用户故事
**As a** 开发者
**I want** FixRule 抽象基类和 Dispatcher
**So that** 新增修复规则只需继承基类、注册到 Dispatcher

## 验收标准
- [x] FixRule(ABC) 定义 analyze() + apply() 抽象方法 <!-- 验证: grep -q "class FixRule.*ABC" fixer/base.py -->
- [x] FixResult dataclass: applied/skipped/errors/actions/diff <!-- 验证: grep -q "class FixResult" fixer/base.py -->
- [x] FixAction dataclass: rule_id/action_type/target_path/old/new/description <!-- 验证: grep -q "class FixAction" fixer/base.py -->
- [x] FixDispatcher.register() + get_rule() + dispatch() <!-- 验证: grep -q "class FixDispatcher" fixer/dispatcher.py -->
- [x] FixRule._backup() 使用 shutil.copy2 生成 .bak <!-- 验证: grep -q "\.bak\|backup" fixer/base.py -->
- [x] FixRule._is_already_fixed() 幂等性检查 <!-- 验证: grep -q "already_fixed\|skip" fixer/base.py -->

## 技术方案
- 模块: `packages/skill-governance/skill_governance/fixer/base.py`
- 模块: `packages/skill-governance/skill_governance/fixer/dispatcher.py`
- 使用标准库 `dataclasses`, `abc`, `difflib`, `shutil`
- 复用 CapPackAdapter 的 dry_run/apply 模式理念
