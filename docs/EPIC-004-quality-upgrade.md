# EPIC-004: 能力包质量升级 — 三层改造 + 健康度检测 + 合并优化

> **epic_id**: `EPIC-004`
> **status**: `draft`
> **created**: 2026-05-14
> **owner**: boku (Emma)
> **前置条件**: 全部 17 模块提取完成（EPIC-003 Phase 1-4）

---

## 〇、需求

### 核心问题

当前能力包提取只完成了 **L1 Skills** 层的复制（SKILL.md 拷贝）。但能力包格式支持三层知识体系：

| 层 | 当前状态 | 目标 |
|:---|:---------|:-----|
| **L1 Skills** | ✅ 已提取（~160+ SKILL.md 复制到 packs/*/SKILLS/） | 保持不变 |
| **L2 Experiences** | ❌ 缺失 | 每个包补充实战经验文档 |
| **L3 Brain** | ❌ 缺失 | 每个包补充概念/实体/分析知识 |

同时，提取过程中跳过了 **健康度检测** 和 **合并去重** 步骤——需要回头补上。

### 目标

```
全部模块提取后 →
    ┌─────────────────────────────────────────────┐
    │ Phase A: 三层改造                            │
    │   每个能力包补充 L2 Experiences + L3 Brain   │
    ├─────────────────────────────────────────────┤
    │ Phase B: 健康度检测                          │
    │   SQS 全量扫描 + 低分标注 + 改进计划          │
    ├─────────────────────────────────────────────┤
    │ Phase C: 合并/清理                           │
    │   识别重叠/冗余 skill → 合并 → 删除废弃       │
    └─────────────────────────────────────────────┘
    │
    ▼ 全部 17 模块达到 CHI ≥ 0.85 质量门槛
```

---

## 一、Phase A — 三层改造

### 现状

每个已提取的 pack 目前只有 `SKILLS/` 目录（L1），缺少 `EXPERIENCES/`（L2）和 `KNOWLEDGE/`（L3）。

### 改造内容

为每个 pack 补充：

```text
packs/<name>/
├── cap-pack.yaml          # ✅ 已有
├── SKILLS/                # ✅ 已有 (L1)
├── EXPERIENCES/           # ❌ 新增 (L2)
│   └── <exp-id>.md        # — 实战经验/教训/最佳实践
└── KNOWLEDGE/             # ❌ 新增 (L3)
    ├── concepts/          # — 核心概念/模式
    ├── entities/          # — 重要实体/工具/人物
    └── summaries/         # — 技术文档摘要
```

**每个包至少 1 个 Experience + 1 个 Knowledge 页面**，大型包（creative-design, developer-workflow 等）至少 3 个。

### 工作量估算

| 包大小 | 包 | 估算 |
|:------|:---|:----:|
| 大型 (16-26 skills) | creative-design, developer-workflow | 各 1h |
| 中型 (8-13 skills) | doc-engine, learning-engine, agent-orchestration | 各 45min |
| 小型 (1-7 skills) | metacognition, quality-assurance, learning-workflow, skill-quality | 各 30min |
| **总计** | **9 个包** | **~6h** |

---

## 二、Phase B — 健康度检测

### 目标

对每个 pack 中的所有 skill 运行 SQS 五维质量评分，建立健康度基线。

### 流程

```bash
# 1. 全量 SQS 审计
python3 ~/.hermes/skills/skill-creator/scripts/skill-quality-score.py \
  --audit --json

# 2. 按 pack 统计健康度（平均分 + 分布）
python3 scripts/skill-tree-index.py --health

# 3. 生成质量报告
# 标注每个 skill 的健康状态
# 🟢 优秀 (≥80)  → 无需处理
# 🟡 良好 (60-79) → 观察
# 🟠 需改进 (40-59) → 制定改进计划
# 🔴 不合格 (<40)  → 标记为待删除/合并
```

### 门禁标准

| 指标 | 当前 | 目标 |
|:-----|:----:|:----:|
| CHI (Capability Health Index) | 0.6355 | ≥ **0.85** |
| SQS 平均分 | 67.9 | ≥ **80** |
| 低分项占比 (<60) | 47% | ≤ **15%** |

---

## 三、Phase C — 合并/清理

### 目标

识别跨包重叠 skill、低质量 skill、废弃 skill，进行合并或清理。

### 流程

```bash
# 1. 运行合并建议引擎
python3 scripts/skill-tree-index.py --consolidate

# 2. 逐项评估建议
#    - 完全重复 → 合并（保留高质量版本）
#    - 部分重叠 → 合并内容（取并集）
#    - 低分废弃 → 标记 deprecated 或删除

# 3. 更新 cap-pack.yaml 反映合并/删除

# 4. 更新 project-report.json 反映变更
```

### 预期成果

| 指标 | 当前 | 目标 |
|:-----|:----:|:----:|
| 总 skill 数 | ~160+ | 合并后减少 10-20% |
| 重叠簇 | 待检测 | 全部识别并处理 |
| SQS 均分 | 67.9 | ≥ **80** |

---

## 四、验收标准

- [ ] AC1: 全部 9+ 能力包具有 L1 + L2 + L3 三层结构
- [ ] AC2: 每个 skill 有 SQS 评分记录，无可隐藏低分
- [ ] AC3: 重复/重叠 skill 全部识别，合并或清理
- [ ] AC4: CHI ≥ 0.85
- [ ] AC5: SQS 平均分 ≥ 80
- [ ] AC6: HTML 全景报告反映三层结构和健康度数据
- [ ] AC7: 产出一份"质量升级报告"文档

---

## 五、前置条件

- [ ] EPIC-003 全部模块提取完成（17/17 模块）
- [ ] project-report.json 反映完整模块体系
- [ ] doc-alignment 强制门禁就位

---

## 六、风险

| 风险 | 概率 | 影响 | 缓解 |
|:-----|:----:|:----:|:-----|
| 三层改造耗时高估 | 中 | Phase A 超期 | 先做大型包的 L2/L3，小包简单补充 |
| 合并建议误判 | 低 | 错误删除 skill | 每项合并需主人确认后再执行 |
| SQS 评分波动 | 低 | 基线不准 | 取 3 次评分平均值作为基线 |
