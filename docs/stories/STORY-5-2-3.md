# Story: 自动适配改造引擎

> **story_id**: `STORY-5-2-3`
> **status**: `draft`
> **priority**: P1
> **epic**: EPIC-005
> **spec_ref**: SPEC-5-2
> **phase**: Phase-2
> **created**: 2026-05-16
> **owner**: boku (Emma)

---

## 用户故事

> **As a** 主人
> **I want** 一条命令就能预览并执行 skill 到 cap-pack 的自动适配
> **So that** 不需要手动编辑 cap-pack.yaml

## 验收标准

- [x] `adapter/cap_pack_adapter.py` — CapPackAdapter 类 <!-- 验证: python3 -c "from skill_governance.adapter.cap_pack_adapter import CapPackAdapter; print('OK')" -->
- [x] `adapt <path> --dry-run` 预览适配方案（不写入） <!-- 验证: grep -q "dry_run\|--dry-run" adapter/cap_pack_adapter.py -->
- [x] `adapt <path> --apply` 执行适配（需确认） <!-- 验证: grep -q "confirm\|ask_approval\|--apply" adapter/cap_pack_adapter.py -->
- [x] 自动推断目标包 + 更新 cap-pack.yaml + 补充 metadata <!-- 验证: grep -q "suggest\|infer\|classify\|update" adapter/cap_pack_adapter.py -->

## 技术方案

```python
class CapPackAdapter:
    def scan(self, path) -> dict       # 检测结果
    def suggest(self, path) -> dict    # 推荐方案
    def dry_run(self, path) -> str     # 预览 diff
    def apply(self, path) -> bool      # 执行（需确认）
```
