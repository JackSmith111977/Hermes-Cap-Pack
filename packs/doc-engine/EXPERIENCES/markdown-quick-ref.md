# Markdown 写作与转换速查

> 从 `markdown-guide` skill 降级（SQS 54.2/100 — 基础语法无版本号）
> 来源: `~/.hermes/skills/markdown-guide/SKILL.md`

## 格式转换 (pandoc)

```bash
# Markdown → PDF
pandoc input.md -o output.pdf --pdf-engine=xelatex

# Markdown → DOCX  
pandoc input.md -o output.docx

# Markdown → HTML
pandoc input.md -o output.html -s

# Markdown → EPUB
pandoc input.md -o output.epub
```

## 高级语法

```markdown
<!-- 表格 -->
| 列1 | 列2 |
|:----|:----|
| A   | B   |

<!-- 脚注 -->
这里需要注释[^1]

[^1]: 注释内容

<!-- 任务列表 -->
- [x] 已完成
- [ ] 未完成

<!-- 数学公式 -->
$$E = mc^2$$

<!-- Mermaid 图表 -->
```mermaid
graph LR
  A-->B
```
```

## 注意

文档生成首选 CAP Pack 的 doc-engine 包。Markdown 是中间格式，最终输出用对应格式的 skill。
