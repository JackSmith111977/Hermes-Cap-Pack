# STORY-4-6: 低分 skill 改进（SQS < 60 → ≥ 60）

> **状态**: `completed` · **Epic**: EPIC-004 · **Spec**: SPEC-4-3
> **SDD 状态**: `completed` · **创建**: 2026-05-14

---

## 用户故事

**As a** 主人
**I want** 全部 SQS < 60 的 26 个 cap-pack skill 提升到 ≥ 60
**So that** 低分项占比从 18.3% 降至 ≤ 15%，CHI 提升至 70+

## 验收标准

- [ ] AC-01: 全部 26 个低分 skill 的 SKILL.md 包含 `depends_on` 字段
- [ ] AC-02: 全部 26 个低分 skill 的 SKILL.md 包含 `see_also` 字段
- [ ] AC-03: S4 关联完整度从 5.0 → ≥ 8.0（预期 +3）
- [ ] AC-04: 全部 low-score skill SQS ≥ 60（批量重扫描确认）
- [ ] AC-05: YAML frontmatter 语法正确（yaml.safe_load 通过）

## 范围

| 包含 | 不包含 |
|:-----|:--------|
| ✅ 26 个 cap-pack 内低分 skill 修复 | ❌ uncategorized 的 11 个 skill |
| ✅ `depends_on` + `see_also` 字段添加 | ❌ skill 正文内容重写 |
| ✅ description 场景补充 | ❌ cap-pack.yaml 修改（STORY-4-7） |
| ✅ YAML 语法验证 | ❌ CI 门禁（STORY-4-8） |

## 涉及能力包

creative-design(6), doc-engine(5), developer-workflow(4), media-processing(4), learning-engine(3), social-gaming(2), network-proxy(1), messaging(1)

## 依赖关系

- 前置: SPEC-4-3 已获批 ✅
- 影响: STORY-4-7（元数据补齐）、STORY-4-8（CI 门禁）
