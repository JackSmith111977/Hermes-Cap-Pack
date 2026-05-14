# 🔧 SPEC-3-1: 核心能力包提取 — Phase 1

> **状态**: `implemented` · **优先级**: P0 · **创建**: 2026-05-14 · **更新**: 2026-05-14
> **SDD 流程**: `CLARIFY ✅ → RESEARCH ✅ → CREATE ✅ → QA_GATE ✅ → REVIEW ✅`
> **关联 Epic**: EPIC-003-module-extraction.md
> **全盘路线图**: EPIC-003-comprehensive-roadmap.md

---

## 〇、需求澄清 (CLARIFY)

### 用户故事

> **As a** 主人
> **I want** 将 developer-workflow、agent-orchestration、metacognition 三个自引用核心模块提取为标准能力包
> **So that** 其他 Agent 也能复用 boku 的开发工作流、Agent 协作和元认知能力

### 范围

| 包含 | 不包含 |
|:-----|:--------|
| ✅ 3 个模块的全流程提取（盘点→质检→合并→提取→补全→验证） | ❌ 修改 skill 内容本身（仅提取，不改造） |
| ✅ 每个模块一个 cap-pack.yaml + SKILLS/ + EXPERIENCES/ | ❌ 其他 Phase 的模块（Phase 2-5 后续进行） |
| ✅ 每个 skill 的 SQS 评分基线 | ❌ MLOps 等跨模块 skill |

---

## 一、三个模块详情

### STORY-3-1: developer-workflow (~16 skills)

| 源 | Skills | 说明 |
|:---|:------:|:------|
| `software-development/` | 13 | TDD, debugging, subagent, code-review, patch-file-safety, plan, writing-plans, spike, python-env, python-debugpy, node-inspect, requesting-code-review, hermes-agent-skill-authoring |
| `communication/` | 1 | 1-3-1 决策框架 |
| `developer-workflow/` | 1 | 开发工作流索引 |
| `writing-styles-guide/` | 1 | 去 AI 味写作指南 |

### STORY-3-2: agent-orchestration (~8 skills)

| 源 | Skills | 说明 |
|:---|:------:|:------|
| `autonomous-ai-agents/` | 7 | hermes-agent, claude-code, codex, opencode, blackbox, honcho, hermes-message-injection |
| `bmad-party-mode-orchestration/` | 1 | 多智能体编排 |

### STORY-3-3: metacognition (~6 skills)

| 源 | Skills | 说明 |
|:---|:------:|:------|
| `meta/` | 2 | self-capabilities-map, architecture-trilemma |
| `self-capabilities-map/` | 1 | 能力认知地图 |
| `skill-creator/` | 1 | 技能创作工作流 |
| `skill-to-pypi/` | 1 | skill 转 PyPI 包 |
| `hermes-ops-tips/` | 1 | Hermes 运维最佳实践 |

*(dogfood 中的 self-review/memory-management 等暂归入后续 Phase)*

---

## 二、执行顺序

```
Week 1: STORY-3-1 developer-workflow → 16 skills → 提取 + 验证
Week 2: STORY-3-2 agent-orchestration → 8 skills → 提取 + 验证
Week 3: STORY-3-3 metacognition     → 6 skills → 提取 + 验证
```

每个 Story 的 6 步 SOP：
```
① 盘点 → ② SQS 质检 → ③ 合并去重 → ④ 提取 → ⑤ 补全 → ⑥ 验证
```

---

## 三、验收标准

| AC ID | 描述 | 验证方式 | 优先级 |
|:------|:-----|:---------|:------:|
| AC-01 | developer-workflow 完整提取 | `validate-pack.py dev-workflow` 通过 | P0 |
| AC-02 | agent-orchestration 完整提取 | `validate-pack.py agent-orch` 通过 | P0 |
| AC-03 | metacognition 完整提取 | `validate-pack.py metacognition` 通过 | P0 |
| AC-04 | 每个 pack 的 skills 有 SQS 评分 | `skill-quality-score.py --pack <name>` 有输出 | P0 |
| AC-05 | 识别并报告重复 skill | `skill-tree-index.py --consolidate` 有输出 | P1 |
| AC-06 | 更新 README + project-state.yaml | `project-state.py verify` 通过 | P0 |
| AC-07 | 101 测试仍然全绿 | `pytest scripts/tests/ -q` 通过 | P0 |
