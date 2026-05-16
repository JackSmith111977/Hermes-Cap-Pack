# Changelog

## [1.0.0] — 2026-05-16 🎉

### Added
- **EPIC-005: Skill 治理引擎** — 全生命周期质量门禁与 Cap-Pack 自动适配
  - Phase 0: 统一标准框架 L0-L3 (Level 0: 兼容层 / Level 1: 强制层 / Level 2: 推荐层 / Level 3: 生态层)
  - Phase 1: 核心引擎 MVP — Scanner + CLI scan/watcher/rules + CheckResult 模型
  - Phase 2: Hermes 深度集成 — pre_flight gate + cron watcher + SRA 质量注入 + HTML 报告
  - Phase 3: 多 Agent 适配层 — Hermes/OpenCode/Claude Code/OpenClaw 适配器
  - **15 个 Stories · 41 个新文件 · ~2691 LOC**
- **EPIC-006: Governance Fix Engine** — 自动修复 + 跨 Agent 适配闭环
  - Phase 0: Fix 基础设施 — FixRule 抽象层 + FixDispatcher + CLI fix + .bak 备份
  - Phase 1: 确定性修复 — F001 SKILL.md 生成 / F006 classification + F007 triggers / H001+H002 树簇
  - Phase 2: LLM 辅助修复 — E001 SRA 元数据 / E002 跨平台兼容性 / E005 断裂链接
  - Phase 3: 跨 Agent 文档 — README v2.0 (readme-for-ai) / ADAPTER_GUIDE / QUICKSTART
  - **12 个 Stories · 全部 202 个测试通过**
- **治理修复引擎 Bug 修复**: `_setup_fix_dispatcher()` 不注册 FixRule 的 TODO 已实现
- **全项目治理修复 v1**: 对所有 17 个能力包执行 E001/E002/F001 自动修复，合计 **174 fixes** · 0 errors
  - L3 Ecosystem Score: 全包 60% → 80% ↑20%
- **治理引擎修复包** (`packages/skill-governance/`): 正式 Python 包化
  - `skill_governance/cli/` — CLI 入口 (scan/fix/watcher/rules)
  - `skill_governance/fixer/` — FixRule + Dispatcher + LLM Assist
  - `skill_governance/scanner/` — L0-L4 扫描器
  - `skill_governance/adapter/` — 四目标适配器
  - `skill_governance/watcher/` — Fingerprint 变更监控
  - `skill_governance/reporter/` — HTML + JSON 报告
  - `skill_governance/integration/` — pre_flight / cron / SRA 注入
  - **61 个单元测试 (新增)**
- **跨 Agent 文档三件套**: README.md (readme-for-ai 标准) + ADAPTER_GUIDE.md + QUICKSTART.md

### Changed
- README.md 全面升级 v2.0 — readme-for-ai 11 条标准 + 三列 CLI 参考表
- 完整全量测试: 从 141 → **202 个测试**
- 项目状态全面对齐: project-state.yaml + project-report.json + EPIC 文档同步

### Fixed
- 文档-代码对齐漂移 6 处（EPIC-006 状态/EPIC-005 计数/测试数/CHANGELOG/版本号）
- schema 版本命名对齐 (v0.9.1schema → v1.0.0schema)

## [0.9.1] — 2026-05-14

### Added
- **doc-engine 质量升级**: 三层改造 (L2 Experiences + 微技能降级) + 健康 KPI + SRA 验证
- **合并工作流**: knowledge-base → learning-engine + BMAD 跨层合并 + 微技能降级文档化
- **治理引用**: `references/governance-fix-strategies.md` — 扫描→修复闭环设计
- **修复模式速查**: `references/fix-pattern-cookbook.md` — 7 种可复用代码模式

### Changed
- EPIC-005 统一标准框架完成（4 层级 + 可执行门禁）
- CHI 基线锁定: doc-engine 0.6388 → 目标 ≥ 0.75

## [0.8.0] — 2026-05-14

### Added
- **EPIC-004: 能力包质量升级** — 增量循环 · 三层改造 + 健康度 + 合并优化
  - **12 个 Stories** 全面交付: 后置质量升级 + L2 Experiences + CHI 健康度 + 合并优化 + 门禁固化
  - 三层改造 (L1 Skills → L2 Experiences → L3 Knowledge)
  - doc-engine 健康诊断: 17 skills → 10 skills + 11 experiences
  - 六维 KPI + CHI 综合健康指数
  - 合并建议引擎 + BMAD 冗余检测
- **外部集成架构** (External Integration Pattern): 五层纯外部方案
- **多 Agent CLI 架构**: Adapter Registry + `--target hermes|opencode|auto`
- **验证门禁模式** (Verification Gate Pattern): 安装后四层验证 + 自动回滚
- **治理修复引擎架构** (Governance Fix Engine Architecture): 确定性+LLM 混合方案

### Changed
- CI 管道新增: chi-gate / validate-pack 增强 / pre-push 门禁强制
- 项目结构: 18 个能力包已完成品质基线

## [0.7.1] — 2026-05-14

### Added
- **统一状态机管理中枢** (`docs/project-state.yaml` + `scripts/project-state.py`): 所有项目实体状态的唯一真相来源
  - 8 个管理命令: status / verify / scan / sync / gate / transition / list / history
  - 每次状态变更带门禁检查 + 日志审计 + 自动纠偏
  - 已融入 SDD / Dev / QA / Startup 四个工作流
- **沉淀为 Hermes Skill** (`unified-state-machine`): 可复用的项目状态管理技能
- **CI 门禁**: `.github/workflows/ci.yml` 新增 `project-state.py verify` 步骤
- **SPEC-2-4**: 项目报告生成器工作流集成规范
- **STORY-2-4-1**: project-report-generator skill 创建与 SDD 工作流集成

### Changed
- 四个工作流 skill 新增 `unified-state-machine` 依赖引用
- 修复 8 个状态漂移（EPIC-001 Story 状态与文档不一致）

## [0.7.0] — 2026-05-13

### Added
- **第三方适配器开发指南** (`docs/developer-guide-adapter.md`): 完整文档指引
  - AgentAdapter Protocol 详解 + 参数/返回值说明
  - 6 步实现流程（骨架→安装→CLI 注册→测试→对等性→发布）
  - 完整 Cursor 适配器示例（可直接作为模板）
  - 9 种 Agent 路径速查表
  - 适配器设计决策模板 + 测试指南
- **SPEC-1-4 全部 6 个 AC 完成** 🎉

### Changed
- README 新增 OpenCodeAdapter + developer-guide 条目

## [0.6.0] — 2026-05-13

### Added
- **OpenCodeAdapter** (`scripts/adapters/opencode.py`): OpenCode CLI Agent 适配器
  - Skill 安装到 `~/.config/opencode/skills/{id}/SKILL.md`，自动转换 frontmatter 为 OpenCode 兼容格式
  - MCP 配置注入到 `~/.config/opencode/opencode.json` 的 `mcp` 字段
  - 利用 OpenCode 对 `~/.claude/skills/` 的原生兼容性（自动兼容 Claude Code）
- **CLI 多 Agent 支持**: 所有命令新增 `--target` 参数（`hermes`/`opencode`/`auto`）
  - `cap-pack install packs/doc-engine --target opencode` — 安装到 OpenCode
  - `cap-pack remove doc-engine --target opencode` — 从 OpenCode 卸载
  - `cap-pack list --target opencode` — 列出 OpenCode 已安装
- **跨 Agent 对等性测试**: `scripts/tests/test_parity.py` — 4 个测试验证 Hermes + OpenCode 适配器一致性
- **64 个单元测试** (新增 8 个): 覆盖 OpenCodeAdapter install/uninstall/verify + 对等性测试
- Story 文档: STORY-1-4-8-opencode-adapter.md

### Changed
- CLI install/remove/verify/list 全部支持 `--target` 参数，可指定目标 Agent
- `_get_adapter()` 函数实现 auto-detect（优先检测 Hermes，回退 OpenCode）

## [0.5.0] — 2026-05-13

### Added
- **HermesAdapter** (`scripts/adapters/hermes.py`): 完整的 Hermes Agent 适配器，实现 AgentAdapter Protocol
  - `install()` — 安装 skill 文件 + MCP 配置注入 + 跟踪记录
  - `uninstall()` — 卸载能力包（含备份恢复）
  - `update()` — 版本更新
  - `list_installed()` — 列出已安装
  - `verify()` — skill 文件完整性 + MCP 配置存在性验证
- **SnapshotManager**: 安装前快照 / 失败自动回滚机制
  - `create()` — 快照 skills + config.yaml mcp_servers + 跟踪状态
  - `restore()` — 从快照完整恢复
  - `cleanup()` — 安装成功后清理
- MCP 配置注入: 自动将能力包的 `mcp_servers` 写入 `~/.hermes/config.yaml`
- **51 个单元测试** (新增 14 个): 覆盖 HermesAdapter install/uninstall/verify/list + SnapshotManager

### Changed
- CLI `commands.py` 全面重构: 所有命令底层使用 HermesAdapter，消除内联代码重复
- CLI `main.py` 路径管理优化

## [0.4.0] — 2026-05-13

### Added
- **UCA Core 框架** (`scripts/uca/`): 统一适配器核心基础设施
  - `protocol.py` — `AgentAdapter` Protocol + `CapPack`/`AdapterResult` 数据类
  - `parser.py` — `PackParser`，解析 cap-pack.yaml → CapPack 对象，支持 JSON Schema 验证
  - `dependency.py` — `DependencyChecker`，检查 Python 包依赖和前置 skill
  - `verifier.py` — `PackVerifier`，验证已安装 skill 文件完整性
- **cap-pack CLI** (`scripts/cli/`): 命令行能力包管理工具
  - `cap-pack install <pack-dir>` — 安装能力包（解析 + 依赖检查 + 文件复制 + 跟踪）
  - `cap-pack remove <pack-name>` — 卸载能力包（备份恢复）
  - `cap-pack verify <pack-name>` — 验证已安装的能力包完整性
  - `cap-pack list` — 列出所有已安装的能力包
  - `cap-pack inspect <pack-dir>` — 检查能力包内容（不安装）
- **单元测试**: 37 个测试覆盖 protocol/parser/dependency/verifier 全部组件
- **Story 文档**: STORY-1-4-4-uca-core.md, STORY-1-4-5-uca-cli.md

### Changed
- 所有 `scripts/uca/` 内部导入改为相对导入，提高可移植性
- CLI 入口自动添加项目根目录到 sys.path，支持从任意目录运行

### Fixed
- `scripts/uca/__init__.py` 延迟导入依赖：Parser/Dependency/Verifier 按需创建

## [0.3.0] — 2026-05-13

### Added
- **自动化版本管理**: `pyproject.toml` (version: 0.3.0) + `scripts/bump-version.py`
  - 支持 `patch`/`minor`/`major` 自动递增
  - 自动更新 pyproject.toml + CHANGELOG + git tag
- GitHub Actions CI pipeline (`.github/workflows/ci.yml`)
  - 4 parallel jobs: lint, validate-packs, health-gate, cross-ref-consistency
  - YAML syntax validation + Python syntax check
  - cap-pack.yaml manifest validation via validate-pack.py
  - Cross-pack reference integrity checker
- CI helper scripts: `scripts/ci-check-yaml.py`, `scripts/ci-check-cross-refs.py`

### Fixed
- **CI 失败根因**: `cache: pip` 找不到 `pyproject.toml` → 已创建该文件
- cap-pack.yaml manifests: added missing `type: capability-pack` and `compatibility` fields
- Removed non-existent pack depends_on references
- Renamed `pipeline-progress.yaml` → `.md` (was markdown content in YAML extension)

### Changed
- README 文档对齐:
  - 项目结构: 新增 `pyproject.toml`, `.github/workflows/`, `scripts/*` 完整列表
  - Phase 1 进度: doc-engine 技能数从 12→9, 经验从 5→11
  - Phase 1 进度: 新增 CI + 版本管理条目
  - 初始结构: doc-engine 计数与实际对齐

## [0.2.0] — 2026-05-13

### Added
- EPIC-002: Skill 树状层次管理与健康度优化系统
  - `docs/EPIC-002-tree-health.md` — EPIC 文档（含研究记录、架构决策、交付物）
  - `docs/SPEC-2-1.md` — 树状索引系统规范（三层模型 + CLI 接口）
  - `docs/SPEC-2-2.md` — SQS 质量评分系统规范（五维评分 + 生命周期状态机）
  - `docs/stories/STORY-2-1-1~STORY-2-2-4` — 5 个 Story 文档（索引整合/SQS嵌入/cron报告/仪表盘/合并建议）
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
- SPEC-1-1: Module splitting (18 modules + 3 extension slots)
- SPEC-1-2: Module lifecycle management
- SPEC-1-3: Module iteration loop
- SPEC-1-4: Cross-agent adaptation (UCA architecture)
- Lifecycle tracking report (dark theme HTML)
- Phase 1 kickoff: Git init, cap-pack.yaml format design
