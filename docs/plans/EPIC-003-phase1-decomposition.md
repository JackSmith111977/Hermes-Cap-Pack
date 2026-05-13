# EPIC-003 Phase 1 Story 分解方案

> **关联 EPIC**: EPIC-003-module-extraction.md
> **状态**: `clarify`（等待主人确认后创建正式 Story）

---

## Phase 1 全景

```
Phase 1 (P0): 3 个模块 / ~42 skills
  ├── STORY-3-1: developer-workflow  (~20 skills)
  ├── STORY-3-2: agent-orchestration (~10 skills)
  └── STORY-3-3: metacognition       (~12 skills)
```

## STORY-3-1: developer-workflow 模块提取

### 覆盖的 Hermes skill

| 源目录 | Skill 数 | 包含内容 |
|:-------|:--------:|:---------|
| `software-development/` | 13 | TDD、debugging、subagent、code-review、spike、writing-plans、plan、python-env、python-debugpy、node-inspect、patch-file-safety、requesting-code-review、hermes-agent-skill-authoring |
| `dogfood/sdd-workflow` | 1 | SDD 工作流全生命周期管理 |
| `dogfood/generic-dev-workflow` | 1 | 通用 7 步开发流程 |
| `dogfood/sprint-planning` | 1 | Sprint 规划方法论 |
| `dogfood/development-workflow-index` | 1 | 开发工作流决策树索引 |
| `communication/` | 1 | 1-3-1 决策框架 |
| 其他零散 | ~2 | 待盘点时确认 |

### 6 步 SOP 计划

```
Step 1: 盘点 → 逐个 skill 读取 description + triggers
Step 2: 质检 → SQS 五维评分（完整性/清晰度/可操作性/时效性/可维护性）
Step 3: 合并 → 识别重复（如 TDD 相关可能有重叠）
Step 4: 提取 → 创建 packs/developer-workflow/cap-pack.yaml
Step 5: 补全 → 添加交叉引用、经验文档
Step 6: 验证 → validate-pack.py + CLI 安装测试
```

### 不做的范围
- ❌ 修改 skill 本身的内容（仅提取，不改造）
- ❌ MLOps、creative-design 等其他模块

## STORY-3-2: agent-orchestration 模块提取

### 覆盖的 Hermes skill

| 源目录 | Skill 数 | 包含内容 |
|:-------|:--------:|:---------|
| `autonomous-ai-agents/` | 7 | Claude Code、Codex、OpenCode、Blackbox、Honcho、hermes-agent |
| `bmad-party-mode-orchestration` | 1 | 多智能体编排 |
| `dogfood/anti-repetition-loop` | 1 | 防重复循环检测 |
| `dogfood/hermes-message-injection` | 1 | 消息注入（SRA 相关） |

### 关键设计决策
- 此 pack 的 MCP 配置丰富（多个 Agent 的 MCP 配置）
- 需要调研各 Agent 的 MCP 配置格式

## STORY-3-3: metacognition 模块提取

### 覆盖的 Hermes skill

| 源目录 | Skill 数 | 包含内容 |
|:-------|:--------:|:---------|
| `dogfood/self-review` | 1 | 自我审查 |
| `dogfood/memory-management` | 1 | 记忆管理 |
| `dogfood/hermes-self-analysis` | 1 | 自我分析 |
| `dogfood/information-decomposition` | 1 | 信息分解 |
| `dogfood/file-classification` | 1 | 文件分类 |
| `dogfood/file-system-manager` | 1 | 文件系统管理 |
| `dogfood/analysis-workflow` | 1 | 大文件分析工作流 |
| `dogfood/adversarial-ux-test` | 1 | 对抗性 UX 测试 |
| `dogfood/browser-automation` | 1 | 浏览器自动化 |
| `meta/skill-creator` | 1 | 技能创作 |
| `meta/self-capabilities-map` | 1 | 能力认知地图 |
| `skill-to-pypi` | 1 | skill 转 PyPI 包 |

---

## 实施顺序

```
Week 1: STORY-3-1 developer-workflow  → 盘点 + 质检 + 提取 + 验证
Week 2: STORY-3-2 agent-orchestration → 盘点 + 质检 + 提取 + 验证
Week 3: STORY-3-3 metacognition       → 盘点 + 质检 + 提取 + 验证
```

每个 Story 完成后，产出一个可安装的 cap-pack + SQS 质检报告。
