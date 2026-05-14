---
type: decision-tree
skill_ref: "pdf tool decision tree"
keywords: [pdf-tool-decision-tree]
created: 2026-05-14
---

# PDF 渲染工具选型决策树

> **类型**: decision-tree · **关联技能**: pdf-layout, pdf-render-comparison, latex-guide
> **创建**: 2026-03 · **更新**: 2026-05

## 决策树

```
需要生成 PDF？
    ↓
① 文档复杂度？
    ├── 简单文档（纯文本 + 少量表格/图片）
    │   └── WeasyPrint (HTML→PDF, 最简单)
    ├── 复杂排版（多栏/页眉页脚/精确位置）
    │   └── ReportLab (程序化布局, 最灵活)
    ├── 学术论文/书籍
    │   └── LaTeX (排版质量最高)
    └── 数据分析报告（含图表）
        └── Matplotlib + ReportLab / WeasyPrint
    ↓
② 中文支持需求？
    ├── 大量中文
    │   └── WeasyPrint (fontconfig 自动识别)
    ├── 少量中文但要求精确位置
    │   └── ReportLab + TTFont 注册
    └── 学术中文论文
        └── LaTeX + ctex 宏包
    ↓
③ 环境约束？
    ├── 无头服务器
    │   └── WeasyPrint (依赖少, 启动快)
    ├── Docker 容器
    │   └── WeasyPrint (只需 apt install + pip)
    └── CI/CD 流水线
        └── WeasyPrint (缓存友好, 可纯内存)
```

## 对比矩阵

| 维度 | WeasyPrint | ReportLab | LaTeX | python-pptx |
|:-----|:----------|:----------|:------|:------------|
| 学习曲线 | 🟢 低 | 🟡 中 | 🔴 高 | 🟢 低 |
| 布局灵活性 | 🟢 CSS 标准 | 🔴 需要计算坐标 | 🟡 声明式 | 🟢 模板式 |
| 中文支持 | 🟢 fontconfig | 🟡 需手动注册 | 🟢 ctex | 🟡 需 XML 操作 |
| 图表集成 | 🟡 SVG/图片 | 🟢 原生绘图 | 🟢 TikZ | ❌ 需图片 |
| 渲染速度 | 🟢 快 | 🟢 快 | 🟡 慢 | 🟢 快 |
| 输出格式 | PDF/PNG | PDF/SVG | PDF | PPTX |
| Docker 友好 | 🟢 3 个 apt | 🟡 2 个 apt | 🔴 500MB+ | 🟢 纯 pip |

## 推荐组合

```
文档生成流水线（实战经验）:
  1. 数据分析报告 → Matplotlib -> SVG -> WeasyPrint (HTML模板)
  2. 专业标书 → ReportLab (精确布局)
  3. 学术论文 → LaTeX (ctex + bibtex)
  4. 演示简报 → python-pptx (模板 + 数据填充)
```
