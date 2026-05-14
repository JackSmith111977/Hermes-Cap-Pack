# 🌳 SPEC-2-1: 树状 Skill 层次索引系统

> **状态**: `create` · **优先级**: P1 · **创建**: 2026-05-13 · **更新**: 2026-05-14
> **SDD 流程**: `CLARIFY ✅ → RESEARCH ✅ → CREATE ✅ → QA_GATE ⬜ → REVIEW ⬜`
> **关联 Epic**: EPIC-002-tree-health.md
> **审查人**: 主人

---

## 〇、需求澄清记录 (CLARIFY)

### 要解决的核心问题

> 如何将 302 个扁平的 SKILL.md 文件组织为「**18 包 → ~70 簇 → ~200 技能**」的三层树状结构，让主人可以浏览、搜索、理解整个技能体系的全貌？

### 确认的范围

| 包含 | 不包含 |
|:-----|:--------|
| ✅ 三层树状索引自动生成工具 (`skill-tree-index.py`) | ❌ 自动分类 AI（当前按规则 + 手动映射） |
| ✅ 重复 skill 自动检测（名称/内容相似度分析） | ❌ 自动合并（只建议不执行） |
| ✅ 微小 skill 检测（应降级为经验的 <50 行 skill） | ❌ 自动降级 |
| ✅ 路由型 skill 检测（被过度拆分的「救火队员」skill） | ❌ 路由重路由 |
| ✅ 系统健康度速览 (`--health` 模式) | ❌ 跨 Agent 树同步 |
| ✅ 合并潜力分析与建议 (`--consolidate` 模式) | ❌ 合并后的验证 |

### 前置依赖

| 依赖 | 类型 | 状态 |
|:-----|:----:|:----:|
| EPIC-001 的 18 模块分类体系 | 数据 | ✅ `approved` |
| skill-creator 元数据扫描能力 | 工具链 | ✅ `completed` |
| `pre_flight.py` 门禁系统 | 门禁 | ✅ `completed` |

---

## 一、RESEARCH — 深度调研

### 理论基础

三层本体架构已在学术界和业界充分验证：

| 来源 | 层级设计 | 结论 |
|:-----|:---------|:------|
| Colaberry AI (16,896 skills) | Taxonomy → Relation Graph → Collection | ✅ 完全匹配 |
| OntoSkills | OWL 2 三层本体 | ✅ 概念对齐 |
| 本体工程 (Ontology Engineering) | L1 分类 → L2 语义 → L3 实例 | ✅ 经典模式 |
| 信息架构 (IA) | 分类体系 → 导航标签 → 内容单元 | ✅ 设计一致 |

详细研究见 `reports/skill-tree-architecture-research.html`。

### 现有工具调查

| 工具 | 语言 | 行数 | 当前状态 |
|:-----|:----:|:----:|:---------|
| `skill-tree-index.py` | Python | ~500 行 | ✅ 已完成，在 cap-pack 项目 `scripts/` |

---

## 二、架构设计

### 2.1 三层索引模型

```text
Layer 1: Capability Pack (领域层, 18 个)
├── 包身份: ID + name + emoji + 描述
├── 路由规则: 标签映射 → skill 自动归包
└── 健康度: 包内 skill 平均 SQS 分

Layer 2: Skill Cluster (功能簇, ~70 个)
├── 簇身份: 按功能子领域聚合
├── 聚合规则: 同一包的 skill 按功能再分组
├── 典型簇: doc-engine → { pdf/, pptx/, docx/, html/, meta/ }
└── 健康度: 簇内 skill 平均 SQS 分

Layer 3: Atomic Skill (实现层, ~200 个)
├── 技能身份: SKILL.md + version + tags + score
├── 文件引用: linked files (references/ + scripts/ + templates/)
└── 依赖信息: depends_on 声明
```

### 2.2 检测算法

| 检测类型 | 算法 | 阈值 | 输出 |
|:---------|:-----|:----:|:-----|
| 重复 skill | 名称相似度 (Levenshtein) + 内容重叠率 | >80% | 合并候选列表 |
| 微小 skill | 文件行数统计 | <50 行 | 降级建议清单 |
| 路由型 skill | SKILL.md 内容模式匹配 "路由/调度/分发" | 关键词命中 | 报警列表 |
| 未分类 skill | 标签 vs 18 模块映射缺失 | 映射为空白 | 待分类清单 |

### 2.3 CLI 接口

```bash
# 基本操作
python3 scripts/skill-tree-index.py                    # 全量索引 → stdout
python3 scripts/skill-tree-index.py --pack doc-engine  # 只看某个包
python3 scripts/skill-tree-index.py --json             # JSON 结构化输出
python3 scripts/skill-tree-index.py --health           # 系统健康度速览
python3 scripts/skill-tree-index.py --consolidate      # 合并建议
python3 scripts/skill-tree-index.py --output file.yaml # 输出到文件

# 输出示例 (--health)
# 🌳 Hermes Skill 系统健康度报告
# 📊 总技能: 302 (18 包 / ~70 簇)
# 🟢 平均 SQS: ~72/100
# 🔴 需关注: 3 技能 < 50 分
# 🟡 合并潜力: 23 个候选对
```

---

## 三、接口契约

### 3.1 JSON 输出格式

```json
{
  "meta": {
    "generated_at": "2026-05-13T12:00:00",
    "total_skills": 302,
    "total_packs": 18,
    "total_clusters": 71
  },
  "analysis": {
    "duplicates": [{"skill_a": "...", "skill_b": "...", "overlap_pct": 85}],
    "micro_skills": [{"name": "...", "lines": 32}],
    "unclassified": ["skill-name-1", "skill-name-2"],
    "router_skills": ["doc-design"]
  },
  "tree": {
    "doc-engine": {
      "name": "文档生成",
      "emoji": "📄",
      "clusters": {
        "pdf": {
          "skills": ["pdf-layout", "pdf-pro-design", "pdf-render-comparison"]
        }
      }
    }
  }
}
```

### 3.2 错误处理

| 场景 | 行为 |
|:-----|:------|
| SKILLS_DIR 不存在 | 报错退出，显示 `Error: 技能目录不存在` |
| 无 skill 可扫描 | 输出空索引 `{"skills": []}` |
| JSON Schema 校验失败 | 警告但继续，标记对应 skill 为 `invalid` |

---

## 四、验收标准

| ID | 描述 | 验证方式 |
|:---|:-----|:---------|
| AC-01 | 工具可执行并输出三层结构 | `--json | jq '.tree | length' == 18` |
| ✅ AC-01 | 工具可执行并输出三层结构 | `--json` 输出为有效 list 含 module_id |
| AC-02 | 重复检测可发现已知重复 | `--consolidate` 输出建议数 >0 |
| AC-03 | 健康度模式包含系统概览 | `--health` 输出含 `总数/未分类` 字段 |
| AC-04 | 单包过滤有效 | `--pack` 参数不崩溃 |
| AC-05 | 可独立运行 | `scripts/` 下执行无需额外配置 |

---

## 五、边界与约束

| 约束 | 说明 |
|:-----|:------|
| **性能** | 全量扫描必须在 5 秒内完成 |
| **兼容性** | 输入只读 SKILL.md，不修改任何文件 |
| **可重复性** | 相同输入必须产生相同输出（确定性算法） |
