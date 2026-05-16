# SPEC-5-1: Skill 治理引擎核心 — 原子性/树状/工作流/合规检测器 + CLI

> **spec_id**: `SPEC-5-1`
> **status**: `draft`
> **epic**: `EPIC-005`
> **created**: 2026-05-16
> **updated**: 2026-05-16
> **owner**: boku (Emma)
> **优先级**: P1
> **估算**: ~10h（4 Stories）

---

## 一、范围 (Scope)

### 包含 (In Scope)

- ✅ 治理引擎核心 Python 包结构（`skill_governance/`）
- ✅ 原子性扫描器（Atomicity Scanner）— 四问测试 + 量化指标
- ✅ 树状结构检查器（Tree Validator）— 簇归属 + 簇大小检查
- ✅ 工作流编排检测器（Workflow Detector）— pipeline/DAG/depends_on 检测
- ✅ Cap-Pack 合规检查器（Compliance Checker）— 对照 v2 schema + SQS + 冗余
- ✅ CLI 工具封装 — `skill-governance scan <path>` 命令
- ✅ JSON 和 HTML 报告输出
- ✅ 新增 Skill Watcher — fingerprint 快照 + cron 自动检测

### 不包含 (Out of Scope)

- ❌ pre_flight gate 集成（Phase 1）
- ❌ SRA 质量注入（Phase 1）
- ❌ 自动适配改造引擎（Phase 1）
- ❌ 多 Agent 适配器（Phase 2）
- ❌ MCP Server（Phase 2）

---

## 二、技术方案

### 2.1 包结构

```
packages/skill-governance/
├── __init__.py
├── cli/
│   └── main.py                 ← typer CLI 入口
├── scanner/
│   ├── __init__.py
│   ├── atomicity.py            ← 原子性扫描器
│   ├── tree_validator.py       ← 树状结构检查器
│   ├── workflow_detector.py    ← 工作流编排检测器
│   └── compliance.py           ← Cap-Pack 合规检查器
├── watcher/
│   ├── __init__.py
│   └── fingerprint.py          ← 快照 + 新增检测
├── reporter/
│   ├── __init__.py
│   ├── json_reporter.py        ← JSON 输出
│   └── html_reporter.py        ← HTML 报告
├── models/
│   ├── __init__.py
│   └── result.py               ← 检测结果数据模型
├── tests/
│   ├── test_atomicity.py
│   ├── test_tree_validator.py
│   ├── test_workflow_detector.py
│   ├── test_compliance.py
│   └── test_cli.py
├── pyproject.toml
└── README.md
```

### 2.2 核心数据模型

```python
@dataclass
class ScanResult:
    skill_path: str
    skill_name: str
    passed: bool
    checks: dict[str, CheckResult]

@dataclass
class CheckResult:
    passed: bool
    score: float       # 0.0 - 1.0
    details: list[str]
    suggestions: list[str]

@dataclass
class ScanReport:
    scanned_at: str
    total_skills: int
    passed_count: int
    failed_count: int
    results: list[ScanResult]
    summary: dict[str, float]  # 整体统计
```

### 2.3 各检测器设计要点

#### 原子性扫描器

| 指标 | 测量方式 | 阈值 |
|:-----|:---------|:----:|
| 行数 | SKILL.md 行数 | > 500 → 警告（可能不够原子） |
| 主题数 | 从 description 和 body 提取语义主题 | > 3 → 建议拆分 |
| 依赖数 | depends_on 声明的 skill 数 | > 5 → 依赖过重 |
| 功能内聚 | SKILL.md 中是否有多个独立操作指令 | LLM 辅助判断 |

**四问测试自动判断**：
```python
def check_atomicity(path: str) -> CheckResult:
    """
    自动化四问测试：
    Q1: 用户能不假思索地说出这个 skill 干什么？ → description 清晰度检查
    Q2: skill 是否包含多个独立能力？ → 主题数 + 操作指令数
    Q3: 移除后其他 skill 是否受影响？ → depends_on 引用分析
    Q4: SKILL.md 行数 > 500? → 行数检查
    """
```

#### 树状结构检查器

```python
def check_tree_membership(skill_name: str, tree_index: dict) -> CheckResult:
    """
    1. 读取 skill-tree-index.json（若存在）
    2. 检查 skill 是否在某 cluster 中
    3. 如果是游离 skill → 标记
    4. 检查所在 cluster 大小（3-15 为合理区间）
    """
```

#### 工作流编排检测器

```python
def check_workflow_orchestration(path: str) -> CheckResult:
    """
    检查 SKILL.md 中是否有以下编排声明：
    - frontmatter: design_pattern: pipeline|chain|dag|workflow
    - frontmatter: depends_on → 依赖声明
    - body 中是否有步骤式编排（Step 1 ... Step 2 ...）
    - lifecycle hooks 声明
    """
```

#### Cap-Pack 合规检查器

```python
def check_cap_pack_compliance(skill_name: str, cap_pack_dir: str) -> CheckResult:
    """
    对照 cap-pack-v2.schema.json 检查：
    1. 是否可映射到某个 cap-pack 包的领域？
    2. SQS 评分 ≥ 60?
    3. version 字段是否存在？
    4. tags 是否匹配包分类？
    5. 与同包其他 skill 的内容重叠度 < 60%?
    """
```

### 2.4 CLI 接口设计

```bash
# 扫描单个 skill
skill-governance scan ./path/to/skill
skill-governance scan ./path/to/skill --json     # JSON 输出
skill-governance scan ./path/to/skill --html      # HTML 报告

# 扫描整个 skills 目录
skill-governance scan ~/.hermes/skills --recursive
skill-governance scan ~/.hermes/skills --recursive --json > report.json

# Watcher: 初始化指纹
skill-governance watcher init ./skills/            # 创建 .fingerprint.json

# Watcher: 检查变更
skill-governance watcher check ./skills/           # 对比指纹，输出新增/修改的 skill
```

### 2.5 Watcher 机制

```python
class FingerprintWatcher:
    """
    基于 skill 目录快照的变更检测机制：
    - init(): 扫描所有 SKILL.md，记录 name + path + mtime + sha256 到 .fingerprint.json
    - check(): 重新扫描，对比指纹
    - 检测到新 skill → 自动触发全量检查链
    - 检测到修改 skill → 自动触发增量检查（新增 watcher events）
    """
```

---

## 三、Stories

### STORY-5-1-1: 原子性 + 树状 + 工作流检测器

| 字段 | 值 |
|:-----|:----|
| **估算** | 3h |
| **验收标准** | |
| AC1 | `AtomicityScanner` 可扫描 skill 并给出原子性评分和拆分建议 |
| AC2 | `TreeValidator` 可读取 skill-tree-index.json 并判断簇归属 |
| AC3 | `WorkflowDetector` 可检测 SKILL.md 中的编排声明 |
| AC4 | 三个检测器返回统一的 `CheckResult` 格式 |
| **技术方案** | `scanner/atomicity.py`, `scanner/tree_validator.py`, `scanner/workflow_detector.py` |

### STORY-5-1-2: Cap-Pack 合规检查器

| 字段 | 值 |
|:-----|:----|
| **估算** | 3h |
| **验收标准** | |
| AC1 | `ComplianceChecker` 可对照 cap-pack v2 schema 检查 skill |
| AC2 | 集成 SQS 评分作为合规输入 |
| AC3 | 检测 skill 与 cap-pack 包的语义匹配（领域匹配） |
| AC4 | 输出包内技能重叠检测（> 60% 重叠标记） |
| **技术方案** | `scanner/compliance.py`, 引用 `schemas/cap-pack-v2.schema.json` |

### STORY-5-1-3: CLI 工具 + JSON/HTML 报告

| 字段 | 值 |
|:-----|:----|
| **估算** | 2h |
| **验收标准** | |
| AC1 | `skill-governance scan <path>` 可执行并输出带颜色的 CLI 摘要 |
| AC2 | `--json` 输出可被程序解析的完整结果 |
| AC3 | `--html` 输出美观的可视化报告（暗色主题、卡片布局） |
| AC4 | exit code 反映检测结果（0=全通过, 1=有失败） |
| **技术方案** | `cli/main.py` (typer), `reporter/json_reporter.py`, `reporter/html_reporter.py` |

### STORY-5-1-4: 新增 Skill Watcher

| 字段 | 值 |
|:-----|:----|
| **估算** | 2h |
| **验收标准** | |
| AC1 | `skill-governance watcher init` 可创建 skills 目录指纹快照 |
| AC2 | `skill-governance watcher check` 可检测新增/修改的 skill |
| AC3 | 新 skill 检测后自动触发扫描检查链 |
| AC4 | 支持注册 cron 定时任务（Hermes cronjob） |
| **技术方案** | `watcher/fingerprint.py`, 使用 SHA-256 文件哈希 |

---

## 四、集成方案

### 4.1 项目管理位置

治理引擎作为 cap-pack 项目的子包，放在 `packages/skill-governance/` 下：

```
~/projects/hermes-cap-pack/
├── packages/
│   └── skill-governance/         ← 本次新建
│       ├── skill_governance/
│       ├── cli/
│       ├── scanner/
│       ├── watcher/
│       ├── reporter/
│       └── tests/
├── docs/
│   ├── EPIC-005-skill-governance-engine.md
│   └── research/EPIC-005-skill-governance-research.md
├── scripts/                       ← 已有工具
└── schemas/                       ← cap-pack schema
```

### 4.2 与现有工具的关系

| 现有工具 | 关系 | 集成方式 |
|:---------|:-----|:---------|
| SQS (`skill-quality-score.py`) | **输入源** | CLI 内部调用 | 
| skill-tree-index.py | **输入源** | 读取 JSON 输出 |
| cap-pack v2 schema | **标准** | 导入 schema 做合规检查 |
| validate-pack.py | **参考** | 复用部分验证逻辑 |

---

## 五、验收标准（Phase 0 全局）

- [x] CLI `skill-governance scan <path>` 可输出完整 4 维检测结果
- [x] `--json` 和 `--html` 两种输出格式可用
- [x] watcher 可检测新增 skill 并自动触发检查
- [x] 所有检测器有对应的 pytest 测试（覆盖率 ≥ 80%）
- [x] 项目状态已同步（project-state.py verify 通过）
