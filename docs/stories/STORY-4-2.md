# STORY-4-2: 健康度优先级排序 + 定位最低分包

> **状态**: `completed` · **Epic**: EPIC-004 · **Spec**: SPEC-4-1
> **SDD 状态**: `completed` · **创建**: 2026-05-14

---

## 用户故事

**As a** 主人
**I want** 根据 SQS 基线数据排出能力包的健康优先级
**So that** Phase 1 和 Phase 2 优先处理最需要改进的包

---

## 验收标准

- [ ] AC-01: `reports/chi-priority-list.md` 已生成
- [ ] AC-02: 列表按 SQS 均分降序排列，标注健康状态（🟢🟡🟠🔴）
- [ ] AC-03: 明确标识前 3 个最低分包作为 Phase 1 目标
- [ ] AC-04: `aggregate-sqs.py --prioritize` 参数可用
- [ ] AC-05: `project-state.py verify` 通过

---

## 执行步骤

### Step 1: 扩展 aggregate-sqs.py --prioritize

新增参数 `--prioritize`，功能：
- 读取按 pack 聚合的 JSON
- 按 SQS 均分降序排列
- 标注健康状态：
  - 🟢 优秀（≥80）
  - 🟡 良好（60-79）
  - 🟠 需改进（40-59）
  - 🔴 不合格（<40）
- 输出 Markdown 表格

### Step 2: 生成优先级报告

```bash
python3 scripts/aggregate-sqs.py --prioritize \
  --input reports/chi-by-pack.json \
  --output reports/chi-priority-list.md
```

### Step 3: 验证

```bash
python3 scripts/project-state.py verify
```

---

## 涉及文件

| 文件 | 动作 | 说明 |
|:-----|:-----|:------|
| `scripts/aggregate-sqs.py` | 🔧 修改 | 新增 `--prioritize` 参数 |
| `reports/chi-priority-list.md` | 🆕 生成 | 按优先级排序的 pack 列表 |

---

## 估算

**0.5h**（脚本扩展 20min + 运行验证 10min）
