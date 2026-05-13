# 💚 SPEC-006: Skill 质量评分与健康度系统

> **状态**: `draft` · **优先级**: P1 · **创建**: 2026-05-13 · **更新**: 2026-05-13
> **SDD 流程**: `CLARIFY ✅ → RESEARCH ✅ → CREATE ⬜ → QA_GATE ⬜ → REVIEW ⬜`
> **关联 Epic**: EPIC-002-tree-health.md
> **审查人**: 主人

---

## 〇、需求澄清记录 (CLARIFY)

### 要解决的核心问题

> 如何量化衡量每个 skill 的质量？如何自动发现 skill 退化？如何建立从创建→评分→审计→退役的完整健康管理流程？

### 确认的范围

| 包含 | 不包含 |
|:-----|:--------|
| ✅ SQS 五维质量评分引擎 | ❌ 自动修复质量问题 |
| ✅ 生命周期审计与退役管理 | ❌ 跨 Agent 质量同步 |
| ✅ 新鲜度检查（最后更新时间追踪） | ❌ 源码级 lint |
| ✅ 依赖完整性检查 | ❌ 自动安装缺失依赖 |
| ✅ 与 pre_flight 门禁集成 | ❌ 浏览器可视化仪表盘（见 STORY-014） |

### 术语表

| 术语 | 定义 |
|:-----|:------|
| **SQS (Skill Quality Score)** | 0-100 评分，五维等权各 20 分 |
| **结构完整性** | YAML frontmatter、目录格式、版本号 |
| **内容质量** | 步骤可执行性、场景覆盖、陷阱章节 |
| **时效新鲜度** | 最后更新日期、版本号新旧程度 |
| **关联完整性** | 依赖声明、交叉引用、linked files |
| **可发现性** | 标签覆盖度、触发词、关键词密度 |

---

## 一、RESEARCH — 深度调研

### 评分哲学

SQS 借鉴了以下质量体系的设计原则：

| 来源 | 借鉴点 |
|:-----|:--------|
| **SonarQube** | 多维量化 + 门禁阈值 + 退化检测 |
| **ISO 25010** | 质量特性分解为可测量子特性 |
| **Google CR** | 代码审查维度分类 |
| **Hermes Skill 最佳实践** | 实际不可行的 skill 往往缺少 YAML header 或陷阱章节 |

### 现有工具调查

| 工具 | 语言 | 行数 | 当前位置 | 状态 |
|:-----|:----:|:----:|:---------|:----:|
| `skill-quality-score.py` | Python | ~200 行 | `~/.hermes/skills/skill-creator/scripts/` | ✅ completed |
| `skill-lifecycle-audit.py` | Python | ~250 行 | `~/.hermes/skills/skill-creator/scripts/` | ✅ completed |

---

## 二、架构设计

### 2.1 SQS 评分模型

```text
SQS = 结构完整性(20) + 内容质量(20) + 时效新鲜度(20) + 关联完整性(20) + 可发现性(20)

维度细则:
─────────────────────────────────────────────────────────
结构完整性 (20分):
  ├── YAML frontmatter 存在                  (5分)
  ├── 包含 name, version, description        (5分)
  ├── 包含 triggers 触发词                   (5分)
  ├── 有 references/ 或 scripts/ 目录        (5分)

内容质量 (20分):
  ├── 步骤可执行（非泛泛而谈）                (6分)
  ├── 有 Red Flags / 陷阱章节                (6分)
  ├── 有验证/测试步骤                        (4分)
  ├── >100 行正文                           (4分)

时效新鲜度 (20分):
  ├── version 格式正确 (semver)              (5分)
  ├── 创建/更新日期 < 90 天                  (8分)
  ├── < 180 天                               (4分)
  ├── < 365 天                               (3分)

关联完整性 (20分):
  ├── depeneds_on 声明 (如果适用)            (5分)
  ├── related_skills 引用                    (5分)
  ├── linked_files 存在且可访问              (5分)
  ├── 跨包引用声明                            (5分)

可发现性 (20分):
  ├── tags 数组 ≥3                           (8分)
  ├── description 包含关键词                 (6分)
  ├── 文件名与 skill 名称对齐                 (6分)
```

### 2.2 生命周期状态机

```text
                    ┌──────────┐
                    │  Created  │  新创建 skill
                    └────┬─────┘
                         │ SQS >= 50
                         ▼
                    ┌──────────┐
                    │  Active   │  正常使用中
                    └────┬─────┘
                         │
              ╔══════════╪══════════╗
              ║          │          ║
              ║  SQS < 40连续2次    ║  deprecate 命令
              ║          │          ║
              ▼          ▼          ▼
        ┌─────────┐ ┌─────────┐ ┌──────────┐
        │Deprecated│ │ Stale   │ │ Archived  │
        │手动标记   │ │新鲜度过期│ │最终归档   │
        └─────────┘ └─────────┘ └──────────┘
              │
              │ revive 命令
              ▼
        ┌──────────┐
        │  Active   │  重新激活
        └──────────┘
```

### 2.3 CLI 接口

```bash
# SQS 评分
python3 skill-quality-score.py pdf-layout           # 评分单个技能
python3 skill-quality-score.py pdf-layout --json    # JSON 输出
python3 skill-quality-score.py --audit              # 审计所有技能
python3 skill-quality-score.py --audit --threshold 70  # 只报告低于阈值

# 生命周期审计
python3 skill-lifecycle-audit.py pdf-layout          # 审计单个 skill
python3 skill-lifecycle-audit.py --audit             # 全量审计
python3 skill-lifecycle-audit.py deprecate <name>    # 标记退役
python3 skill-lifecycle-audit.py revive <name>       # 恢复退役
python3 skill-lifecycle-audit.py status [name]       # 查看状态
```

### 2.4 与 pre_flight 门禁的集成

pre_flight v2.0 的 Gate 3 已集成 SQS 质量门禁：

| SQS 分数 | 门禁行为 |
|:--------:|:---------|
| ≥ 70 | ✅ 允许操作 |
| 50–69 | 🟠 警告但允许（需确认） |
| < 50 | 🔴 禁止部署 |

---

## 三、数据模型

### 3.1 SQS 状态数据库 (`skill-quality.db`)

```sql
-- 评分记录表
CREATE TABLE scores (
    skill_name TEXT PRIMARY KEY,
    structure_score INTEGER,
    content_score INTEGER,
    freshness_score INTEGER,
    relation_score INTEGER,
    discoverability_score INTEGER,
    total_score INTEGER,
    scored_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 生命周期状态表
CREATE TABLE lifecycle (
    skill_name TEXT PRIMARY KEY,
    status TEXT CHECK(status IN ('active','deprecated','stale','archived')),
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    reason TEXT
);
```

### 3.2 审计报告 JSON 输出

```json
{
  "skill": "pdf-layout",
  "sqs": 71.8,
  "status": "active",
  "dimensions": {
    "structure": 16,
    "content": 15,
    "freshness": 12,
    "relation": 14,
    "discoverability": 14.8
  },
  "warnings": ["最后更新 > 90 天", "缺少 related_skills"],
  "suggestions": ["添加依赖声明", "更新版本号"]
}
```

---

## 四、验收标准

| ID | 描述 | 验证方式 |
|:---|:-----|:---------|
| AC-01 | SQS 评分稳定可复现 | 同 skill 连评 3 次，标准差 < 3 |
| AC-02 | 门禁拦截有效 | SQS < 50 的 skill 被 pre_flight 阻止 |
| AC-03 | 退役标记有效且可逆 | `deprecate` → `status` 含标记 → `revive` 恢复 |
| AC-04 | 审计报告含可操作建议 | 输出 `warnings` 和 `suggestions` 数组非空 |
| AC-05 | 全量审计 < 30 秒 | 扫描 300+ skill 在 30s 内完成 |

---

## 五、边界与约束

| 约束 | 说明 |
|:-----|:------|
| **只读策略** | 评分只读 SKILL.md，不修改任何文件 |
| **数据库位置** | `~/.hermes/data/skill-quality.db` |
| **审计频率** | 全量每周一次，增量每次 skill 操作触发 |
| **SQLite 线程安全** | 所有写操作使用 WAL 模式 |
