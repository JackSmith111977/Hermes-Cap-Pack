# EPIC-007: 本地 Cap-Pack 管理系统 — 技能治理、同步与持续进化

> **epic_id**: `EPIC-007`
> **status**: `draft`
> **created**: 2026-05-16
> **updated**: 2026-05-16
> **owner**: boku (Emma)
> **优先级**: P1 — 能力包生态的本地管理闭环
> **估算**: ~28h（5 Phases · ~16 Stories）
> **前置条件**: EPIC-005 治理引擎 ✅ + EPIC-006 修复引擎 ✅ + v1.0.1 release ✅
> **SDD 流程**: `CLARIFY ☐ → RESEARCH ☐ → SPEC ☐ → IMPLEMENT ☐ → QA_GATE ☐ → COMMIT ☐`

---

## 〇、动机与背景

### 全局视角：三层管理系统

```
┌─────────────────────────────────────────────────────────────┐
│  Layer 1: 远程仓库 (GitHub)                                  │
│  ┌─────────────────────────────────────────────────────────┐│
│  │  🏛️ 官方能力包 ≡ 17 个 packs/ · CHI 67.92               ││
│  │  这是「发布态」— 经过治理引擎认证的稳定版本                ││
│  └─────────────────────────────────────────────────────────┘│
│                         ↕ sync                              │
│  Layer 2: 本地 Cap-Pack 管理 (本 EPIC)                      │
│  ┌─────────────────────────────────────────────────────────┐│
│  │  📦 本地工作副本 ≡ 日常开发的 skill 包                     ││
│  │  从官方拉取 · 本地修改 · 治理验证 · 推回官方              ││
│  │  治理引擎集群 × N 个治理引擎 × 快速同步管道                ││
│  └─────────────────────────────────────────────────────────┘│
│                         ↕ convert                            │
│  Layer 3: Hermes 原生技能目录                                │
│  ┌─────────────────────────────────────────────────────────┐│
│  │  📝 ~/.hermes/skills/ 原生技能                           ││
│  │  主 Agent (boku) 日常使用的扁平技能库                     ││
│  └─────────────────────────────────────────────────────────┘│
│                                                             │
│  ┌─────────────────────────────────────────────────────────┐│
│  │  🧠 经验积累系统 (跨层横向)                                ││
│  │  任务出错 → 标记经验 → 路由 → 改良技能包 / 记忆存档       ││
│  └─────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
```

### 为什么要做？

当前 cap-pack 项目完成了「治理引擎能发现问题、修复引擎能自动修复」，但还缺三个关键能力：

| 缺口 | 影响 | 本 EPIC 解决 |
|:-----|:------|:-------------|
| 🔴 **没有本地管理体系** | 技能包只有在 GitHub 上有一份，本地无法方便地管理、修改、测试 | **本地 cap-pack 工作副本 + 同步管道** |
| 🔴 **Hermes 原生技能 → 能力包 转换全靠手动** | 每个新技能需要 boku 手动提取，耗时且易错 | **转换引擎 automate Hermes → Cap-Pack** |
| 🟡 **经验积累无系统** | 技能执行出问题时，修复经验只留在对话中，无法反哺技能包 | **经验积累框架（本 EPIC 搭架子，后续 EPIC 完善）** |

### 核心设计原则

1. **主 Agent 驱动语义分析** — 所有需要 LLM 的工作（分类/分组/描述）由主 Agent（Hermes/boku）通过工具调用完成，不另建 LLM 调用模块
2. **仓库 = 官方发布态** — GitHub 上的 packs/ 是经过治理引擎认证的官方版本，不可直接修改
3. **本地 = 工作副本** — 本地是官方包的 downstream，修改后经治理验证才能推回
4. **经验积累是横向能力** — 不嵌入转换流程，而是跨层的横向系统：任务出错 → 标记经验 → 路由 → 反馈
5. **同步管道的两种模式** — 存在性同步（新增/缺失检测）+ 版本变更同步（修改检测与推送）

---

## 一、三层架构详解

### Layer 1: 远程仓库 — 官方能力包 🏛️

```
GitHub: JackSmith111977/Hermes-Cap-Pack
└── packs/
    ├── doc-engine/           ← 经过治理验证的官方发布
    ├── developer-workflow/
    ├── learning-engine/
    └── ... (17 个)
```

**特征**：
- ✅ 只接受通过 `cap-pack scan + fix` 治理验证的包
- ✅ 每个 release 包含版本号 + CHANGELOG
- ✅ 是「跨 Agent 兼容的官方标准」
- ❌ 不直接在本层开发——开发在本地进行

### Layer 2: 本地 Cap-Pack 管理 (本 EPIC) 📦

```
~/.cap-pack/                    ← 本地管理根目录（与 Hermes 独立）
├── packs/                      ← 本地工作副本
│   ├── doc-engine/             ← 从远程拉取 / 本地修改
│   │   ├── cap-pack.yaml
│   │   ├── SKILLS/
│   │   └── ...
│   ├── my-custom-pack/         ← 本地自建包（不推远程）
│   └── ...
├── state.json                  ← 同步状态：每个包的 remote_version / local_version / sync_status
├── sync.log                    ← 同步操作日志
└── governance/                 ← 治理引擎本地实例
    ├── scanner/                ← 复用 EPIC-005
    └── fixer/                  ← 复用 EPIC-006
```

**核心操作**：

```
cap-pack pull                   从远程拉取官方包到本地
cap-pack push                   本地修改经治理验证后推回远程
cap-pack status                 显示本地 vs 远程差异状态
cap-pack sync                   一键同步（pull + push）
```

### Layer 3: Hermes 原生技能 📝

```
~/.hermes/skills/
├── doc-engine/pdf-layout/SKILL.md    ← boku 日常使用的原生 skill
├── doc-engine/docx-guide/SKILL.md
└── ...
```

**转换管道**：Hermes 原生 skill → （经转换引擎）→ 本地 cap-pack

### 🧠 经验积累系统（横向）

```
                            ┌──────────────────┐
                            │  任务执行出错      │
                            └────────┬─────────┘
                                     │ 标记
                                     ▼
                            ┌──────────────────┐
                            │  经验记录          │
                            │  (在 cap-pack 层面)│
                            └────────┬─────────┘
                                     │ 路由
                          ┌──────────┴──────────┐
                          ▼                     ▼
              ┌───────────────────┐   ┌──────────────────┐
              │ 学习反馈 → 改良    │   │ 记忆存档          │
              │ 技能包            │   │ (经验仅供参考)     │
              └───────────────────┘   └──────────────────┘
```

**本 EPIC 只做架子**：
- 在 `cap-pack.yaml` 中标记 `experience_accumulation: true` 支持
- 预留经验记录格式
- 不实现学习反馈回路（给后续 EPIC）

---

## 二、核心管线设计

### 整体流程

```
            主 Agent (boku) 全权驱动
        ┌──────────────────────────────────┐
        │  技能治理 & 同步 & 转换 统一 CLI   │
        │  cap-pack sync / status / convert │
        └──────────────────────────────────┘
                      │
        ┌─────────────┼─────────────┐
        ▼             ▼             ▼
┌──────────────┐ ┌──────────┐ ┌──────────────┐
│  同步管道      │ │  转换引擎  │ │  本地管理     │
│  sync        │ │ convert  │ │  status/pull │
│  (存在+版本)  │ │ (Hermes→ │ │  /push       │
│              │ │  CapPack) │ │              │
└──────────────┘ └──────────┘ └──────────────┘
        │             │             │
        ▼             ▼             ▼
┌──────────────────────────────────────────────┐
│              治理引擎集群                       │
│  L0 scanner · L1 scanner · FixRule ·         │
│  SQS scoring · schema 验证                    │
└──────────────────────────────────────────────┘
```

### 所有 LLM 工作怎么完成？

**不需要独立的 LLM 调用模块**。所有需要语义分析的地方，主 Agent (boku) 通过工具调用来完成：

```python
# 脚本需要 LLM 分析时 → 委托给主 Agent
def analyze_with_agent(skill_name: str, skill_content: str, packs_info: str) -> dict:
    """主 Agent 分析 skill 分类/分组/描述
    
    脚本不再内置 LLM prompt——通过 subagent 或直接
    调用 Hermes 自身的推理能力来完成。
    """
    # 脚本准备好分析所需的上下文
    context = f"""
Skill: {skill_name}
内容预览: {skill_content[:2000]}
已有包: {packs_info}

请输出分类决策（JSON）...
    """
    # 委托给主 Agent 处理（通过 delegate_task）
    result = delegate_task(goal="分析技能分类和分组", context=context)
    return json.loads(result)
```

**实际上更简单**：整个 `convert` 流程就是一个 Hermes skill（`cap-pack-converter`）。boku 加载这个 skill，按照步骤执行——脚本负责文件操作，boku 负责 LLM 判断。

---

## 三、CLI 设计（全部使用 cap-pack 前缀）

### 同步命令

```bash
# 拉取官方包到本地
cap-pack pull                          # 拉取所有
cap-pack pull doc-engine               # 拉取指定包
cap-pack pull --dry-run                # 预览

# 推送本地修改到远程
cap-pack push                          # 推送所有修改
cap-pack push doc-engine               # 推送指定包
cap-pack push --dry-run                # 预览（显示变更 diff）
cap-pack push --force                  # 跳过治理验证（谨慎）

# 状态查看
cap-pack status                        # 显示所有包的状态
cap-pack status doc-engine             # 显示单个包详情
cap-pack status --format json          # JSON 输出

# 一键同步
cap-pack sync                          # pull + push 一次完成
```

### 转换命令

```bash
# 将 Hermes 原生 skill 转换为 cap-pack
cap-pack convert pdf-layout            # 单个 skill
cap-pack convert --all                 # 批量所有未打包 skill
cap-pack convert pdf-layout --pack doc-engine  # 指定目标包
cap-pack convert --all --dry-run       # 预览
cap-pack convert --unpacked-only       # 只处理未打包的（默认）
```

### 本地管理命令

```bash
cap-pack list                          # 列出本地所有包
cap-pack list --remote                 # 列出远程官方包
cap-pack list --unpacked               # 列出未打包的 Hermes skill
cap-pack inspect doc-engine            # 查看包详情
cap-pack init                          # 初始化本地 ~/.cap-pack/
cap-pack prune                         # 清理本地冗余文件
```

### 经验积累（架子命令）

```bash
cap-pack experience mark <skill> --type pitfall --desc "..."  # 标记经验
cap-pack experience list               # 列出经验
cap-pack experience export             # 导出经验（给学习系统消费）
```

### 输出格式（status 示例）

```bash
$ cap-pack status
📊 Cap-Pack 状态 — 本地 vs 远程

📦 官方包 (17)
├── doc-engine (2.0.0)      ✅ 同步  本地:2.0.0 = 远程:2.0.0
├── developer-workflow (1.0.0) 🔄 已修改  本地有 2 个未推送变更
├── learning-engine (1.0.0)  ⬇️ 可更新  远程为 1.0.1 →
├── network-proxy (1.0.0)   ⬆️ 未推送  本地新建 → 远程无
└── ...

📦 本地自建包 (2)
├── my-workflow (0.1.0)     🏠 仅本地  (无远程对应)
└── team-scripts (0.5.0)    🏠 仅本地

📦 未打包 Hermes skill (5)
├── pdf-layout               → 可转换到 doc-engine
├── clash-config             → 可转换到 network-proxy
└── ...
```

---

## 四、同步管道设计

### 4.1 存在性同步 (Existence Sync)

**检测逻辑**：

```text
本地存在             远程存在             状态
─────────────────────────────────────────────
✅                    ✅                 同步 (版本一致)
✅                    ✅                 可更新 (本地版本 < 远程版本)
✅                    ❌                 仅本地 (自建包或新包待推送)
❌                    ✅                 缺失 (需 pull)
```

**实现方式**：

```python
def check_existence_sync():
    """对比本地 packs/ 与远程 GitHub 目录"""
    local_packs = {p.name for p in Path("~/.cap-pack/packs").iterdir()}
    remote_packs = fetch_remote_pack_list()  # GitHub API
    
    missing_local = remote_packs - local_packs  # 需 pull
    extra_local = local_packs - remote_packs    # 需 push 或标记为仅本地
    
    return {"to_pull": missing_local, "to_push": extra_local}
```

### 4.2 版本变更同步 (Version Sync)

**检测逻辑**：

```python
def check_version_sync():
    """对比本地与远程版本号和文件 hash"""
    local_state = load_local_state()  # ~/.cap-pack/state.json
    for pack_name, local_meta in local_state.items():
        remote_meta = fetch_remote_meta(pack_name)
        
        if local_meta["version"] != remote_meta["version"]:
            # 版本不同 → 需要更新
            if semver.compare(local_meta["version"], remote_meta["version"]) < 0:
                status = "可更新"  # 本地落后
            else:
                status = "已修改"  # 本地领先
        elif file_hash_changed(local_meta, remote_meta):
            status = "已修改"  # 版本相同但内容变了
        
        yield (pack_name, status)
```

**状态矩阵**：

| 本地版本 | 远程版本 | 本地 Hash | 远程 Hash | 状态 | 操作 |
|:--------:|:--------:|:---------:|:---------:|:-----|:-----|
| 2.0.0 | 2.0.0 | abc | abc | ✅ 同步 | 无操作 |
| 2.0.0 | 2.0.0 | abc | def | 🔄 远程已变更 | `pull` 覆盖本地 |
| 2.0.0 | 2.0.0 | def | abc | 🔄 本地已修改 | `push` 推送或 revert |
| 2.0.0 | 2.0.1 | — | — | ⬇️ 可更新 | `pull` 升级 |
| 2.0.1 | 2.0.0 | — | — | ⬆️ 未推送 | `push` 发布 |

### 4.3 推送前治理门禁

```text
cap-pack push → 自动执行治理引擎门禁
    ├── L0 兼容性扫描:     ✅ 通过 → 继续
    ├── L1 结构强制:       ✅ 通过 → 继续
    ├── L2 健康度:         ✅ 通过 或 ⚠️ 警告 → 继续或暂停
    ├── L3 生态检查:       ⚠️ 仅警告 → 可放行
    ├── schema 验证:       ✅ 通过 → 继续
    └── SQS 评分阈值:      ✅ ≥ 60 → 继续
                          ❌ 未通过 → 拦截 + 提示 cap-pack fix
```

---

## 五、转换引擎设计（Hermes 原生 skill → Cap-Pack）

### 核心原则

1. **主 Agent 驱动语义分析** — 脚本做文件操作，所有需要 LLM 判断的地方委托给主 Agent（boku）
2. **支持自动匹配和自定义包** — `--auto` 用 suggest() 自动匹配，`--pack <name>` 指定目标包，`--new-pack <name>` 创建新包
3. **经验积累留架子** — 不在此阶段生成 EXPERIENCES/，只标记 `experience_accumulation: true`

### 五步流程（与 EPIC-007 初版一致，但 LLM 工作委派给主 Agent）

| 步 | 名称 | 谁做 | 操作 |
|:--:|:-----|:----:|:------|
| ① | **SCAN** 枚举 | 🛠️ 脚本 | `~/.hermes/skills/` 扫描 + `packs/` 扫描 → 候选清单 |
| ② | **ANALYZE** 分析 | 🤖 **主 Agent** | 加载 skill 内容 → 由主 Agent 判断分类/分组/描述/标签 |
| ③ | **EXTRACT** 提取 | 🛠️ 脚本 | 创建目录 + 复制文件 + 生成 `cap-pack.yaml` |
| ④ | **GOVERN** 治理 | 🛠️ 脚本 | 复用 scanner + FixRule 自动扫描修复 |
| ⑤ | **REPORT** 报告 | 🛠️ 脚本 | 输出转换摘要 + 验证命令 |

### 步骤② 的实际执行方式

整个 `convert` 流程本身就是一个 Hermes Skill（`cap-pack-converter`）：

```text
1. boku 加载 cap-pack-converter skill
2. 脚本执行 SCAN → 输出候选清单 JSON
3. boku (主 Agent) 读取候选清单 → 调用 LLM 判断：
   - "pdf-layout 属于 doc-engine 包，置信度 92%"
   - "clash-config 建议创建 network-proxy 新包"
4. 脚本根据 boku 的判断执行 EXTRACT
5. 脚本执行 GOVERN (复用 scanner + fixer)
6. 脚本输出 REPORT
```

**脚本 ↔ 主 Agent 交互模式**：

```bash
# 步骤① 脚本扫描
$ cap-pack scan --unpacked-only --format json
# 输出: [{"name":"pdf-layout","tags":["pdf","weasyprint"],"size":"1.2MB"},...]

# 步骤② boku (主 Agent) 看扫描结果 → 做出判断 → 告诉脚本
# 这是通过 skill 流程完成的，不是独立的命令调用

# 步骤③-⑤ 脚本执行
$ cap-pack convert --from-json decisions.json
# 批量提取
```

---

## 六、与现有系统集成

### 代码复用

| 现有组件 | 位置 | 在本 EPIC 中的用途 |
|:---------|:------|:-------------------|
| `scripts/extract-pack.py` | `scripts/` | 文件提取（复用 `find_skill_dir()`、`list_skill_files()`） |
| `adapter/cap_pack_adapter.py` | `skill_governance/` | suggest() 自动匹配（步骤②的参考输入） |
| `scanner/` (全部) | `skill_governance/` | L0-L4 治理扫描 |
| `fixer/rules/` (全部) | `skill_governance/` | 自动修复 |
| `cli/main.py` | `skill_governance/` | CLI 框架 + 命令注册 |
| `schemas/cap-pack-v3.schema.json` | `schemas/` | 包格式验证 |
| `scripts/validate-pack.py` | `scripts/` | 包完整性验证 |
| `scripts/pre-push.sh` | `scripts/` | 推送前门禁（可升级为 `cap-pack push` 的一部分） |

### 需要新增的文件

| 文件 | 用途 | 预计行数 |
|:-----|:------|:--------:|
| `cli/sync_cmd.py` | sync/pull/push/status CLI | ~200 |
| `cli/convert_cmd.py` | convert CLI | ~120 |
| `sync/existence_sync.py` | 存在性同步逻辑 | ~100 |
| `sync/version_sync.py` | 版本变更同步逻辑 | ~150 |
| `sync/state_manager.py` | 本地 state.json 管理 | ~80 |
| `converter/scanner.py` | 步骤① Hermes skill 扫描 | ~100 |
| `converter/extractor.py` | 步骤③ 文件提取 + manifest 生成 | ~200 |
| `converter/governor.py` | 步骤④ 治理集成 | ~80 |
| `converter/reporter.py` | 步骤⑤ 报告 | ~80 |
| `cli/experience_cmd.py` | 经验积累架子命令 | ~60 |
| `tests/` | 测试 | ~300 |
| **总计** | | **~1,470** |

---

## 七、分阶段实施

### Phase 0: 本地管理工作副本 (3 Stories, ~5h)

| Story | 内容 | 产出 |
|:------|:------|:------|
| STORY-7-0-1 | 初始化 `~/.cap-pack/` 目录 + state.json | 本地管理根目录 |
| STORY-7-0-2 | `cap-pack pull` — 从 GitHub 拉取官方包 | 同步：远程→本地 |
| STORY-7-0-3 | `cap-pack list` + `cap-pack list --remote` | 本地/远程包查看 |

### Phase 1: 同步管道 (4 Stories, ~8h)

| Story | 内容 | 产出 |
|:------|:------|:------|
| STORY-7-1-1 | 存在性同步检测 | `cap-pack status` 显示新增/缺失 |
| STORY-7-1-2 | 版本变更同步检测 | `cap-pack status` 显示版本差异 |
| STORY-7-1-3 | `cap-pack push` — 推送前治理门禁 + 推送到 GitHub | 同步：本地→远程 |
| STORY-7-1-4 | `cap-pack sync` — 一键 pull + push | 全同步管道 |

### Phase 2: 转换引擎 (4 Stories, ~6h)

| Story | 内容 | 产出 |
|:------|:------|:------|
| STORY-7-2-1 | SCAN 模块 + convert CLI 架子 | `cap-pack scan --unpacked-only` |
| STORY-7-2-2 | ANALYZE — 主 Agent 驱动 skill 分类/分组 | convert 流程的 LLM 环节 |
| STORY-7-2-3 | EXTRACT — 文件提取 + cap-pack.yaml 生成 | 单个 skill → cap-pack |
| STORY-7-2-4 | GOVERN + REPORT — 治理验证 + 报告 | 全流程 end-to-end |

### Phase 3: 批量与自定义 (3 Stories, ~5h)

| Story | 内容 | 产出 |
|:------|:------|:------|
| STORY-7-3-1 | `--all` — 批量转换 + `--auto` 自动匹配 | 一键全量转换 |
| STORY-7-3-2 | 自定义包创建（直接 `cap-pack init --pack my-custom`） | 非从 Hermes 提取 | 
| STORY-7-3-3 | 一键推送改造（`cap-pack push --all` 经治理门禁同步到 GitHub） | 本地开发→官方发布 |

### Phase 4: 经验积累架子 (2 Stories, ~4h)

| Story | 内容 | 产出 |
|:------|:------|:------|
| STORY-7-4-1 | 经验记录格式 + `cap-pack experience mark` | 经验积累的基础设施 |
| STORY-7-4-2 | 经验路由框架 | 后续 EPIC 接入点 |

---

## 八、路线图全景

```
EPIC-005 ─── 治理引擎 (scanner)
    ↓
EPIC-006 ─── 修复引擎 (FixRule)
    ↓                          ─── 已有，已完成
══════════════════════════════════════════════
    ↓
EPIC-007 ─── 本地 Cap-Pack 管理系统          ← 本 EPIC
    ├── Phase 0: 本地工作副本 (pull/list)
    ├── Phase 1: 同步管道 (status/push/sync)
    ├── Phase 2: 转换引擎 (convert)
    ├── Phase 3: 批量与自定义
    └── Phase 4: 经验积累架子
         ↓
EPIC-008 ─── 经验路由与学习反馈回路（未来）
    ├── 经验→改良技能包
    └── 经验→记忆存档
         ↓
EPIC-009 ─── 多 Agent 治理引擎集群（未来）
    ├── 治理引擎即服务
    ├── Hermes 治理引擎 → OpenCode 治理引擎
    └── 跨 Agent 质量统一管控
```

---

## 九、与行业对比

| 维度 | SkillKit | Agent Skill Porter | **本 EPIC** |
|:-----|:--------:|:------------------:|:-----------:|
| 本地管理 | ✅ workspace sync | ❌ 无 | ✅ **~/.cap-pack/ + state.json** |
| 远程同步 | ✅ marketplace | ❌ 无 | ✅ **GitHub 双向同步** |
| 转换 | ✅ translate (格式) | ✅ sync (格式) | ✅ **Hermes→Cap-Pack 结构化** |
| 治理门禁 | ❌ 无 | ❌ 无 | ✅ **L0-L4 scanner + FixRule** |
| 经验积累 | ❌ 无 | ❌ 无 | ✅ **架子 + 路由框架** |
| 主 Agent 驱动 | ❌ 独立工具 | ❌ 独立工具 | ✅ **主 Agent 做语义分析** |

---

## 十、风险与缓解

| 风险 | 概率 | 影响 | 缓解 |
|:-----|:----:|:----:|:------|
| 同步时网络断开 | 🟡 中 | 🟡 中 | 幂等操作 + state.json 记录断点续传 |
| 本地修改与远程冲突 | 🟢 低 | 🔴 高 | push 前 diff 对比 + 治理门禁拦截 + `--dry-run` 预览 |
| 转换分类不准 | 🟡 中 | 🟡 中 | 主 Agent 验证 + 低 confidence 进待确认 |
| 同步覆盖本地修改 | 🟢 低 | 🔴 高 | pull 前备份当前状态 + 冲突提示 |
| 治理门禁太严格阻碍推送 | 🟡 中 | 🟡 中 | `--force` 跳过 + 记录警告到日志 |
