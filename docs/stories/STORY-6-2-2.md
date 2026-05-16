# Story: E001 SRA 元数据 + E002 跨平台

> **story_id**: `STORY-6-2-2`
> **status**: `completed`
> **priority**: P2
> **epic**: EPIC-006
> **spec_ref**: SPEC-6-2
> **phase**: Phase-2
> **created**: 2026-05-16

## AC
- [x] E001: LLM 生成 3-5 个 SRA triggers + 优化 description <!-- 验证: grep -q "E001\|sra\|triggers" fixer/rules/e001_sra.py -->
- [x] E002: 推断 agent_types 声明 (≥2) <!-- 验证: grep -q "E002\|agent_types\|compatibility" fixer/rules/e002_cross_platform.py -->
