# Changelog

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
- Story 文档: STORY-022-opencode-adapter.md

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
- **Story 文档**: STORY-018-uca-core.md, STORY-019-uca-cli.md

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
