# 🔄 doc-engine 分层改造方案 v1.0

> 基于 2026-05-13 全量诊断结果，对 doc-engine 能力包进行科学分层重组
> 关联 SPEC-005 (树状索引) + SPEC-006 (SQS 质量)

---

## 一、诊断摘要 (Before State)

### 📊 基线指标

| 指标 | Before | After(目标) |
|:-----|:------:|:-----------:|
| 技能总数 | 17 | ~10 |
| 经验数 | 5 | ~11 |
| 簇数 | 11 | ~6 |
| 平均 SQS | **64.0/100** 🟠 | >75 🟢 |
| 低分技能 (<60) | **6** 🔴 | 0 🟢 |
| 无版本号技能 | **7** 🔴 | 0 🟢 |
| 平均 S4 (关联性) | **5.5/20** 🔴 | >10 🟡 |
| 冗余度 (PDF 组) | 5 技能重叠 ~80% | 2-3 🔵 |

### 🔴 发现的问题

| # | 问题 | 影响 | 解决方案 |
|:-:|:-----|:----:|:---------|
| 1 | **6 个微技能** (latex/html/epub/xlsx/docx/markdown) 平均 SQS 48.3，无版本号 | 拖低整体质量分 | 降级为 EXPERIENCES/ |
| 2 | **5 个 PDF 技能重叠 70-90%** | 维护成本高，容易不一致 | 合并为 2-3 个 |
| 3 | **S4 关联性普遍 5/20** | 技能间依赖不可追踪 | 强制 depends_on 声明 |
| 4 | **doc-design 是路由型 skill** | 本身在合理范围，无需处理 | 保持 |

---

## 二、分层重组方案

### 目标结构

```
doc-engine (📄 文档生成)
│
├── 📂 pdf/              [2-3 原子技能]
│   ├── pdf-layout          ← 合并原 pdf-layout + pdf-layout-reportlab + pdf-layout-weasyprint
│   ├── pdf-pro-design      ← 高级排版设计（保持独立，因目标用户不同）
│   └── pdf-render-compare  ← 渲染对比工具
│
├── 📂 html/             [1 原子技能]
│   └── html-presentation   ← 网页演示文稿
│
├── 📂 pptx/             [1 原子技能]
│   └── pptx-guide
│
├── 📂 vision/           [1 原子技能]
│   └── vision-qc-patterns  ← PDF 排版质量检查（跨 pdf/ 和设计）
│
├── 📂 nano/             [1 原子技能]
│   └── nano-pdf
│
├── 📂 router/            [1 原子技能]
│   └── doc-design          ← 格式路由（保持索引功能）
│
├── 📂 readme/            [1 原子技能]
│   └── readme-for-ai
│
└── 📂 experiences/       [11 经验文档]
    ├── latex-guide          ← 从 skill 降级
    ├── html-guide           ← 从 skill 降级
    ├── epub-guide           ← 从 skill 降级
    ├── xlsx-guide           ← 从 skill 降级（可移入 productivity 包）
    ├── docx-guide           ← 从 skill 降级
    ├── markdown-guide       ← 从 skill 降级
    ├── pdf-tool-decision-tree   ← 已有
    ├── reportlab-cjk-encoding   ← 已有
    ├── wqy-font-fallback       ← 已有
    ├── pptx-chinese-fonts      ← 已有
    └── design-crap-principles  ← 已有
```

### 合并路径 (PDF 组)

| 源技能 | SQS | 目标 | 理由 |
|:-------|:---:|:-----|:------|
| `pdf-layout` | 71.8 | 主 skill | ReportLab 基础，最全面 |
| `pdf-layout-reportlab` | 75.2 | 合并入主 skill | 内容 20/20，是 pdf-layout 的子集 |
| `pdf-layout-weasyprint` | 68.2 | 合并入主 skill | WeasyPrint 方案，与 ReportLab 互补 |
| `pdf-pro-design` | 77.2 | **保持独立** | 高级设计指南，目标用户不同（设计师 vs 开发者） |
| `pdf-render-comparison` | 83.2 | **保持独立** | 工具对比/选型决策，独特价值 |

### 降级路径 (6 个微技能)

| 源技能 | SQS | 目标 | 理由 |
|:-------|:---:|:-----|:------|
| `latex-guide` | 45.2 🔴 | EXPERIENCES/ | <50 行，无版本，主题窄 |
| `html-guide` | 46.2 🔴 | EXPERIENCES/ | 75 行，无版本，被 html-presentation 覆盖 |
| `epub-guide` | 47.2 🔴 | EXPERIENCES/ | 97 行，无版本，使用频率极低 |
| `xlsx-guide` | 47.2 🔴 | EXPERIENCES/ · 或移入 productivity 包 | 109 行，实际上是 Excel 操作|
| `docx-guide` | 50.2 🔴 | EXPERIENCES/ | 149 行，无版本 |
| `markdown-guide` | 54.2 🔴 | EXPERIENCES/ | 110 行，无版本，pandoc 转换 |

---

## 三、量化测试框架 (QTF)

### KPI 体系

| KPI | 测量方式 | Before | After(目标) | 权重 |
|:----|:---------|:------:|:-----------:|:----:|
| **KPI-1** 平均 SQS | `skill-quality-score.py --audit --pack doc-engine` | 64.0 | >75 | 30% |
| **KPI-2** 低分率 | SQS<60 技能数 / 总数 | 6/17 (35%) | 0/10 (0%) | 20% |
| **KPI-3** 版本完整率 | 有版本号技能 / 总数 | 10/17 (59%) | 10/10 (100%) | 15% |
| **KPI-4** 关联完整率 | S4 维度均分 | 5.5/20 | >10/20 | 15% |
| **KPI-5** 簇内聚度 | 每簇技能数标准差 | 4.2 | <2.0 | 10% |
| **KPI-6** 维护成本 | 技能总数 | 17 | ~10 | 10% |

### 综合健康指数 (CHI)

```
CHI = (avg_sqs/100 × 0.30) 
    + ((1 - low_score_rate) × 0.20)
    + (version_completeness × 0.15) 
    + (avg_s4/20 × 0.15)
    + (cluster_cohesion × 0.10)
    + (1 - (total_skills-optimal)/optimal × 0.10)

CHI Before: 待计算
CHI Target: ≥ 0.75
```

### 验证脚本

```bash
#!/bin/bash
# doc-engine 健康验证脚本

echo "=== doc-engine 健康验证 ==="

# KPI-1: 平均 SQS
echo -n "KPI-1 平均SQS: "
python3 scripts/skill-quality-score.py --pack doc-engine --json | \
  python3 -c "import sys,json; d=json.load(sys.stdin); print(f'{sum(s[\"sqs_total\"] for s in d)/len(d):.1f}')"

# KPI-2: 低分率
echo -n "KPI-2 低分率: "
python3 scripts/skill-quality-score.py --pack doc-engine --json | \
  python3 -c "import sys,json; d=json.load(sys.stdin); low=sum(1 for s in d if s['sqs_total']<60); print(f'{low}/{len(d)} ({low*100//len(d)}%)')"

# KPI-3: 版本完整率
echo -n "KPI-3 版本完整率: "
python3 scripts/skill-quality-score.py --pack doc-engine --json | \
  python3 -c "import sys,json; d=json.load(sys.stdin); ver=sum(1 for s in d if s.get('version','?')!='?'); print(f'{ver}/{len(d)} ({ver*100//len(d)}%)')"

# KPI-4: 关联完整率  
echo -n "KPI-4 S4均分: "
python3 scripts/skill-quality-score.py --pack doc-engine --json | \
  python3 -c "import sys,json; d=json.load(sys.stdin); print(f'{sum(s[\"dimensions\"][\"relation\"] for s in d)/len(d):.1f}/20')"

# KPI-5: 簇内聚度
echo -n "KPI-5 簇数: "
python3 scripts/skill-tree-index.py --pack doc-engine --json | \
  python3 -c "import sys,json; d=json.load(sys.stdin); print(f'{len(d[\"clusters\"])} clusters, {len(d[\"skills\"])} skills')"

echo "=== 验证完成 ==="
```

### 自动门禁

在 `packs/doc-engine/` 添加 `health-gate.yaml`：

```yaml
# health-gate.yaml — doc-engine 质量门禁
gates:
  - id: min-avg-sqs
    description: "平均 SQS ≥ 70"
    check: "python3 scripts/skill-quality-score.py --pack doc-engine --json | python3 -c 'import sys,json; d=json.load(sys.stdin); exit(0 if sum(s[\"sqs_total\"] for s in d)/len(d) >= 70 else 1)'"
    
  - id: zero-low-score
    description: "无 SQS<60 技能"
    check: "python3 scripts/skill-quality-score.py --pack doc-engine --json | python3 -c 'import sys,json; d=json.load(sys.stdin); exit(0 if all(s[\"sqs_total\"]>=60 for s in d) else 1)'"
    
  - id: full-version
    description: "所有技能有版本号"
    check: "python3 scripts/skill-quality-score.py --pack doc-engine --json | python3 -c 'import sys,json; d=json.load(sys.stdin); exit(0 if all(s.get(\"version\",\"?\")!=\"?\" for s in d) else 1)'"
```

---

## 四、分层验证策略

### 分层测试 (Layer-by-layer)

```
L0: 基础设施验证 → pre_flight + SQS 工具链正常
    ├── gate: python3 scripts/skill-quality-score.py --help
    └── gate: python3 scripts/skill-tree-index.py --help
    
L1: 技能级验证 → 每个技能 SQS ≥ 60, 有版本号
    ├── gate: 批量运行 quality-score --json
    └── metrics: SQS 分布直方图
    
L2: 簇级验证 → 每簇 2-4 技能，语义内聚
    ├── gate: skill-tree-index 输出簇数
    └── metrics: 簇内技能 SQS 方差
    
L3: 包级验证 → CHI 综合指数 ≥ 0.75
    ├── gate: health-gate.yaml 全部通过
    └── metrics: CHI 趋势 (历史对比)
```

### 回归保护

每次修改 doc-engine 中的 skill 后自动触发：
1. `pre_flight.py` 检测到技能操作 → 加载 skill-creator
2. 运行 `dependency-scan.py` 检查引用断裂
3. 运行 SQS 全量审计
4. 对比 CHI 指数 before/after
5. CHI 下降 > 0.05 → 自动回滚并报警
