---
type: pitfall
skill_ref: capability-pack-design
keywords: [extraction, project-state, doc-alignment, drift, ci-failure]
---

# 能力包提取文档对齐陷阱

## 问题现象
CI 的 `project-state.py verify` 门禁报错，YAML 状态与 SDD 文档状态不一致。

## 根因分析

### 1. 提取流程退化
第一次 batch 提取（github-ecosystem → security-audit）正确更新了 `project-state.yaml` + story docs，但第二次 batch（media-processing → social-gaming）退化到只更新 PROJECT-PANORAMA.html + EPIC 文档。

### 2. 每次提取涉及 7 个文档，但实际只更新了 3 个
| 文档 | 角色 | 更新了吗？ |
|:-----|:-----|:---------|
| `cap-pack.yaml` + SKILLS/ | 能力包主体 | ✅ |
| PROJECT-PANORAMA.html | 可视化管理面板 | ✅ |
| EPIC-003 模块表 | 提取进度记录 | ✅ |
| EPIC-003 全景路线图 | 阶段规划追踪 | ✅ |
| **project-state.yaml** | **状态机一致性** | ❌ 最后 3 个模块 |
| **STORY-3-*.md** | **Story 状态** | ❌ 全部 7 个（approved→应为 completed） |
| **README.md** | **项目身份** | 最后 1 个版本号不对齐 |

### 3. SOP 有但没执行
`capability-pack-design` 的 §四-B Step 5 明确要求更新 project-state.yaml，但在快速 batch 提取中没有重新加载 SOP skill 来执行。

### 4. SOP 本身有盲点
Step 5 没提到更新 Story doc 的 frontmatter 状态（`approved` → `completed`），也没提供自动化工具体。

### 5. 无本地预防机制
CI 是第一道防线而非最后一道——缺少 pre-commit 或 pre-push 本地校验。

## 修复手段
1. `project-state.py sync` — 同步 YAML 与文档状态
2. `pyproject.toml` 版本对齐 — 修复 README/pyproject 不一致
3. 创建 `complete-extraction.py` — 统一完成脚本
4. 创建 pre-push 本地门禁
