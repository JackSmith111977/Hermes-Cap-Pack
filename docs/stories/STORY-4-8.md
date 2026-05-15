# STORY-4-8: CHI 门禁脚本嵌入 CI（chi-gate.py + GitHub Actions）

> **状态**: `completed` · **Epic**: EPIC-004 · **Spec**: SPEC-4-3
> **SDD 状态**: `completed` · **创建**: 2026-05-14

---

## 用户故事

**As a** 主人
**I want** PR 提交时自动检查 CHI 不降级
**So that** 质量基线的退化能被自动捕获

## 验收标准

- [ ] AC-01: `scripts/chi-gate.py` 脚本实现 CHI 基线比对
- [ ] AC-02: CI `.github/workflows/ci.yml` 中包含 CHI 门禁 job
- [ ] AC-03: 阈值可配置（逐步 0.75 → 0.80 → 0.85）
- [ ] AC-04: CHI 下降时 CI 报 warning（非 blocking，渐进式）
- [ ] AC-05: 基线存于 `reports/chi-baseline.json`

## 范围

| 包含 | 不包含 |
|:-----|:--------|
| ✅ chi-gate.py 脚本 | ❌ skill 内容修改 |
| ✅ GitHub Actions job | ❌ phase-gate.py 修改 |
| ✅ CHI 基线对齐 | ❌ 跨包合并检测 |

## 依赖关系

- 前置: STORY-4-6（低分 skill 改进，确保基线合理）
- 前置: STORY-4-7（元数据补齐）
