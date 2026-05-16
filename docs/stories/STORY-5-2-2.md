# Story: SRA 质量注入 + 编排感知推荐

> **story_id**: `STORY-5-2-2`
> **status**: `draft`
> **priority**: P1
> **epic**: EPIC-005
> **spec_ref**: SPEC-5-2
> **phase**: Phase-2
> **created**: 2026-05-16
> **owner**: boku (Emma)

---

## 用户故事

> **As a** SRA 推荐引擎
> **I want** 技能推荐的权重包含 SQS 质量分和编排声明评分
> **So that** 高质量、可编排的 skill 被优先推荐

## 验收标准

- [x] `integration/sra_quality_injector.py` — SQS → SRA 权重映射 <!-- 验证: python3 -c "from skill_governance.integration.sra_quality_injector import inject_quality_to_sra; print('OK')" -->
- [x] SQS ≥ 80 → weight 1.0, ≥ 60 → 0.85, < 60 → 0.5 <!-- 验证: grep -q "0.85\|0.5\|1.0" integration/sra_quality_injector.py -->
- [x] 有编排声明 → weight *= 1.2 <!-- 验证: grep -q "1.2\|workflow\|编排" integration/sra_quality_injector.py -->
- [x] 输出格式兼容 SRA 的 JSON 权重配置 <!-- 验证: grep -q "sra\|weight\|score" integration/sra_quality_injector.py -->

## 技术方案

扩展 `sqs-sync.py`，在同步 SQS 分的同时注入编排感知因子。
