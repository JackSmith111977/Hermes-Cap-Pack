# Story: pre_flight gate 集成

> **story_id**: `STORY-5-2-1`
> **status**: `completed`
> **priority**: P1
> **epic**: EPIC-005
> **spec_ref**: SPEC-5-2
> **phase**: Phase-2
> **created**: 2026-05-16
> **owner**: boku (Emma)

---

## 用户故事

> **As a** 主人
> **I want** pre_flight.py 在每次任务前自动运行 skill-governance scan 检查变更的 skill
> **So that** 不合规的 skill 在开发前就被拦截

## 验收标准

- [x] `integration/pre_flight_gate.py` — 治理门禁插件，返回 PASS/WARN/BLOCKED <!-- 验证: python3 -c "from skill_governance.integration.pre_flight_gate import check_gate; print('OK')" -->
- [x] pre_flight.py 集成 — 作为 Gate 插入检查链 <!-- 验证: grep -q "pre_flight_gate\|governance" ~/.hermes/scripts/pre_flight.py -->
- [x] L0+L1 blocking 规则失败 → BLOCKED，阻止任务继续 <!-- 验证: grep -q "BLOCKED\|exit(1)" integration/pre_flight_gate.py -->

## 技术方案

```python
# pre_flight.py 集成点（新增 Gate）
from skill_governance.integration.pre_flight_gate import check_gate

def governance_pre_flight(skill_path: str) -> bool:
    result = check_gate(skill_path)
    if result.status == "BLOCKED":
        print(f"❌ [Governance Gate] {result.message}")
        return False
    print(f"✅ [Governance Gate] {result.message}")
    return True
```
