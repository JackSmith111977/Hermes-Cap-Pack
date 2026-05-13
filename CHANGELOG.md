# Changelog

## [0.2.0] — 2026-05-13

### Added
- EPIC-002: Skill 树状层次管理与健康度优化系统
  - `docs/EPIC-002-tree-health.md` — EPIC 文档（含研究记录、架构决策、交付物）
  - `docs/SPEC-005-tree-index.md` — 树状索引系统规范（三层模型 + CLI 接口）
  - `docs/SPEC-006-quality-health.md` — SQS 质量评分系统规范（五维评分 + 生命周期状态机）
  - `docs/stories/STORY-011~015` — 5 个 Story 文档（索引整合/SQS嵌入/cron报告/仪表盘/合并建议）
- New pack: `packs/quality-assurance/`（质量保障能力包，含 SQS 评分 + 审计 + 树索引）
- Scripts integrated into cap-pack project:
  - `scripts/skill-tree-index.py` — 三层树状索引生成器
  - `scripts/skill-quality-score.py` — SQS 五维质量评分引擎
  - `scripts/skill-lifecycle-audit.py` — 生命周期审计 + deprecate/revive 管理
- Research report enhancement: `reports/skill-tree-architecture-research.html`
  - 所有来源链接改为可点击 `<a>` 标签（arxiv 论文、业界网站等）

### Changed
- README 新增 EPIC-002 状态追踪表、项目结构扩展（6 个 scripts + 2 packs）
- 分类体系 #6 `quality-assurance` 新增 SQS评分/生命周期审计能力描述

## [0.1.0] — 2026-05-13

### Added
- Initial project structure (Phase 0: Feasibility Research)
- EPIC-001: Capability modularization feasibility study
- SPEC-001: Module splitting (18 modules + 3 extension slots)
- SPEC-002: Module lifecycle management
- SPEC-003: Module iteration loop
- SPEC-004: Cross-agent adaptation (UCA architecture)
- Lifecycle tracking report (dark theme HTML)
- Phase 1 kickoff: Git init, cap-pack.yaml format design
