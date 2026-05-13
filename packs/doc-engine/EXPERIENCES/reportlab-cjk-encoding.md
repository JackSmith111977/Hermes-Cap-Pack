# ReportLab 中文字体编码问题

> **类型**: pitfall · **关联技能**: pdf-layout
> **发现**: 2026-01 · **更新**: 2026-03

## 问题描述

使用 ReportLab 生成含中文的 PDF 时，`drawString` 报错：
```
UnicodeEncodeError: 'latin-1' codec can't encode characters in position ...
```

## 根因

ReportLab 的默认字体（Helvetica）不支持 CJK 字符。必须显式注册中文字体并使用 TTFont。

## 解决方案

```python
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# 注册中文字体（必须在任何绘制操作之前）
pdfmetrics.registerFont(TTFont("WQY-ZenHei", "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc"))

# 使用已注册字体
c.setFont("WQY-ZenHei", 12)
c.drawString(100, 500, "中文内容")  # 不再报错
```

## 常见陷阱

1. **字体路径错误**：`.ttc` 和 `.ttf` 后缀都能用，但不同系统路径不同
2. **注册顺序**：必须先 registerFont 再 setFont，否则静默回退到 Helvetica
3. **canvas.drawString vs drawAlignedString**：都支持已注册的 CJK 字体
4. **字体名称区分大小写**：`WQY-ZenHei` 与 `wqy-zenhei` 在 fontconfig 中等效，但在 ReportLab 中区分
