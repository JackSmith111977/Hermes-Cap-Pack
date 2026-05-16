# Story: LLM 辅助修复框架 + F006 增强

> **story_id**: `STORY-6-2-1`
> **status**: `completed`
> **priority**: P2
> **epic**: EPIC-006
> **spec_ref**: SPEC-6-2
> **phase**: Phase-2
> **created**: 2026-05-16

## AC
- [x] LLMAssistRule 基类: _call_llm() 通过 opencode run 调用 <!-- 验证: grep -q "LLMAssistRule\|_call_llm" fixer/llm_assist.py -->
- [x] F006 增强: LLM 辅助推断 classification <!-- 验证: grep -q "classification\|llm" fixer/llm_assist.py -->
