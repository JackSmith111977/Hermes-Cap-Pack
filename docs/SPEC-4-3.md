# 🔧 SPEC-4-3: 质量提升迭代 — EPIC-004 Phase 2

> **状态**: `approved` · **优先级**: P0 · **创建**: 2026-05-14
> **SDD 流程**: `CLARIFY ✅ → RESEARCH ✅ → CREATE ✅ → REVIEW ✅ → APPROVED ✅`
> **关联 Epic**: EPIC-004-quality-upgrade.md

---

## 〇、需求澄清 (CLARIFY)

### 用户故事

> **As a** 主人
> **I want** 提升全部能力包的 SQS 质量评分，CHI 从 67.92 → 75+
> **So that** 能力包达到可发布水平，低分技能不再拖累整体健康度

### 范围

| 包含 | 不包含 |
|:-----|:--------|
| ✅ 低分 skill (SQS < 60) S4 关联修复 | ❌ 重写全部 skill 内容 |
| ✅ 边缘 skill (SQS 60-65) 批量提升 | ❌ L2/L3 层修改（Phase 1 已完成） |
| ✅ cap-pack.yaml 元数据补齐 | ❌ 跨包合并（Phase 3） |
| ✅ CI CHI 不降级门禁 | ❌ 全模块提取 |

### 验收标准

- [ ] AC1: 全部 SQS < 60 的 skill 提升至 ≥ 60
- [ ] AC2: 全部 cap-pack.yaml 至少包含 name/version/description/author/triggers
- [ ] AC3: CI pr-check 包含 CHI 不降级门禁（阈值 0.75 渐进目标）
- [ ] AC4: CHI ≥ 75（渐进目标），低分项占比 ≤ 15%
- [ ] AC5: S4 关联完整度从 5.0 提升至 ≥ 8.0

### Out of Scope

- L2/L3 层内容修改（Phase 1 已完成）
- 跨包 skill 合并（Phase 3 专属）
- 新能力包提取（独立 EPIC）

---

## 一、技术调研 (RESEARCH)

### 当前基线

| 指标 | 当前值 | 目标值 |
|:-----|:------:|:------:|
| CHI | 67.92 | ≥ 75 |
| SQS 平均分 | 67.92 | ≥ 75 |
| 低分项 (<60) | 37 个 (18.3%) | ≤ 15% |
| S4 关联完整度 | 5.0/20 | ≥ 8.0 |

### 37 个低分 skill 分布

| 能力包 | 数量 | 主要问题 |
|:-------|:----:|:---------|
| creative-design | 6 | S4 关联 + S2 描述不足 |
| doc-engine | 5 | S4 关联缺失 |
| developer-workflow | 4 | S4 关联 + S2 描述不足 |
| media-processing | 4 | S4 关联缺失 |
| uncategorized | 11 | 包归属未定（非本 Phase 范围）|
| learning-engine | 3 | S4 关联缺失 |
| social-gaming | 2 | S4 关联缺失 |
| network-proxy | 1 | S4 关联缺失 |
| messaging | 1 | S4 关联缺失 |

### 改进策略

**S4 修复模式**：在每个低分 skill 的 SKILL.md frontmatter 中添加 `depends_on` 和 `see_also` 字段，将 S4 从 5.0 → ≥ 8.0。

**S2 修复模式**：在 description 中补充使用场景描述。

---

## 二、Stories

| Story | 标题 | 估算 | 依赖 |
|:------|:-----|:----:|:-----|
| STORY-4-6 | 低分 skill 改进（SQS < 60 的 26 个 cap-pack skill） | 2h | SPEC-4-3 获批 |
| STORY-4-7 | 缺失元数据补充（16 个包 cap-pack.yaml 补齐字段） | 1h | STORY-4-6 |
| STORY-4-8 | CHI 门禁脚本嵌入 CI（chi-gate.py + GitHub Actions） | 1h | STORY-4-6, 4-7 |

---

## 三、风险

| 风险 | 概率 | 影响 | 缓解 |
|:-----|:----:|:----:|:-----|
| S4 修复后 SQS 提升不明显 | 中 | 低 | 同时提升 S2 内容描述 |
| 直接修改 SKILL.md 破坏 YAML | 低 | 中 | 批量脚本验证 YAML 语法 |
| CI 门禁过严格阻塞开发 | 低 | 中 | 渐进阈值（0.75→0.80→0.85） |
