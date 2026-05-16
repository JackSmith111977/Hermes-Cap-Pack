# 🛠️ SPEC-6-1: Fix 基础设施 + 确定性修复规则 — Phase 0+1

> **spec_id**: `SPEC-6-1`
> **status**: `completed`
> **epic**: `EPIC-006`
> **phase**: `Phase-0+1`
> **created**: 2026-05-16
> **updated**: 2026-05-16
> **owner**: boku (Emma)
> **优先级**: P1
> **估算**: ~10h（7 Stories）
> **前置**: EPIC-005 全部完成 ✅

---

## 〇、需求澄清 (CLARIFY) 

### 用户故事

> **As a** 主人
> **I want** 一条 `skill-governance fix` 命令能根据扫描结果自动修复包的合规问题
> **So that** 从「检测→看报告→手动修→再检测」的慢循环变成「检测→一键修复→确认」

### 背景

跨包扫描结果显示，18 个包的 **平均合规分仅 79.6**，主要问题是：

| 规则 | 问题 | 影响范围 | 修复类型 |
|:-----|:-----|:--------:|:---------|
| **F001** | SKILL.md 文件缺失 | **100%** (5/5) | 🟢 确定性 |
| **F006** | classification 无效 | **100%** (5/5) | 🟡 启发式 |
| **F007** | triggers 为空 | **100%** (5/5) | 🟢 确定性 |
| **E001** | SRA 发现性不足 | **100%** (5/5) | 🧠 LLM 辅助 |
| **E002** | 跨平台兼容缺失 | **100%** (5/5) | 🧠 LLM 辅助 |
| **H001** | 树簇未归属 | **80%** (4/5) | 🟢 算法 |
| **H002** | 簇大小异常 | 20% (1/5) | 🟢 算法 |

### 范围

| 包含 (In Scope) | 不包含 (Out of Scope) |
|:----------------|:---------------------|
| FixRule 抽象层 + Dispatcher | Web UI 仪表盘 |
| CLI `fix` 子命令（--dry-run/--apply/--rules/--all） | 自动 git commit |
| 5 条确定性/算法修复规则 | 修改 SKILL.md 正文内容 |
| LLM 辅助修复框架（接口定义，实现留 Phase 2） | 与非 cap-pack 生态集成 |
| dry_run 统一 diff 输出格式 | |
| 修复前后对比报告 | |

---

## 一、架构设计 (ARCHITECT)

### 1.1 整体架构

基于深度分析结论，Fix Engine 架构如下：

```
CLI: skill-governance fix
    │
    ▼
┌─────────────────────────────────────────────────────┐
│                 cli/main.py (扩展)                     │
│  @app.command("fix")                                  │
│  → 解析参数 → 加载扫描 → 分派 FixRule                │
└─────────────────────┬───────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────┐
│              fixer/dispatcher.py                      │
│  FixDispatcher: rule_id → FixRule 路由                │
│  FixPlan: 聚合多个 FixAction → dry_run/apply          │
└─────────────────────┬───────────────────────────────┘
                      │
          ┌───────────┼───────────┐
          ▼           ▼           ▼
┌─────────────────┐ ┌─────────┐ ┌─────────────────┐
│  fixer/base.py   │ │ fixer/  │ │ fixer/llm_      │
│  FixRule(ABC)    │ │ rules/  │ │ assist.py       │
│  FixAction       │ │ F001    │ │ (Phase 2 接口)   │
│  FixResult       │ │ F006    │ │                  │
│  dry_run/apply   │ │ F007    │ │                  │
│  接口            │ │ H001    │ │                  │
│                  │ │ H002    │ │                  │
└─────────────────┘ └─────────┘ └─────────────────┘
```

### 1.2 核心数据模型

```python
# fixer/base.py

@dataclass
class FixAction:
    """单次修复动作"""
    rule_id: str                    # 规则 ID (如 "F001")
    action_type: str                # create / modify / delete
    target_path: str                # 目标文件路径
    old_content: str = ""           # 原内容（用于 diff）
    new_content: str = ""           # 新内容（用于 diff）
    description: str = ""           # 人工可读的描述

@dataclass
class FixResult:
    """FixRule 执行结果"""
    rule_id: str
    dry_run: bool
    applied: int = 0                # 成功修复数
    skipped: int = 0                # 已合规跳过数
    errors: list[str] = field(default_factory=list)
    actions: list[FixAction] = field(default_factory=list)
    
    @property
    def diff(self) -> str:
        """生成 unified diff 文本"""
        return "\n".join(
            difflib.unified_diff(
                a.action.old_content.splitlines(keepends=True),
                a.action.new_content.splitlines(keepends=True),
                fromfile=a.action.target_path,
                tofile=a.action.target_path
            )
            for a in self.actions if a.old_content != a.new_content
        )

class FixRule(ABC):
    """Fix 规则抽象基类"""
    
    rule_id: str                    # 规则 ID
    description: str                # 规则描述
    severity: str                   # blocking / warning / info
    
    @abstractmethod
    def analyze(self, pack_path: str, scan_result: dict) -> FixResult:
        """分析包，生成修复计划（dry_run 模式）"""
        ...
    
    @abstractmethod
    def apply(self, pack_path: str, scan_result: dict) -> FixResult:
        """执行修复"""
        ...
    
    def _backup(self, path: str) -> str:
        """备份文件到 .bak"""
        ...
    
    def _is_already_fixed(self, pack_path: str) -> bool:
        """幂等性检查：已合规则跳过"""
        ...
```

### 1.3 Dispatcher

```python
# fixer/dispatcher.py

class FixDispatcher:
    """Rule ID → FixRule 路由"""
    
    def __init__(self):
        self._rules: dict[str, FixRule] = {}
    
    def register(self, rule: FixRule):
        self._rules[rule.rule_id] = rule
    
    def get_rule(self, rule_id: str) -> Optional[FixRule]:
        return self._rules.get(rule_id)
    
    def dispatch(self, report: dict, rules_filter: list[str] = None) -> list[FixResult]:
        """根据扫描报告分派修复"""
        results = []
        for layer_id in ["L0", "L1", "L2", "L3", "L4"]:
            for check in report.get("layers", {}).get(layer_id, {}).get("checks", []):
                if check.get("passed"):
                    continue
                rid = check["rule_id"]
                if rules_filter and rid not in rules_filter:
                    continue
                rule = self._rules.get(rid)
                if rule:
                    results.append(rule.analyze(report["target_path"], check))
        return results
```

### 1.4 CLI 命令设计

```python
@app.command()
def fix(
    pack_path: str = typer.Argument(None, help="能力包路径，或 --all 表示全部"),
    rules: str = typer.Option(None, "--rules", "-r", help="规则 ID 列表，逗号分隔"),
    dry_run: bool = typer.Option(True, "--dry-run/--apply", help="预览模式/执行模式"),
    all_packs: bool = typer.Option(False, "--all", help="修复全部 18 个包"),
    output: str = typer.Option(None, "--output", "-o", help="输出文件路径"),
):
```

### 1.5 文件结构

```
packages/skill-governance/skill_governance/fixer/
├── __init__.py                  # 导出 FixRule, FixDispatcher, FixResult
├── base.py                      # FixRule ABC + 数据模型
├── dispatcher.py                # FixDispatcher 路由
├── rules/
│   ├── __init__.py
│   ├── f001_skill_md.py         # 生成缺失 SKILL.md
│   ├── f006_classification.py   # 推断 classification
│   ├── f007_triggers.py         # 提取 triggers
│   ├── h001_cluster.py          # Jaccard 树簇归属
│   └── h002_cluster_size.py     # 簇大小优化
├── llm_assist.py                # (Phase 2) LLM 辅助修复接口
└── batch.py                     # (Phase 3) --all 批量逻辑

packages/skill-governance/tests/
├── conftest.py                  # temp_pack 夹具
├── test_fixer_base.py           # FixRule ABC + Dispatcher
├── test_fixer_f001.py           # SKILL.md 创建测试
├── test_fixer_f006.py           # classification 推断测试
├── test_fixer_f007.py           # triggers 提取测试
├── test_fixer_h001.py           # 树簇归属测试
└── test_fixer_h002.py           # 簇大小测试
```

---

## 二、详细修复规则设计

### 2.1 F001: 生成缺失 SKILL.md

**检测**：扫描器检测到二级制目录下有 skill 条目但缺少 SKILL.md

**修复动作**：
1. 读取 cap-pack.yaml 中该 skill 的条目数据（id/name/description/tags）
2. 从 `scripts/adapters/hermes.py` 或模板生成 SKILL.md 骨架
3. 写入 `SKILLS/<skill-id>/SKILL.md`

**模板**：
```yaml
---
name: {skill_id}
description: {description}
version: "1.0.0"
tags: [{tags}]
triggers:
  - {从 tags/name 推断}
---
# {name}

{description}

## 功能

## 使用方式
```

**复用来源**：`scripts/fix-low-score-skills.py` 的 frontmatter 正则 + `scripts/fix-pack-metadata.py` 的 YAML RMW

**验证**：`m time fix packs/doc-engine/ --rules F001 --dry-run`

### 2.2 F006: 推断 classification

**检测**：skill 的 frontmatter 中 classification 字段为空或不在允许列表中

**修复动作**：
1. 从 SKILL.md 的 name/description/tags 中提取关键词
2. 使用启发式规则推断：
   - 包名含 "skill" / "quality" / "engine" → `infrastructure`
   - 包名含 "workflow" / "process" → `toolset`
   - 包名含 "creative" / "design" / "analysis" → `domain`
   - 默认为 `toolset`
3. 更新 SKILL.md frontmatter

**复用来源**：`scripts/fix-l2-frontmatter.py` 的 `detect_type()` 启发式模式

### 2.3 F007: 提取 triggers

**检测**：SKILL.md 中 triggers 为空

**修复动作**：
1. 从 SKILL.md 的 tags[] 中取前 3 个作为 triggers
2. 从 name/description 提取 1-2 个关键词
3. 更新 frontmatter

### 2.4 H001: Jaccard 树簇归属

**检测**：cap-pack.yaml 的 skills[] 中有 skill 缺少 cluster 归属

**修复动作**：
1. 复用 `CapPackAdapter._jaccard_similarity()`
2. 对比该 skill 的 tags 与所有已定义簇的 tags
3. 匹配最佳簇
4. 更新 cap-pack.yaml 中的 cluster 字段

**复用来源**：`adapter/cap_pack_adapter.py` 的 `_jaccard_similarity()` 算法

### 2.5 H002: 簇大小优化

**检测**：某簇 skill 数量 < 3

**修复动作**：
1. 找到相邻最近簇（基于 Jaccard）
2. 建议合并（不自动执行，仅报告建议）

---

## 三、Story 分解

| ID | 标题 | 内容 | 估算 | 产出物 |
|:---|:-----|:-----|:----:|:-------|
| STORY-6-0-1 | **FixRule 抽象层 + Dispatcher** | FixRule ABC, FixAction/FixResult 数据模型, FixDispatcher | 2h | `fixer/base.py`, `fixer/dispatcher.py` |
| STORY-6-0-2 | **CLI fix 子命令** | `@app.command("fix")`, 参数解析, _build_report 复用 | 1h | `cli/main.py` 扩展 |
| STORY-6-0-3 | **dry_run/apply 报告格式** | 统一 diff 输出, 修复前后对比 JSON | 1h | 终端输出格式 + JSON 报告 |
| STORY-6-1-1 | **F001: 生成缺失 SKILL.md** | 模板引擎 + 文件创建 + 幂等性检查 | 1.5h | `fixer/rules/f001_skill_md.py` |
| STORY-6-1-2 | **F006+F007: classification + triggers** | 启发式推断 + 从 tags 提取 | 1.5h | `fixer/rules/f006_classification.py`, `fixer/rules/f007_triggers.py` |
| STORY-6-1-3 | **H001+H002: 树簇 + 簇大小** | Jaccard 匹配 + 合并建议 | 1.5h | `fixer/rules/h001_cluster.py`, `fixer/rules/h002_cluster_size.py` |
| STORY-6-1-4 | **测试套件** | conftest.py + 6 个测试文件 | 1.5h | `packages/skill-governance/tests/` |

---

## 四、验收标准

### STORY-6-0-1
- [x] `FixRule` 抽象基类定义 `analyze()` + `apply()` 抽象方法 + `_backup()` + `_is_already_fixed()` <!-- 验证: grep -q "class FixRule.*ABC" fixer/base.py -->
- [x] `FixResult` dataclass 包含 applied/skipped/errors/actions/diff 属性 <!-- 验证: grep -q "class FixResult" fixer/base.py -->
- [x] `FixAction` dataclass 包含 rule_id/action_type/target_path/old_content/new_content <!-- 验证: grep -q "class FixAction" fixer/base.py -->
- [x] `FixDispatcher` 支持 register/get_rule/dispatch 方法 <!-- 验证: grep -q "class FixDispatcher" fixer/dispatcher.py -->

### STORY-6-0-2
- [x] CLI 支持 `skill-governance fix <path>` 命令 <!-- 验证: PYTHONPATH=packages/skill-governance python3 -m skill_governance.cli.main fix --help -->
- [x] 支持 `--rules F001,F007` 规则过滤 <!-- 验证: grep -q "rules" cli/main.py -->
- [x] 支持 `--dry-run` / `--apply` 模式 <!-- 验证: grep -q "dry_run\|apply" cli/main.py -->

### STORY-6-1-1 (F001)
- [x] 对缺失 SKILL.md 的 skill 自动生成骨架文件 <!-- 验证: python3 -m pytest tests/test_fixer_f001.py -q -->
- [x] 生成的 SKILL.md 包含有效 YAML frontmatter <!-- 验证: grep -q "name\|description\|version\|tags" fixer/rules/f001_skill_md.py -->
- [x] 幂等：已存在的 SKILL.md 不被覆盖 <!-- 验证: grep -q "_is_already_fixed\|skip" fixer/rules/f001_skill_md.py -->

### STORY-6-1-2 (F006+F007)
- [x] F006: 从 SKILL.md name/description 推断 classification <!-- 验证: grep -q "classification\|domain\|toolset\|infrastructure" fixer/rules/f006_classification.py -->
- [x] F007: 从 tags[] 提取 triggers <!-- 验证: grep -q "triggers" fixer/rules/f007_triggers.py -->

### STORY-6-1-3 (H001+H002)
- [x] H001: Jaccard 相似度匹配最佳簇 <!-- 验证: grep -q "jaccard\|similarity" fixer/rules/h001_cluster.py -->
- [x] H002: 簇 < 3 skill 时建议合并 <!-- 验证: grep -q "cluster.*size\|merge" fixer/rules/h002_cluster_size.py -->

### 整体
- [x] 全部测试通过 <!-- 验证: python3 -m pytest packages/skill-governance/tests/ -q -->
- [x] 在 doc-engine 上运行 `fix --dry-run` 显示预期修改 <!-- 验证: PYTHONPATH=packages/skill-governance python3 -m skill_governance.cli.main fix packs/doc-engine/ --rules F001 --dry-run -->
- [x] 零新增 pip 依赖 <!-- 验证: 只使用 pyyaml/typer/rich + 标准库 -->

---

## 五、复用路线图

| 已有资产 | 位置 | 在 Fix Engine 中的用途 |
|:---------|:-----|:----------------------|
| `_load_skills_from_pack()` | `cli/main.py:42` | Fix 命令加载包数据 |
| `_build_report()` | `cli/main.py:83` | 修复前/后扫描对比 |
| `_parse_frontmatter()` | `adapter/cap_pack_adapter.py:160` | F001 创建 SKILL.md |
| `_jaccard_similarity()` | `adapter/cap_pack_adapter.py:105` | H001 簇归属匹配 |
| `_extract_skill_tags_and_desc()` | `adapter/cap_pack_adapter.py:124` | F006/F007 数据提取 |
| YAML RMW 模式 | `scripts/fix-pack-metadata.py:103` | F006/F007 YAML 修改 |
| Frontmatter 正则 | `scripts/fix-low-score-skills.py:40` | F001/F006/F007 frontmatter 编辑 |
| 启发式类型检测 | `scripts/fix-l2-frontmatter.py:23` | F006 classification 推断 |
| `tmp_path` 夹具模式 | `scripts/tests/test_cli_commands.py:27` | Fix 测试套件 |

**零新增 pip 依赖**：所有功能使用 pyyaml + typer + rich + 标准库实现。

---

## 六、决策记录 (ADR)

参考调研结论：`docs/research/SPEC-6-1-research.md`

### ADR-6-1: FixRule 双阶段设计
**状态**: accepted | **来源**: RESEARCH Round 2
- 方案 A: 单方法 + dry_run 参数 → 耦合
- **方案 B (选)**: `analyze()` 生成计划 + `apply()` 执行计划 ✅
- 方案 C: 策略模式 → 过度设计

### ADR-6-2: .bak 文件备份
**状态**: accepted | **来源**: RESEARCH Round 1
- **方案 A (选)**: `shutil.copy2` 生成 `.bak` 文件 ✅
- 方案 B: git auto-commit → 修复不总需要 git
- 方案 C: 临时目录快照 → 管理成本高

### ADR-6-3: README 采用 readme-for-ai 方法论
**状态**: accepted | **来源**: RESEARCH Round 2
- 方案 A: 传统 README → AI 扫描效率低
- **方案 B (选)**: 编号中文章节 + 三列 CLI 表 + 每节验证命令 ✅
- 方案 C: 纯 markdown 表格 → 缺概念解释

### ADR-6-4: CLI fix 在 cli/main.py
**状态**: accepted | **来源**: RESEARCH Round 1
- **方案 A (选)**: `@app.command("fix")` 复用 `_load_skills_from_pack()` ✅
- 方案 B: 独立 fix.py → 代码重复
- 方案 C: fixer/cli.py → 层级复杂

---

## 七、复用路线图

| 决策 | 选项 | 选择 | 理由 |
|:-----|:-----|:-----|:------|
| 模块位置 | `fixer/` vs. 分散到现有模块 | **`fixer/` 独立目录** | 职责单一，与 scanner/adapter 平级 |
| 数据模型 | 新建 vs. 复用 `models/result.py` | **新建 `FixResult`** | 扫描结果和修复结果是不同概念 |
| 测试位置 | `scripts/tests/` vs. 包内 `tests/` | **包内 `tests/`** | 标准 Python 包实践，解耦 |
| LLM 集成时机 | Phase 1 立即 vs. Phase 2 | **Phase 2** | 确定性修复已覆盖 70% 问题 |
| YAML 编辑 | `ruamel.yaml` vs. `pyyaml` | **`pyyaml`** | 零新增依赖，YAML 注释丢失可接受 |
