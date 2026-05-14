# 🔧 SPEC-4-1: 健康度基线扫描 — Phase 0

> **状态**: `approved` · **优先级**: P0 · **创建**: 2026-05-14
> **关联 Epic**: EPIC-004-quality-upgrade.md
> **依赖**: 无（第一个 Phase）

---

## 〇、需求澄清 (CLARIFY)

### 用户故事

> **As a** 主人
> **I want** 对全部 18 个现有能力包运行全量 SQS 评分 + 建立 CHI 趋势仪表盘
> **So that** 知道质量基线在哪、最低分包是谁、从哪里开始改进

### 范围

| 包含 | 不包含 |
|:-----|:--------|
| ✅ 全量 SQS 扫描（五维评分：结构/内容/时效/关联/可发现性） | ❌ 自动修复低分 skill |
| ✅ CHI 仪表盘 v2（按包分组、HTML 可交互） | ❌ L2/L3 内容补充（Phase 1） |
| ✅ 健康度优先级排序（最低分包优先） | ❌ CI 门禁集成（Phase 2） |
| ✅ JSON 基线导出（供后续比较） | ❌ 跨包合并检测（Phase 3） |

---

## 一、技术方案 (RESEARCH)

### 现有工具分析

| 工具 | 能力 | 本次如何使用 |
|:-----|:-----|:------------|
| `skill-quality-score.py --audit --json` | 全量 SQS 扫描 | ⚙️ 直接使用 |
| `skill-tree-index.py --health` | 健康度概览 | ⚙️ 需新增 `--dashboard` 参数 |
| 缺失 | 按 pack 聚合 SQS 数据 | 🆕 新增 `scripts/aggregate-sqs.py` |

### 执行流程

```bash
# Step 1: 全量 SQS 扫描
python3 scripts/skill-quality-score.py --audit --json \
  --output reports/chi-baseline.json

# Step 2: 按 pack 聚合 SQS 数据（新增脚本）
python3 scripts/aggregate-sqs.py \
  --input reports/chi-baseline.json \
  --output reports/chi-by-pack.json

# Step 3: 生成 HTML 仪表盘（扩展 skill-tree-index.py）
python3 scripts/skill-tree-index.py --dashboard \
  --input reports/chi-by-pack.json \
  --output reports/chi-dashboard-v2.html

# Step 4: 优先级排序（新增功能）
python3 scripts/aggregate-sqs.py --prioritize \
  --input reports/chi-by-pack.json \
  --output reports/chi-priority-list.md
```

---

## 二、Stories

### STORY-4-1: 全量 SQS 扫描 + CHI 仪表盘 v2

**内容**：
1. 运行 `skill-quality-score.py --audit --json` 获取全量数据
2. 编写 `scripts/aggregate-sqs.py` 按 pack 分组聚合
3. 扩展 `skill-tree-index.py` 新增 `--dashboard` 参数 → 生成可交互 HTML

**产出物**：
- `reports/chi-baseline.json` — 全量 SQS 原始数据
- `reports/chi-by-pack.json` — 按 pack 聚合数据
- `reports/chi-dashboard-v2.html` — 交互式仪表盘
- `scripts/aggregate-sqs.py` — 新增脚本
- `skill-tree-index.py` — 新增 `--dashboard` 模式

**估算**: 1h

### STORY-4-2: 健康度优先级排序 + 定位最低分包

**内容**：
1. 分析聚合数据，输出按 SQS 均分排序的 pack 列表
2. 标注健康状态：🟢 ≥80 / 🟡 60-79 / 🟠 40-59 / 🔴 <40
3. 明确标识前 3 个最低分包
4. 写入 `docs/reports/chi-priority-list.md`

**产出物**：
- `reports/chi-priority-list.md` — 优先级排序报告
- 确定 Phase 1 的优先处理目标

**估算**: 0.5h

---

## 三、验收标准

| AC ID | 描述 | 验证方式 | 优先级 |
|:------|:-----|:---------|:------:|
| AC-01 | `chi-baseline.json` 已生成（含全部 18+ pack 的 SQS 五维评分） | 文件存在，JSON 有效 | P0 |
| AC-02 | `chi-dashboard-v2.html` 在浏览器正常渲染 | 打开 HTML 验证 | P0 |
| AC-03 | `chi-priority-list.md` 标记了前 3 个最低分包 | 文件存在，内容合理 | P0 |
| AC-04 | `scripts/aggregate-sqs.py` 存在且可运行 | `--help` 有输出 | P0 |
| AC-05 | 全部 101+ 测试仍然绿 | `pytest scripts/tests/ -q` | P0 |
| AC-06 | project-state.py verify 通过 | exit code 0 | P0 |

---

## 四、依赖与风险

| # | 依赖/风险 | 类型 | 缓解 |
|:-:|:----------|:----:|:-----|
| 1 | skill-quality-score.py 可能漏扫某些 skill | 技术 | 执行后验证 skill 总数 ~202 |
| 2 | HTML 仪表盘需要依赖 matplotlib/plotly | 环境 | 无新增依赖：纯 HTML/CSS/JS 生成 |
| 3 | 现有 101 测试不覆盖新脚本 | 流程 | STORY-4-1 完成后补充测试 |
