---
type: tutorial
skill_ref: "docx quick ref"
keywords: [docx-quick-ref]
created: 2026-05-14
---

# Word 文档操作速查

> 从 `docx-guide` skill 降级（SQS 50.2/100 — 无版本号，内容简单）
> 来源: `~/.hermes/skills/docx-guide/SKILL.md`

## 基本用法

```bash
pip install python-docx
```

```python
from docx import Document
from docx.shared import Inches, Pt, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH

doc = Document()

# 标题
doc.add_heading('文档标题', level=1)

# 段落
p = doc.add_paragraph('正文内容')
p.alignment = WD_ALIGN_PARAGRAPH.LEFT

# 表格
table = doc.add_table(rows=3, cols=2)
table.style = 'Table Grid'
cell = table.cell(0, 0)
cell.text = '姓名'

# 图片
doc.add_picture('image.png', width=Inches(4))

# 保存
doc.save('output.docx')
```

## 适用场景

- 需要生成 .docx 格式报告
- 与飞书/微信等平台配合发送
- 不适用于 PDF/LaTeX 排版需求
