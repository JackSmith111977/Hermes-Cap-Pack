# 文档对齐根因分析与流程改进方案

> **背景**: 2026-05-16 hermes-cap-pack v1.0.1 发布过程中发现多处文档漂移
> **分析者**: boku (Emma)
> **参考行业实践**: Docs-as-Code 方法论、DocDrift、driftcheck、docsync
> **日期**: 2026-05-16

---

## 一、现状：信息冗余矩阵

当前项目中，同一个数据存在于多个文件，且无任何文件被定义为权威来源：

| 数据项 | 存在的文件数 | 涉及的文件 |
|:-------|:----------:|:-----------|
| 项目版本号 | **5** | pyproject.toml, README.md, project-report.json, project-state.yaml, PROJECT-PANORAMA.html |
| 测试数量 | **4** | README.md, project-report.json, PROJECT-PANORAMA.html, pytest (运行时) |
| EPIC 状态 | **3** | project-report.json, project-state.yaml, 各 EPIC-*.md 文件 |
| CLI 入口 | **4** | README.md, project-report.json, QUICKSTART.md, ADAPTER_GUIDE.md |
| Python 最低版本 | **3** | README.md, project-report.json, pyproject.toml |
| 依赖列表 | **3** | README.md, project-report.json, pyproject.toml |
| 能力包列表 | **3** | README.md, project-report.json, packs/*/cap-pack.yaml |

**结论**：每个数据项平均存在 3.6 个副本，意味着每次更新有 2.6 个机会忘记同步。

---

## 二、根因分析：六层问题

### 第 1 层：🔄 冗余无主 — 没有单一事实来源 (Single Source of Truth)

```
问题: 版本号在 5 个文件中？哪个是权威？
结果: 每个文件都可能被单独修改 → 必然漂移
根源: 设计阶段没有定义数据层级
```

### 第 2 层：🚪 无门禁 — 提交前没有自动检查

```
问题: 改 pyproject.toml 版本号时，没人检查 README 是否同步更新
结果: v1.0.0 → v1.0.1 时，project-report.json 留在了 1.0.0
根源: git commit 前没有跨文件一致性检查
```

### 第 3 层：🧠 依赖人脑 — 「我记住了」是最不可靠的机制

```
问题: boku 觉得「我改好了版本号」，其实只改了 pyproject.toml
结果: 每次发布都有遗漏
根源: 人类记忆不可靠 + 无自动化兜底
```

### 第 4 层：📋 信息过载 — 太多文件需要维护

```
问题: 7 个 EPIC 文档 + project-report.json + project-state.yaml 
      + README.md + PANORAMA.html + QUICKSTART.md + ADAPTER_GUIDE.md
结果: 每次变更需要更新 3-5 个文件，认知负担太大
根源: 文档体系设计时未考虑维护成本
```

### 第 5 层：🔙 反应式对齐 — 不是预防而是事后补救

```
问题: 漂移被发现时才去修复（如今天）
结果: 修复成本随时间指数增长
根源: 没有建立「持续对齐」的习惯和门禁
```

### 第 6 层：⚙️ 手动生成 — 可自动化的信息被手动维护

```
问题: PANORAMA.html 中的版本号、EPIC 状态本可以从数据源生成
结果: 手动改 → 忘记改 → 漂移
根源: 没做「数据驱动生成」的设计
```

---

## 三、行业最佳实践参考

| 工具/方法 | 核心理念 | 可借鉴点 |
|:----------|:---------|:---------|
| **Docs-as-Code** | 文档和代码同等对待：同仓库、同 PR、同 CI/CD | 文档变更和代码变更在同一 PR 中完成 |
| **DocDrift** | pre-commit 时自动检测文档漂移 | **git diff 检测 → 自动找相关文档 → 标注不一致** |
| **driftcheck** | pre-push hook + LLM 驱动的文档检查 | **交互式修复：发现问题 → 生成修复 → 应用** |
| **项目状态机** | 单一数据源 + 自动推导 | **project-state.yaml = 唯一真相源 → 其他文件据此生成** |
| **数据驱动文档** | 从结构化数据生成展示层 | **README 的元数据从 pyproject.toml 自动提取** |

---

## 四、改进方案

### 方案 A: 定义数据层级（立即实施, ~30min）

为每个数据项指定「权威来源」和「派生来源」：

```
数据层级 (→ 表示「从此读取」):

版本号:
  权威: pyproject.toml
  派生: README.md → 从 pyproject.toml 读取
  派生: project-report.json → 从 pyproject.toml 读取
  派生: PANORAMA.html → 从 project-report.json 读取

测试数:
  权威: pytest --collect-only (运行时)
  派生: README.md → 手动同步（标记 TODO 自动化）
  派生: project-report.json → 手动同步

EPIC 状态:
  权威: project-state.yaml
  派生: project-report.json → 从 state.yaml 读取
  派生: EPIC-*.md → 手动维护（但验证与 state.yaml 一致）

CLI 入口:
  权威: README.md 项目身份表
  派生: 所有其他文档 → 以 README 为准
```

**产出**: `docs/DATA-AUTHORITY.md` 文件，团队共识

### 方案 B: 创建 pre-commit 漂移检测脚本（短期, ~2h）

参考 DocDrift 模式，在 `scripts/pre-push.sh` 中增加文档一致性检查：

```bash
# pre-push.sh 新增检查项

check_doc_consistency() {
    local errors=0
    
    # 1. 版本号一致性
    PYPROJ_VER=$(grep "^version" pyproject.toml | grep -oP '\d+\.\d+\.\d+')
    README_VER=$(grep -m1 '版本' README.md | grep -oP '\d+\.\d+\.\d+')
    if [ "$PYPROJ_VER" != "$README_VER" ]; then
        echo "❌ 版本号不一致: pyproject=$PYPROJ_VER vs README=$README_VER"
        errors=$((errors+1))
    fi
    
    # 2. 测试数一致性
    ACTUAL=$(python -m pytest --collect-only -q 2>&1 | tail -1 | grep -oP '\d+')
    README_TEST=$(grep -m1 '测试' README.md | grep -oP '\d+(?= ✅)')
    if [ "$ACTUAL" != "$README_TEST" ]; then
        echo "❌ 测试数不一致: actual=$ACTUAL vs README=$README_TEST"
        errors=$((errors+1))
    fi
    
    # 3. EPIC 状态一致性（project-report.json vs project-state.yaml）
    PYTHON_CMD=$(cat << 'PYEOF'
import json, yaml, sys
report = json.load(open('docs/project-report.json'))
state = yaml.safe_load(open('docs/project-state.yaml'))
state_epics = {k: v['state'] for k, v in state['entities']['epics'].items()}
report_epics = {e['id']: e['status'] for e in report['epics']}
errors = []
for eid, s_state in state_epics.items():
    s_report = report_epics.get(eid)
    if s_state != s_report:
        errors.append(f"{eid}: state={s_state} vs report={s_report}")
sys.exit(1 if errors else 0)
PYEOF
    )
    if ! python3 -c "$PYTHON_CMD"; then
        echo "❌ EPIC 状态在 project-report.json 和 project-state.yaml 之间不一致"
        errors=$((errors+1))
    fi
    
    if [ "$errors" -gt 0 ]; then
        echo "🔴 发现 $errors 个文档漂移问题，请修复后再推送"
        return 1
    fi
    echo "✅ 文档一致性检查通过"
    return 0
}
```

### 方案 C: GitHub Actions CI 文档漂移门禁（中期, ~1h）

在 `.github/workflows/ci.yml` 中增加文档一致性 Job：

```yaml
  doc-consistency:
    name: 📋 Doc Consistency Gate
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - name: Check version consistency
        run: |
          PYPROJ_VER=$(grep "^version" pyproject.toml | grep -oP '\d+\.\d+\.\d+')
          README_VER=$(grep -m1 '版本' README.md | grep -oP '\d+\.\d+\.\d+')
          if [ "$PYPROJ_VER" != "$README_VER" ]; then
            echo "❌ Version mismatch: pyproject=$PYPROJ_VER vs README=$README_VER"
            exit 1
          fi
          echo "✅ Version consistent: $PYPROJ_VER"
      
      - name: Check test count consistency
        run: |
          pip install pyyaml typer rich jsonschema
          ACTUAL=$(python -m pytest --collect-only -q 2>&1 | tail -1 | grep -oP '\d+')
          README_TEST=$(grep -m1 '测试' README.md | grep -oP '\d+(?= ✅)')
          if [ "$ACTUAL" != "$README_TEST" ]; then
            echo "❌ Test count mismatch: actual=$ACTUAL vs README=$README_TEST"
            exit 1
          fi
          echo "✅ Tests consistent: $ACTUAL"
      
      - name: Check EPIC status consistency
        run: |
          python3 scripts/check-epic-consistency.py
```

**新增脚本**: `scripts/check-epic-consistency.py`

### 方案 D: 减少冗余 — 数据驱动生成（长期）

将重复信息集中管理，能自动生成的就不要手写：

| 当前 | 改进方案 |
|:-----|:---------|
| README 中手写版本号 | **用 badge 生成器 + 读取 pyproject.toml** |
| project-report.json 手动维护 EPIC 状态 | **从 project-state.yaml 自动生成 EPIC 段** |
| PANORAMA.html 手动维护 | **从 project-report.json 生成**（已有 generate script，但需自动化触发） |
| QUICKSTART 中 CLI 命令 | **模板化：从 README 的身份表引用** |

### 方案 E: 提交模板提醒（快速见效, ~5min）

在 `.gitmessage` 或 commit 模板中加入提醒：

```
# === 提交前检查清单 ===
# □ 版本号同步了？（pyproject.toml → README / project-report / PANORAMA）
# □ EPIC 状态更新了？（state.yaml → project-report.json）
# □ 测试数更新了？
# □ CLI 命令一致？
```

---

## 五、推荐实施路线

| 优先级 | 方案 | 估时 | 效果 |
|:------:|:-----|:----:|:------|
| 🔴 **立即** | A: 定义数据层级 + E: 提交模板 | ~30min | 建立共识，防止新增漂移 |
| 🔴 **立即** | B: pre-commit 漂移检测脚本 | ~2h | 提交前拦截，阻止漂移进入仓库 |
| 🟡 **短期** | C: GitHub Actions CI 门禁 | ~1h | CI 层面兜底，双重保险 |
| 🟢 **中期** | D: 数据驱动生成（逐步减少冗余） | ~4h | 从根源消除部分漂移 |

---

## 六、可复用经验（本次实践沉淀）

### 经验 1: 文档漂移的「修复成本曲线」

```
修复成本的三个阶段:
🟢 提交前: git diff 时发现 → 改 1 个文件 → 成本 10 秒
🟡 提交后: push 后 CI 发现 → 改 N 个文件 + 新 commit → 成本 5 分钟
🔴 发布后: release 后用户发现 → 改所有文件 + 新 release + 道歉 → 成本 30min+

结论: 📍 门禁越靠左，成本越低
```

### 经验 2: 不要相信「我记住了」

今天反复出现的模式：
1. boku 改 pyproject.toml 版本号 → 忘记改 project-report.json
2. boku 改 README → 忘记改 project-state.yaml
3. boku 改代码 → 忘记同步 QUICKSTART.md

**教训**: 任何「我记住了」的承诺，都应该有一个门禁兜底。

### 经验 3: 单一事实来源的威力

`project-state.yaml` 作为 EPIC 状态的权威来源后，project-report.json 的 EPIC 段应该从它生成，而不是手写维护。**数据驱动 > 手动维护**。

### 经验 4: 文档对齐不是一次性任务，是持续过程

今天做的「文档全面对齐」是**反应式**的——漂移已经发生了才修。  
真正的目标是**预防式**的——在漂移发生前就拦截。  
这需要门禁（pre-commit/CI）而不是手动检查。
