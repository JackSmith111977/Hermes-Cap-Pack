# 文档对齐为何失效？—— BMAD 式声明依赖 + 缺失门禁分析

> **分析者**: boku (Emma)
> **触发**: 主人指出「为什么现在的文档对齐文档 skill 不能很好发挥作用」
> **核心洞察**: BMAD 的 `input` 字段声明式依赖机制 + 当前工作流缺失多个变更场景的对齐门禁
> **日期**: 2026-05-16

---

## 一、为什么 doc-alignment skill 不能很好发挥作用？

当前 `doc-alignment` skill 的定位是：**一份描述「如何手动对齐」的操作手册**。这有四个致命缺陷：

### 缺陷 1: 它是反应式工具，不是预防式门禁

```text
现状: 发现漂移 → 想起有 doc-alignment skill → 翻阅 5 个阶段 → 手动修复
       ↑                            ↑                        ↑
     漂移已发生                   认知负担高                做对一次就够累
     
理想: 提交变更 → 自动检测漂移 → 提示修复 → 提交
       ↑                            ↑
     自动化                      零认知负担
```

**核心问题**: Skill 是「事后修补说明书」，不是「事前拦截门禁」。

### 缺陷 2: 文档不声明自己依赖什么

当前项目的所有文档——README.md、QUICKSTART.md、EPIC-*.md、ADAPTER_GUIDE.md——**没有任何一个声明了「我包含哪些派生数据，这些数据从哪来」**。

```text
对比:
  无声明: README 中版本号 1.0.1 → 不知道从哪来的 → 漂移了也不知道
  有声明: README 中 version ← pyproject.toml → 改 pyproject 就知道要检查 README
```

### 缺陷 3: 没有层级事实链 (Hierarchical Fact Chain)

BMAD 的核心思想是 **事实层级**——每个事实有一个权威来源，其他都是派生。但我们的文档体系是扁平的：

```text
当前: pyproject.toml  (版本)
      README.md       (版本)  ← 平等关系 → 改一个另一个不会触发检查
      project-report  (版本)
      
BMAD 式:
      pyproject.toml  ─── 权威来源 (Level 0)
           ↓
      README.md       ─── 派生 (声明 input: pyproject.toml)
           ↓
      project-report  ─── 派生 (声明 input: README)
```

### 缺陷 4: 没有「声明 → 验证」的自动化管道

Skill 描述的手动流程在工作流中没有对应的自动化节点：

```text
现有工作流: 代码变更 → git add → git commit → git push → CI
                                              ↑
                                    没有这里插入的「文档对齐检查」
```

---

## 二、BMAD `input` 字段的启示：声明式文档依赖

BMAD 在 TOML 中通过 `persistent_facts` 声明「我需要哪些上下文」——这是一种**显式依赖声明**。同样的模式可以应用到文档对齐中：

### 核心理念

> **每个文档在 frontmatter 中声明它派生了哪些外部数据源。**

```yaml
# REANME.md 的 frontmatter 示例
---
name: hermes-cap-pack
input:
  - source: pyproject.toml
    fields: [version]
    rule: "grep -oP '\\d+\\.\\d+\\.\\d+'"
  - source: pytest --collect-only
    fields: [test_count]
    rule: "tail -1 | grep -oP '\\d+'"
  - source: docs/project-state.yaml
    fields: [epic_count]
    rule: "python3 -c \"import yaml; d=yaml.safe_load(open('docs/project-state.yaml')); print(len(d['entities']['epics']))\""
derive_sections:
  - section: "项目概览 blockquote"
    maps_to: [version, test_count]  # 这些派生数据出现在这个段落
  - section: "项目身份表"
    maps_to: [cli_entry, python_version, dependencies]
---
```

### 这样做的三个好处

#### 好处 1: 依赖可追溯

```bash
# 自动发现「pyproject.toml 改了，谁依赖它？」
python3 scripts/find-dependent-docs.py pyproject.toml
# 输出: README.md (version), project-report.json (version), PANORAMA.html (version)
```

#### 好处 2: 变更可验证

```bash
# 自动验证某个文档的派生数据是否最新
python3 scripts/validate-derived-data.py README.md
# 输出: ✅ version 1.0.1 = pyproject.toml 1.0.1
#       ✅ tests 202 = pytest 202
#       ❌ epic_count: README=6, state.yaml=7 → 需更新
```

#### 好处 3: 门禁可自动化

pre-commit hook 或 GitHub Actions 读取所有文档的 `input` 声明，只检查**本次变更涉及的数据源**对应的文档：

```bash
# 检查 git diff 涉及的文件 → 查找依赖这些文件的文档 → 只验证它们
python3 scripts/drift-gate.py --check-staged
```

---

## 三、当前工作流缺失的对齐门禁

以下是所有「变更 → 文档需要同步」的场景，以及当前是否有门禁：

| # | 变更场景 | 变什么 | 影响什么文档 | 有门禁？ |
|:-:|:---------|:-------|:------------|:--------:|
| 1 | **版本升级** | `pyproject.toml version` | README, project-report.json, PANORAMA.html | ❌ **无** |
| 2 | **测试增减** | pytest 收集测试数变化 | README, project-report.json, PANORAMA.html | ❌ **无** |
| 3 | **EPIC 完成** | `project-state.yaml` EPIC 状态 | project-report.json, EPIC-*.md | ❌ **无** |
| 4 | **CLI 变更** | CLI 命令实现 | README, QUICKSTART.md, ADAPTER_GUIDE.md | ❌ **无** |
| 5 | **依赖变更** | pyproject.toml dependencies | README, project-report.json | ❌ **无** |
| 6 | **Python 版本变** | pyproject.toml python_requires | README, project-report.json | ❌ **无** |
| 7 | **Schema 版本变** | schemas/ 目录文件 | README 项目身份表 | ❌ **无** |
| 8 | **能力包新增/删除** | packs/ 目录 | README 包列表, project-report.json | ❌ **无** |
| 9 | **适配器变更** | scripts/adapters/ | README 适配器表, ADAPTER_GUIDE.md | ❌ **无** |
| 10 | **CHI 评分变化** | 运行 health-check | README 概览, project-report.json | ❌ **无** |

**结论**: **10 个变更场景，0 个有自动门禁** —— 文档全靠精神力对齐。

### 缺失门禁的深层原因

```text
根因 1: 没有声明式依赖 → 不知道「什么变化会影响什么文档」
         → 无法精准检查 → 只能全量手动检查 → 累 → 跳过 → 漂移

根因 2: 工作流没有「文档对齐」这个阶段
         → 门禁只在 SDD 流程中 (pre_flight)
         → 但文档对齐不是 SDD 流程的一部分
         → 它是被遗忘的横向环节

根因 3: 现有 pre-commit hook 只有 4 道门禁 (scripts/pre-push.sh)
         → 没有一道是检查文档一致性的
         → 都是代码/质量检查
```

---

## 四、改进方案：声明式依赖 + 自动化门禁

### 整体架构

```
┌─────────────────────────────────────────────────────────────────┐
│                     文档对齐 2.0 架构                            │
│                                                                  │
│  ① 声明层                                                       │
│     每个文档的 frontmatter 声明 input 依赖                       │
│     └── 文件: README.md, QUICKSTART.md, EPIC-*.md, ...          │
│                                                                  │
│  ② 解析层                                                       │
│     读取所有文档的 input 声明，构建依赖图                         │
│     └── 脚本: scripts/doc-dependency-graph.py                   │
│                                                                  │
│  ③ 验证层                                                       │
│     给定 git diff → 找出受影响的数据源 → 只检查相关文档            │
│     └── 脚本: scripts/validate-derived-data.py                  │
│                                                                  │
│  ④ 门禁层                                                       │
│     pre-commit + CI 双重拦截                                      │
│     └── pre-push.sh 增加、CI 增加 doc-consistency job            │
└─────────────────────────────────────────────────────────────────┘
```

### 第一步：文档声明 `input` 字段

以 README.md 为例，在文件开头添加 frontmatter：

```markdown
---
input:
  - source: pyproject.toml
    fields: [version, python_requires]
    extract: |
      VERSION=$(grep "^version" pyproject.toml | grep -oP '\d+\.\d+\.\d+')
      PYTHON=$(grep "python_requires" pyproject.toml | grep -oP '>=\s*\S+' | tr -d ' ')
      echo "version=$VERSION python=$PYTHON"
  - source: pytest --collect-only
    fields: [test_count]
    extract: "python -m pytest --collect-only -q 2>&1 | tail -1 | grep -oP '\\d+'"
  - source: docs/project-state.yaml
    fields: [epic_status]
    extract: "python3 -c \"import yaml; d=yaml.safe_load(open('docs/project-state.yaml')); [print(f'{k}={v[\\\"state\\\"]}') for k,v in d['entities']['epics'].items()]\""
  - source: packs/
    fields: [pack_list, pack_count]
    extract: "ls -d packs/*/ | wc -l"
derive_sections:
  - section: "项目概览 blockquote"
    uses: [version, test_count, pack_count]
  - section: "项目身份表"
    uses: [python, dependencies]
---

# hermes-cap-pack
...
```

### 第二步：解析层脚本 `scripts/doc-dependency-graph.py`

```python
#!/usr/bin/env python3
"""读取所有文档的 input 声明，构建依赖图"""

import re, yaml, json, pathlib

def parse_frontmatter(path):
    """解析文件的 frontmatter（支持 --- 块）"""
    content = path.read_text()
    if not content.startswith("---"):
        return {}, content
    parts = content.split("---", 2)
    if len(parts) < 3:
        return {}, content
    try:
        fm = yaml.safe_load(parts[1])
        return fm or {}, parts[2]
    except:
        return {}, content

def build_dependency_graph(docs_dir="."):
    """扫描目录下的所有 md 文件，构建 {source → [docs]} 映射"""
    graph = {}  # source → [(doc_path, fields)]
    for path in pathlib.Path(docs_dir).rglob("*.md"):
        fm, _ = parse_frontmatter(path)
        inputs = fm.get("input", [])
        if not inputs:
            continue
        for inp in inputs:
            source = inp.get("source")
            fields = inp.get("fields", [])
            if source not in graph:
                graph[source] = []
            graph[source].append((str(path), fields))
    
    # 输出依赖图
    print(json.dumps(graph, indent=2, ensure_ascii=False))
    
    # 输出反向引用（文档 → 数据源）
    reverse = {}
    for path in pathlib.Path(docs_dir).rglob("*.md"):
        fm, _ = parse_frontmatter(path)
        inputs = fm.get("input", [])
        if inputs:
            reverse[str(path)] = [i["source"] for i in inputs]
    print("\n=== 文档 → 数据源 ===")
    print(json.dumps(reverse, indent=2, ensure_ascii=False))
    
    return graph

if __name__ == "__main__":
    import sys
    build_dependency_graph(sys.argv[1] if len(sys.argv) > 1 else ".")
```

### 第三步：验证层 `scripts/validate-derived-data.py`

```python
#!/usr/bin/env python3
"""给定被修改的文件列表，只验证受影响的派生文档"""

import sys, json, yaml, subprocess, pathlib

def get_affected_docs(changed_files, graph):
    """根据变更的文件找出哪些文档需要验证"""
    affected = set()
    for changed in changed_files:
        for source, docs in graph.items():
            # source 可能是文件名、命令、glob 模式
            if source.startswith("pytest") or source.startswith("python"):
                continue  # 运行时命令不匹配文件
            if source in changed or pathlib.PurePosixPath(changed).match(source):
                for doc_path, fields in docs:
                    affected.add((doc_path, tuple(fields)))
    return affected

def validate_doc(doc_path, fields, frontmatter):
    """验证文档中指定的字段是否与数据源一致"""
    errors = []
    for inp in frontmatter.get("input", []):
        extract = inp.get("extract", "")
        if not extract:
            continue
        try:
            if inp["source"].startswith(("pyproject", "pytest", "python", "packs/")):
                result = subprocess.run(
                    extract, shell=True, capture_output=True, text=True, cwd=project_root
                )
                actual_value = result.stdout.strip()
                # 检查文档中是否包含这个值
                # ... (具体实现按字段类型定)
        except:
            pass
    return errors
```

### 第四步：门禁集成

**pre-commit 新增检查** (在 `scripts/pre-push.sh` 中)：

```bash
check_doc_alignment() {
    echo "🔍 检查文档对齐..."
    # 获取本次变更的文件
    CHANGED=$(git diff --cached --name-only)
    
    # 找出受影响的文档
    AFFECTED=$(python3 scripts/doc-dependency-graph.py --changed "$CHANGED" --check)
    
    if [ -n "$AFFECTED" ]; then
        echo "⚠️ 以下文件的数据源已被修改，请同步更新："
        echo "$AFFECTED"
        echo "运行 python3 scripts/validate-derived-data.py 查看详情"
        return 1  # 警告但不阻塞（或 return 1 阻塞）
    fi
    echo "✅ 文档对齐检查通过"
}
```

### 第五步：更新 doc-alignment skill

将当前「手动操作手册」升级为：「声明式依赖框架 + 自动门禁」的完整方案。核心变化：

| 当前 | 改进后 |
|:-----|:-------|
| 描述如何手动检查 | 提供声明式 input 框架 + 验证脚本 |
| 5 阶段手动流程 | 声明 → 自动解析 → 自动验证 → CI 门禁 |
| 依赖人工记忆 | 依赖机器可读的 frontmatter 声明 |
| 反应式（发现漂移再修） | 预防式（提交前拦截） |
| 全量检查 | 仅检查受影响的部分 |

---

## 五、实施路线

### Phase 0: 建立声明机制（~1h）
- 定义 `input` 字段的规范格式
- 创建 `scripts/doc-dependency-graph.py` 解析层
- 创建 `scripts/validate-derived-data.py` 验证层

### Phase 1: 为关键文档添加声明（~1h）
- README.md → 版本/测试数/EPIC 数
- project-report.json → 版本/EPIC 状态/测试数
- QUICKSTART.md → CLI 入口
- EPIC docs → EPIC 状态

### Phase 2: 集成门禁（~1h）
- pre-push.sh 增加文档对齐检查
- GitHub Actions 增加 doc-consistency job

### Phase 3: 声明全覆盖
- 所有 MD 文档添加 input 声明
- 所有 YAML/JSON 数据文件考虑是否可作为数据源
