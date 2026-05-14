---
type: lesson-learned
skill_ref: "wqy font fallback"
keywords: [wqy-font-fallback]
created: 2026-05-14
---

# WQY 字体回退问题

> **类型**: pitfall · **关联技能**: pdf-layout, pdf-pro-design
> **发现**: 2025-12 首次 · **更新**: 2026-03

## 问题描述

在 ReportLab 中使用 WQY 微米黑字体（文泉驿）生成中文 PDF 时，字体注册失败导致中文显示为方框 `□□□`。

## 根因

WQY 字体的 TTF 文件路径在不同 Linux 发行版中位置不同：

| 发行版 | 路径 |
|:-------|:-----|
| Ubuntu 22.04+ | `/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc` |
| Debian 12 | `/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc` |
| CentOS 8 | `/usr/share/fonts/wqy-zenhei/wqy-zenhei.ttc` |
| Docker (python:3.11-slim) | 未预装，需 apt install |

## 解决方案

```python
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os

# 方案一：自动探测路径
def register_wqy_font():
    candidates = [
        "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
        "/usr/share/fonts/wqy-zenhei/wqy-zenhei.ttc",
    ]
    for path in candidates:
        if os.path.exists(path):
            pdfmetrics.registerFont(TTFont("WQY-ZenHei", path))
            return True
    return False

# 方案二：手动指定（推荐在配置中声明）
pdfmetrics.registerFont(TTFont("WQY-ZenHei", "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc"))
```

## 验证方式

```python
from reportlab.pdfgen import canvas
c = canvas.Canvas("/tmp/font-test.pdf")
c.setFont("WQY-ZenHei", 14)
c.drawString(100, 500, "中文测试：你好世界！")
c.save()
```

## 补充：WeasyPrint 中的字体配置

WeasyPrint 使用系统 fontconfig，WQY 通常自动识别。若失败：
```bash
fc-cache -f && fc-list | grep -i wqy
```
在 CSS 中指定：
```css
body { font-family: "WQY-ZenHei", "Noto Sans CJK SC", sans-serif; }
```
