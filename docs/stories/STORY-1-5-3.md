# STORY-1-5-3: 端到端集成测试

> **story_id**: `STORY-1-5-3`
> **status**: `implemented`
> **priority**: P0
> **epic**: EPIC-001-feasibility
> **spec_ref**: SPEC-1-5
> **created**: 2026-05-14
> **owner**: boku

## 用户故事

> **As a** 系统维护者
> **I want** 能力包安装引擎通过端到端验证
> **So that** 真实场景下 install → verify → uninstall 全链路可靠

## 验收标准

### AC-3: 端到端集成测试
- [x] learning-workflow 包通过 `cap-pack install` 实际安装到 Hermes（模拟环境验证）
- [x] 安装后 skill 文件存在且 YAML frontmatter 完整
- [x] 安装后脚本在目标目录存在且可执行
- [x] 安装后引用文件存在
- [x] 安装后 verify 通过（valid_skills=1, script_count=3）
- [x] 卸载后 tracking 清除
- [x] 缺失依赖时安装成功（非阻塞警告）

## 代码变更

| 文件 | 变更 |
|:-----|:------|
| `scripts/tests/test_hermes_adapter.py` | 新增 `TestEndToEndInstall` 类（4 个测试） |
| `packs/learning-workflow/cap-pack.yaml` | 新建 — 补全 skeleton 包的完整清单 |

## 测试覆盖

| 测试 | 验证内容 |
|:-----|:---------|
| `test_install_skill_and_scripts` | skill 文件存在/frontmatter/脚本可执行/引用存在/tracking |
| `test_verify_after_install` | verify() 完整通过 |
| `test_uninstall_restores_state` | 卸载清除 tracking |
| `test_install_with_missing_deps` | 缺失依赖不阻塞，有警告 |
