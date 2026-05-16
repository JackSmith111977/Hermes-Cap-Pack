# Story: dry_run/apply 报告格式 + 备份机制

> **story_id**: `STORY-6-0-3`
> **status**: `completed`
> **priority**: P1
> **epic**: EPIC-006
> **spec_ref**: SPEC-6-1
> **phase**: Phase-0
> **created**: 2026-05-16
> **owner**: boku (Emma)

## 用户故事
**As a** 主人
**I want** dry_run 显示清晰的修改预览，apply 自动备份
**So that** 修复前能确认影响范围，出问题能回滚

## 验收标准
- [x] dry_run 输出 unified diff 格式修改预览 <!-- 验证: grep -q "diff\|unified_diff" fixer/base.py -->
- [x] apply 前自动创建 `.bak` 备份文件 <!-- 验证: grep -q "\.bak" fixer/base.py -->
- [x] 输出包含: 创建/修改/删除文件列表 <!-- 验证: grep -q "create\|modify\|delete" fixer/base.py -->
- [x] 修复前后统计: applied/skipped/errors <!-- 验证: grep -q "applied.*skipped.*errors\|FixResult" fixer/base.py -->
- [x] 支持 `--output` 导出 JSON 报告 <!-- 验证: grep -q "output.*json\|--output" cli/main.py -->

## 技术方案
- dry_run 输出复用 `difflib.unified_diff` 生成标准 diff
- apply 备份使用 `shutil.copy2(src, src + ".bak")`
- JSON 报告包含: 时间戳、包路径、每条规则的 applied/skipped/errors
