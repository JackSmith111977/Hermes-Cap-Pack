# 🏛️ SPEC-5-0: 统一标准制定 — Phase 0

> **spec_id**: `SPEC-5-0`
> **status**: `completed`
> **epic**: `EPIC-005`
> **phase**: `Phase-0`
> **created**: 2026-05-16
> **updated**: 2026-05-16
> **owner**: boku (Emma)
> **优先级**: P1（前置门禁 — Phase 0 未完成 → Phase 1-3 不能启动）
> **估算**: ~6h（3 Stories）

---

## 〇、需求澄清 (CLARIFY)

### 用户故事

> **As a** 主人
> **I want** 制定 Cap-Pack 统一管理标准的四层体系（L0-L4），包含 machine-checkable 规则集和 Workflow 编排模式
> **So that** 治理引擎的检测器有明确的合规依据，标准先于检测器实现

### 为什么需要 Phase 0？

| 问题 | 影响 |
|:-----|:------|
| 标准不锁定 → 检测器维度模糊 | 实现过程中需要反复澄清，方向可能跑偏 |
| CAP-PACK-STANDARD.md 仅有初稿框架 | 缺少量化阈值、machine-checkable 规则、workflow 编排定义 |
| 标准先于检测器（铁律） | 强制要求 Phase 0 完全结束后才能进入 Phase 1 引擎实现 |

### 范围

| 包含 (In Scope) | 不包含 (Out of Scope) |
|:----------------|:---------------------|
| L0-L4 四层标准体系定稿 | 检测器代码实现（Phase 1） |
| 每层的 machine-checkable 规则（JSON/YAML） | CLI 工具开发 |
| v3 schema 更新（兼容 v2） | Hermes / MCP 集成 |
| Workflow 编排模式定义（DAG/顺序/条件/并行） | 自动适配引擎 |
| rules.yaml 标准规则集 | |

---

## 一、技术方案

### 1.1 四层标准体系（L0-L4）

继承并完善现有 `CAP-PACK-STANDARD.md` 初稿的四层架构：

```text
Layer 4: 工作流编排调度层
  └── DAG Pipeline · 顺序链 · 条件路由 · 并行扇出

Layer 3: 生态层 (Ecosystem)
  └── SRA 可发现性 · 跨平台兼容 · 跨包无冗余

Layer 2: 健康组织层 (Health & Organization)
  └── 树状簇归属 · 簇大小 3-15 · 内聚性 < 60% 重叠

Layer 1: 基础合规层 (Foundation)
  └── SKILL.md 存在 · frontmatter 合法 · SQS ≥ 60

Layer 0: 兼容层 (Compatibility)
  └── 100% 兼容 Agent Skills Spec，不 fork 标准
```

### 1.2 Machine-Checkable 规则集

每层标准的检查规则将以结构化格式定义：

```yaml
# standards/rules.yaml (示例结构)
layers:
  - level: 1
    name: foundation
    rules:
      - id: F001
        description: "SKILL.md 文件存在"
        check: "file_exists"
        path: "SKILLS/{skill_id}/SKILL.md"
        severity: blocking
      - id: F002
        description: "YAML frontmatter 含 name/description"
        check: "frontmatter_has_fields"
        fields: [name, description]
        severity: blocking
      - id: F003
        description: "SQS >= 60"
        check: "sqs_minimum"
        threshold: 60
        severity: blocking
```

### 1.3 Workflow 编排模式

定义 Skill 间协作的四种基本模式：

| 模式 | 描述 | 示例 |
|:-----|:------|:------|
| **sequential** | 线性链式执行 | pdf-layout → vision-qc → feishu-send |
| **parallel** | 并行扇出 | 同时搜索多个数据源 |
| **conditional** | 条件路由 | SQS ≥ 60 → 放行，否则告警 |
| **dag** | 有向无环图组合 | 任意组合上述三种 |

### 1.4 schema 升级策略

```yaml
# v2 → v3 核心变更
# - 新增 compliance_levels 字段（引用 Layer 1-3）
# - 新增 workflows 定义块（Layer 4）
# - 保持 v2 所有字段向后兼容
```

---

## 二、Story 分解

| ID | 标题 | 内容 | 估算 | 产出物 |
|:---|:-----|:-----|:----:|:-------|
| STORY-5-0-1 | **制定四层统一标准** | 完善 CAP-PACK-STANDARD.md，覆盖 L0-L4 各层详细规则、量化阈值、检查方式 | 2h | `docs/CAP-PACK-STANDARD.md` 正式版 |
| STORY-5-0-2 | **machine-checkable 规则集** | 将标准翻译为 JSON/YAML 规则文件，更新 v3 schema | 2h | `schemas/cap-pack-v3.schema.json` + `standards/rules.yaml` |
| STORY-5-0-3 | **Workflow 编排模式定义** | 定义四种编排模式（DAG/顺序/条件/并行）及其 schema | 2h | `standards/workflow-patterns.md` + workflow schema |

---

## 三、验收标准 (AC)

- [x] CAP-PACK-STANDARD.md 覆盖 L0-L4 全部四层，每层有明确的规则描述 <!-- 验证: grep -c "^### Layer" docs/CAP-PACK-STANDARD.md → 4 -->
- [x] 每层标准有对应的 machine-checkable 规则（standards/rules.yaml） <!-- 验证: python3 -c "import yaml; yaml.safe_load(open('standards/rules.yaml'))" -->
- [x] v3 schema 兼容 v2，新增字段不破坏已有校验 <!-- 验证: python3 -c "import json; json.load(open('schemas/cap-pack-v3.schema.json')); print('OK')" -->
- [x] Layer 4 workflow 模式支持 sequential/parallel/conditional/dag 四种 <!-- 验证: grep -q "sequential\|parallel\|conditional\|dag" standards/workflow-patterns.md -->
- [x] 标准通过主人审阅批准 <!-- 验证: spec-state.py status SPEC-5-0 → approved -->

---

## 四、不做的范围 (Out of Scope)

| 项目 | 理由 |
|:-----|:------|
| ❌ 检测器代码实现 | 这是 Phase 1 的工作，标准未锁定前不能写检测器 |
| ❌ CLI 工具 | 同样属于 Phase 1 |
| ❌ Hermes pre_flight 集成 | Phase 2 |
| ❌ SRA 质量注入 | Phase 2 |
| ❌ 自动适配改造引擎 | Phase 2 |
| ❌ 多 Agent 适配器 | Phase 3 |

---

## 五、风险与缓解

| 风险 | 概率 | 缓解策略 |
|:-----|:----:|:---------|
| 标准过于抽象无法 machine-checkable | 🟡 中 | 每层至少 3 条可自动化检查的规则 |
| v3 schema 与 v2 不向后兼容 | 🟢 低 | schema 用 `allOf` + `if/then` 做兼容扩展 |
| 标准定稿后回头修改成本高 | 🟢 低 | Phase 0 就是专门用来试错定稿的，改标准比改代码便宜 |
