# 文档对齐 2.0 — BMAD 式声明式依赖 + 层级事实链规范

> **来源**: BMAD Method 文档工程化设计模式
> **核心理念**: 每个文档在 frontmatter 中声明 `inputs` 依赖，形成可机器验证的层级事实链
> **参考**:
>   - BMAD Progressive Disclosure (4 Layers)
>   - BMAD Document-as-Cache Pattern
>   - BMAD `inputs` Frontmatter Field
>   - Project-context.md as Central Source of Truth
>   - DocDrift / driftcheck (pre-commit drift detection)

---

## 一、核心理念

### 从 BMAD 学到的四个模式

| BMAD 模式 | 核心思想 | 应用到文档对齐 |
|:----------|:---------|:--------------|
| **① `inputs` 字段** | 文档在 frontmatter 声明依赖的数据源 | 每个文档声明 `inputs: [{source, fields, extract}]` |
| **② 渐进披露 (4 Layers)** | 只加载当前需要的上下文 | 文档对齐从「全量人工检查」变成「按需自动验证」 |
| **③ 文档即缓存** | 输出文档存储 workflow 状态 | 文档 frontmatter 记录对齐状态、最后验证时间、漂移记录 |
| **④ 层级事实链** | 每个阶段产出是下一阶段的上下文 | 定义 SSoT 层级: L0(权威) → L1(派生) → L2(展示) |

### 我们当前的问题 vs BMAD 的解法

| 问题 | 当前 | BMAD 式解法 |
|:-----|:-----|:------------|
| 文档不声明依赖 | 版本号在 README 中，但 README 没说从哪来 | 在 frontmatter 写 `inputs: [{source: pyproject.toml, fields: [version]}]` |
| 漂移靠人脑记 | boku「我记得要同步版本号」 | 脚本自动解析 `inputs`，发现 pyproject.toml 变了就检查 README |
| 手工全量检查 | 每次对齐要检查所有文档 | 只检查 `inputs` 声明依赖了被修改文件的文档 |
| 无状态追踪 | 不知道上次对齐是什么时候 | frontmatter 记录 `alignment_status.last_verified` |

---

## 二、`inputs` 字段规范

### 格式定义

每个文档在 YAML frontmatter 中声明 `inputs` 数组：

```yaml
---
name: my-document
description: 文档描述
# ... 其他 frontmatter 字段

# ── 声明式数据依赖 ──
inputs:
  - source: pyproject.toml                          # 数据源文件路径（相对项目根）
    fields: [version, python_requires]              # 本文档用到的字段
    description: "项目版本号和 Python 版本要求"       # 人类可读说明
  - source: "pytest --collect-only"                 # 也可以是 shell 命令
    fields: [test_count]
    description: "当前测试总数"
  - source: docs/project-state.yaml
    fields: [epic_status]                           # 只关心 EPIC 状态
    description: "所有 EPIC 的状态"
    extract: |                                      # 可选：如何从数据源提取值
      python3 -c "
      import yaml
      d = yaml.safe_load(open('docs/project-state.yaml'))
      for k, v in d['entities']['epics'].items():
          print(f'{k}={v[\"state\"]}')
      "

# ── 文档对齐状态追踪 ──
alignment:
  last_verified: "2026-05-16"        # 最后对齐验证时间
  verified_by: "boku"                # 验证者
  drift_count: 0                     # 当前漂移数
  sources_hash: "a1b2c3d4"           # 数据源的 hash，用于快速检测变更
---
```

### 字段详解

| 字段 | 必填 | 类型 | 说明 |
|:-----|:----:|:-----|:------|
| `source` | ✅ | string | 数据源路径或命令。文件路径相对于项目根，命令以 shell 语法写 |
| `fields` | ✅ | string[] | 本文档从此源使用的字段名列表 |
| `description` | ❌ | string | 人类可读的说明 |
| `extract` | ❌ | string | 提取值的 shell 命令。不写则用默认方式（grep 文件） |

### `source` 的三种类型

| 类型 | 语法 | 示例 | 验证方式 |
|:-----|:------|:------|:---------|
| 文件路径 | 直接路径 | `pyproject.toml` | 检查文件是否被 git 修改 |
| shell 命令 | 完整命令 | `"pytest --collect-only"` | 运行命令对比输出 |
| glob 模式 | 含通配符 | `packs/*/cap-pack.yaml` | 检查匹配的文件是否变更 |

---

## 三、层级事实链设计 (Hierarchical Fact Chain)

### 三层架构

```
Level 0: 权威来源 (Single Source of Truth)
┌─────────────────────────────────────────────┐
│  pyproject.toml         ← 版本号、依赖、Python│
│  docs/project-state.yaml ← EPIC 状态、Story 数│
│  pytest --collect-only  ← 测试数（运行时）     │
│  packs/*/cap-pack.yaml  ← 能力包列表          │
│  schemas/               ← schema 版本         │
└─────────────────────────────────────────────┘
         ↓ 派生 (从 L0 生成或手动同步)
Level 1: 结构化数据派生
┌─────────────────────────────────────────────┐
│  docs/project-report.json ← 从 L0 聚合       │
│  JSON 格式，机器可读                          │
└─────────────────────────────────────────────┘
         ↓ 派生 (从 L1 读取，人工维护作为展示层)
Level 2: 人类可读展示
┌─────────────────────────────────────────────┐
│  README.md              ← 项目主页           │
│  QUICKSTART.md          ← 快速上手指南        │
│  ADAPTER_GUIDE.md       ← 适配器指南          │
│  PROJECT-PANORAMA.html  ← 全景报告            │
│  EPIC-*.md              ← EPIC 设计文档        │
└─────────────────────────────────────────────┘
```

### 各文档的 `inputs` 声明示例

```yaml
# README.md
---
inputs:
  - source: pyproject.toml
    fields: [version, python_requires, dependencies]
  - source: "pytest --collect-only -q 2>&1 | tail -1 | grep -oP '\\d+'"
    fields: [test_count]
  - source: docs/project-state.yaml
    fields: [epic_status]
  - source: packs/
    fields: [pack_count, adapter_count]
---
```

```yaml
# docs/project-report.json
---
inputs:
  - source: pyproject.toml
    fields: [version]
  - source: docs/project-state.yaml
    fields: [epic_status]  
  - source: "pytest --collect-only -q 2>&1 | tail -1 | grep -oP '\\d+'"
    fields: [test_count]
  - source: packs/
    fields: [pack_list]
---
```

```yaml
# docs/EPIC-005-skill-governance-engine.md
---
inputs:
  - source: docs/project-state.yaml
    fields: [EPIC-005]
  - source: docs/project-report.json
    fields: [epic_status]
---
```

---

## 四、自动验证引擎

### 整体架构

```
┌──────────────────────────────────────────────────────────────────┐
│                     文档对齐 2.0 验证引擎                          │
│                                                                  │
│  ① 解析层 — scripts/parse-inputs.py                              │
│     读取所有文档的 frontmatter → 构建依赖图 {source → [docs]}     │
│                                                                  │
│  ② 检测层 — scripts/detect-drift.py                              │
│     给定 git diff → 找出受影响的数据源 →          │
│     确定哪些文档需要验证                                           │
│                                                                  │
│  ③ 验证层 — scripts/validate-inputs.py                           │
│     对目标文档运行 extract 命令 → 比较结果 → 输出漂移报告          │
│                                                                  │
│  ④ 门禁层 — pre-commit + CI                                      │
│     pre-push.sh 调用检测+验证                                     │
│     CI 中作为质量门禁 job                                         │
└──────────────────────────────────────────────────────────────────┘
```

### ① 解析层 `scripts/parse-inputs.py`

```python
#!/usr/bin/env python3
"""解析目录下所有文档的 inputs 声明，构建依赖图"""
import yaml, json, pathlib, re

def parse_frontmatter(content: str) -> dict:
    """提取 YAML frontmatter"""
    if not content.startswith("---"):
        return {}
    parts = content.split("---", 2)
    if len(parts) < 3:
        return {}
    try:
        return yaml.safe_load(parts[1]) or {}
    except:
        return {}

def build_source_map(docs_dir: str) -> dict:
    """构建 source → [(doc_path, fields)] 映射
    
    输出:
    {
      "pyproject.toml": [
        ("README.md", ["version", "test_count"]),
        ("docs/project-report.json", ["version"])
      ],
      "docs/project-state.yaml": [
        ("docs/EPIC-005-*.md", ["status"])
      ]
    }
    """
    source_map = {}
    for path in pathlib.Path(docs_dir).rglob("*.md"):
        fm = parse_frontmatter(path.read_text())
        inputs = fm.get("inputs", [])
        for inp in inputs if isinstance(inputs, list) else []:
            source = inp.get("source", "")
            fields = inp.get("fields", [])
            if source not in source_map:
                source_map[source] = []
            source_map[source].append((str(path), fields))
    
    # 也解析 JSON/YAML 文件（有 frontmatter 的可能）
    for path in pathlib.Path(docs_dir).rglob("*.json"):
        fm = parse_frontmatter(path.read_text())
        # ...
    
    return source_map

if __name__ == "__main__":
    import sys
    root = sys.argv[1] if len(sys.argv) > 1 else "."
    result = build_source_map(root)
    print(json.dumps(result, indent=2, ensure_ascii=False))
```

### ② 检测层 `scripts/detect-drift.py`

```python
#!/usr/bin/env python3
"""检测本次变更涉及哪些文档需要重新验证"""
import subprocess, json, sys
from parse_inputs import build_source_map

def get_changed_files(git_ref="HEAD"):
    """获取 git diff 涉及的变更文件"""
    result = subprocess.run(
        ["git", "diff", "--name-only", f"{git_ref}~1..{git_ref}"],
        capture_output=True, text=True
    )
    return [f.strip() for f in result.stdout.split("\n") if f.strip()]

def find_affected_docs(changed_files, source_map):
    """找到受变更影响的文档"""
    affected = {}
    for changed in changed_files:
        for source, docs in source_map.items():
            # 匹配 source（文件路径、命令、glob）
            if source.startswith(("pytest", "python", "pip")):
                continue  # 运行时命令无法通过文件变更检测
            if changed == source or path_matches(changed, source):
                for doc_path, fields in docs:
                    if doc_path not in affected:
                        affected[doc_path] = set()
                    affected[doc_path].update(fields)
    return affected

if __name__ == "__main__":
    source_map = build_source_map(".")
    changed = get_changed_files()
    affected = find_affected_docs(changed, source_map)
    print(json.dumps(affected, indent=2, ensure_ascii=False))
```

### ③ 验证层 `scripts/validate-inputs.py`

```python
#!/usr/bin/env python3
"""验证文档的 inputs 声明是否与数据源一致"""
import yaml, subprocess, json, sys, pathlib, re
from parse_inputs import parse_frontmatter

def validate_doc(doc_path: str) -> list:
    """验证单个文档的所有 inputs 声明"""
    content = pathlib.Path(doc_path).read_text()
    fm = parse_frontmatter(content)
    inputs = fm.get("inputs", [])
    errors = []
    
    for inp in inputs if isinstance(inputs, list) else []:
        source = inp.get("source", "")
        fields = inp.get("fields", [])
        extract_cmd = inp.get("extract", "")
        
        # 运行 extract 命令获取实际值
        try:
            if extract_cmd:
                result = subprocess.run(
                    extract_cmd, shell=True, capture_output=True, text=True
                )
                actual = result.stdout.strip()
            else:
                # 默认方式：从文件 grep 字段值
                actual = default_extract(source, fields)
        except Exception as e:
            errors.append({"source": source, "error": str(e)})
            continue
        
        # 检查文档中是否包含实际值
        doc_text = content.lower()
        actual_lines = actual.split("\n")
        for line in actual_lines:
            if not line.strip():
                continue
            if line.lower() not in doc_text:
                errors.append({
                    "source": source,
                    "expected": line,
                    "field": fields,
                    "severity": "drift"
                })
    
    return errors

if __name__ == "__main__":
    doc_path = sys.argv[1]
    errors = validate_doc(doc_path)
    if errors:
        print(json.dumps(errors, indent=2))
        print(f"\n❌ 发现 {len(errors)} 个漂移")
        sys.exit(1)
    else:
        print(f"✅ {doc_path} 全部 inputs 验证通过")
```

---

## 五、文档对齐 Skill 2.0 设计

### 定位变化

| v3.3 (当前) | v4.0 (BMAD 式改进) |
|:------------|:-------------------|
| 📖 手动操作手册 | ⛓️ 声明式依赖框架 + 自动门禁 |
| 5 阶段手工流程 | 4 层自动化架构（解析→检测→验证→门禁） |
| 全量检查 | 增量检查（只验证受影响文档） |
| 无状态追踪 | 文档自身存储对齐状态 (frontmatter `alignment`) |
| 一次性的 | 持续集成的 |

### Skill 结构

```yaml
---
name: doc-alignment-v2
description: >
  声明式文档对齐系统 — 基于 BMAD 式 inputs 字段的层级事实链。
  文档在 frontmatter 声明数据依赖 → 脚本自动检测漂移 → 门禁拦截。
  使用当: 文档对齐、漂移检测、版本同步、一致性检查。
version: 4.0.0
inputs:
  - source: docs/analysis/doc-alignment-deep-dive.md
    fields: [bmad_patterns, hfact_chain]
triggers:
  - 文档对齐
  - 漂移检测
  - inputs 声明
  - 层级事实链
  - 一致性检查
---
```

### Skill 核心步骤

```text
[触发] 当主人说"对齐文档"/"检查漂移" 或 git commit 自动触发

Step 1: 解析 inputs 声明
  → python3 scripts/parse-inputs.py .
  → 输出依赖图

Step 2: 检测变更
  → python3 scripts/detect-drift.py
  → 输出受影响文档列表

Step 3: 验证受影响文档
  → python3 scripts/validate-inputs.py <doc_path>
  → 输出漂移报告

Step 4: 门禁判定
  → 漂移=0 → 通过
  → 漂移>0 → 显示差异 + 建议修复命令

Step 5: 更新对齐状态
  → 修复后更新 frontmatter 的 alignment 字段
```

---

## 六、实施路线

### Phase 0: 基础设施（~1h）
- 创建 3 个核心脚本: `parse-inputs.py`, `detect-drift.py`, `validate-inputs.py`
- 定义 `inputs` 字段规范（本文件即为规范）

### Phase 1: 关键文档添加 inputs（~30min）
- README.md → version, test_count, epic_status
- project-report.json → version, epic_status, test_count
- QUICKSTART.md → cli_entry

### Phase 2: 门禁集成（~1h）
- pre-push.sh 增加 `validate-inputs --check-staged`
- GitHub Actions 增加 doc-alignment job

### Phase 3: 全覆盖（~1h）
- 所有文档添加 inputs 声明
- 更新 doc-alignment skill 为 v4.0
