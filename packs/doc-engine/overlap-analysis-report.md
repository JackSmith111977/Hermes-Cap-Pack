# Doc-Engine 能力包 12 Skill 功能重叠度深度分析报告

> 分析日期: 2026-05-13
> 分析工具: 手工读取 SKILL.md + 目录结构扫描

---

## 一、各 Skill 元数据汇总

| # | Skill 名称 | 版本 | 描述摘要 | Tags (核心) | 行数/大小 | 子目录 | 依赖 | 设计模式 |
|:-|:---|:---:|:---|:---|:---:|:---|:---|:---:|
| 1 | **pdf-layout** | 2.0.0 | ReportLab 高级中文 PDF 排版 | pdf, reportlab, chinese, typography | 188/6.2K | references/ (3), checklists/ (1) | doc-design, mermaid-guide | generator |
| 2 | **pdf-pro-design** | 2.0.0 | 专业 PDF 设计系统 (CRAP/CSS) | (无 YAML tags) 排版设计, 优秀文档 | 133/5.1K | 无 | visual-aesthetics, web-access | pipeline |
| 3 | **pdf-render-comparison** | 1.0.0 | PDF 工具选型决策树 | pdf 工具选型, pdf 渲染对比 | 184/6.8K | references/ (2) | pdf-layout, pdf-pro-design | Tool Wrapper |
| 4 | **pptx-guide** | 1.0.0 | PPT 原子操作 (python-pptx) | powerpoint, pptx, presentation | 225/6.5K | references/ (1) | - | doc-generation |
| 5 | **docx-guide** | 1.0.0 | Word 原子操作 (python-docx) | word, docx, document, office | 148/3.4K | 无 | - | doc-generation |
| 6 | **html-guide** | 1.0.0 | HTML/CSS 打印网页 | html, css, web, print | 74/1.9K | 无 | - | doc-generation |
| 7 | **markdown-guide** | 1.0.0 | Markdown 写作+转换 | markdown, pandoc, writing | 109/1.9K | 无 | - | doc-generation |
| 8 | **latex-guide** | 1.0.0 | LaTeX 学术论文排版 | latex, academic, paper, thesis | 93/1.8K | 无 | - | doc-generation |
| 9 | **epub-guide** | 1.0.0 | EPUB 电子书生成 | epub, ebook, publishing | 96/2.4K | 无 | - | doc-generation |
| 10 | **doc-design** | 5.1.0 | 文档排版路由/索引 | document, design, formatting, **index** | 141/4.7K | references/ (14), pdf-layout-reportlab/, pdf-layout-weasyprint/, html-presentation/ | 8 个子 skill | **index** |
| 11 | **vision-qc-patterns** | 1.0.0 | 排版错误模式库 | 排版错误, 视觉质检, vision qc | 214/5.7K | scripts/ (1), references/ (1) | pdf-layout, pdf-pro-design | **Reviewer** |
| 12 | **readme-for-ai** | 1.1.0 | AI 友好 README 方法论 | documentation, readme, ai-friendly | 151/4.1K | references/ (1) | - | methodology |

> **注意**: ~/.hermes/skills/readme-for-ai/ 目录不存在（未安装到 Hermes），只存在于 cap-pack 仓库中。

---

## 二、功能重叠度分析

### 2.1 🔴 高重叠区域：PDF 技能群（4 个 Skill 严重重叠）

#### 重叠矩阵

| | pdf-layout | pdf-pro-design | pdf-layout-reportlab (doc-design 内) | pdf-layout-weasyprint (doc-design 内) |
|:---|:---:|:---:|:---:|:---:|
| **pdf-layout** | — | 中 | **高** | 中 |
| **pdf-pro-design** | 中 | — | 低 | **高** |
| **pdf-layout-reportlab** | **极高** | 低 | — | 低 |
| **pdf-layout-weasyprint** | 中 | **高** | 低 | — |

**详细分析：**

#### A) `pdf-layout` vs `pdf-layout-reportlab`（doc-design 子 skill）— 重叠度 90%

| 对比维度 | pdf-layout | pdf-layout-reportlab |
|:---|:---|:---|
| 核心内容 | ReportLab + WQY ZenHei 中文 PDF | ReportLab + WQY ZenHei 中文 PDF |
| 字体方案 | WQY > CIDFONT, TTC CFF 检测 | 相同的 WQY ZenHei/STSong-Light |
| Table 处理 | Paragraph 包装、斑马纹 | Paragraph 包装 |
| 版本 | v2.0.0 | v1.0.0 |
| 位置 | 独立 SKILL 目录 | doc-design 子目录 |

**结论**: 这两个 skill 功能几乎完全重复。`pdf-layout` 是 v2.0（更完整），`pdf-layout-reportlab` 是 v1.0（更基础）。应合并为一个。

#### B) `pdf-pro-design` vs `pdf-layout-weasyprint`（doc-design 子 skill）— 重叠度 70%

| 对比维度 | pdf-pro-design | pdf-layout-weasyprint |
|:---|:---|:---|
| 核心工具 | WeasyPrint + Chrome | WeasyPrint |
| CSS 内容 | CRAP + @page + 分页控制 | @font-face + 中文 CSS |
| 场景 | 技术/商务/学术 三大模板 | 通用中文 PDF |
| 设计理论 | CRAP 原则完整 | 无设计理论 |

**结论**: `pdf-pro-design` 是 `pdf-layout-weasyprint` 的超集（多了 CRAP 理论和 Chrome 支持）。建议合并。

#### C) 重叠根因分析

所有 PDF 技能的共同覆盖领域：
- **中文字体配置**：WQY ZenHei / Noto Sans CJK / CIDFont — 4 个 skill 都提到
- **@font-face / TTFont 注册**：重复代码片段
- **Table 样式**：Paragraph 包装、斑马纹
- **分页控制**：page-break / keepWithNext

### 2.2 🟡 中等重叠：原子 Guide 系列（6 个 Skill）

| skill | 格式 | 核心库 | 设计模式 | 是否包含设计理论 |
|:---|:---|:---|:---|:---:|
| docx-guide | .docx | python-docx | CRAP（引用 doc-design） | ❌ |
| pptx-guide | .pptx | python-pptx | **自带 CRAP 完整** | ✅ |
| html-guide | .html | (原生) | 基础 CSS | ❌ |
| markdown-guide | .md | pandoc | 语法参考 | ❌ |
| latex-guide | .tex | xelatex | 学术模板 | ❌ |
| epub-guide | .epub | ebooklib | 电子书标准 | ❌ |

**重叠点：**
1. **CRAP 设计原则重复** — `pdf-pro-design` 有完整 CRAP，`pptx-guide` 有 CRAP，`doc-design` 也有 CRAP。重复了 3 次。
2. **pandoc 转换命令重复** — `markdown-guide` 有 pandoc 转换表，`doc-design` 也有 pandoc 转换表，`pdf-render-comparison` 也提到 pandoc。
3. **工具安装检测重复** — 每个 skill 开头都有 `pip install` 和 `venv` 创建命令。

**结论**: 这 6 个 skill 的功能重叠度本身不高（各有格式边界），但**共享的辅助内容**（CRAP、pandoc、安装检测）在多个 skill 中重复出现。

### 2.3 🟢 低重叠：辅助/跨切面 Skill

| Skill | 与谁重叠 | 重叠度 | 说明 |
|:---|:---|:---:|:---|
| **pdf-render-comparison** | pdf-layout, pdf-pro-design | 30% | 决策树内容与两个 PDF skill 中的"选型"段落有交叉 |
| **vision-qc-patterns** | pdf-pro-design (视觉质检段落) | 40% | pdf-pro-design 有"视觉质检流程"节，vision-qc-patterns 将其扩展为完整模式库 |
| **readme-for-ai** | 其余 11 个 skill | 0% | **完全不同的领域**— 不是文档生成，是撰写方法论 |

---

## 三、角色不当分析

### 3.1 实为"经验/决策树"而非完整 Skill

| Skill | 实际角色 | 判定依据 |
|:---|:---|:---|
| **pdf-render-comparison** | 🟠 **决策树/经验** | 全部内容是「决策树 + 对比矩阵 + 代码模板」。不生成任何文档，不涉及独特的工作流，只是一个**选型指南**。should 被降级为 EXPERIENCES/ |
| **vision-qc-patterns** | 🟢 **合理存在**（但类型特殊） | 虽然是错误模式库（更像知识库），但配合 scripts/vision_qc.py 和 vision_analyze 工具有明确的工作流，且使用 `design_pattern: Reviewer`。属于有独立价值的辅助 skill，建议保留但明确标记为 "knowledge-base"。 |
| **markdown-guide** | 🟡 **接近经验** | 内容非常简单（74 行基础语法 + pandoc 命令），大部分是 Markdown 语法教程而非 Hermes 特有技能。语法教程本应成为外部文档而非 skill。 |

### 3.2 实为"路由/索引"Skill

| Skill | 判定 |
|:---|:---|
| **doc-design** | ✅ **明确的路由索引 skill**。其 `design_pattern: index` 正确标识了角色。 |

### 3.3 领域不当

| Skill | 问题 |
|:---|:---|
| **readme-for-ai** | ❌ **不属于 doc-engine 能力包**。该 skill 是"如何为 AI Agent 写 README"的方法论，与「文档生成引擎」无直接关系。建议移入独立的 documentation-methodology 能力包或 communication 能力包。 |

---

## 四、doc-design 路由索引 Skill 深度评估

### 4.1 现状

- **版本**: v5.1.0（最高的版本号，暗示经历大量迭代）
- **角色**: 显式声明为 `design_pattern: index`，充当所有文档格式的统一入口
- **子结构**:
  ```
  doc-design/
  ├── SKILL.md                 ← 路由表 + CRAP 原则 + 转换矩阵
  ├── pdf-layout-reportlab/    ← 子 skill
  ├── pdf-layout-weasyprint/   ← 子 skill
  ├── html-presentation/       ← 子 skill
  └── references/ (14 文件)    ← 各格式独立参考 + 设计指南
  ```

### 4.2 为什么 doc-design 存在？

**直接原因：原子 Skill 太分散，缺少统一入口。**

12 个 skill 中，6 个格式原子 skill（docx/pptx/html/md/latex/epub）+ 3 个 PDF skill（layout/pro-design/render-comparison）+ 1 个视觉质检 = 10 个用 `"文档"` 或 `"排版"` 等通用关键词触发的 skill。如果没有 doc-design，AI 需要自己判断该加载哪个——doc-design 提供了**集中路由**。

### 4.3 doc-design 自身的问题

| 问题 | 严重程度 | 说明 |
|:---|:---:|:---|
| **references/ 膨胀** | 🔴 高 | 14 个参考文件几乎覆盖了所有原子 skill 的内容，实际上制造了**重复维护**（doc-design 的 references/docx-guide.md 与 docx-guide/SKILL.md 内容重叠） |
| **内含子 skill** | 🟠 中 | pdf-layout-reportlab 和 pdf-layout-weasyprint 应该与独立的 pdf-layout / pdf-pro-design 合并，而不是藏在 doc-design 下 |
| **CRAP 内容重复** | 🟡 低 | doc-design 自带的 CRAP 原则与 pdf-pro-design 和 pptx-guide 中的 CRAP 重复 |
| **依赖声明混乱** | 🔴 高 | depends_on 写的是 "pdf-layout-reportlab" 和 "pdf-layout-weasyprint"（内嵌路径），但 cap-pack 声明的是 "pdf-layout"（独立路径）。同一件事有不同名字。 |

### 4.4 本质判断

> **doc-design 是一个「能力包中能力包」的过度工程产物。** 它的存在是因为 PDF 相关的 skill 没有合理拆分——如果 `pdf-layout` 合并掉 `pdf-layout-reportlab`、`pdf-pro-design` 合并掉 `pdf-layout-weasyprint`，doc-design 的子 skill 数量会减少一半。同时它的 references/ 目录试图"缓存"其他 skill 的内容，导致碎片化加剧。

---

## 五、结构优化建议

### 5.1 合并方案（推荐）

```
现状 (12 skills)                                   建议 (7-8 skills)
─────────────────────────────────                  ──────────────────────────
pdf-layout (独立)                ── 合并 ──→  pdf-layout v3 (ReportLab + WQY)
pdf-layout-reportlab (doc-design下) ── 合并 ──→  (并入 pdf-layout)
                                                                              
pdf-pro-design (独立)            ── 合并 ──→  pdf-pro-design v3 (WeasyPrint + CRAP)
pdf-layout-weasyprint (doc-design下) ── 合并 ─(并入 pdf-pro-design)
                                                                              
pdf-render-comparison (独立)     ── 降级 ──→  EXPERIENCES/pdf-tool-decision-tree.md
                                                                              
pptx-guide (独立)                ── 保留 ──→  pptx-guide
docx-guide (独立)                ── 保留 ──→  docx-guide
html-guide (独立)                ── 保留 ──→  html-guide
markdown-guide (独立)            ── 保留 ──→  markdown-guide
latex-guide (独立)               ── 保留 ──→  latex-guide
epub-guide (独立)                ── 保留 ──→  epub-guide
                                                                              
doc-design (路由索引)            ── 精简 ──→  doc-design v6 (只保留路由 + 转换表，移除 references/ 和子skill)
                                                                              
vision-qc-patterns (独立)        ── 保留 ──→  vision-qc-patterns (标记为 knowledge-base)
                                                                              
readme-for-ai (独立)             ── 移出 ──→  移出 doc-engine, 放入独立能力包
```

### 5.2 具体合并路径

| 合并动作 | 目标 | 收益 |
|:---|:---|:---|
| pdf-layout + pdf-layout-reportlab → pdf-layout@v3 | 1 个 ReportLab PDF skill | 减少 1 个 skill，消除 90% 内容重复 |
| pdf-pro-design + pdf-layout-weasyprint → pdf-pro-design@v3 | 1 个 WeasyPrint/CSS PDF skill | 减少 1 个 skill，消除 70% 内容重复 |
| pdf-render-comparison → EXPERIENCES/ | 1 个经验文档 | 消除决策树 vs skill 的角色混淆 |
| readme-for-ai 移出 | 0 个（移出能力包） | 恢复能力包领域一致性 |
| doc-design references/ → 删除（改用 skill_view 引用） | references/ 从 14 文件 → 0 | 消除重复维护 |

### 5.3 合并后的能力包结构

```
doc-engine/
├── cap-pack.yaml
├── SKILLS/
│   ├── pdf-layout/          ← 合并后的 ReportLab PDF skill
│   ├── pdf-pro-design/      ← 合并后的 WeasyPrint PDF + CRAP skill
│   ├── pptx-guide/
│   ├── docx-guide/
│   ├── html-guide/
│   ├── markdown-guide/
│   ├── latex-guide/
│   ├── epub-guide/
│   ├── doc-design/          ← 精简为纯路由 (无 references 子skill)
│   └── vision-qc-patterns/  ← 保留
├── EXPERIENCES/
│   ├── pdf-tool-decision-tree.md  ← 从 pdf-render-comparison 降级
│   └── ... (其他经验)
```

---

## 六、总结

### 核心发现

1. **PDF 领域严重过载**：4 个 skill 覆盖 PDF（pdf-layout, pdf-layout-reportlab, pdf-pro-design, pdf-layout-weasyprint），内容重叠度高达 70-90%，完全可以合并为 2 个。

2. **pdf-render-comparison 角色不当**：它是一个决策树/经验文档，不应以 standalone skill 存在。应降级为 EXPERIENCES/。

3. **doc-design 是"救火队员"**：它的高版本号 (v5.1.0) 和 14 个 references/ 文件恰恰证明了原子 skill 拆分得过于零散，不得不造一个中心路由来管理碎片。

4. **readme-for-ai 领域不符**：与"文档生成引擎"无关，应移出。

5. **references/ 膨胀是关键问题**：doc-design 的 14 个参考文件与各个独立 skill 的 SKILL.md 内容大量重叠，造成双向维护负担。

### 量化重叠度

| 分组 | Skill 数量 | 建议数量 | 重叠度 | 操作 |
|:---|:---:|:---:|:---:|:---|
| PDF 生成 (ReportLab) | 2 | 1 | 90% | 合并 |
| PDF 生成 (WeasyPrint/设计) | 2 | 1 | 70% | 合并 |
| PDF 工具选型 | 1 | 0 (降级为经验) | 100% | 降级 |
| 格式原子 skill (pptx/docx/html/md/latex/epub) | 6 | 6 | 10% | 保留 |
| 路由索引 | 1 | 1 | 0% | 精简 |
| 视觉质检 | 1 | 1 | 0% | 保留 |
| 领域不符 | 1 | 0 | 0% | 移出 |
| **总计** | **12** | **8-9** | | |

### 风险提示

合并需要注意：
- `pdf-layout` (v2.0.0) 和 `pdf-layout-reportlab` (v1.0.0) 的版本号要协调
- 合并后更新所有 depends_on 和 related_skills 引用
- doc-design 的 references/ 删除后，确保 skill_view 的路径解析能正确回退到独立 SKILL.md
- hermes.yaml 中的 `pdf-layout-reportlab` 路径（内嵌在 doc-design/）与独立 `pdf-layout` 路径可能冲突
