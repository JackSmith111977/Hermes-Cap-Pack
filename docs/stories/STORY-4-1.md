# STORY-4-1: 全量 SQS 扫描 + CHI 仪表盘 v2

> **状态**: `completed` · **Epic**: EPIC-004 · **Spec**: SPEC-4-1
> **SDD 状态**: `completed` · **创建**: 2026-05-14

---

## 用户故事

**As a** 主人
**I want** 对全部 18 个能力包运行全量 SQS 评分并生成 CHI 仪表盘
**So that** 我们知道质量基线在哪、哪些包需要优先改进

---

## 验收标准

- [ ] AC-01: `reports/chi-baseline.json` 已生成，含全部 18+ pack 的五维 SQS 评分
- [ ] AC-02: `reports/chi-dashboard-v2.html` 在浏览器正常渲染
- [ ] AC-03: `scripts/aggregate-sqs.py` 存在且 `--help` 有输出
- [ ] AC-04: `skill-tree-index.py --dashboard` 参数可运行
- [ ] AC-05: 全部 101 测试仍然绿（`pytest scripts/tests/ -q`）
- [ ] AC-06: `project-state.py verify` 通过

---

## 执行步骤

### Step 1: 全量 SQS 扫描

```bash
python3 scripts/skill-quality-score.py --audit --json \
  > reports/chi-baseline.json 2>&1
```

验证：JSON 包含 `"skills"` 数组，每个 skill 有 5 个维度的分数。

### Step 2: 编写 aggregate-sqs.py

新建 `scripts/aggregate-sqs.py`，功能：
- `--input <json>` 读取全量 SQS 数据
- `--output <json>` 输出按 pack 分组聚合（pack name, avg_sqs, skill_count, distribution）
- `--dashboard` 整合输出到 skill-tree-index.py 的 HTML 生成

### Step 3: 扩展 skill-tree-index.py --dashboard

新增参数 `--dashboard`，接收聚合后的 JSON，生成 HTML 页面：
- CHI 总体指标卡
- 每个 pack 的 SQS 均分条形图
- 评分分布直方图
- 最低分包高亮

### Step 4: 生成仪表盘

```bash
python3 scripts/aggregate-sqs.py \
  --input reports/chi-baseline.json \
  --output reports/chi-by-pack.json

python3 scripts/skill-tree-index.py --dashboard \
  --input reports/chi-by-pack.json \
  --output reports/chi-dashboard-v2.html
```

### Step 5: 验证

```bash
pytest scripts/tests/ -q
python3 scripts/project-state.py verify
```

---

## 涉及文件

| 文件 | 动作 | 说明 |
|:-----|:-----|:------|
| `scripts/aggregate-sqs.py` | 🆕 新建 | ~80 行，按 pack 分组聚合 SQS |
| `scripts/skill-tree-index.py` | 🔧 修改 | 新增 `--dashboard` 参数 |
| `reports/chi-baseline.json` | 🆕 生成 | 全量 SQS 扫描结果 |
| `reports/chi-by-pack.json` | 🆕 生成 | 按 pack 聚合数据 |
| `reports/chi-dashboard-v2.html` | 🆕 生成 | 交互式仪表盘 |

---

## 估算

**1h**（脚本编写 40min + 运行验证 20min）
