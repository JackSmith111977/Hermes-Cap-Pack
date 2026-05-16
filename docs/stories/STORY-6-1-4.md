# Story: F006 启发式增强 + 测试套件

> **story_id**: `STORY-6-1-4`
> **status**: `completed`
> **priority**: P1
> **epic**: EPIC-006
> **spec_ref**: SPEC-6-1
> **phase**: Phase-1
> **created**: 2026-05-16
> **owner**: boku (Emma)

## 用户故事
**As a** 开发者
**I want** 完整的测试套件覆盖 Phase 0+1 所有 FixRule
**So that** 修复行为可预期，无回归

## 验收标准
- [x] conftest.py: temp_pack 夹具创建带已知问题的包 <!-- 验证: test -f packages/skill-governance/tests/conftest.py -->
- [x] test_fixer_base.py: FixRule ABC + Dispatcher 单元测试 <!-- 验证: grep -q "test_fixer_base" packages/skill-governance/tests/ -->
- [x] test_fixer_f001.py: F001 的 4 种场景测试 <!-- 验证: grep -q "test_fixer_f001" packages/skill-governance/tests/ -->
- [x] test_fixer_f006+f007.py: F006+F007 测试 <!-- 验证: test -f packages/skill-governance/tests/test_fixer_f006_f007.py -->
- [x] test_fixer_h001+h002.py: H001+H002 测试 <!-- 验证: test -f packages/skill-governance/tests/test_fixer_h001_h002.py -->
- [x] test_cli_fix.py: CLI fix 命令集成测试 <!-- 验证: test -f packages/skill-governance/tests/test_cli_fix.py -->
- [x] F006 增强: 支持从 SKILL.md 的 tags/description/keywords 多维度推断 <!-- 验证: grep -q "tags\|description\|keywords" fixer/rules/f006_classification.py -->

## 技术方案
- 测试目录: `packages/skill-governance/tests/`
- 夹具: `temp_pack` 用 `tmp_path` 创建含已知问题的包
- 每个 FixRule 测试: dry_run 不修改文件 → apply 修改 → 幂等验证
- F006 增强: 除了包名启发式，还从 SKILL.md 具体内容的多维关键词推断
