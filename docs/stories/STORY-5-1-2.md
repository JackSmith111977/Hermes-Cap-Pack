# Story: Cap-Pack 合规检查器

> **story_id**: `STORY-5-1-2`
> **status**: `completed`
> **priority**: P1
> **epic**: EPIC-005
> **spec_ref**: SPEC-5-1
> **phase**: Phase-1
> **created**: 2026-05-16
> **owner**: boku (Emma)

---

## 用户故事

> **As a** 治理引擎
> **I want** 对照 `standards/rules.yaml` 的 L1+F 和 L3+E 规则全面检查 skill 合规性
> **So that** 不合规的 skill 可在纳入 cap-pack 前被拦截

## 验收标准

- [x] `scanner/compliance.py` — L1 Foundation (F001-F007) + L3 Ecosystem (E001-E005) 检测 <!-- 验证: pytest tests/test_compliance.py -q -->
- [x] 集成 SQS 评分作为合规输入 <!-- 验证: grep -q "sqs\|SQS\|quality-score" scanner/compliance.py -->
- [x] 跨包重叠检测（调用 merge-suggest.py） <!-- 验证: grep -q "merge-suggest\|overlap" scanner/compliance.py -->
- [x] v3 Schema 引用验证 <!-- 验证: grep -q "cap-pack-v3\|v3.schema" scanner/compliance.py -->

## 技术方案

详见 SPEC-5-1 §2.3 Compliance Checker。
