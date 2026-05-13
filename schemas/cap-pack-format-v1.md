# 📦 Capability Pack 格式规范 v1

> **版本**: 1.0.0 · **状态**: `draft` · **更新**: 2026-05-13
> **作用**: 这是能力包的标准格式定义，所有模块必须遵循此规范。

---

## 一、文件结构

```
cap-pack/{name}/
├── cap-pack.yaml          ← 模块清单（必需）
├── SKILLS/                ← 技能目录（至少一个）
│   ├── skill-a.md
│   └── skill-b.md
├── EXPERIENCES/           ← 经验目录（可选）
│   ├── pitfall-foo.md     # type: pitfall
│   └── decision-bar.md    # type: decision-tree
└── MCP/                   ← MCP 配置目录（可选）
    └── server.yaml
```

## 二、cap-pack.yaml 字段定义

### 2.1 顶层字段

| 字段 | 类型 | 必需 | 说明 |
|:-----|:----:|:----:|:------|
| `name` | string | ✅ | 模块 ID，小写字母+连字符，全局唯一 |
| `version` | string | ✅ | 语义版本号 `MAJOR.MINOR.PATCH` |
| `type` | string | ✅ | 固定值 `capability-pack` |
| `classification` | string | ✅ | `domain`（推荐）/ `toolset` / `skill` |
| `display_name` | string | ✅ | 人类可读名称 |
| `description` | string | ✅ | 模块功能描述（1-3 句话） |
| `author` | string | ❌ | 作者/维护者 |
| `created` | date | ✅ | 创建日期 `YYYY-MM-DD` |
| `updated` | date | ✅ | 最后更新日期 `YYYY-MM-DD` |

### 2.2 `compatibility` — 兼容性声明

| 字段 | 类型 | 必需 | 说明 |
|:-----|:----:|:----:|:------|
| `agent_types` | array | ✅ | 支持的 Agent 类型列表，如 `[hermes, claude-code, codex-cli]` |
| `requires_mcp` | bool | ❌ | 是否需要 MCP 运行时（默认 false） |
| `requires_network` | bool | ❌ | 是否需要网络访问（默认 false） |
| `requires_env` | array | ❌ | 需要的环境变量列表 |

### 2.3 `dependencies` — 依赖声明

| 字段 | 类型 | 必需 | 说明 |
|:-----|:----:|:----:|:------|
| `cap_packs` | array | ❌ | 依赖的其他能力包 `[{name, version}]` |
| `system_packages` | array | ❌ | 系统包（apt/dnf 名称列表） |
| `python_packages` | array | ❌ | Python 包列表 |
| `node_packages` | array | ❌ | Node.js 包列表 |

### 2.4 `skills` — 技能列表

每项：

| 字段 | 类型 | 必需 | 说明 |
|:-----|:----:|:----:|:------|
| `id` | string | ✅ | 技能唯一 ID |
| `path` | string | ✅ | 相对于包根目录的路径 |
| `version` | string | ❌ | 技能版本（默认继承包版本） |
| `description` | string | ✅ | 一句话说明 |
| `tags` | array | ❌ | 标签列表 |
| `experience_refs` | array | ❌ | 关联的经验 ID 列表 |

### 2.5 `experiences` — 经验列表

每项：

| 字段 | 类型 | 必需 | 说明 |
|:-----|:----:|:----:|:------|
| `id` | string | ✅ | 经验唯一 ID |
| `path` | string | ✅ | 相对于包根目录的路径 |
| `type` | string | ✅ | 类型: `pitfall` / `decision-tree` / `comparison` / `lesson` |
| `description` | string | ✅ | 一句话说明 |
| `skill_refs` | array | ❌ | 关联的技能 ID 列表 |

### 2.6 `mcp_servers` — MCP 服务列表

每项：

| 字段 | 类型 | 必需 | 说明 |
|:-----|:----:|:----:|:------|
| `id` | string | ✅ | MCP 服务 ID |
| `command` | string | ❌ | 启动命令（与 url 二选一） |
| `url` | string | ❌ | 远程 URL（与 command 二选一） |
| `transport` | string | ❌ | `stdio` / `sse` / `streamable-http`（默认 stdio） |
| `tools` | array | ❌ | 可用工具列表 |
| `env` | object | ❌ | 需要的环境变量键值对 |

### 2.7 `config_defaults` — 默认配置

自由格式键值对，适配器将其写入 Agent 的对应配置位置。

### 2.8 `hooks` — 生命周期钩子

| 字段 | 类型 | 必需 | 说明 |
|:-----|:----:|:----:|:------|
| `on_activate` | array | ❌ | 安装/激活时执行 |
| `on_deactivate` | array | ❌ | 卸载/停用时执行 |
| `on_update` | array | ❌ | 版本更新时执行 |

每项 hook：

| 字段 | 类型 | 说明 |
|:-----|:----:|:------|
| `type` | string | `shell` / `notify` / `python` |
| `command` | string | type=shell 时的命令 |
| `message` | string | type=notify 时的消息 |
| `code` | string | type=python 时的代码片段 |

---

## 三、完整示例

```yaml
name: doc-engine
version: 1.0.0
type: capability-pack
classification: domain
display_name: 文档生成引擎
description: >
  全套文档生成能力——PDF 排版、PPT 演示文稿、DOCX 报告、
  HTML 网页、Markdown 文档、LaTeX 论文和 EPUB 电子书。
  涵盖字体配置、中文排版、跨平台兼容性等实战经验。
author: boku (Emma/小玛)
created: 2026-05-13
updated: 2026-05-13

compatibility:
  agent_types: [hermes, claude-code, codex-cli]
  requires_mcp: false
  requires_network: false
  requires_env: []

dependencies:
  system_packages:
    - libpango-1.0-0
    - libpangocairo-1.0-0
    - libgdk-pixbuf2.0-0
  python_packages:
    - weasyprint>=60
    - python-pptx>=0.6
    - python-docx>=1.0
    - reportlab>=4.0

skills:
  - id: pdf-layout
    path: SKILLS/pdf-layout.md
    version: 1.2.0
    description: 使用 ReportLab 和 WeasyPrint 生成 PDF
    tags: [pdf, reportlab, weasyprint, 中文排版]
    experience_refs: [wqy-font-fallback, reportlab-cjk-encoding]

  - id: pptx-guide
    path: SKILLS/pptx-guide.md
    version: 1.1.0
    description: 使用 python-pptx 创建 PPT
    tags: [pptx, presentation, python-pptx]
    experience_refs: [pptx-chinese-fonts]

  - id: docx-guide
    path: SKILLS/docx-guide.md
    version: 1.0.0
    description: 使用 python-docx 创建 DOCX
    tags: [docx, word, python-docx]

  - id: html-guide
    path: SKILLS/html-guide.md
    version: 1.0.0
    description: 使用 HTML/CSS 排版网页文档
    tags: [html, css, web]

  - id: markdown-guide
    path: SKILLS/markdown-guide.md
    version: 1.0.0
    description: Markdown 写作与 Pandoc 转换
    tags: [markdown, pandoc]

  - id: latex-guide
    path: SKILLS/latex-guide.md
    version: 1.0.0
    description: LaTeX 学术论文排版
    tags: [latex, academic, thesis]

  - id: epub-guide
    path: SKILLS/epub-guide.md
    version: 1.0.0
    description: 使用 ebooklib 生成 EPUB
    tags: [epub, ebook, ebooklib]

  - id: doc-design
    path: SKILLS/doc-design.md
    version: 1.0.0
    description: 文档排版设计索引与路由
    tags: [design, routing]

  - id: pdf-pro-design
    path: SKILLS/pdf-pro-design.md
    version: 1.0.0
    description: PDF 专业排版设计系统
    tags: [pdf, design, advanced]
    experience_refs: [design-crap-principles]

  - id: pdf-render-comparison
    path: SKILLS/pdf-render-comparison.md
    version: 1.0.0
    description: PDF 渲染工具选型决策树
    tags: [pdf, decision, comparison]

  - id: vision-qc-patterns
    path: SKILLS/vision-qc-patterns.md
    version: 1.0.0
    description: PDF 排版错误视觉检测模式库
    tags: [pdf, qc, vision, patterns]

  - id: readme-for-ai
    path: SKILLS/readme-for-ai.md
    version: 1.0.0
    description: 模型友好型 README 编写方法论
    tags: [readme, documentation, ai-agent]

experiences:
  - id: wqy-font-fallback
    path: EXPERIENCES/wqy-font-fallback.md
    type: pitfall
    description: WQY 微米黑字体在 ReportLab 中的注册与回退
    skill_refs: [pdf-layout, pdf-pro-design]

  - id: reportlab-cjk-encoding
    path: EXPERIENCES/reportlab-cjk-encoding.md
    type: pitfall
    description: ReportLab 中文字体编码问题与解决方案
    skill_refs: [pdf-layout]

  - id: pptx-chinese-fonts
    path: EXPERIENCES/pptx-chinese-fonts.md
    type: pitfall
    description: python-pptx 中文字体名称映射与跨平台兼容
    skill_refs: [pptx-guide]

  - id: design-crap-principles
    path: EXPERIENCES/design-crap-principles.md
    type: comparison
    description: CRAP 设计原则（对比/重复/对齐/亲近）的排版应用
    skill_refs: [pdf-pro-design, doc-design]

  - id: pdf-tool-decision-tree
    path: EXPERIENCES/pdf-tool-decision-tree.md
    type: decision-tree
    description: WeasyPrint vs ReportLab vs LaTeX 选型决策
    skill_refs: [pdf-layout, pdf-render-comparison, latex-guide]

mcp_servers: []

config_defaults:
  pdf_font: WQY-ZenHei
  pdf_dpi: 300
  presentation_theme: dark-minimal

hooks:
  on_activate:
    - type: shell
      command: pip install weasyprint python-pptx python-docx reportlab ebooklib
  on_deactivate:
    - type: notify
      message: doc-engine 已卸载，相关技能将不可用
```

---

## 四、版本号规则

```
MAJOR.MINOR.PATCH

MAJOR: 格式不兼容变更（字段删除/重命名/必需性变更）
MINOR: 新增能力（新技能/新经验/新 MCP 配置）
PATCH: 内容修正（技能步骤更新/经验补充/文档修正）
```

## 五、与现有体系的映射

| 能力包组件 | Hermes 对应 | Claude Code 对应 | Codex CLI 对应 |
|:-----------|:------------|:-----------------|:---------------|
| SKILLS/ | `~/.hermes/skills/{cat}/{id}/SKILL.md` | `~/.claude/skills/{pack}/{id}.md` | `.codex/rules/{id}.md` |
| EXPERIENCES/ | skill references/ 目录 | 嵌入 CLAUDE.md | 嵌入 rules 文件 |
| MCP/ | `config.yaml` → `mcpServers` | `claude.json` → `mcpServers` | `.codex/mcp.json` |
| hooks | 安装后执行 shell | 安装后执行 shell | 安装后执行 shell |
| config_defaults | Profile 配置覆盖 | 无原生等价物 | 无原生等价物 |
