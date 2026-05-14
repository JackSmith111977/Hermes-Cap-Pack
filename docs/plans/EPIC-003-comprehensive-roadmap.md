# 🗺️ EPIC-003 全盘提取路线图

> **状态**: `clarify` → **本文件已替代旧的 `EPIC-003-phase1-decomposition.md`**
> **创建**: 2026-05-14 · **更新**: 2026-05-14
> **覆盖**: 18 模块全部提取路线 + 3 扩展槽

---

## 一、全景一览

| 模块 ID | 名称 | 预估 skills | 已有包 | 优先级 | 复杂度 | 依赖 |
|:--------|:-----|:----------:|:------:|:------:|:------:|:-----|
| doc-engine | 📄 文档生成 | 13 | ✅ 已提取 | 🏁 | ★★☆ | — |
| quality-assurance | ✅ 质量保障 | 4 | ✅ 已提取 | 🏁 | ★☆☆ | — |
| learning-workflow | 🧠 学习流程 | 1 | ✅ 已提取 | 🏁 | ★★☆ | — |
| **developer-workflow** | 💻 开发工作流 | 16 | ⬜ | 🔴 P0 | ★★★ | knowledge-base |
| **agent-orchestration** | 🤖 Agent 协作 | 8 | ⬜ | 🔴 P0 | ★★☆ | mcp-integration |
| **metacognition** | 🪞 元认知系统 | 6+ | ⬜ | 🔴 P0 | ★★☆ | — |
| **creative-design** | 🎨 创意设计 | 27 | ⬜ | 🟡 P1 | ★★★ | media-processing |
| **learning-engine** | 🧠 学习引擎 | 15 | ⬜ | 🟡 P1 | ★★☆ | — |
| **github-ecosystem** | 🐙 GitHub 生态 | 9 | ⬜ | 🟡 P1 | ★☆☆ | — |
| **messaging** | 💬 消息平台 | 9 | ⬜ | 🟡 P1 | ★★☆ | — |
| **devops-monitor** | 🔧 运维监控 | 9 | ⬜ | 🟢 P2 | ★☆☆ | — |
| **security-audit** | 🔒 安全审计 | 5 | ⬜ | 🟢 P2 | ★☆☆ | — |
| **media-processing** | 🎵 音视频媒体 | 5 | ⬜ | 🟢 P2 | ★☆☆ | creative-design |
| **mcp-integration** | 🔌 MCP 集成 | 3 | ⬜ | 🟢 P2 | ★☆☆ | — |
| **network-proxy** | 🌐 网络代理 | 3 | ⬜ | 🔵 P3 | ★☆☆ | — |
| **news-research** | 📰 新闻研究 | 2 | ⬜ | 🔵 P3 | ★☆☆ | — |
| **financial-analysis** | 📊 金融分析 | 2 | ⬜ | 🔵 P3 | ★☆☆ | data-science |
| **social-gaming** | 🎮 社交娱乐 | 4 | ⬜ | 🔵 P3 | ★☆☆ | — |
| knowledge-base | 📚 知识库系统 | 3 | ⬜ | 🟣 P4 | ★★☆ | — |
| **预留: hermes-new-features** | 🆕 | — | ⬜ | ⏳ | — | — |
| **预留: custom-plugin** | 🔌 | — | ⬜ | ⏳ | — | — |
| **预留: future-domain** | 🔮 | — | ⬜ | ⏳ | — | — |

---

## 二、Phase 分配

### 🔴 Phase 0 — 快速补完（当前 Sprint 4）
已完成 3 个包，跑通全流程：

```
✅ doc-engine      → 13 skills, 验证通过
✅ quality-assurance → 4 skills, 基线建立
✅ learning-workflow → 1 skill, 状态机集成

产出: 提取 SOP 标准化 + validate-pack.py + CI 门禁
```

### 🔴 Phase 1 — 核心自引用模块（P0, ~30 skills）
**依赖**: 其他模块提取时这些包本身会被用到

| Story | 模块 | Skills | 预计 | 依赖 |
|:------|:-----|:------:|:----:|:-----|
| **STORY-3-1** | developer-workflow | 16 | 1天 | — |
| **STORY-3-2** | agent-orchestration | 8 | 1天 | mcp-integration (先提取) |
| **STORY-3-3** | metacognition | 6 | 1天 | — |

**6 步 SOP 验证通过后推广到后续 Phase。**

### 🟡 Phase 2 — 高价值模块（P1, ~60 skills）
**依赖**: Phase 1 完成，SOP 已成熟

| Story | 模块 | Skills | 预计 | 备注 |
|:------|:-----|:------:|:----:|:-----|
| STORY-3-4 | creative-design | 27 | 2天 | 最大包，含 dogfood 部分 skill |
| STORY-3-5 | learning-engine | 15 | 1天 | 含 night-study, deep-research |
| STORY-3-6 | github-ecosystem | 9 | 0.5天 | 边界清晰 |
| STORY-3-7 | messaging | 9 | 1天 | 多平台适配 |

### 🟢 Phase 3 — 中等优先级（P2, ~22 skills）

| Story | 模块 | Skills | 预计 |
|:------|:-----|:------:|:----:|
| STORY-3-8 | devops-monitor | 9 | 0.5天 |
| STORY-3-9 | security-audit | 5 | 0.5天 |
| STORY-3-10 | media-processing | 5 | 0.5天 |
| STORY-3-11 | mcp-integration | 3 | 0.5天 |

### 🔵 Phase 4 — 低优先级（P3, ~11 skills）

| Story | 模块 | Skills | 预计 |
|:------|:-----|:------:|:----:|
| STORY-3-12 | network-proxy | 3 | 0.5天 |
| STORY-3-13 | news-research | 2 | 0.5天 |
| STORY-3-14 | financial-analysis | 2 | 0.5天 |
| STORY-3-15 | social-gaming | 4 | 0.5天 |

### 🟣 Phase 5 — 收尾（P4, ~3 skills + 扩展槽）

| Story | 模块 | Skills | 预计 |
|:------|:-----|:------:|:----:|
| STORY-3-16 | knowledge-base | 3 | 0.5天 |
| STORY-3-17 | 跨模块清理 + 扩展槽配置 | 残余 | 1天 |

---

## 三、依赖关系图

```
Phase 1                  Phase 2               Phase 3              Phase 4
┌─────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│ developer-   │──→  │ creative-    │     │ devops-      │     │ network-     │
│ workflow    │     │ design       │←──  │ monitor      │     │ proxy        │
└─────────────┘     └──────────────┘     └──────────────┘     └──────────────┘
┌─────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│ agent-       │←──  │ learning-    │     │ security-    │     │ news-        │
│ orchestration│     │ engine       │     │ audit        │     │ research     │
└──────┬───────┘     └──────────────┘     └──────────────┘     └──────────────┘
       │           ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
       └──────────→│ github-      │     │ media-       │     │ financial-   │
                   │ ecosystem    │     │ processing   │──→  │ analysis     │
                   └──────────────┘     └──────┬───────┘     └──────────────┘
                   ┌──────────────┐          │             ┌──────────────┐
                   │ messaging    │     ┌──────────────┐  │ social-      │
                   └──────────────┘     │ mcp-         │  │ gaming       │
                                        │ integration  │  └──────────────┘
                   ┌──────────────┐     └──────────────┘
                   │ metacognition│     
                   └──────────────┘     ┌──────────────┐
                                        │ knowledge-   │
                                        │ base         │
                                        └──────────────┘
```

---

## 四、提取 SOP（每个模块标准化 6 步）

```
Step 1 ── 盘点
  读取 Hermes skill 目录下每个 SKILL.md 的 description + triggers
  输出: 候选技能清单

Step 2 ── 质检
  SQS 五维评分（结构/内容/时效/关联/发现）
  标记 < 60 分的 skill 为"需改进"

Step 3 ── 合并
  识别重复/重叠 skill（用 skill-tree-index.py --consolidate）
  输出: 合并建议

Step 4 ── 提取
  创建 packs/<module-id>/cap-pack.yaml
  复制 skill 到 SKILLS/ 目录
  编写经验文档到 EXPERIENCES/

Step 5 ── 补全
  添加 MCP 配置（如有）
  添加交叉引用
  更新分类映射表 cap-pack-categories.yaml

Step 6 ── 验证
  validate-pack.py 完整性验证
  python3 scripts/ci-check-cross-refs.py 引用检查
  python3 scripts/project-state.py verify 状态同步

  门禁: 全部绿色后才能 Merge
```

---

## 五、状态机跟踪

```yaml
# 在 project-state.yaml 中注册所有新 Story
entities:
  stories:
    STORY-3-1: { state: draft, epic: EPIC-003, spec: SPEC-3-1 }
    STORY-3-2: { state: draft, epic: EPIC-003, spec: SPEC-3-1 }
    STORY-3-3: { state: draft, epic: EPIC-003, spec: SPEC-3-1 }
    STORY-3-4: { state: draft, epic: EPIC-003, spec: SPEC-3-2 }
    ...
```

每次完成一个 Story → `project-state.py transition STORY-3-1 completed "..."` → 自动同步 YAML。

---

## 六、关键指标

| 指标 | 当前 | Phase 1 后 | 全部完成后 |
|:-----|:----:|:----------:|:----------:|
| 已提取模块 | 3/18 | 6/18 | 18/18 |
| 已提取 skills | ~20 | ~50 | ~160+ |
| 覆盖 skill 比例 | ~12% | ~30% | ~85%+ |
| 新增 cap-pack.yaml | 3 | 6 | 18 |
| SQS 覆盖 skills | 201 | 201 | 201 |
