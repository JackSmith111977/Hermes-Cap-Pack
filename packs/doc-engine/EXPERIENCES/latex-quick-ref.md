---
type: tutorial
skill_ref: "latex quick ref"
keywords: [latex-quick-ref]
created: 2026-05-14
---

# LaTeX 排版速查

> 从 `latex-guide` skill 降级（SQS 45.2/100 — 行数不足，无版本号）
> 来源: `~/.hermes/skills/latex-guide/SKILL.md`

## 适用场景

需要生成 LaTeX 学术论文、技术报告时。日常文档请用 PDF skill。

## 基本命令

```bash
# 安装
sudo apt install texlive-latex-base texlive-xetex texlive-lang-chinese

# 编译
xelatex paper.tex

# 带参考文献
xelatex paper.tex && bibtex paper && xelatex paper.tex && xelatex paper.tex
```

## 快速模板

```latex
\documentclass[12pt]{article}
\usepackage{ctex}  % 中文支持
\usepackage{amsmath, amssymb}
\usepackage{graphicx}
\usepackage{hyperref}

\title{论文标题}
\author{作者}
\date{\today}

\begin{document}
\maketitle
\tableofcontents

\section{引言}
正文内容...

\end{document}
```

## 踩坑记录

- **中文字体**：XeLaTeX + ctex 包最稳定，pdflatex 不支持中文
- **图片路径**：使用 `\includegraphics[width=\textwidth]{images/fig1.png}`
- **表格跨页**：用 `longtable` 包替代 `tabular`
- **参考文献**：推荐用 `biblatex` + Biber 替代传统 BibTeX
