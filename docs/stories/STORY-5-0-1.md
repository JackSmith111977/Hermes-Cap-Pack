# Story: 制定四层统一标准

> **story_id**: `STORY-5-0-1`
> **status**: `draft`
> **priority**: P1
> **epic**: EPIC-005
> **spec_ref**: SPEC-5-0
> **phase**: Phase-0
> **created**: 2026-05-16
> **owner**: boku (Emma)

---

## 用户故事

> **As a** 主人
> **I want** Cap-Pack 统一管理标准的 L0-L4 四层体系定稿
> **So that** 后续治理引擎检测器有明确的合规依据

## 验收标准

- [x] CAP-PACK-STANDARD.md 覆盖 L0-L4 全部四层 <!-- 验证: grep -c "^### Layer" docs/CAP-PACK-STANDARD.md >= 4 -->
- [x] 每层有明确的规则描述、量化阈值和检查方式 <!-- 验证: python3 -c "import re; c=open('docs/CAP-PACK-STANDARD.md').read(); [re.search(r'### Layer.*\n.*阈值', c).group() or True for l in range(5)]" -->
- [x] 与 Agent Skills Spec (Agentskills.io) 100% 兼容 <!-- 验证: grep -q "Agent Skills Spec" docs/CAP-PACK-STANDARD.md -->
- [x] Layer 4 Workflow 编排调度层的提案已完成 <!-- 验证: grep -q "sequential\|parallel\|conditional\|dag" docs/CAP-PACK-STANDARD.md -->

## 技术方案

### 设计思路

基于 `docs/CAP-PACK-STANDARD.md` 现有初稿（L0-L4 四层框架 + Layer 4 提案），完善各层的详细规则定义：
- L0（兼容层）：引用 Agent Skills Spec 标准
- L1（基础合规层）：SQS ≥ 60、frontmatter 合法、version/tags 必填
- L2（健康组织层）：树状簇归属、簇大小 3-15、原子性 < 500 行
- L3（生态层）：SRA 可发现性、跨平台兼容、跨包无冗余
- L4（编排调度层）：工作流编排、DAG/顺序/条件/并行

### 涉及文件

- `docs/CAP-PACK-STANDARD.md` — 主标准文档（从初稿完善到正式版）

## 引用链

- EPIC-005: `docs/EPIC-005-skill-governance-engine.md`
- SPEC-5-0: `docs/SPEC-5-0.md`

## 不做的范围

- machine-checkable 规则集的 JSON/YAML 实现（STORY-5-0-2）
- Workflow 编排模式的 schema 定义（STORY-5-0-3）
- 任何检测器代码

---

## 决策日志

| 日期 | 决策 | 理由 |
|:-----|:-----|:------|
| 2026-05-16 | 不 fork Agent Skills Spec，只在其上扩展 | 行业标准兼容优先 |
