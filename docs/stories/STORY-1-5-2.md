# STORY-1-5-2: 依赖检查与验证门禁

> **story_id**: `STORY-1-5-2`
> **status**: `implemented`
> **priority**: P0
> **epic**: EPIC-001-feasibility
> **spec_ref**: SPEC-1-5
> **created**: 2026-05-14
> **owner**: boku

## 用户故事

> **As a** 系统维护者
> **I want** 安装能力包时自动检查包级依赖（`depends_on`）并在安装后验证完整性
> **So that** 缺失依赖有警告、破损安装自动回滚

## 验收标准

### AC-2: 依赖检查
- [x] `depends_on` 中声明的依赖包已安装时静默通过
- [x] 缺失依赖时输出清晰警告，不阻塞安装
- [x] 依赖检查可通过 `--skip-deps` 跳过

### AC-4: 验证门禁
- [x] 安装后自动执行 `chmod +x` 所有脚本（通过 post_install）
- [x] 自动验证 skill YAML frontmatter 完整性（id/name/description）
- [x] 自动验证脚本文件可执行（os.access X_OK）
- [x] 失败时自动回滚到安装前状态

## 代码变更

| 文件 | 变更 |
|:-----|:------|
| `scripts/uca/protocol.py` | CapPack 新增 `depends_on: dict` 字段 |
| `scripts/uca/parser.py` | 新增 `_parse_depends_on()` 解析方法 |
| `scripts/adapters/hermes.py` | 新增 `_check_dependencies()` + `_verify_installation()`；更新 `install()` 流程；增强 `verify()` |
| `scripts/tests/test_hermes_adapter.py` | 新增 8 个测试（依赖检查4 + 验证门禁4） |
