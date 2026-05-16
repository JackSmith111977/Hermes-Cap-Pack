# cap-pack 统一管理标准 v1.0

> **正式版** — 基于深度研究（Agent Skills Spec · skill-tree · USK · Perplexity · SkillRouter）
> **2026-05-16** · ✅ 已批准
>
> **核心理念**: 不 fork 行业标准（Agent Skills Spec），只在其上扩展 cap-pack 特有的合规层。

---

## 〇、总览

### 四层架构

```text
┌─────────────────────────────────────────────────────────────┐
│  Layer 4: Workflow Orchestration (编排调度层)                  │
│  调度原子 skill 完成特定工作任务                                │
│  DAG Pipeline · 顺序链 · 条件路由 · 并行扇出                   │
├─────────────────────────────────────────────────────────────┤
│  Layer 3: Ecosystem (生态层)                                  │
│  SRA 可发现性 · 跨平台兼容 · 跨包无冗余 · MCP 集成            │
├─────────────────────────────────────────────────────────────┤
│  Layer 2: Health & Organization (健康组织层)                    │
│  树状簇归属 · 簇大小 3-15 · 内聚性 < 60%                      │
│  原子性 < 500行 · 编排声明 · 版本规范                          │
├─────────────────────────────────────────────────────────────┤
│  Layer 1: Foundation (基础合规层)                              │
│  SKILL.md 存在 · frontmatter 合法 · SQS ≥ 60                  │
│  version/tags/classification 必填                              │
├─────────────────────────────────────────────────────────────┤
│  Layer 0: Compatibility (兼容层)                               │
│  100% 兼容 Agent Skills Spec (Agentskills.io)                 │
│  不 fork 标准，只扩展 metadata                                 │
└─────────────────────────────────────────────────────────────┘
```

### 合规等级

| 等级 | 要求 | 含义 |
|:-----|:-----|:------|
| **🔄 Orchestrated** | Excellent + L4 workflow 声明 | 可编排：skill 可参与工作流 |
| **🏆 Excellent** | Healthy + L3 pass | 🏆 优秀：生态友好，跨平台可用 |
| **🟢 Healthy** | Compliant + L2 pass | 🟢 健康：组织合理，内聚性好 |
| **✅ Compliant** | L0 pass + L1 pass | ✅ 合规：满足最低门槛，可纳入 cap-pack |
| **❌ Non-Compliant** | L0 未通过 或 L1 关键规则失败 | ❌ 不合规：不可纳入 cap-pack |

---

## 一、Layer 0 — 兼容层 (Compatibility)

> **目标**: 与 Agent Skills Spec 保持 100% 兼容，确保 cap-pack 的 skill 可被任何兼容 Agent Skills Spec 的工具读取。

### 1.1 目录结构

| 检查项 | 标准 | 来源 |
|:-------|:-----|:------|
| `name` 字段 | 1-64 字符，小写+连字符，匹配目录名 | Agent Skills Spec §3.1 |
| `description` 字段 | 1-1024 字符，含触发词 | Agent Skills Spec §3.2 |
| 目录结构 | 只允许 scripts/references/assets 作为子目录 | Agent Skills Spec §4.0 |
| SKILL.md 行数 | < 500 行（推荐） | Agent Skills Spec §4.3 |
| 渐进披露 | 三级加载: metadata → instructions → resources | Agent Skills Spec §5.0 |

### 1.2 判定

- **通过**: 全部检查项满足 → 标记为 `compatible`
- **不通过**: 任意一项不满足 → 标记为 `incompatible`，不合规

### 1.3 检查方式

```bash
# 文件存在性
test -f "SKILLS/{id}/SKILL.md"

# frontmatter 有效性
head -20 "SKILLS/{id}/SKILL.md" | grep -q "^---" # 必须有 YAML frontmatter

# 行数检查
wc -l < "SKILLS/{id}/SKILL.md"  # < 500
```

---

## 二、Layer 1 — 基础合规层 (Foundation)

> **目标**: 确保 skill 满足 cap-pack 的最低质量门槛，防止「无效 skill」进入包体系。

### 2.1 规则清单

| ID | 规则 | 阈值 | 严重度 | 检查方式 |
|:---|:-----|:----:|:------|:---------|
| F001 | SKILL.md 存在 | 文件必须存在 | 🔴 blocking | `file_exists` |
| F002 | YAML frontmatter 含 name/description | 必须包含 | 🔴 blocking | `frontmatter_fields` |
| F003 | SQS 总分 ≥ 60 | ≥ 60 | 🔴 blocking | `sqs_minimum` |
| F004 | version 字段 | 必填，semver | 🔴 blocking | `field_present` |
| F005 | tags 至少 2 个 | ≥ 2 | 🟡 warning | `field_min_items` |
| F006 | classification 必填 | domain/toolset/infrastructure | 🔴 blocking | `field_value_in` |
| F007 | triggers 非空 | ≥ 1 | 🟡 warning | `field_min_items` |

### 2.2 判定

| 条件 | 结果 |
|:-----|:------|
| 所有 blocking 规则通过 | ✅ **Compliant** |
| 任意 blocking 规则失败 | ❌ **Non-Compliant** — 不可纳入 cap-pack |

### 2.3 量化阈值说明

- **SQS ≥ 60**: 使用 `skill-quality-score.py` 的五维评分，总分低于 60 表示技能质量严重不足（结构缺陷、内容空洞或时效过期）
- **version semver**: 严格遵循 `MAJOR.MINOR.PATCH`（如 `1.0.0`），禁止使用 `^1.0`、`latest` 等格式
- **classification**: 决定 skill 在包体系中的角色——业务能力包（domain）、工具类（toolset）、基础设施（infrastructure）

```bash
# 检查 SQS
python3 scripts/skill-quality-score.py <skill-id> --json | python3 -c "import json,sys; d=json.load(sys.stdin); print(d['sqs_total'])" 

# 检查 frontmatter
head -30 SKILL.md | grep -E "^name:|^description:" 

# 检查 version
head -30 SKILL.md | grep "^version:"
```

---

## 三、Layer 2 — 健康组织层 (Health & Organization)

> **目标**: 确保 skill 的组织结构合理，簇内内聚、簇间低耦合，便于发现和维护。

### 3.1 规则清单

| ID | 规则 | 阈值 | 严重度 | 检查方式 |
|:---|:-----|:----:|:------|:---------|
| H001 | 树状簇归属 | 每个 skill 至少属于一个 cluster | 🟡 warning | `tree_membership` |
| H002 | 簇大小 | 3-15 个 skill/簇 | 🟡 warning | `cluster_size` |
| H003 | 包内语义重叠 | 同包 skill 间 < 60% | 🟡 warning | `overlap_ratio` |
| H004 | 原子性（行数） | SKILL.md < 500 行 | 🟡 warning | `line_count` |
| H005 | 原子性（主题数） | 主题数 ≤ 3 | 🟡 warning | `topic_count` |
| H006 | 编排声明 | 有编排的 skill 声明 `design_pattern` | 🟢 info | `workflow_declared` |
| H007 | 版本规范 | semver + CHANGELOG | 🟡 warning | `version_audit` |
| H008 | 低分率 | SQS < 60 的 skill < 15% | 🟡 warning | `low_score_rate` |

### 3.2 判定

| 条件 | 结果 |
|:-----|:------|
| Compliant + 所有 warning 通过 | 🟢 **Healthy** |
| Compliant + 部分 warning 未通过 | 🟡 **Needs Improvement** |
| Compliant + 75%+ warning 通过 | 🟢 边缘健康 |

### 3.3 量化阈值说明

- **簇大小 3-15**: 基于 academic research (arxiv 2601.04748) 的相变临界点研究——簇大小低于 3 则 skill 过于孤立，超过 15 则簇内语义混淆度上升会导致 LLM 选择精度下降
- **语义重叠 < 60%**: 使用 `merge-suggest.py` 的内容相似度分析。超过 60% 意味着两个 skill 可能应该合并
- **原子性 < 500 行**: Agent Skills Spec 推荐。超过 500 行的 SKILL.md 应拆分为多个 skill 或降级为经验文档
- **低分率 < 15%**: 允许少数历史遗留低分 skill 存在，但比例过高说明包质量未达标

```bash
# 检查树状归属
python3 scripts/skill-tree-index.py --json | python3 -c "import json,sys; d=json.load(sys.stdin); [print(c['name'], len(c.get('skills',[]))) for c in d if c.get('skills')]"

# 检查包内重叠
python3 scripts/merge-suggest.py --pack <name>

# 检查低分率
python3 scripts/health-check.py --json | python3 -c "import json,sys; d=json.load(sys.stdin); print('low_rate:', d.get('low_rate'))"
```

---

## 四、Layer 3 — 生态层 (Ecosystem)

> **目标**: 确保 skill 在 Agent 生态中可发现、可移植、可组合，最大化复用价值。

### 4.1 规则清单

| ID | 规则 | 阈值 | 严重度 | 检查方式 |
|:---|:-----|:----:|:------|:---------|
| E001 | SRA 可发现性 | SRA 推荐命中率 > 80% | 🟢 info | `sra_discoverable` |
| E002 | 跨平台兼容 | 至少声明 2 个 agent_types | 🟢 info | `compatibility_check` |
| E003 | 跨包无冗余 | 不同包间无 > 60% skill 重叠 | 🟢 info | `cross_pack_overlap` |
| E004 | L2 Experiences 文档 | 至少 1 篇 | 🟢 info | `experience_exists` |
| E005 | 链接有效性 |  SKILL.md 内无死链 | 🟢 info | `link_validator` |

### 4.2 判定

| 条件 | 结果 |
|:-----|:------|
| Healthy + 所有 info 通过 | 🏆 **Excellent** |
| Healthy + 部分未通过 | 🟢 **Good**（生态层为推荐非强制） |

### 4.3 量化阈值说明

- **SRA 命中率 > 80%**: 通过 `sra-discovery-test.py` 的 15 条测试查询验证。命中率低于 80% 说明 skill 的触发词和描述未能覆盖常见使用场景
- **跨平台兼容 ≥ 2 种 Agent**: cap-pack 的设计目标就是跨平台复用。只支持 Heremes 不满足生态要求
- **跨包重叠 < 60%**: 与 H003 类似但跨包。用于发现是否两个包实际上应合并

```bash
# 检查 SRA 命中率
python3 scripts/sra-discovery-test.py --json

# 检查跨包重叠
python3 scripts/merge-suggest.py --cross-pack

# 检查 Experience 文档
find packs/<name>/EXPERIENCES -name "*.md" 2>/dev/null | wc -l
```

---

## 五、Layer 4 — 工作流编排调度层 (Workflow Orchestration)

> **目标**: 提供原子 skill 之上的协作编排能力，让多个 skill 组合完成复杂任务。

### 5.1 编排模式

支持四种基本编排模式，可自由组合：

| 模式 | 标识 | 说明 | 示例 |
|:-----|:----:|:------|:------|
| **顺序链** | `sequential` | 线性链式执行 | pdf-layout → vision-qc → feishu-send |
| **并行扇出** | `parallel` | 同时执行多个独立 skill | 同时 web-search + arxiv-search |
| **条件路由** | `conditional` | 根据条件选择分支 | SQS ≥ 60 → 放行，否则告警 |
| **有向无环图** | `dag` | 任意组合上述三种 | 复杂多步骤流水线 |

### 5.2 声明方式

#### 方式 A：skill 内轻量声明

```yaml
skills:
  - id: pdf-layout
    workflow:
      pattern: sequential
      next: [vision-qc, feishu-send]
      condition: "生成成功"
```

适用于 **线性流程**，单个 skill 知道自己的下游是谁。

#### 方式 B：独立 workflow 块

```yaml
workflows:
  - id: generate-report
    description: 生成 PDF 报告并分发
    pattern: dag
    steps:
      - id: render
        skill: pdf-layout
      - id: qc
        skill: vision-qc-patterns
        depends_on: [render]
      - id: send
        skill: feishu-send
        depends_on: [qc]
        condition: "quality_check == pass"
```

适用于 **复杂编排**，工作流作为独立实体定义，skill 间无耦合。

### 5.3 规则清单

| ID | 规则 | 严重度 | 检查方式 |
|:---|:-----|:------|:---------|
| W001 | Workflow 中的 skill 引用存在 | 🔴 blocking | `skills_referenced_exist` |
| W002 | DAG 无循环依赖 | 🔴 blocking | `dag_no_cycles` |
| W003 | DAG 无死锁（所有节点可达） | 🟡 warning | `dag_deadlock_free` |
| W004 | pattern 值合法 | 🔴 blocking | `pattern_valid` |
| W005 | 条件表达式语法正确 | 🟡 warning | `condition_syntax` |

### 5.4 判定

| 条件 | 结果 |
|:-----|:------|
| Excellent + W001-W005 通过 | 🔄 **Orchestrated** — 可编排 |
| 部分通过 | ⚙️ **Partially Orchestrated** |
| 无 workflow 声明 | 📄 **Single Skill** — 无编排 |

---

## 六、合规判定流程

### 6.1 逐层判定

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

### 6.2 最终等级速查

| 等级 | L0 | L1 | L2 | L3 | L4 |
|:-----|:---|:---|:---|:---|:---|
| 🔄 **Orchestrated** | ✅ | ✅ | ✅ | ✅ | ✅有声明 |
| 🏆 **Excellent** | ✅ | ✅ | ✅ | ✅ | 任意 |
| 🟢 **Healthy** | ✅ | ✅ | ✅ | 任意 | 任意 |
| 🟡 **Needs Improvement** | ✅ | ✅ | ❌ | 任意 | 任意 |
| ✅ **Compliant** | ✅ | ✅ | ❌ | 任意 | 任意 |
| ❌ **Non-Compliant** | ❌ | — | — | — | — |

---

## 七、与已有体系的关系

| 体系 | 关系 | 说明 |
|:-----|:-----|:------|
| **Agent Skills Spec** | L0 — 100% 兼容 | 不 fork，只扩展 metadata |
| **cap-pack-v2.schema.json** | L1 — schema 验证 | 合规检查的 JSON Schema 基础 |
| **SQS (quality-score)** | L1 — 质量分 | SQS ≥ 60 是 L1 的门禁条件 |
| **skill-tree-index.py** | L2 — 树状结构 | 簇归属和簇大小由树索引提供 |
| **merge-suggest.py** | L2/L3 — 冗余检测 | 包内和跨包重叠分析 |
| **sra-discovery-test.py** | L3 — 可发现性 | SRA 命中率验证 |

---

## 八、版本记录

| 版本 | 日期 | 变更 |
|:-----|:-----|:------|
| v0.1 (初稿) | 2026-05-16 | 四层架构 + Layer 4 提案 + 规则集草案 |
| **v1.0 (正式版)** | **2026-05-16** | **L0-L4 逐层详细规则 + 量化阈值 + 检查方式 + 合规判定矩阵** |

---

> *遵循标准优先铁律：标准必须先于检测器。本 v1.0 标准是 Phase 1 治理引擎检测器的规范来源。*
