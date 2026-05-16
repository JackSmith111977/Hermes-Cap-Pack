# Workflow 编排模式定义

> **所属标准**: CAP-PACK-STANDARD v1.0 — Layer 4: Workflow Orchestration（编排调度层）
> **版本**: 1.0.0
> **日期**: 2026-05-16
> **状态**: ✅ 正式版

---

## 目录

1. [概述](#1-概述)
2. [四种编排模式](#2-四种编排模式)
3. [YAML Schema 定义](#3-yaml-schema-定义)
4. [完整示例](#4-完整示例)
5. [模式组合规则](#5-模式组合规则)
6. [条件表达式语法与规则](#6-条件表达式语法与规则)
7. [编排验证规则](#7-编排验证规则)
8. [与已有体系的关系统一](#8-与已有体系的关系)
9. [附录：合规判定](#9-附录合规判定)

---

## 1. 概述

Layer 4 编排调度层提供原子 skill 之上的协作编排能力，让多个 skill 组合完成复杂任务。
工作流引擎支持四种基本编排模式，并可自由嵌套组合。

### 1.1 核心设计原则

| 原则 | 说明 |
|:-----|:------|
| **声明式** | 工作流以 YAML 声明，不依赖编程语言 |
| **可组合** | 四种模式可嵌套组合，DAG 内可包含顺序链 |
| **可验证** | 循环检测、死锁检测、skill 存在性检查均为自动 |
| **无侵入** | 被编排的 skill 无需感知工作流存在 |
| **渐进披露** | 从轻量内联声明到独立 workflow 块，随复杂度递进 |

### 1.2 两种声明方式

| 方式 | 适用场景 | 耦合度 |
|:-----|:---------|:-------|
| **方式 A：skill 内轻量声明** | 线性流程，单个 skill 知道下游 | 中（skill 声明 next） |
| **方式 B：独立 workflow 块** | 复杂编排，工作流独立于 skill | 低（解耦） |

---

## 2. 四种编排模式

### 2.1 Sequential（顺序链）

> **标识**: `sequential`
> **说明**: 线性链式执行，前一个 skill 的输出作为后一个 skill 的输入上下文。严格串行。

**特征**:
- 执行顺序严格按 `steps` 或 `next` 列表
- 前一节点成功后才启动下一节点
- 任一节点失败则整个流程中止（可选的 `on_error` 策略）
- 适合：有严格依赖关系的流水线

**拓扑**:
```text
[A] ──→ [B] ──→ [C] ──→ [D]
```

### 2.2 Parallel（并行扇出）

> **标识**: `parallel`
> **说明**: 同时执行多个独立 skill，所有分支完成后汇聚。

**特征**:
- 所有分支并行启动，互不依赖
- 支持 `wait_for`（等待全部/任意完成）
- 支持 `max_concurrency` 控制并发上限
- 适合：独立子任务（同时搜索多个数据源、多维度分析）

**拓扑**:
```text
          ┌─→ [B1] ─┐
[A] ──→ [A] ─→ [B2] ──→ [C] (join)
          └─→ [B3] ─┘
```

### 2.3 Conditional（条件路由）

> **标识**: `conditional`
> **说明**: 根据条件表达式选择执行分支，类似 switch/case 或 if/else。

**特征**:
- 基于前序步骤的输出上下文做条件判断
- 支持 `switch`（多分支）和 `if/else`（二分支）两种形式
- 每个分支可包含子流程（嵌套任意模式）
- 无匹配分支时走 `default` 或报错
- 适合：质量门禁、A/B 选择、异常分支处理

**拓扑**:
```text
          ┌─ condition: score ≥ 60 ──→ [pass: deploy]
[A] ──→ ─┼─ condition: score ≥ 40 ──→ [warn: review]
          └─ default ────────────────→ [fail: reject]
```

### 2.4 DAG（有向无环图）

> **标识**: `dag`
> **说明**: 有向无环图 — 支持任意 DAG 拓扑，节点间通过 `depends_on` 声明依赖，引擎自动拓扑排序执行。

**特征**:
- 节点通过 `depends_on` 声明依赖关系
- 引擎自动推导执行顺序（拓扑排序）
- 无依赖的节点可并行执行
- DAG 内每个节点可以是任意模式（sequential / parallel / conditional / nested DAG）
- DAG 整体是一个「复合节点」，可被上层 DAG 引用
- 适合：复杂多步骤流水线、跨 skill 编排

**拓扑**:
```text
        [A]
       /   \
     [B]   [C]
      |     |
     [D]   [E]
       \   /
        [F]
```

---

## 3. YAML Schema 定义

### 3.1 方式 A：skill 内轻量声明 Schema

```yaml
# 嵌入在 skill 的 frontmatter 或 SKILL.md 中
workflow:
  pattern: sequential | parallel | conditional | dag
  next:                     # sequential 模式：下游 skill 列表
    - <skill-id>
  next_if:                  # conditional 模式：条件分支
    - condition: <expression>
      target: <skill-id>
  max_concurrency: <int>    # parallel 模式：并发上限（可选）
  wait_for: all | any       # parallel 模式：汇聚策略（可选）
  on_error: stop | skip | continue  # 错误处理策略（可选）
  condition: <expression>   # sequential 的基础条件（可选）
```

**验证规则**:
- `pattern` 为必填，值必须在枚举范围内
- `next` + `next_if` 不能同时出现
- `next` 仅用于 `sequential` 模式
- `next_if` 仅用于 `conditional` 模式

### 3.2 方式 B：独立 workflow 块 Schema

```yaml
workflows:
  - id: <string>                           # 工作流唯一标识
    description: <string>                   # 描述（可选）
    pattern: sequential | parallel | conditional | dag
    max_concurrency: <int>                  # parallel 模式的并发上限（可选）
    wait_for: all | any                     # parallel 模式的汇聚策略（可选）
    on_error: stop | skip | continue       # 错误处理策略（可选）
    condition: <expression>                 # 前提条件（可选）
    
    # --- sequential / parallel / dag 模式下使用 ---
    steps:
      - id: <string>                       # 步骤唯一标识
        skill: <skill-id>                   # 引用的 skill
        pattern: sequential | parallel | conditional | dag  # 嵌套模式（可选）
        steps: [...]                        # 嵌套子步骤（可选）
        depends_on:                         # DAG 模式下声明依赖
          - <step-id>                       # 依赖的步骤 ID
        condition: <expression>             # 步骤级条件
        on_error: stop | skip | continue   # 步骤级错误处理（覆盖全局）
        input:                              # 输入映射（可选）
          <key>: <value-or-expression>
        output:                             # 输出映射（可选）
          <key>: <value-or-expression>
    
    # --- conditional 模式下使用 ---
    branches:                               # conditional 模式的分支列表
      - id: <string>
        condition: <expression>             # 条件表达式
        steps: [...]                        # 分支内的步骤
      - id: <string>                        # default 分支
        default: true
        steps: [...]
```

### 3.3 完整 JSON Schema（workflow 校验用）

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "CAP Pack Workflow Pattern Schema",
  "description": "Validation schema for cap-pack workflow orchestration definitions",
  "definitions": {
    "pattern": {
      "type": "string",
      "enum": ["sequential", "parallel", "conditional", "dag"],
      "description": "Workflow orchestration pattern type"
    },
    "on_error": {
      "type": "string",
      "enum": ["stop", "skip", "continue"],
      "default": "stop",
      "description": "Error handling strategy for workflow steps"
    },
    "condition": {
      "type": "string",
      "description": "Condition expression — see Condition Expression Syntax section"
    },
    "step": {
      "type": "object",
      "required": ["id", "skill"],
      "properties": {
        "id": { "type": "string", "pattern": "^[a-z][a-z0-9-]+$" },
        "skill": { "type": "string", "description": "Referenced skill ID" },
        "pattern": { "$ref": "#/definitions/pattern" },
        "steps": {
          "type": "array",
          "items": { "$ref": "#/definitions/step" },
          "description": "Nested sub-steps — allows pattern composition"
        },
        "depends_on": {
          "type": "array",
          "items": { "type": "string" },
          "description": "List of step IDs this step depends on (DAG mode)"
        },
        "condition": { "$ref": "#/definitions/condition" },
        "on_error": { "$ref": "#/definitions/on_error" },
        "input": {
          "type": "object",
          "additionalProperties": true,
          "description": "Input variable mappings"
        },
        "output": {
          "type": "object",
          "additionalProperties": true,
          "description": "Output variable mappings"
        }
      },
      "allOf": [
        {
          "if": { "properties": { "pattern": { "const": "dag" } } },
          "then": {
            "if": { "properties": { "depends_on": { "not": { "type": "array" } } } },
            "then": { "properties": { "steps": false } }
          }
        }
      ]
    },
    "branch": {
      "type": "object",
      "properties": {
        "id": { "type": "string", "pattern": "^[a-z][a-z0-9-]+$" },
        "condition": { "type": "string", "description": "Condition expression" },
        "default": { "type": "boolean", "description": "Default branch (no condition check)" },
        "steps": {
          "type": "array",
          "items": { "$ref": "#/definitions/step" }
        }
      },
      "oneOf": [
        { "required": ["condition", "steps"] },
        { "required": ["default", "steps"] }
      ]
    },
    "workflow_inline": {
      "type": "object",
      "properties": {
        "pattern": { "$ref": "#/definitions/pattern" },
        "next": {
          "type": "array",
          "items": { "type": "string" },
          "description": "Next skills in sequence (sequential only)"
        },
        "next_if": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "condition": { "type": "string" },
              "target": { "type": "string" }
            },
            "required": ["condition", "target"]
          },
          "description": "Conditional next (conditional only)"
        },
        "max_concurrency": { "type": "integer", "minimum": 1, "default": 10 },
        "wait_for": { "type": "string", "enum": ["all", "any"], "default": "all" },
        "on_error": { "$ref": "#/definitions/on_error" },
        "condition": { "$ref": "#/definitions/condition" }
      },
      "required": ["pattern"],
      "allOf": [
        {
          "if": { "properties": { "pattern": { "const": "sequential" } } },
          "then": {
            "if": { "properties": { "next": false } },
            "then": { "properties": { "pattern": false } }
          }
        },
        {
          "if": { "properties": { "pattern": { "const": "conditional" } } },
          "then": { "required": ["next_if"] }
        }
      ]
    },
    "workflow_block": {
      "type": "object",
      "required": ["id", "pattern"],
      "properties": {
        "id": { "type": "string", "pattern": "^[a-z][a-z0-9-]+$" },
        "description": { "type": "string", "maxLength": 500 },
        "pattern": { "$ref": "#/definitions/pattern" },
        "max_concurrency": { "type": "integer", "minimum": 1, "default": 10 },
        "wait_for": { "type": "string", "enum": ["all", "any"], "default": "all" },
        "on_error": { "$ref": "#/definitions/on_error" },
        "condition": { "$ref": "#/definitions/condition" },
        "steps": {
          "type": "array",
          "items": { "$ref": "#/definitions/step" }
        },
        "branches": {
          "type": "array",
          "items": { "$ref": "#/definitions/branch" },
          "description": "Conditional branches (conditional pattern only)"
        }
      },
      "allOf": [
        {
          "if": { "properties": { "pattern": { "const": "conditional" } } },
          "then": { "required": ["branches"] }
        },
        {
          "if": {
            "properties": {
              "pattern": {
                "enum": ["sequential", "parallel", "dag"]
              }
            }
          },
          "then": { "required": ["steps"] }
        }
      ]
    }
  },
  "type": "object",
  "properties": {
    "workflows": {
      "type": "array",
      "items": { "$ref": "#/definitions/workflow_block" }
    }
  }
}
```

---

## 4. 完整示例

### 4.1 Sequential — PDF 报告生成流水线

```yaml
workflows:
  - id: generate-report
    description: 生成 PDF 报告并飞书分发
    pattern: sequential
    steps:
      - id: render
        skill: pdf-layout
        input:
          template: "monthly-report"
          data: "${context.data}"
      - id: quality-check
        skill: vision-qc
        input:
          pdf: "${steps.render.output.file}"
        condition: "config.quality_gate == true"
      - id: send
        skill: feishu-send
        input:
          file: "${steps.quality-check.output.file}"
          channel: "team-report"
```

### 4.2 Parallel — 多源搜索与聚合

```yaml
workflows:
  - id: multi-source-research
    description: 多源信息检索与聚合
    pattern: parallel
    wait_for: all
    max_concurrency: 5
    steps:
      - id: web-search
        skill: web-search
        input:
          query: "${context.query}"
      - id: arxiv-search
        skill: arxiv-search
        input:
          query: "${context.query}"
      - id: news-search
        skill: news-rss
        input:
          query: "${context.query}"
    output:
      combined: |
        - Web: ${steps.web-search.output.summary}
        - Arxiv: ${steps.arxiv-search.output.summary}
        - News: ${steps.news-search.output.summary}
```

### 4.3 Conditional — 质量门禁

```yaml
workflows:
  - id: quality-gate
    description: SQS 质量门禁 — 根据质量分决定是否放行
    pattern: conditional
    branches:
      - id: pass
        condition: "sqs_total >= 60"
        steps:
          - id: deploy
            skill: pack-deploy
            input:
              skill_id: "${context.skill_id}"
      - id: warn
        condition: "sqs_total >= 40 && sqs_total < 60"
        steps:
          - id: review
            skill: quality-review
            input:
              skill_id: "${context.skill_id}"
              report: "${context.sqs_report}"
      - id: fail
        default: true
        steps:
          - id: reject
            skill: pack-reject
            input:
              skill_id: "${context.skill_id}"
              reason: "SQS 低于 40，质量严重不足"
```

### 4.4 DAG — 复杂发布流水线

```yaml
workflows:
  - id: release-pipeline
    description: 完整发布流水线 — 测试、构建、审查、发布
    pattern: dag
    steps:
      - id: lint
        skill: code-linter
      - id: unit-test
        skill: test-runner
        depends_on: [lint]
      - id: build
        skill: pack-builder
        depends_on: [lint]
      - id: integration-test
        skill: integration-tester
        depends_on: [build]
      - id: code-review
        skill: code-reviewer
        depends_on: [unit-test, build]
      - id: security-scan
        skill: security-auditor
        depends_on: [build]
      - id: qc-gate
        skill: quality-gate
        pattern: conditional
        depends_on: [integration-test, code-review, security-scan]
        condition: "steps.code-review.output.approved == true"
        steps:
          - id: qc-pass
            skill: pack-sign
          - id: qc-fail
            skill: pack-reject
            condition: "steps.code-review.output.approved != true"
      - id: publish
        skill: pack-publisher
        depends_on: [qc-gate]
```

### 4.5 方式 A 内联声明示例（skill 内）

```yaml
# 在 SKILL.md 的 frontmatter 中
name: pdf-layout
version: 1.0.0
workflow:
  pattern: sequential
  next:
    - vision-qc
    - feishu-send
  condition: "生成成功"
  on_error: stop
```

```yaml
# 条件路由版内联声明
name: quality-gate
workflow:
  pattern: conditional
  next_if:
    - condition: "sqs_total >= 60"
      target: pack-deploy
    - condition: "sqs_total >= 40"
      target: quality-review
    - condition: "true"
      target: pack-reject
```

---

## 5. 模式组合规则

### 5.1 组合原则

1. **DAG 是顶级容器**：DAG 内每个节点（step）可以是任意一种模式（sequential / parallel / conditional / nested DAG）
2. **嵌套深度限制**：最大嵌套深度为 5 层（防止过于复杂的编排导致验证困难）
3. **sequential 内不可嵌套并行**（但 sequential 的某个 step 可以引用一个 parallel 模式的子工作流）
4. **parallel 分支相互独立**：分支间不允许有跨分支数据依赖
5. **conditional 分支收敛**：条件分支最终应汇聚到统一的后续节点（DAG 模式下通过 depends_on 实现）

### 5.2 合法组合矩阵

| 父模式 | 可嵌套子模式 | 说明 |
|:-------|:-------------|:------|
| `dag` | sequential, parallel, conditional, dag | DAG 是万能容器 |
| `sequential` | sequential, conditional | 顺序链中可嵌套顺序或条件 |
| `parallel` | sequential, parallel, conditional | 并行分支中各含子流程 |
| `conditional` | sequential, parallel, conditional, dag | 条件分支可含任意子流程 |

### 5.3 组合示例：DAG 内含 Sequential 子流程

```yaml
workflows:
  - id: complex-research
    description: 深度研究 — DAG 内含顺序链
    pattern: dag
    steps:
      - id: gather-sources
        skill: source-gatherer
      
      # 顺序子流程：阅读 → 摘要 → 翻译
      - id: read-chain
        pattern: sequential
        depends_on: [gather-sources]
        steps:
          - id: read
            skill: document-reader
          - id: summarize
            skill: text-summarizer
          - id: translate
            skill: translator
            condition: "config.language != 'zh'"
      
      # 并行子流程：分析与审核同时进行
      - id: analysis
        pattern: parallel
        depends_on: [read-chain]
        steps:
          - id: deep-analysis
            skill: research-analyzer
          - id: fact-check
            skill: fact-checker
      
      - id: final-report
        skill: report-generator
        depends_on: [analysis]
```

### 5.4 组合示例：Conditional 内嵌 Parallel

```yaml
workflows:
  - id: multi-strategy
    description: A/B 测试方案 — 条件路由后并行执行
    pattern: conditional
    branches:
      - id: ab-test
        condition: "config.strategy == 'ab_test'"
        steps:
          - id: experiments
            pattern: parallel
            wait_for: all
            steps:
              - skill: variant-a-tester
              - skill: variant-b-tester
      - id: rollout
        condition: "config.strategy == 'rollout'"
        steps:
          - skill: gradual-rollout
```

---

## 6. 条件表达式语法与规则

### 6.1 语法定义

条件表达式使用类 C 语法，支持变量引用、比较运算、逻辑运算和字面量。

```ebnf
expression     = or_expr ;
or_expr        = and_expr { "||" and_expr } ;
and_expr       = compare_expr { "&&" compare_expr } ;
compare_expr   = primary_expr [ ("==" | "!=" | ">=" | ">" | "<=" | "<") primary_expr ] ;
primary_expr   = variable_ref | literal | "(" expression ")" | "!" primary_expr ;
variable_ref   = "${" identifier { "." identifier } "}" | identifier { "." identifier } ;
literal        = string_lit | number_lit | bool_lit | "null" ;
string_lit     = "\"" { char } "\"" | "'" { char } "'" ;
number_lit     = "-"? digit { digit } [ "." digit { digit } ] ;
bool_lit       = "true" | "false" ;
```

### 6.2 变量引用

变量通过 `${}` 语法或裸标识符引用，来源包括：

| 变量来源 | 示例 | 说明 |
|:---------|:-----|:------|
| 上下文变量 | `${context.user_id}` | 工作流启动时传入的上下文 |
| 步骤输出 | `${steps.render.output.file}` | 前序步骤的输出 |
| 配置 | `${config.quality_gate}` | 工作流配置参数 |
| 环境变量 | `${env.HOME}` | 系统环境变量 |
| 字面量 | `"pass"`, `60`, `true` | 直接值 |

### 6.3 运算符

| 类别 | 运算符 | 说明 |
|:-----|:-------|:------|
| 比较 | `==`, `!=` | 等于/不等于（支持字符串、数字、布尔） |
| 比较 | `>`, `>=`, `<`, `<=` | 数值/字符串比较 |
| 逻辑 | `&&` | 逻辑与 |
| 逻辑 | `\|\|` | 逻辑或 |
| 逻辑 | `!` | 逻辑非 |
| 字符串 | `in` | 包含判断（`"A" in steps.x.output.tags`） |
| 存在性 | `has` | 字段存在判断（`has steps.x.output.result`） |

### 6.4 表达式示例

```
# 简单比较
sqs_total >= 60
steps.qc.output.passed == true

# 字符串匹配
steps.review.output.status == "approved"

# 逻辑组合
sqs_total >= 60 && steps.lint.output.passed == true

# 复杂条件
(config.strategy == "ab_test" || config.strategy == "rollout") && env.DEPLOY_ENV != "production"

# 使用 in 运算符
"critical" in steps.scan.output.severities

# 使用 has 运算符
has steps.render.output.file

# 默认 fallback
sqs_total >= 40  # 相当于 ${context.sqs_total} >= 40
```

### 6.5 规则约束

| 规则 | 说明 | 严重度 |
|:-----|:------|:-------|
| 表达式长度 ≤ 500 字符 | 防止过于复杂的条件 | 🟡 warning |
| 引用的变量必须可解析 | 变量必须在上下文或前序步骤输出中存在 | 🔴 blocking |
| 不允许副作用 | 条件表达式只读，不能修改状态 | 🔴 blocking |
| 不允许函数调用 | 条件表达式仅为布尔逻辑，不支持函数 | 🟡 warning |
| 类型安全 | 比较操作两边的类型必须兼容 | 🟡 warning |

### 6.6 歧义处理

| 场景 | 处理规则 |
|:-----|:---------|
| `null == null` | → `true` |
| `"60" == 60` | → `true`（宽松类型比较） |
| `null == 0` | → `false` |
| `"" == false` | → `false`（空字符串不视为 false） |
| 变量未定义 | → `null` |
| `true && null` | → `false` |
| `null || false` | → `false` |

---

## 7. 编排验证规则

### 7.1 规则清单

| ID | 规则 | 检查方式 | 严重度 | 说明 |
|:---|:-----|:---------|:------|:------|
| **W001** | Workflow 中的 skill 引用存在 | `skills_referenced_exist` | 🔴 blocking | 所有 `skill:` 字段引用的 skill ID 必须在包内注册 |
| **W002** | DAG 无循环依赖 | `dag_no_cycles` | 🔴 blocking | 通过拓扑排序检测环 |
| **W003** | DAG 无死锁（所有节点可达） | `dag_deadlock_free` | 🟡 warning | 从起始节点出发，所有节点必须可达 |
| **W004** | pattern 值合法 | `pattern_valid` | 🔴 blocking | pattern 必须是四种预定义值之一 |
| **W005** | 条件表达式语法正确 | `condition_syntax` | 🟡 warning | 表达式能通过语法解析 |
| **W006** | 步骤 ID 唯一 | `step_id_unique` | 🔴 blocking | 同工作流内步骤 ID 不能重复 |
| **W007** | 嵌套深度 ≤ 5 | `nesting_depth` | 🟡 warning | 模式嵌套不超过 5 层 |
| **W008** | depends_on 引用有效 | `depends_on_valid` | 🔴 blocking | DAG 中 depends_on 引用的步骤 ID 必须存在 |
| **W009** | parallel 分支无互依赖 | `parallel_no_cross_dep` | 🟡 warning | parallel 子步骤间不可有 depends_on 关系 |
| **W010** | 变量引用可解析 | `variable_resolvable` | 🟡 warning | 条件/输入表达式中引用的变量必须存在 |

### 7.2 循环检测算法（W002）

使用拓扑排序（Kahn 算法）检测 DAG 中的循环依赖：

```
输入: 节点集合 V, 依赖边集合 E (v → w 表示 v 依赖于 w)
输出: 是否为 DAG（无环），以及环路径（如有）

算法:
1. 计算每个节点的入度 indegree[v]
2. 将所有 indegree = 0 的节点入队
3. while 队列非空:
   a. 弹出节点 v，加入拓扑序列表
   b. 对 v 的所有后继 u:
      - indegree[u]--
      - 如果 indegree[u] == 0, 入队
4. 如果拓扑序列表长度 < |V|:
   → 存在环, 返回环中节点集合
5. 否则 → 无环
```

**伪代码实现**:

```python
def detect_cycles(steps):
    """检测 DAG 步骤中的循环依赖。返回 (is_dag, cycle_nodes)"""
    # 构建邻接表和入度表
    in_degree = {s.id: 0 for s in steps}
    adjacency = {s.id: [] for s in steps}
    
    for s in steps:
        if s.depends_on:
            for dep in s.depends_on:
                adjacency[dep].append(s.id)
                in_degree[s.id] += 1
    
    # Kahn 算法
    queue = [s.id for s in steps if in_degree[s.id] == 0]
    topo_order = []
    
    while queue:
        node = queue.pop(0)
        topo_order.append(node)
        for successor in adjacency[node]:
            in_degree[successor] -= 1
            if in_degree[successor] == 0:
                queue.append(successor)
    
    if len(topo_order) == len(steps):
        return True, []  # 无环
    
    # 找到环中的节点
    cycle_nodes = [s.id for s in steps if in_degree[s.id] > 0]
    return False, cycle_nodes
```

### 7.3 死锁检测算法（W003）

死锁指图中存在不可达节点（没有路径可以从起始节点到达该节点）。

```
输入: 节点集合 V, 依赖边集合 E, 起始节点集合 S（无入度的节点）
输出: 所有不可达节点

算法:
1. 从所有起始节点 S 出发做 BFS/DFS
2. 记录所有可达节点
3. 返回 V - 可达节点
```

```python
def detect_deadlocks(steps):
    """检测不可达节点。返回 deadlocked_node_ids"""
    # 构建正向邻接表
    adjacency = {s.id: [] for s in steps}
    for s in steps:
        if s.depends_on:
            for dep in s.depends_on:
                adjacency[dep].append(s.id)
    
    # 找起始节点（无依赖的节点）
    has_deps = set()
    for s in steps:
        if s.depends_on:
            has_deps.update(s.depends_on)
    all_ids = {s.id for s in steps}
    start_nodes = all_ids - has_deps
    
    if not start_nodes:
        # 如果有依赖闭环但没有起始节点，所有节点都是死锁
        return all_ids
    
    # BFS 标记可达节点
    reachable = set()
    queue = list(start_nodes)
    while queue:
        node = queue.pop(0)
        if node in reachable:
            continue
        reachable.add(node)
        for successor in adjacency.get(node, []):
            queue.append(successor)
    
    return all_ids - reachable
```

### 7.4 Skill 存在性检查（W001）

```python
def check_skills_exist(workflow_steps, registered_skills):
    """检查工作流中引用的 skill 是否已注册。返回缺失的 skill ID 列表"""
    referenced = set()
    def collect_skills(steps):
        for s in steps:
            if 'skill' in s:
                referenced.add(s['skill'])
            if 'steps' in s:
                collect_skills(s['steps'])
            if 'branches' in s:
                for b in s['branches']:
                    collect_skills(b.get('steps', []))
    
    collect_skills(workflow_steps)
    return referenced - set(registered_skills)
```

### 7.5 验证流程

```text
              Start
                │
                ▼
      ┌──────────────────┐
      │ W004: pattern    │──失败──→ ❌ 无效 pattern
      │ 值合法检查        │
      └──────────────────┘
        通过
                │
                ▼
      ┌──────────────────┐
      │ W006: 步骤 ID    │──失败──→ ❌ ID 重复
      │ 唯一性检查        │
      └──────────────────┘
        通过
                │
                ▼
      ┌──────────────────┐
      │ W001: skill      │──失败──→ ❌ 引用缺失
      │ 存在性检查        │
      └──────────────────┘
        通过
                │
                ▼
      ┌──────────────────┐
      │ W008: depends_on │──失败──→ ❌ 引用失效
      │ 引用有效性检查     │
      └──────────────────┘
        通过
                │
                ▼
      ┌──────────────────┐
      │ W002: DAG        │──失败──→ ❌ 存在循环依赖
      │ 循环检测          │
      └──────────────────┘
        通过
                │
                ▼
      ┌──────────────────┐
      │ W003: DAG        │──失败──→ 🟡 死锁警告
      │ 死锁检测          │
      └──────────────────┘
        通过
                │
                ▼
      ┌──────────────────┐
      │ W005: 条件表达式   │──失败──→ 🟡 语法警告
      │ 语法检查          │
      └──────────────────┘
        通过
                │
                ▼
      ┌──────────────────┐
      │ W007: 嵌套深度    │──失败──→ 🟡 嵌套过深
      │ ≤ 5              │
      └──────────────────┘
        通过
                │
                ▼
      ┌──────────────────┐
      │ W009: parallel   │──失败──→ 🟡 跨分支依赖
      │ 跨分支依赖检查     │
      └──────────────────┘
        通过
                │
                ▼
      ┌──────────────────┐
      │ W010: 变量引用    │──失败──→ 🟡 变量无法解析
      │ 可解析性检查       │
      └──────────────────┘
        通过
                │
                ▼
      ✅ 验证通过
```

### 7.6 错误处理策略

`on_error` 字段控制步骤失败时的行为：

| 策略 | 行为 | 适用场景 |
|:-----|:------|:---------|
| `stop` | 立即中止整个工作流（默认） | 关键路径，失败不可忽略 |
| `skip` | 跳过当前步骤，继续执行后续 | 非关键步骤，如日志收集 |
| `continue` | 忽略错误，继续执行 | 可选增强步骤 |

```yaml
# 错误处理示例
workflows:
  - id: resilient-pipeline
    pattern: dag
    on_error: stop  # 全局默认
    steps:
      - id: critical
        skill: database-sync
        # 继承全局 on_error: stop
      - id: optional-log
        skill: log-collector
        on_error: skip  # 日志收集失败不阻塞
      - id: enhancement
        skill: report-enricher
        on_error: continue  # 增强步骤可选
```

---

## 8. 与已有体系的关系

### 8.1 与 Agent Skills Spec 的关系

| 维度 | Agent Skills Spec | CAP Pack Layer 4 |
|:-----|:------------------|:------------------|
| 定位 | 原子 skill 定义标准 | 原子 skill 之上的编排标准 |
| 模式 | 无编排模式定义 | 四种编排模式 + 组合规则 |
| 声明 | SKILL.md frontmatter | 独立 workflow 块 + skill 内联声明 |
| 关系 | L0 兼容层继承来源 | L4 在 L0 上扩展，兼容 Agent Skills Spec |

**不 fork 原则**：CAP Pack 不修改 Agent Skills Spec 的 skill 定义格式，仅在 `skills[].workflow` 字段和独立 `workflows[]` 块中扩展编排能力。

### 8.2 与 BMAD Party Mode 的关系

| 维度 | CAP Pack Layer 4 Workflow | BMAD Party Mode |
|:------|:--------------------------|:-----------------|
| 抽象层级 | **声明式编排** — 定义 skill 间的依赖和执行顺序 | **运行时模式** — 指导 Subagent 的并行调用方式 |
| 关注点 | **任务流水线** — 数据在 skill 间流转、条件门禁、质量关卡 | **协作模式** — 多 Agent 并行独立思考、动态上下文路由 |
| 核心模式 | sequential / parallel / conditional / dag | parallel spawn / 动态上下文路由 / 上下文压缩 |
| 对应关系 | `parallel` 模式 ≈ Party Mode 的并行扇出 | Party Mode 是 parallel 的运行时实现策略 |
| 互补性 | Layer 4 定义「做什么」（what to run） | BMAD 定义「怎么做」（how to orchestrate at runtime） |
| 适用范围 | 批量/异步工作流（CI/CD、报告生成、数据处理） | 实时/交互式多 Agent 讨论（专家会议、多视角分析） |

**集成方式**：CAP Pack 工作流引擎可以在执行 `parallel` 模式的 skill 时，通过 BMAD Party Mode 策略来实现真正的 Subagent 级并行：

```
# 工作流引擎检测到 parallel 模式
# → 调用 BMAD Party Mode 策略
# → 每个并行分支作为一个 Subagent Spawn
# → Party Mode 负责上下文压缩、结果收集
# → 结果汇聚回工作流引擎继续流程
```

### 8.3 与 Hermes Agent Skill Authoring 的关系

| 维度 | CAP Pack Layer 4 | Hermes Agent Skill Authoring |
|:-----|:-----------------|:-----------------------------|
| 角色 | **编排定义者** | **skill 开发者** |
| 产出 | workflow YAML 声明 | SKILL.md + 指令文件 |
| 责任 | 定义 skill 间的协作拓扑 | 定义单个 skill 的功能和触发词 |
| 依赖 | 依赖已注册的 skill | 不感知编排层 |

### 8.4 全体系关系矩阵

| 体系 | 层次 | 关系 |
|:-----|:-----|:------|
| **Agent Skills Spec** | L0 | 100% 兼容，不 fork，只扩展 metadata |
| **cap-pack-v2.schema.json** | L1 | Schema 验证基础，workflow 块引用扩展 |
| **SQS (quality-score)** | L1 | 质量门禁可作为 conditional 模式的条件输入 |
| **skill-tree-index.py** | L2 | 树状簇归属为 workflow skill 引用提供注册表 |
| **merge-suggest.py** | L2/L3 | 冗余检测避免编排中引用相似 skill |
| **sra-discovery-test.py** | L3 | SRA 可发现性辅助 workflow 引擎做 skill 选择 |
| **BMAD Party Mode** | L4 运行时 | 提供并行模式的 Subagent 级实现策略 |
| **CAP Pack 合规引擎** | 全层 | W001-W010 验证由合规引擎执行 |

---

## 9. 附录：合规判定

### 9.1 编排等级

| 条件 | 结果 | 含义 |
|:-----|:-----|:------|
| Excellent + W001-W005 通过 | 🔄 **Orchestrated** | 可编排：skill 可参与工作流 |
| 部分 W 规则通过 | ⚙️ **Partially Orchestrated** | 部分可编排 |
| 无 workflow 声明 | 📄 **Single Skill** | 无编排能力 |

### 9.2 完整合规流程（含 L4）

```text
               Start
                 │
                 ▼
          L0 兼容层 ──失败──→ ❌ Non-Compliant
          通过
                 │
                 ▼
          L1 基础层 ──失败──→ ❌ Non-Compliant
          通过
                 │
                 ▼
          ✅ Compliant
                 │
                 ▼
       ┌──── L2 健康层 ──失败──→ 🟡 Needs Improvement
       │     通过
       │      │
       │      ▼
       │  🟢 Healthy
       │      │
       │      ▼
       │ ┌─ L3 生态层 ──部分──→ 🟢 Good
       │ │    通过
       │ │     │
       │ │     ▼
       │ │  🏆 Excellent
       │ │     │
       │ │     ▼
       │ │  L4 编排层 ──无声明──→ 📄 Single Skill
       │ │     │
       │ │     ▼
       │ │  🔄 Orchestrated
```

### 9.3 最终等级速查

| 等级 | L0 | L1 | L2 | L3 | L4 |
|:-----|:---|:---|:---|:---|:---|
| 🔄 **Orchestrated** | ✅ | ✅ | ✅ | ✅ | ✅ 有声明 |
| 🏆 **Excellent** | ✅ | ✅ | ✅ | ✅ | 任意 |
| 🟢 **Healthy** | ✅ | ✅ | ✅ | 任意 | 任意 |
| 🟡 **Needs Improvement** | ✅ | ✅ | ❌ | 任意 | 任意 |
| ✅ **Compliant** | ✅ | ✅ | ❌ | 任意 | 任意 |
| ❌ **Non-Compliant** | ❌ | — | — | — | — |

---

## 版本记录

| 版本 | 日期 | 变更 |
|:-----|:-----|:------|
| v1.0 | 2026-05-16 | 初始正式版 — 基于 CAP-PACK-STANDARD v1.0 Layer 4 章节扩展 |

---

> **依据标准优先铁律**：标准必须先于检测器。本文档是 Layer 4 编排检测器的规范来源。
> 遵循 CAP-PACK-STANDARD v1.0 §5（Layer 4 — 工作流编排调度层）的定义框架。
