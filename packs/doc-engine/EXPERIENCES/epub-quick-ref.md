---
type: experience
skill_ref: "epub quick ref"
keywords: [epub-quick-ref]
created: 2026-05-14
---

# EPUB 电子书生成速查

> 从 `epub-guide` skill 降级（SQS 47.2/100 — 使用频率极低）
> 来源: `~/.hermes/skills/epub-guide/SKILL.md`

## 基本用法

```bash
pip install ebooklib
```

```python
from ebooklib import epub

book = epub.EpubBook()
book.set_identifier('id-001')
book.set_title('电子书标题')
book.set_language('zh-CN')
book.add_author('作者')

# 创建章节
chapter = epub.EpubHtml(title='第一章', file_name='chap_1.xhtml', lang='zh-CN')
chapter.content = '<h1>第一章</h1><p>正文内容...</p>'
book.add_item(chapter)

# 设置目录结构
book.toc = [epub.Link('chap_1.xhtml', '第一章', 'chap_1')]
book.add_item(epub.EpubNcx())
book.add_item(epub.EpubNav())

# 输出
epub.write_epub('output.epub', book, {})
```

## 适用场景

- 长篇文档导出 EPUB 格式
- 电子书分发
- 不适用于 PDF/打印排版需求
