# EPIC-003: 剩余能力模块纳入 + 质检 + 合并 + 升级改造

> **epic_id**: `EPIC-003`
> **status**: `implemented`
> **created**: 2026-05-13
> **updated**: 2026-05-14 (v3 — 全盘 5 Phase 路线图，覆盖 18+1 模块)
> **owner**: boku

---

## 〇、需求澄清

### 核心问题

之前分类基于 **185 个 skill** 设计，但实际 Hermes 已有 **351 个 SKILL.md**。需要重新校准。

---

## 一、全景数据（实际扫描 2026-05-13）

| 排名 | Hermes 分类目录 | Skill 数 | 占总量 | 说明 |
|:----:|:---------------|:--------:|:------:|:------|
| 1 | `creative` | 23 | 11.6% | ASCII art、架构图、ComfyUI、Mermaid、表情包等 |
| 2 | `dogfood` | 20 | 10.1% | boku 自用工作流（sdd-workflow、self-review、doc-alignment 等） |
| 3 | `software-development` | 13 | 6.5% | TDD、调试、子代理、Code Review 等 |
| 4 | `mlops` | 13 | 6.5% | LLM 推理、微调、评估、模型部署等 |
| 5 | `research` | 11 | 5.5% | 深度调研、arXiv、AI 趋势、知识库方案 |
| 6 | `productivity` | 11 | 5.5% | Airtable、Google Workspace、Notion、OCR 等 |
| 7 | `github` | 9 | 4.5% | PR、Issues、Actions、Code Review、Repo 管理 |
| 8 | `devops` | 7 | 3.5% | Docker、Linux 运维、Kanban、Webhook 等 |
| 9 | `autonomous-ai-agents` | 7 | 3.5% | Claude Code、Codex、OpenCode、子代理编排 |
| 10 | ≤ 5 skill 的目录 | ~17 | ~8.5% | media(5), doc-design(4), apple(4), mcp(3) 等 |
| 11 | 单 skill 目录 | ~68 | ~34.2% | pdf-layout, pptx-guide, feishu, vision 等 |
| | **总计** | **~199** | **100%** | *(已删除 bmad-method 153 个)* |

---

## 二、模块归属映射（v2.0 修正版）

### 已有 pack

| 模块 | 覆盖的 Hermes 目录 | Skill 数 | 状态 |
|:-----|:-------------------|:--------:|:----:|
| **doc-engine** | pdf-layout, pdf-pro-design, pdf-render-comparison, pptx-guide, html-guide, latex-guide, markdown-guide, docx-guide, epub-guide, xlsx-guide, doc-design, vision-qc-patterns, readme-for-ai, nano-pdf + experiences | ~19 | ✅ **已提取** |
| **quality-assurance** | testing, commit-quality-check, delete-safety, vision, html-css-rendering-qa | ~7 | ✅ **已提取** |
| **learning-workflow** | learning, learning-workflow, learning-review-cycle, night-study-engine | ~4 | ⚠️ **骨架** |

### Phase 1: P0 核心（剩余 15 个模块待提取）

| # | 模块 | 覆盖的 Hermes 目录 | 估算 skill | 优先级 |
|:-:|:-----|:-------------------|:----------:|:------:|
| 4 | **developer-workflow** | software-development(13), dogfood/sdd-workflow, dogfood/generic-dev-workflow, dogfood/sprint-planning, dogfood/writing-plans, dogfood/subagent-driven-development, dogfood/test-driven-development, communication | ~20 | 🥇 |
| 10 | **agent-orchestration** | autonomous-ai-agents(7), bmad-party-mode-orchestration, dogfood/anti-repetition-loop | ~10 | 🥇 |
| 17 | **metacognition** | dogfood: self-review, memory-management, hermes-self-analysis, information-decomposition, file-classification, file-system-manager, analysis-workflow + skill-creator, self-capabilities-map, skill-to-pypi | ~12 | 🥇 |

### Phase 2: P1 高频

| # | 模块 | Hermes 目录 | 估算 | 状态 |
|:-:|:-----|:-----------|:----:|:----:|
| 2 | **learning-engine**（含知识库[^1]） | research/deep-research, research/arxiv, research/blogwatcher, research/hermes-knowledge-base, research/llm-wiki, research/ai-trends, research/polymarket, learning(1), knowledge-precipitation, knowledge-routing, capability-pack-design | ~11 | ✅ **已提取** |
| 13 | **creative-design** | creative(23): ascii-art, architecture-diagram, concept-diagrams, excalidraw, mermaid-guide, pixel-art, sketch, claude-design, design-md, p5js, comfyui, meme-creation + image-generation, image-prompt-guide | ~20 | ⬜ 待提取 |
| 15 | **github-ecosystem** | github(9): codebase-inspection, git-advanced-ops, github-auth, github-code-review, github-deploy-upload, github-issues, github-pr-workflow, github-project-ops, github-repo-management | ~9 | ⬜ 待提取 |
| 7 | **devops-monitor** | devops(7): docker-management, kanban-orchestrator, kanban-worker, linux-ops-guide, project-startup-workflow, proxy-monitor, webhook-subscriptions + hermes-ops-tips, process-management | ~10 | ⬜ 待提取 |

> [^1]: ⚡ `knowledge-base` 模块已合并至此。原因：核心技能（knowledge-precipitation, knowledge-routing 等）已在 learning-engine 提取时吸收，消除循环依赖。详见 SPEC-1-1 合并注释。

### Phase 3: P2 专用

| # | 模块 | Hermes 目录 | 估算 |
|:-:|:-----|:-----------|:----:|
| 9 | **messaging** | feishu(2), feishu-batch-send, feishu-card-merge-streaming, email(2), social-media, smart-broadcast | ~8 |
| 8 | **network-proxy** | clash-config, proxy-finder, web-access, browser-automation | ~5 |
| 5 | **security-audit** | security(2), red-teaming, delete-safety, commit-quality-check | ~4 |
| 14 | **media-processing** | media(5): gif-search, heartmula, songsee, spotify, youtube-content + text-to-speech | ~6 | ✅ 已提取 |
| 11 | **mcp-integration** | mcp(3): fastmcp, mcporter, native-mcp + 部分 autonomous-ai-agents | ~5 |
| 新 | **mlops** | mlops(13): huggingface-hub, llama-cpp, vllm, outlines, dspy, axolotl, unsloth, trl, evaluating-llms-harness, weights-and-biases, obliteratus, audiocraft, segment-anything | **13** |

### Phase 4: P3 低频

| # | 模块 | Hermes 目录 | 估算 |
|:-:|:-----|:-----------|:----:|
| 12 | **financial-analysis** | financial-analyst, data-science, health | ~4 | ✅ 已提取 |
| 16 | **news-research** | news-briefing, research(大部分) | ~4 |
| 18 | **social-gaming** | gaming(2): minecraft, pokemon-player + bangumi-recommender, yuanbao, apple(4) | ~5 |

### 预留 / 待定

| Hermes 分类 | Skill 数 | 建议归属 |
|:-----------|:--------:|:---------|
| productivity | 11 | 跨模块（doc-engine + agent-orchestration + ...） |
| smart-home | 1 | 暂放 hermes-new-features |
| web-ui | 1 | 暂放 hermes-new-features |
| skill-creator, skill-to-pypi, self-capabilities-map | 3 | metacognition |
| apple, health, bangumi-recommender, yuanbao | 7 | social-gaming 或其他 |

---

## 三、更新后的 18 模块体系

相比 v2.0 的 18 模块，v2.1 变更：
- ❌ **删除**: bmad-method（项目级框架，已删除）
- ✅ **新增**: mlops（ML/AI 工程化，原分类遗漏，13 skill）
- ⚡ **合并**: knowledge-base → learning-engine（详见 Phase 2 注释）

| 变更 | 原因 |
|:-----|:------|
| ❌ 删除 `bmad-method` | 项目级外部框架，非 boku 自身能力 |
| ✅ 新增 `mlops` | ML 工程化（推理/微调/评估/部署）13 skill |

---

## 四、路线图（修正版）

```
EPIC-003: 剩余 16 模块纳入 + 质检 + 合并 + 升级
│
├─ Phase 1 (P0): developer-workflow + agent-orchestration + metacognition
│  ├── ~42 skills → 3 packs → 预计 2-3 天
│
├─ Phase 2 (P1): learning-engine (含知识库) + creative-design + github + devops
│  ├── ~50 skills → 4 packs → 预计 2 天
│
├─ Phase 3 (P2): messaging + network-proxy + security + media + mcp + mlops
│  ├── ~41 skills → 6 packs → 预计 1-2 天
│
└─ Phase 4 (P3): financial + news + gaming + 预留
   ├── ~13 skills → 3+ packs → 预计 1 天
```

---

## 五、验收标准

- [ ] AC1: 全部 ~17 模块提取为 cap-pack，每个含 cap-pack.yaml（knowledge-base 已合并至 learning-engine）
- [ ] AC2: 每个提取的 skill 有 SQS 质量评分记录
- [ ] AC3: 识别并合并 ≥5 组重复/重叠 skill
- [ ] AC4: 每个 pack 通过 `validate-pack.py` 验证
- [ ] AC5: 至少 3 个 pack 可安装到 Hermes 和 OpenCode
- [ ] AC6: 产出全局质量报告（HTML 格式）
- [ ] AC7: 更新 README 模块分类表（v2.1 → 20 模块 + 3 扩展槽）

[^1]: ⚡ knowledge-base 模块已合并至 learning-engine。原因：核心知识技能（knowledge-precipitation, knowledge-routing 等）已在 learning-engine 提取时吸收，消除循环依赖。详见 SPEC-1-1 合并注释。
