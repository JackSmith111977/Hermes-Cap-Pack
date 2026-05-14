---
type: concept
domain: doc-engine
keywords: [document-generation, pdf, layout, rendering]
created: 2026-05-14
---

# Document Generation

## Definition

Document Generation is the process of programmatically creating formatted documents from data and templates. It encompasses multiple output formats (PDF, DOCX, HTML, EPUB, LaTeX, Markdown) and involves layout composition, typography, asset embedding, and content flow. Unlike manual document creation, programmatic generation enables repeatability, version control, and integration into automated workflows.

## Core Concepts

### Document Generation Pipeline

```
Data Source → Template Engine → Layout Composition → Rendering → Output
   │              │                   │                  │          │
 JSON/API    Jinja2/Mustache     Page flow, fonts    wkhtmltopdf   PDF
 Database    Pandoc templates    Stylesheets         Prince XML    DOCX
 YAML        Custom directives   Grid systems        WeasyPrint    HTML
                                                                   EPUB
```

### Format Selection Criteria

| Format | Best For | Limitations |
|:-------|:---------|:------------|
| **PDF** | Fixed layout, printing, distribution | Not easily editable, accessibility challenges |
| **DOCX** | Editing, collaboration, track changes | Inconsistent rendering across Word versions |
| **HTML** | Web publishing, responsive, accessibility | No fixed pagination, print CSS complexity |
| **LaTeX** | Academic papers, technical docs | Steep learning curve, limited design flexibility |
| **EPUB** | E-readers, books, mobi conversion | Limited complex layout support |
| **Markdown** | Docs, README, simple formatting | No native page layout control |

### Key Challenges

- **CJK font handling**: Chinese/Japanese/Korean text requires specific font configuration and often causes rendering issues in PDF engines
- **Page break control**: Orphan/widow control, table splitting, image placement — each renderer handles differently
- **Cross-format consistency**: A document designed for PDF may not translate well to EPUB or HTML
- **Performance**: Large documents (1000+ pages) stress memory and rendering time, especially with complex tables and images

## Relationships

- **Implements**: `doc-design` (document design system), `pdf-layout` (PDF-specific layout)
- **Supported by**: `markdown-guide`, `latex-guide`, `html-guide` (format-specific skills)
- **Quality checked by**: `vision-qc-patterns` (visual quality control), `readme-for-ai` (AI-readable docs)
- **Used in**: Report generation, book publishing, documentation pipelines
