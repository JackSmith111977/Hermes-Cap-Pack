# EPIC-005: Skill 治理引擎 — 技能全生命周期质量门禁与 Cap-Pack 自动适配

> **epic_id**: `EPIC-005`
> **status**: `approved`
> **created**: 2026-05-16
> **updated**: 2026-05-16
> **owner**: boku (Emma)
> **优先级**: P1 — 治理是 cap-pack 生态成熟的关键一环
> **估算**: ~30h（4 Phases · ~15 Stories）
> **前置条件**: EPIC-004 质量升级完成（CHI 门禁 + 质量基准已锁定）

---

## 〇、动机与背景

### 为什么需要 Skill 治理引擎？

当前 cap-pack 项目的 Skill 质量管理存在以下问题：

| 问题 | 影响 | 根因 |
|:-----|:------|:------|
| 🔍 **Skill 发现全靠 boku 手动** | 新技能→需要手动检查是否合规→容易遗漏 | 无自动化扫描机制 |
| 🌳 **树状结构靠自觉维护** | skill-tree-index 需手动触发→游离 skill 增多 | 无强制树归属门禁 |
| 🔄 **工作流编排不检测** | 有编排能力的 skill 未被识别→SRA 推荐不准确 | 无编排检测器 |
| 📦 **Cap-Pack 合规靠人工审查** | 新 skill 加入 cap-pack 需要主人+ boku 手动评估 | 无自动合规检查 |
| 🛠️ **适配改造靠手动** | 新 skill 需要手工改 cap-pack.yaml→耗时且易出错 | 无自动适配器 |

### 行业调研结论

2025-2026 年 Agent Skill 治理赛道已涌现 **12+ 个工具**（skill-validator / skill-guard / SkillCompass / Skilldex / skill-tree 等），但 **没有任何工具覆盖以下三个维度**：

| 维度 | 现有工具 | 差距 |
|:-----|:---------|:-----|
| Cap-Pack 合规检测 | ❌ 空白 | **最大差异化** — cap-pack 特有的质量维度 |
| 工作流编排检测 | ❌ 空白 | 完全未被其他工具覆盖 |
| 自动适配改造 | ❌ 空白 | 所有工具只报告问题，不自动修复 |

**核心价值**：现有工具做「发现问题→报告问题」，我们做「发现问题→报告问题→自动适配到 Cap-Pack 标准」。

详细调研报告见：`docs/research/EPIC-005-skill-governance-research.md`

---

## 一、解决方案全景

### 架构设计：三层分离

```
┌──────────────────────────────────────────┐
│  Layer 3: Agent 适配层                    │
│  HermesAdapter / OpenCodeAdapter /        │ ─── 可插拔
│  ClaudeAdapter / MCP Server               │
├──────────────────────────────────────────┤
│  Layer 2: 治理引擎核心 (核心产出)          │
│  Scanner → Watcher → Adapter → Reporter  │ ─── 平台无关
├──────────────────────────────────────────┤
│  Layer 1: Cap-Pack 规范层 (已有积累)       │
│  Schema / 质量标准 / 树结构 / 工作流定义   │ ─── 项目定制
```

### 七维检测引擎

| 检测维度 | 说明 | 创新度 |
|:---------|:-----|:------:|
| ① **原子性扫描** | 基于四问测试判断 skill 是否原子化 | ⚡ 整合现有 |
| ② **树状结构检查** | 检查 skill 是否有簇归属、簇大小是否合理 | ⚡ 整合 skill-tree |
| ③ **工作流编排检测** | 检测 SKILL.md 的编排声明（pipeline/DAG/depends_on） | 🔥 **新维度** |
| ④ **Cap-Pack 合规检查** | 对照 cap-pack-v2 schema 检查是否符合包标准 | 🔥 **新维度** |
| ⑤ **新增检测 (Watcher)** | 定时扫描 + fingerprint 对比 → 自动触发检查链 | ⚡ 整合 |
| ⑥ **质量测试** | SQS + CHI + 冲突检测 + 链接有效性 | ⚡ 整合现有 |
| ⑦ **自动适配改造** | 自动分类 → 匹配包 → 生成 cap-pack.yaml 条目 | 🔥 **新维度** |

---

## 二、Phase 计划

### Phase 0 — 统一标准制定（前置条件 · 3 Stories · ~6h）

> **门禁**: Phase 0 未完成 → Phase 1-3 不能启动。标准是治理引擎的根基。

| Story | 内容 | 估算 | 产出物 |
|:------|:-----|:----:|:-------|
| STORY-5-0-1 | **制定四层统一标准** — 基于行业研究，定义 L0-L4 各层规则 | 2h | `docs/CAP-PACK-STANDARD.md` 正式标准文档 |
| STORY-5-0-2 | **创建 machine-checkable 规则集** — 将标准翻译为 JSON/YAML 规则，更新 v3 schema | 2h | `schemas/cap-pack-v3.schema.json` + `standards/rules.yaml` |
| STORY-5-0-3 | **Workflow 编排模式定义** — Layer 4 的 DAG/顺序/条件/并行模式规范 | 2h | `standards/workflow-patterns.md` + workflow schema |

**Phase 0 验收标准：**
- [x] CAP-PACK-STANDARD.md 覆盖 L0-L4 全部四层
- [x] 每层有明确的 machine-checkable 规则（JSON/YAML 格式）
- [x] Layer 4 workflow 模式支持 sequential/parallel/conditional/dag
- [x] 标准通过主人审阅批准

### Phase 1 — 核心引擎 MVP（4 Stories · ~10h）

> **目标**: 对照 Phase 0 的标准实现检测器 CLI

| Story | 内容 | 估算 | 产出物 |
|:------|:-----|:----:|:-------|
| STORY-5-1-1 | **L1 基础检测器 + L2 健康检测器** | 3h | `scanner/l1_foundation.py`, `scanner/l2_health.py` |
| STORY-5-1-2 | **L3 生态检测器 + L4 编排检测器** | 3h | `scanner/l3_ecosystem.py`, `scanner/l4_workflow.py` |
| STORY-5-1-3 | **CLI 工具 + JSON/HTML 报告** | 2h | `cli/skill-governance.py` + Reporter 类 |
| STORY-5-1-4 | **新增 Skill Watcher（cron + fingerprint）** | 2h | `watcher/fingerprint.py` + cron 任务注册 |

**Phase 1 验收标准：**
- [x] CLI `skill-governance scan <path>` 按四层输出检测结果
- [x] 每层有独立的 pass/fail + 分数
- [x] `--json` 和 `--html` 输出格式
- [x] watcher 可检测新 skill 并触发全链路检查

### Phase 2 — Hermes 深度集成 + 自动适配（4 Stories · ~10h）✅

| Story | 内容 | 估算 | 产出物 |
|:------|:-----|:----:|:-------|
| STORY-5-2-1 | **Hermes pre_flight gate 集成（四层门禁）** | 2h | `pre_flight` 新增 governance gate |
| STORY-5-2-2 | **SRA 质量注入 + 编排感知推荐** | 2h | `sqs-sync.py` 扩展 + workflow 感知权重 |
| STORY-5-2-3 | **自动适配改造引擎（dry-run → 确认 → 执行）** | 4h | `adapter/cap-pack-adapter.py` |
| STORY-5-2-4 | **cron 定时扫描 + 报告推送** | 2h | cron 注册 + 飞书消息推送 |

**Phase 2 验收标准：**
- [x] pre_flight.py 新增 governance gate，对变更 skill 自动扫描 L0+L1
- [x] SRA 推荐权重包含 SQS 质量分 + 编排感知因子
- [x] 自动适配引擎支持 scan/suggest/dry_run/apply 四步流程
- [x] 每日 cron 扫描 + 飞书推送合规报告
- [x] 以上全部通过 SDD→DEV→QA→COMMIT 完整链式验证

### Phase 3 — 多 Agent 适配层（3 Stories · ~6h）✅ 已完成

| Story | 内容 | 估算 | 产出物 |
|:------|:-----|:----:|:-------|
| STORY-5-3-1 | **适配器抽象层 + OpenCode 适配器** | 2h | `adapter/base.py`, `adapter/opencode_adapter.py` |
| STORY-5-3-2 | **MCP Server 暴露治理 + 编排能力** | 2h | `mcp/skill-governance-server.py` |
| STORY-5-3-3 | **OpenClaw / Claude Code 适配器** | 2h | `adapter/openclaw_adapter.py`, `adapter/claude_adapter.py` |

**Phase 3 验收标准：**
- [x] `adapter/base.py` 定义 SkillGovernanceAdapter 抽象基类（6 个抽象方法）
- [x] OpenCode/OpenClaw/Claude 三个适配器全部继承基类并实现全部方法
- [x] HermesAdapter 重构为继承 SkillGovernanceAdapter（向后兼容）
- [x] MCP Server 暴露 5 个 tools + 3 个 resources
- [x] 全部 141 测试通过
- [x] 以上全部通过联合工作流 SPEC→DEV→QA→COMMIT

---

## 三、关键设计决策

| 决策 | 选项 | 选择 | 理由 |
|:-----|:-----|:-----|:------|
| **架构模式** | 插件 vs 工具 vs 独立 CLI | **独立 Python CLI + MCP Server** | 平台无关、易测试、可集成到任意 Agent |
| **自动适配** | 自动 vs dry-run 后手动确认 | **dry-run → 手动确认 → 执行** | 适配改造涉及 skill 文件变更，需要主人监督 |
| **合规标准** | 内置 vs 引用 cap-pack schema | **引用 cap-pack v2 schema** | 与项目规范保持一致，schema 变更自动同步 |
| **检测触发** | 被动(cron) vs 主动(event) | **两者都有** | cron 做定时扫描 + pre_flight gate 做事件触发 |
| **多 Agent 策略** | 多适配器 vs 单一 MCP | **适配器抽象层 + MCP 兜底** | 核心逻辑复用，适配器可插拔，MCP 提供通用入口 |

---

## 四、不做的范围 (Out of Scope)

| 项目 | 理由 |
|:-----|:------|
| ❌ UI 界面（Web Dashboard） | CLI + HTML 报告已满足需求，UI 后续再说 |
| ❌ 公共注册中心 | 属于 cap-pack 生态的其他环节 |
| ❌ 与其他 Agent 生态的 skill marketplace 集成 | scope 太大，留待后续 |
| ❌ 自动修改 skill 内容（仅建议改造方向） | 适配只改 cap-pack.yaml 和归类，不修改 SKILL.md 内容 |

---

## 五、成功指标

| 指标 | 目标值 | 测量方式 |
|:-----|:------:|:---------|
| 检测覆盖率 | 7/7 维度全部实现 | Story AC 审计 |
| Cap-Pack 合规通过率 | ≥ 90% 新 skill 自动合规 | 扫描报告统计 |
| 误报率 | ≤ 10%（dry-run 适配方案被主人拒绝率） | 适配确认日志 |
| 多 Agent 覆盖 | ≥ 3 种（Hermes / OpenCode / MCP） | 适配器列表 |
| 检测速度 | ≤ 30s / 100 skills | `scan --benchmark` |

---

## 六、与现有系统的关系

| 系统 | 关系 | 说明 |
|:-----|:-----|:------|
| **skill-quality-score.py** | 输入源 | 治理引擎调用 SQS 作为质量输入 |
| **skill-tree-index.py** | 输入源 | 治理引擎调用树索引判断树归属 |
| **cap-pack-v2 schema** | 合规标准 | 治理引擎的合规检查对照此 schema |
| **pre_flight.py** | 集成点 | Phase 1 新增 governance gate |
| **SRA** | 集成点 | 治理评分→推荐权重因子 |
| **install-pack.py** | 输出目标 | 适配改造的最终交付 |

---

## 七、风险与缓解

| 风险 | 概率 | 缓解策略 |
|:-----|:----:|:---------|
| 过度设计 | 🟡 中 | Phase 0 只做核心扫描，不做完美架构 |
| 与现有工具重复 | 🟢 低 | Cap-Pack 合规是独特维度，可复用现有工具输出 |
| 自动适配误操作 | 🔴 高（已识别） | 强制 dry-run + 主人确认 + git 可回滚 |
| 多 Agent 差异过大 | 🟡 中 | 先做 Hermes + MCP 兜底，其他适配器按需添加 |
