# python-pptx 中文字体问题

> **类型**: pitfall · **关联技能**: pptx-guide
> **发现**: 2026-02 · **更新**: 2026-03

## 问题描述

使用 python-pptx 创建含中文的 PPT 时，PowerPoint/WPS 打开后中文显示为乱码或方框。

## 根因

python-pptx 设置字体名称时，不同平台对字体名称的映射不同：
- Windows: `SimSun`（宋体）
- macOS: `STSong`（华文宋体）
- Linux: `WQY-ZenHei` / `Noto Sans CJK SC`
- PowerPoint for Web: 使用 `Calibri` 作为西文默认，中文自动回退

## 解决方案

```python
from pptx.util import Pt, Inches
from pptx.dml.color import RGBColor

run = paragraph.add_run()
run.text = "中文内容"

# 同时设置西文和东亚字体
from pptx.oxml.ns import qn
rPr = run._r.get_or_add_rPr()
rPr.set(qn('a:altLang'), 'zh-CN')

# 方案一：用 latin 字段设置中文兼容字体
run.font.name = 'SimSun'  # Windows 兼容

# 方案二（推荐）：直接操作 XML 设置东亚字体
from lxml import etree
nsmap = {'a': 'http://schemas.openxmlformats.org/drawingml/2006/main'}
ea = rPr.find('.//a:ea', nsmap)
if ea is None:
    ea = etree.SubElement(rPr, '{http://schemas.openxmlformats.org/drawingml/2006/main}ea')
ea.set('typeface', 'SimSun')
```

## 跨平台兼容策略

| 平台 | 推荐字体 | 说明 |
|:-----|:---------|:-----|
| Windows | SimSun, Microsoft YaHei | 原生支持 |
| macOS | STSong, PingFang SC | 原生支持 |
| Linux | WQY-ZenHei, Noto Sans CJK SC | 需安装 |
| Web | system-ui, sans-serif | 自动回退 |
