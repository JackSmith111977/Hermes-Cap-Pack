---
name: pdf-layout
version: 3.0.0
description: "专业 PDF 排版与生成 — 双引擎（ReportLab + WeasyPrint）覆盖所有 PDF 场景。合并自 pdf-layout (v2.0.0)、pdf-layout-reportlab (v1.0.0)、pdf-layout-weasyprint (v2.0.0)"
tags: [pdf, layout, reportlab, weasyprint, 排版, 中文PDF, 生成PDF]
triggers: [pdf, 排版, 生成pdf, pdf生成, reportlab, weasyprint, 中文pdf]
design_pattern: generator
depends_on:
  - python-env-guide
  - quality-assurance/skill-quality-score
---

# PDF 排版与生成（合并版 v3.0）

> 本 skill 合并了原 `pdf-layout`, `pdf-layout-reportlab`, `pdf-layout-weasyprint` 三个技能。
> 统一入口，双引擎覆盖，根据需求选择方案。

---

## 引擎选择决策

```text
需要生成 PDF？
    │
    ├─ 文字为主、格式简单 → WeasyPrint（HTML+CSS → PDF）
    │   └─ 优点: CSS 熟悉、模板友好
    │   └─ 缺点: 复杂表格支持弱
    │
    ├─ 复杂排版、精确控制 → ReportLab
    │   └─ 优点: 像素级控制、图表嵌入
    │   └─ 缺点: 学习曲线陡
    │
    └─ 已有 HTML 页面 → WeasyPrint（直接转换）
```

---

## 方案 A：WeasyPrint（推荐给 Web 开发者）

### 安装

```bash
pip install weasyprint
# 中文支持
sudo apt install fonts-wqy-zenhei fonts-wqy-microhei
```

### 基本用法

```python
from weasyprint import HTML

# 从 HTML 字符串生成
HTML(string='<h1 style="color:red">Hello</h1><p>中文内容</p>') \
    .write_pdf('output.pdf')

# 从文件生成
HTML(filename='report.html').write_pdf('report.pdf')

# 带 CSS
HTML(string='<h1>标题</h1>').write_pdf('styled.pdf', stylesheets=['style.css'])
```

### CSS 打印样式关键点

```css
@page {
  size: A4;
  margin: 2.5cm 2cm;
  @top-center { content: element(pageHeader); }
}

body {
  font-family: 'WenQuanYi Zen Hei', 'Noto Sans CJK SC', serif;
  font-size: 11pt;
  line-height: 1.8;
  color: #333;
}

/* 避免分页断裂 */
h1, h2, h3, h4 { page-break-after: avoid; }
table { page-break-inside: avoid; }
img { page-break-inside: avoid; }

/* 代码块换行 */
pre {
  white-space: pre-wrap;
  word-break: break-all;
  background: #f5f5f5;
  padding: 12px;
  font-size: 9pt;
}
```

### WeasyPrint 优点
- CSS 技能直接复用
- 模板友好（Jinja2 + CSS）
- 支持 @page 规则

### WeasyPrint 限制
- 复杂表格渲染不稳定
- 不支持 CMYK
- 大文件内存消耗高

---

## 方案 B：ReportLab（推荐给精确控制需求）

### 安装

```bash
pip install reportlab
# 中文字体
sudo apt install fonts-wqy-zenhei
```

### 基本用法

```python
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm, mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# 注册中文字体
pdfmetrics.registerFont(TTFont('WQY', '/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc'))
pdfmetrics.registerFont(TTFont('WQY-Bold', '/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc'))

# 构建文档
doc = SimpleDocTemplate(
    'output.pdf',
    pagesize=A4,
    topMargin=2.5*cm,
    bottomMargin=2*cm,
    leftMargin=2*cm,
    rightMargin=2*cm
)

# 样式
styles = getSampleStyleSheet()
title_style = ParagraphStyle(
    'CustomTitle',
    parent=styles['Title'],
    fontName='WQY',
    fontSize=18,
    spaceAfter=12
)

# 内容
story = []
story.append(Paragraph('文档标题', title_style))
story.append(Spacer(1, 0.5*cm))
story.append(Paragraph('正文内容使用 WQY 中文字体', styles['Normal']))

# 表格
data = [['列1', '列2', '列3'],
        ['数据A', '数据B', '数据C']]
table = Table(data, colWidths=[4*cm, 4*cm, 4*cm])
table.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2563eb')),
    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
    ('FONTNAME', (0, 0), (-1, -1), 'WQY'),
    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
]))
story.append(table)

doc.build(story)
```

### ReportLab 中文要点

| 问题 | 解决方案 |
|:-----|:---------|
| 中文方块 | 注册 TTFont + 设置 fontName |
| 字体未找到 | `fc-list :lang=zh` 查找已安装字体 |
| 粗体无效 | 注册两个字体条目（TTFont 支持自动 bold） |
| 表格中文截断 | 增加 colWidths + 使用 allowMultiCell |
| 分页断裂 | keepWithNext, pageBreak 手动控制 |

### ReportLab 优点
- 像素级排版控制
- 强大的表格系统
- 图表嵌入（LinePlot, PiePlot）
- 支持 CMYK / 印刷级

### ReportLab 限制
- 学习曲线较陡
- HTML→PDF 不直观
- 需要手动管理 flowables

---

## 复杂排版示例

### 双引擎对比

| 特性 | WeasyPrint | ReportLab |
|:-----|:----------:|:---------:|
| CSS 支持 | ✅ 完整 | ❌ 无 |
| 中文支持 | ✅ 系统字体 | ✅ 注册字体 |
| 表格 | 🟡 中等 | ✅ 强大 |
| 图表 | ❌ 无 | ✅ 内置 |
| 分页控制 | 🟡 @page | ✅ 精确 |
| 性能 | 🟡 大文件慢 | ✅ 稳定 |
| 学习曲线 | 🟢 低 | 🔴 高 |

### 推荐选项速查

| 你要做什么 | 推荐引擎 |
|:-----------|:---------|
| 简单的文本报告 | WeasyPrint |
| 带复杂表格的报表 | ReportLab |
| HTML 页面转 PDF | WeasyPrint |
| 印刷级排版 | ReportLab |
| 数据可视化报告 | ReportLab |
| 批量生成（>100页） | ReportLab |

---

## 常见陷阱

| 陷阱 | 症状 | 解决方案 |
|:-----|:-----|:---------|
| WeasyPrint 中文白页 | 输出空白 PDF | `font_config.font_map` 检测中文字体 |
| ReportLab 中文方块 | □□□ | 注册 TTFont，确认字体路径 |
| 表格内容溢出 | 文字超出单元格 | 设置 `allowMultiCell=True` |
| 页眉页脚重复 | 内容重叠 | 使用 `onPage` 回调（ReportLab） |
| 图片模糊 | 像素化 | 使用向量图 SVG |
| 字体版权 | 部署后字体缺失 | 使用 WQY 开源字体 |
