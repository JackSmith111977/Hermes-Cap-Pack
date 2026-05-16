# Story: E005 断裂链接检测与修复

> **story_id**: `STORY-6-2-3`
> **status**: `completed`
> **priority**: P2
> **epic**: EPIC-006
> **spec_ref**: SPEC-6-2
> **phase**: Phase-2
> **created**: 2026-05-16

## AC
- [x] E005: curl --head 验证链接有效性 <!-- 验证: grep -q "curl.*head\|broken_links" fixer/rules/e005_broken_links.py -->
- [x] E005: LLM 搜索替代 URL 建议 <!-- 验证: grep -q "llm\|opencode\|suggest\|替代" fixer/rules/e005_broken_links.py -->
