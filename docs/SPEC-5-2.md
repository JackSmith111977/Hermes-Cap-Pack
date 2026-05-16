# 🔌 SPEC-5-2: Hermes 深度集成 + 自动适配 — Phase 2

> **spec_id**: `SPEC-5-2`
> **status**: `draft`
> **epic**: `EPIC-005`
> **phase**: `Phase-2`
> **created**: 2026-05-16
> **updated**: 2026-05-16
> **owner**: boku (Emma)
> **优先级**: P1
> **估算**: ~10h（4 Stories）
> **前置**: Phase 0（标准就绪）✅ + Phase 1（引擎 MVP）✅

---

## 〇、需求澄清 (CLARIFY)

### 用户故事

> **As a** 主人
> **I want** Skill 治理引擎自动集成到 Hermes 的日常开发流程中（pre_flight / SRA / cron）
> **So that** 每次开发、推荐、定时扫描都自动执行合规检查

### 范围

| 包含 (In Scope) | 不包含 (Out of Scope) |
|:----------------|:---------------------|
| pre_flight gate 集成 | 多 Agent 适配器（Phase 3） |
| SRA 质量分注入 + 编排感知权重 | MCP Server（Phase 3） |
| 自动适配改造引擎（dry-run 模式） | OpenCode / Claude Code 适配器 |
| cron 定时扫描 + 飞书推送 | Web UI 仪表盘 |

---

## 一、技术方案

### 1.1 包结构（扩展）

```
packages/skill-governance/skill_governance/
├── ...（Phase 1 已有结构）
├── integration/                    ← 新增
│   ├── __init__.py
│   ├── pre_flight_gate.py         ← pre_flight.py 的门禁插件
│   ├── sra_quality_injector.py    ← SRA 质量分注入
│   └── cron_reporter.py           ← cron 定时扫描 + 飞书推送
└── adapter/                       ← 新增
    ├── __init__.py
    └── cap_pack_adapter.py        ← 自动适配改造引擎
```

### 1.2 pre_flight gate 集成

```python
# pre_flight_gate.py
# 插入 pre_flight.py 的 Gate 检查链中

def check_gate(skill_path: str) -> GateResult:
    """
    在 pre_flight.py 中作为新增 Gate 调用：
    
    1. 对变更的 skill 运行 skill-governance scan
    2. 检查 L0+L1 是否通过（blocking rules）
    3. 输出: PASS / WARN / BLOCKED
    
    集成方式:
      pre_flight.py 中新增:
        from skill_governance.integration.pre_flight_gate import check_gate
        result = check_gate(changed_skill_path)
    """
```

### 1.3 SRA 质量注入

```python
# sra_quality_injector.py
# 扩展 sqs-sync.py 的同步逻辑

def inject_quality_to_sra(sqs_scores: dict) -> dict:
    """
    将 SQS 评分和编排信息注入 SRA 推荐权重：
    
    1. 读取 skill-governance 的 SQS 数据库
    2. 读取 workflow 编排声明（如有）
    3. 输出到 SRA 可消费的 JSON 格式
    4. SRA 推荐时: weight = base_weight * sqs_factor
       - SQS >= 80: weight *= 1.0
       - SQS >= 60: weight *= 0.85
       - SQS < 60:  weight *= 0.5
       - 有编排声明: weight *= 1.2 (编排感知)
    """
```

### 1.4 自动适配改造引擎

```python
# cap_pack_adapter.py

class CapPackAdapter:
    """
    自动将 skill 适配到 cap-pack 体系。
    
    流程:
      1. scan(skill_path) → 检测结果
      2. suggest(skill_path) → 推荐目标包 + 建议的 cap-pack.yaml 修改
      3. dry_run(skill_path) → 预览修改（不实际写入）
      4. apply(skill_path) → 执行修改（需主人确认）
    
    适配内容:
      - 将 skill 归类到最匹配的 cap-pack 包
      - 更新 cap-pack.yaml 的 skills[] 条目
      - 补充 version/tags/classification（从现有数据推断）
    """
```

### 1.5 cron 定时扫描

```python
# cron_reporter.py

def setup_cron(interval: str = "daily") -> CronJob:
    """
    注册 Hermes cronjob：
    
    1. 每日 6:00 运行全量 skill scan
    2. 对比前次结果，检测降级/新增违规
    3. 通过飞书推送报告
    """
```

---

## 二、Story 分解

| ID | 标题 | 内容 | 估算 | 产出物 |
|:---|:-----|:-----|:----:|:-------|
| STORY-5-2-1 | **pre_flight gate 集成** | 治理引擎门禁插入 pre_flight.py 检查链 | 2h | `integration/pre_flight_gate.py` |
| STORY-5-2-2 | **SRA 质量注入 + 编排感知** | SQS 分注入 SRA 权重，编排 skill 优先推荐 | 2h | `integration/sra_quality_injector.py` |
| STORY-5-2-3 | **自动适配改造引擎** | dry-run → 确认 → 自动改 cap-pack.yaml | 4h | `adapter/cap_pack_adapter.py` |
| STORY-5-2-4 | **cron 定时扫描 + 飞书推送** | 每日自动扫描 + 异常告警 | 2h | `integration/cron_reporter.py` |

---

## 三、验收标准

- [x] pre_flight.py 新增 governance gate，对变更 skill 自动扫描 L0+L1 <!-- 验证: grep -q "pre_flight_gate\|governance" ~/.hermes/scripts/pre_flight.py -->
- [x] SRA 推荐权重包含 SQS 质量分 + 编排感知因子 <!-- 验证: python3 -c "from skill_governance.integration.sra_quality_injector import inject_quality_to_sra; print('OK')" -->
- [x] `skill-governance adapt --dry-run` 预览适配方案（不实际写入） <!-- 验证: skill-governance adapt packs/doc-engine/cap-pack.yaml --dry-run -->
- [x] `skill-governance adapt --apply` 执行适配（需要主人确认） <!-- 验证: grep -q "confirm\|--apply\|ask_approval" adapter/cap_pack_adapter.py -->
- [x] 每日 cron 扫描 → 飞书推送合规报告 <!-- 验证: grep -q "cron\|feishu\|report" integration/cron_reporter.py -->

---

## 四、依赖关系

| 依赖 | 类型 | 说明 |
|:-----|:-----|:------|
| Phase 0 标准 | 前置 | CAP-PACK-STANDARD.md v1.0 — 合规标准已就绪 ✅ |
| Phase 1 引擎 | 前置 | skill-governance 引擎已实现 ✅ |
| pre_flight.py | 运行时 | 位于 ~/.hermes/scripts/，需要作为 gate 插入点 |
| SRA | 运行时 | 位于 ~/projects/sra/，需要 SQS 数据注入 |

---

## 五、不做的范围

| 项目 | 理由 |
|:-----|:------|
| ❌ OpenCode 适配器 | Phase 3 范围 |
| ❌ Claude Code 适配器 | Phase 3 范围 |
| ❌ MCP Server | Phase 3 范围 |
| ❌ Web UI 仪表盘 | 超出 Scope |
