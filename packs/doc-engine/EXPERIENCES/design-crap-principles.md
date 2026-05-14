---
type: lesson-learned
skill_ref: "design crap principles"
keywords: [design-crap-principles]
created: 2026-05-14
---

# CRAP 设计原则在排版中的应用

> **类型**: comparison · **关联技能**: pdf-pro-design, doc-design
> **创建**: 2026-04

## 四个原则速览

| 原则 | 英文 | 作用 | 常见错误 |
|:-----|:-----|:-----|:---------|
| **对比** | Contrast | 建立视觉层级 | 所有元素大小/颜色相同 |
| **重复** | Repetition | 统一视觉风格 | 标题样式不统一 |
| **对齐** | Alignment | 创造视觉秩序 | 元素随机放置 |
| **亲近** | Proximity | 组织信息分组 | 相关元素距离太远 |

## 在 PDF 排版中的实战应用

### 对比 (Contrast)

**好**：标题 24pt 粗体 + 正文 11pt → 一眼区分层级
**不好**：标题 14pt + 正文 12pt → 看不出结构

实现：
```css
/* WeasyPrint */
h1 { font-size: 24pt; font-weight: 700; color: #1a1a2e; }
h2 { font-size: 18pt; font-weight: 600; color: #333; }
body { font-size: 11pt; line-height: 1.6; }
```

### 重复 (Repetition)

- 所有一级标题完全相同的样式
- 所有代码块完全相同的样式
- 列表符号一致

### 对齐 (Alignment)

- **左对齐**：正文（中文阅读习惯）
- **居中对齐**：封面、标题页
- **右对齐**：页码、日期

### 亲近 (Proximity)

```
不好：
  标题A
  一段关于A的文字
  标题B
  一段关于B的文字
  图片说明（离图片很远）

好：
  标题A
  一段关于A的文字        ← 紧密
  图片
  图片说明               ← 紧贴图片
  ---（分隔）
  标题B
  一段关于B的文字
```
