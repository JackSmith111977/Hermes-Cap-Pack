# STORY-1-5-5: 卸载增强与快照回滚测试

> **story_id**: `STORY-1-5-5`
> **status**: `implemented`
> **priority**: P1
> **epic**: EPIC-001-feasibility
> **spec_ref**: SPEC-1-5
> **created**: 2026-05-14
> **owner**: boku

## 用户故事

> **As a** 系统维护者
> **I want** 能力包卸载后恢复到干净状态，安装失败时自动回滚
> **So that** 系统始终处于一致状态

## 验收标准

### AC-3（卸载部分）
- [x] 卸载后 tracking 完全清除
- [x] 卸载时备份恢复（.bak → skill 目录）
- [x] 安装失败（验证门禁）→ 自动回滚，不影响其他已安装包
- [x] 卸载不存在的包返回清晰的错误信息

## 代码变更

| 文件 | 变更 |
|:-----|:------|
| `scripts/tests/test_hermes_adapter.py` | 新增 `TestEnhancedUninstall` 类（4 个测试） |
