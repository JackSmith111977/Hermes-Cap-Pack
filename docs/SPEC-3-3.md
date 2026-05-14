# 📋 SPEC-3-3: Phase 2 高频能力包提取

> **状态**: `draft` · **优先级**: P1 · **创建**: 2026-05-14
> **关联 Epic**: EPIC-003-module-extraction.md
> **前序**: Phase 1 (3 pack) ✅ → Phase 2 (5 pack) 🆕

---

## 〇、需求澄清

### 用户故事

> **As a** 主人
> **I want** 将剩余高频 Hermes 能力模块提取为标准 v2 能力包
> **So that** 覆盖率从 37% 提升至 ~65%，更多技能可跨 Agent 复用

### Scope

| In Scope | Out of Scope |
|:---------|:-------------|
| ✅ Phase 2 的 5 个模块提取 | ❌ Phase 3-4 的模块（messaging, mlops 等） |
| ✅ 每个包完整 cap-pack.yaml + 素材 | ❌ skill 内容修改（仅提取，不改原文） |
| ✅ SQS 质量评分基线 | ❌ 跨 Agent 适配器修改 |
| ✅ 包间交叉引用检测 | ❌ Git 推送部署 |

---

## 一、5 个待提取模块

### 1. learning-engine (~8 skills)

| 源目录 | Skills | 说明 |
|:-------|:-------|:-----|
| `research/deep-research` | 1 | 深度调研工作流 |
| `research/arxiv` | 1 | 论文搜索与检索 |
| `research/blogwatcher` | 1 | RSS/Blog 监控 |
| `research/hermes-knowledge-base` | 1 | 知识库构建方案 |
| `research/llm-wiki` | 1 | Karpathy LLM Wiki |
| `research/ai-trends` | 1 | AI 前沿趋势追踪 |
| `research/polymarket` | 1 | 预测市场查询 |
| `learning/learning` | 1 | 学习原子技能 |
| `knowledge-precipitation` | 1 | 三层知识库维护 |
| `knowledge-routing` | 1 | 知识路由决策 |
| *可能还需*: `capability-pack-design` | 1 | 能力包设计方法 |

### 2. creative-design (~20 skills)

| 源目录 | 估算 | 说明 |
|:-------|:----:|:------|
| `creative/ascii-art` | 1 | pyfiglet ASCII |
| `creative/architecture-diagram` | 1 | SVG 架构图 |
| `creative/concept-diagrams` | 1 | 概念图 |
| `creative/excalidraw` | 1 | 手绘风图表 |
| `creative/mermaid-guide` | 1 | Mermaid 图表 |
| `creative/pixel-art` | 1 | 像素画 |
| `creative/sketch` | 1 | HTML 原型 |
| `creative/claude-design` | 1 | 设计 artifacts |
| `creative/design-md` | 1 | DESIGN.md |
| `creative/p5js` | 1 | 交互式视觉 |
| `creative/comfyui` | 1 | ComfyUI 工作流 |
| `creative/meme-creation` | 1 | 表情包制作 |
| `creative/image-generation` | 1 | 图片生成 |
| `creative/image-prompt-guide` | 1 | Prompt 编写 |
| `creative/humanizer` | 1 | 去 AI 味 |
| `creative/baoyu-comic` | 1 | 知识漫画 |
| `creative/baoyu-infographic` | 1 | 信息图 |
| `creative/ideation` | 1 | 创意发散 |
| `creative/visual-aesthetics` | 1 | 审美指南 |
| `creative/songwriting-and-ai-music` | 1 | AI 音乐 |
| `creative/touchdesigner-mcp` | 1 | TouchDesigner |

### 3. github-ecosystem (~9 skills)

| 源目录 | Skills |
|:-------|:-------|
| `github/codebase-inspection` | 1 |
| `github/git-advanced-ops` | 1 |
| `github/github-auth` | 1 |
| `github/github-code-review` | 1 |
| `github/github-deploy-upload` | 1 |
| `github/github-issues` | 1 |
| `github/github-pr-workflow` | 1 |
| `github/github-project-ops` | 1 |
| `github/github-repo-management` | 1 |

### 4. devops-monitor (~10 skills)

| 源目录 | Skills |
|:-------|:-------|
| `devops/docker-management` | 1 |
| `devops/kanban-orchestrator` | 1 |
| `devops/kanban-worker` | 1 |
| `devops/linux-ops-guide` | 1 |
| `devops/project-startup-workflow` | 1 |
| `devops/proxy-monitor` | 1 |
| `devops/webhook-subscriptions` | 1 |
| `dogfood/process-management` | 1 |
| `hermes-ops-tips` | 1 |
| `docker-terminal` | 1 |

### 5. learning-engine（含 knowledge-base 合并）

> ⚡ knowledge-base 已合并至此模块。详见 SPEC-1-1 合并注释。

#### 源 skills 清单（~11 skills）

| 源目录 | Skills | 说明 |
|:-------|:-------|:-----|
| `research/deep-research` | 1 | 深度调研工作流 |
| `research/arxiv` | 1 | 论文搜索与检索 |
| `research/blogwatcher` | 1 | RSS/Blog 监控 |
| `research/hermes-knowledge-base` | 1 | 知识库构建方案（知识库合并） |
| `research/llm-wiki` | 1 | Karpathy LLM Wiki（知识库合并） |
| `research/ai-trends` | 1 | AI 前沿趋势追踪 |
| `research/polymarket` | 1 | 预测市场查询 |
| `learning/learning` | 1 | 学习原子技能 |
| `knowledge-precipitation` | 1 | 三层知识库维护（知识库合并） |
| `knowledge-routing` | 1 | 知识路由决策（知识库合并） |
| `capability-pack-design` | 1 | 能力包设计方法 |

---

## 二、执行计划

### 每个模块的提取 SOP

```
① 盘点 (Inventory) → 确定 Hermes 中实际 skill 文件位置
② SQS 质检 → 记录基线质量分
③ 合并去重 → 识别重叠 skill（预留步骤）
④ 提取 → 创建 cap-pack.yaml + 复制 skill 到 SKILLS/ 目录
⑤ 补全 → verification/integration/behavior 等 v2 字段
⑥ 验证 → cap-pack-v2.schema.json 验证通过
```

### 执行顺序

> ⚡ knowledge-base 已合并至 learning-engine（详见 SPEC-1-1 合并注释）

```
[Day 1] learning-engine（含知识库）→ ~11 skills → 预计 3h ✅ 已完成
[Day 2] creative-design     → ~20 skills → 预计 4h
[Day 2] github-ecosystem    → ~9 skills  → 预计 2h
[Day 3] devops-monitor      → ~10 skills → 预计 2h
[Day 3] 全局验证 + 交叉引用  → 全部 4 pack → 预计 1h
```

---

## 三、验收标准

|| AC ID | 描述 | 优先级 |
||:------|:-----|:------:|
|| AC-01 | learning-engine（含知识库）cap-pack.yaml + SKILLS/ 完整 | P1 |
|| AC-02 | creative-design cap-pack.yaml + SKILLS/ 完整 | P1 |
|| AC-03 | github-ecosystem cap-pack.yaml + SKILLS/ 完整 | P1 |
|| AC-04 | devops-monitor cap-pack.yaml + SKILLS/ 完整 | P1 |
|| AC-05 | ~~knowledge-base~~ → 已合并至 AC-01（learning-engine） | 🗑️ |
|| AC-06 | 全部 4 pack 通过 v2 schema 验证 | P0 |
|| AC-07 | 覆盖率提升: 37% → ~65% (8/17 → 12/17) | P1 |
| AC-08 | 无断裂引用（dependency-scan 全绿） | P1 |

---

## 四、风险

| 风险 | 概率 | 影响 | 缓解 |
|:-----|:----:|:----:|:-----|
| creative-design 20 skill 太多 | 中 | 提取耗时 | 先提取核心 10 个，其余分批 |
| learning-engine 与 knowledge-base 重叠 | 高 | 重复 | 共享 skill 用 source 引用 |
| 部分 skill 已过时/断裂 | 低 | 低 | SQS 记录即可，不改内容 |
