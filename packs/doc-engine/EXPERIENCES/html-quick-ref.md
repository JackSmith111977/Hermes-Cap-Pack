---
type: tutorial
skill_ref: "html quick ref"
keywords: [html-quick-ref]
created: 2026-05-14
---

# HTML 文档排版速查

> 从 `html-guide` skill 降级（SQS 46.2/100 — 内容被 html-presentation 覆盖）
> 来源: `~/.hermes/skills/html-guide/SKILL.md`

## 适用场景

需要生成简单的 HTML 文档/报告页面时。复杂演示文稿请用 html-presentation skill。

## 快速模板

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>文档标题</title>
<style>
  body { font-family: -apple-system, 'PingFang SC', sans-serif; 
         max-width: 800px; margin: 0 auto; padding: 20px; 
         line-height: 1.8; color: #333; }
  h1, h2, h3 { color: #1a1a2e; }
  code { background: #f4f4f4; padding: 2px 6px; border-radius: 4px; }
  pre { background: #f4f4f4; padding: 16px; border-radius: 8px; overflow-x: auto; }
</style>
</head>
<body>
<h1>文档标题</h1>
<p>正文内容...</p>
</body>
</html>
```

## 打印样式

```css
@media print {
  body { max-width: none; font-size: 12pt; }
  nav, footer { display: none; }
}
```
