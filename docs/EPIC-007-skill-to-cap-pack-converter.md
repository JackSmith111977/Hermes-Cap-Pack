# EPIC-007: Skill → Cap-Pack 转换引擎 — 从原生技能目录到标准化能力包

> **epic_id**: `EPIC-007`
> **status**: `draft`
> **created**: 2026-05-16
> **updated**: 2026-05-16
> **owner**: boku (Emma)
> **优先级**: P1 — 能力包生态闭环的关键拼图
> **估算**: ~24h（4 Phases · ~14 Stories）
> **前置条件**: EPIC-005 治理引擎 ✅ + EPIC-006 修复引擎 ✅
> **SDD 流程**: `CLARIFY ☐ → RESEARCH ☐ → SPEC ☐ → IMPLEMENT ☐ → QA_GATE ☐ → COMMIT ☐`

---

## 〇、动机与背景

### 为什么要做？

当前 cap-pack 项目中已经有 17 个能力包，但全部是 boku **手动**从 `~/.hermes/skills/` 提取的。这个流程存在三个根本问题：

| 问题 | 影响 | 根因 |
|:-----|:------|:------|
| 🐢 **全手动提取** | 提取一个包需 20-40 分钟，17 个包 = 6h+ | 无自动化转换工具 |
| 🧠 **智力依赖 boku** | 新技能上线→boku 不在时无法打包 | 分类/分组/经验提取依赖人工判断 |
| 🎭 **格式不一致** | 各包质量参差不齐（CHI 67.92 🟡） | 缺乏统一转换标准 |

**核心判断**：治理引擎（EPIC-005）能 「发现问题」，修复引擎（EPIC-006）能「修复问题」，但还没有能力 **「把原始技能自动组织成标准能力包」**。

### 行业现状

2026 年 Skill 工具生态已出现多个标准化方向：

| 工具/标准 | 核心功能 | 与 EPIC-007 的关系 |
|:----------|:---------|:-------------------|
| **SkillKit** ⭐935 | 跨 46 个 Agent 的 skill 安装/翻译/推荐 | 验证了「SKILL.md 标准」的跨平台可行性——46 个 Agent 用同一格式。`skillkit translate` 做格式转换但不做语义分组。 |
| **Agent Skill Porter** | 7 Agent 间 skill 格式互转 + 占位符转换 | 证明了 SkillBundle 中间格式的有效性。其「Chimera Hub」模式与我们的 converter 复用解码器+编解码器的思路一致。 |
| **Agent Skills Standard** | Hermes/Claude/Copilot/Cursor 共用 SKILL.md 格式 | 确认了输入格式（Hermes SKILL.md）与输出格式（cap-pack 的 SKILL.md）本质是同一标准——转换的重点不在格式翻译，而在**结构化重组**。 |
| **Microsoft Agent Framework** | 企业级 Agent Skills 实现 | 四阶段渐进披露模式验证了 skills/references/resources/scripts 的四层组织是正确的设计。 |

**关键洞察**：现有工具都在做「SKILL.md 格式转换」（Hermes → Claude → Cursor），但没有工具做 **「扁平 skill 目录 → 语义化能力包」** 的结构化重组。这正是我们的独特价值。

### 目标

| 维度 | 当前（手动） | 目标（自动化） |
|:-----|:------------|:--------------|
| 单 skill 提取耗时 | ~10 min | **< 10 秒**（自动化） |
| 批量全目录转换 | ❌ 不存在 | **`convert --all` 一键完成** |
| cap-pack.yaml 生成 | 手写 YAML | **LLM 推断 + 自动填充** |
| 分类准确率 | 依赖 boku 经验 | **80%+ 自动分类正确** |
| 经验提取 | 手动复制粘贴 | **LLM 自动识别 + 提取** |
| 新技能→已有包匹配 | 手动判断 | **`suggest()` 自动推荐** |

---

## 一、架构设计

### 整体架构

```
┌──────────────────────────────────────────────────────────────────┐
│                skill-governance convert 命令                       │
└──────────────────────────┬───────────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────────┐
│                    Converter 核心管线                              │
│                                                                   │
│  ┌──────────┐   ┌────────────┐   ┌────────────┐   ┌───────────┐ │
│  │ ① SCAN  │──▶│ ② ANALYZE  │──▶│ ③ EXTRACT  │──▶│ ④ GOVERN  │ │
│  │ 枚举扫描  │   │ LLM分类 +  │   │ 复制文件 + │   │ 治理扫描  │ │
│  │          │   │ 分组决策    │   │ 生成结构   │   │ + LLM调优 │ │
│  └──────────┘   └────────────┘   └────────────┘   └─────┬─────┘ │
│                                                          │       │
│              ┌──────────────┐                            │       │
│              │ ⑤ REPORT     │◀───────────────────────────┘       │
│              │ 输出摘要      │                                    │
│              └──────────────┘                                     │
└──────────────────────────────────────────────────────────────────┘
         │              │                  │
         ▼              ▼                  ▼
   ~/.hermes/skills/  packs/<name>/    skill-governance
   (输入源)            (输出目标)       scanner + fixer
```

### 五阶段管线

| Phase | 名称 | 谁驱动 | 输入 → 输出 |
|:-----:|:-----|:------:|:----------|
| **① SCAN** | 枚举与盘点 | 🛠️ 脚本 | `~/.hermes/skills/*/SKILL.md` → 候选清单 + 已有包索引 |
| **② ANALYZE** | 智能分析 | 🧠 **LLM** | 每个 skill 的 frontmatter + 内容 → 分类、分组、描述、经验标记 |
| **③ EXTRACT** | 提取与构建 | 🛠️ 脚本 | 候选清单 + LLM 决策 → 目录结构 + 文件复制 + cap-pack.yaml 生成 |
| **④ GOVERN** | 治理与调优 | 🛠️+🧠 | 新包 → L0-L4 扫描 + FixRule 修复 + E001/E002 LLM 调优 |
| **⑤ REPORT** | 报告与验证 | 🛠️ | 修复后结果 → 转换摘要 + schema 验证 + 验证命令 |

---

## 二、各阶段详细设计

### Phase ① SCAN — 枚举与盘点 🛠️

**纯脚本，不调用 LLM。**

#### 扫描 Hermes 技能目录

```python
# 复用 CLI 的 --list 能力
def scan_hermes_skills() -> list[SkillCandidate]:
    """扫描 ~/.hermes/skills/ 下的所有 skill"""
    skills_dir = Path("~/.hermes/skills").expanduser()
    candidates = []
    for skill_dir in sorted(skills_dir.iterdir()):
        if skill_dir.name.startswith(".") or skill_dir.name.startswith("_"):
            continue
        skill_md = skill_dir / "SKILL.md"
        if not skill_md.exists():
            continue
        fm = parse_frontmatter(skill_md)
        candidates.append(SkillCandidate(
            name=skill_dir.name,
            dir=skill_dir,
            frontmatter=fm,
            file_count=count_files(skill_dir),
        ))
    return candidates
```

#### 扫描已有能力包

```python
def scan_cap_packs() -> list[PackInfo]:
    """扫描 packs/ 下的所有已提取能力包"""
    packs_dir = Path("packs")
    packs = []
    for pack_dir in sorted(packs_dir.iterdir()):
        manifest = pack_dir / "cap-pack.yaml"
        if not manifest.exists():
            continue
        data = yaml.safe_load(manifest.read_text())
        packs.append(PackInfo(
            name=pack_dir.name,
            manifest=data,
            existing_skills=[s["id"] for s in data.get("skills", [])],
        ))
    return packs
```

#### 输出格式

```json
{
  "unpacked_skills": [
    {"name": "pdf-layout", "tags": ["pdf", "weasyprint"], "classification": null, "dir_size": "1.2MB"}
  ],
  "existing_packs": [
    {"name": "doc-engine", "skills": ["pdf-layout", "docx-guide"], "classification": "domain"}
  ]
}
```

**产出文件**: `~/.hermes/learning/converter_scan_result.json`

---

### Phase ② ANALYZE — 智能分析 🧠 LLM 核心

**LLM 驱动的批量分析。每个 skill 发送一次 LLM 请求（可批量合并减少调用次数）。**

#### LLM Prompt 模板

```markdown
你是一个能力包分类专家。需要分析一个 Hermes Skill 并决定它属于哪个能力包。

## Skill 信息
- 名称: {skill_name}
- 描述: {frontmatter_description}
- 标签: {tags}
- 分类: {classification if available}
- SKILL.md 前 1000 字: {content_preview}

## 已有能力包清单
{existing_packs_summary}

## 你的任务

请输出以下 JSON（只输出 JSON，不要多余文字）：

```json
{
  "should_pack": true/false,
  "target_pack": "已有包名 或 'new'",
  "new_pack_name": "如果创建新包，建议的名称（小写+连字符）",
  "new_pack_display_name": "人类可读包名",
  "new_pack_classification": "domain/toolset/infrastructure",
  "new_pack_description": "包描述（一句话）",
  "new_pack_tags": ["tag1", "tag2"],
  "confidence": 0-100,
  "reasoning": "分类理由（一句话）",
  "has_experience_content": true/false,
  "experience_types": ["pitfall"/"decision-tree"/"comparison"],
  "suggested_triggers": ["trigger1", "trigger2"]
}
```

如果 `confidence < 60`，放入待确认列表，由主人审核。
```

#### 批量策略

| 场景 | LLM 调用次数 | 备注 |
|:-----|:----------:|:-----|
| 1 个 skill → 已有包 | **1** | 快速追加 |
| N 个 skill → 新包 | **N** | 逐个分析后 auto-group |
| ——all ——auto | **N + 1** | N 个 skill 分析 + 1 次分组聚合 |

**批量优化**：将 5-10 个 skill 合并到一个 prompt 中，减少 LLM 调用。

#### 已有包匹配逻辑（脚本辅助）

安装 `CapPackAdapter.suggest()` 作为 LLM 的参考输入：

```python
from skill_governance.adapter.cap_pack_adapter import CapPackAdapter

adapter = CapPackAdapter()
suggestion = adapter.suggest(skill_path)
# 输出: {"best_pack": "doc-engine", "score": 0.85, "reason": "tags overlap: PDF..."}
# 这个结果作为 LLM prompt 的参考输入
```

---

### Phase ③ EXTRACT — 提取与构建 🛠️

**纯脚本。根据 LLM 的决策输出执行文件操作。**

```text
步骤:
1. 创建目标目录结构
   packs/<pack_name>/
   ├── SKILLS/<skill_name>/
   │   ├── SKILL.md        (复制)
   │   ├── references/     (复制)
   │   ├── scripts/        (复制)
   │   ├── templates/      (复制)
   │   └── checklists/     (复制)
   ├── EXPERIENCES/        (如有经验内容 → 由 LLM 提取)
   └── KNOWLEDGE/          (可选)

2. 生成 cap-pack.yaml
   name: <pack_name>
   version: 1.0.0
   type: capability-pack
   classification: <from LLM>
   description: <from LLM>
   skills:
     - id: <skill_name>
       path: SKILLS/<skill_name>/SKILL.md
       description: <from frontmatter>
   compatibility:
     agent_types: [hermes]

3. 如果已有 cap-pack.yaml → 合并（追加 skills 条目）

4. 更新 pack 级元数据（聚合 version / dependencies / compatibility）
```

**复用现有组件**: `scripts/extract-pack.py` 中的 `find_skill_dir()`, `list_skill_files()`, `copy_skill_files()`

---

### Phase ④ GOVERN — 治理与调优 🛠️ + 🧠

**脚本先行 + LLM 兜底。**

| 检查 | 方式 | 操作 |
|:-----|:----|:------|
| L0 格式合规 | 🛠️ `schema 验证` | 自动修复 (复用) |
| L1 结构强制 | 🛠️ `scanner` | FixRule 自动修 (复用) |
| L2 健康度 | 🛠️ `scanner` | 报告待改进项 |
| E001 SRA 元数据 | 🧠 **LLM** | 为 skill 生成 SRA 推荐描述 |
| E002 跨平台声明 | 🧠 **LLM** | 推断兼容性平台 |
| **经验提取** | 🧠 **LLM** | 从 SKILL.md 的 Pitfalls/经验/对比 → EXPERIENCES/ 文件 |

#### 经验提取 Prompt

```markdown
从以下 SKILL.md 中提取可复用的经验知识。

## Skill: {name}
{full_content}

请识别以下三类经验并输出 JSON:

1. **Pitfall** — "操作步骤 X 会报错 Y，因为 Z，正确做法是 W"
2. **Decision Tree** — "在场景 A 下用方案 X，在场景 B 下用方案 Y"
3. **Comparison** — "方案 X 比方案 Y 快 3 倍，但需要额外依赖 Z"

如果某类没有内容，输出空数组。

```json
{
  "experiences": [
    {"type": "pitfall", "title": "...", "content": "...", "section_ref": "## Common Pitfalls"},
    {"type": "decision-tree", "title": "...", "content": "...", "section_ref": "..."}
  ]
}
```
```

---

### Phase ⑤ REPORT — 报告与验证 🛠️

**纯脚本，汇总转换结果。**

```bash
=== 转换报告 ===
📦 目标包: doc-engine (已有)
├── 新增 skill: pdf-layout (SQS 78.2)
├── cap-pack.yaml: 已更新 (skills: 10 → 11)
├── schema 验证: ✅ 通过
└── 经验提取: 2 个 pitfall → EXPERIENCES/

📦 目标包: network-proxy (新建)
├── 新增技能: clash-config, proxy-monitor, proxy-finder
├── cap-pack.yaml: 已创建
├── schema 验证: ✅ 通过
└── LLM 辅助完成: 分类推断 ✅ / 经验提取: 3 条

⚠️ 待确认: social-gaming (confidence 55%)
└── boku 不确定这是 domain 还是 toolset，请主人审核

验证命令:
  cap-pack scan packs/doc-engine
  cap-pack fix packs/doc-engine
```

---

## 三、CLI 设计

```bash
# 转换单个 skill（自动推荐/创建包）
cap-pack convert pdf-layout
cap-pack convert pdf-layout --pack doc-engine       # 指定目标包
cap-pack convert pdf-layout --dry-run               # 预览

# 批量转换
cap-pack convert --all                              # 所有未打包 skill
cap-pack convert --all --auto                       # 自动分组+创建
cap-pack convert --all --interactive                # 逐个确认

# 批量+分组优化
cap-pack convert --all --group-by domain            # 按领域分组
cap-pack convert --all --group-by toolset           # 按工具分组

# 仅分析不执行
cap-pack convert --all --dry-run --format json      # 输出分析结果供审查

# 增量：只处理未打包的 skill
cap-pack convert --unpacked-only                    # 默认模式

# 重做：强制重新提取已有包中的 skill
cap-pack convert --all --force
```

---

## 四、与现有系统的关系

```
EPIC-005 (治理引擎) ─── 提供 scanner/fixer 基础设施
     ↓                          ↓
EPIC-006 (修复引擎) ── 提供 FixRule 自动修复
     ↓                          ↓
EPIC-007 (转换引擎) ── 消费 scanner + fixer 作为治理阶段
                         ↑
                   提供 convert 命令到治理 CLI

    Hermes 原生技能       Cap-Pack 包
    ~/.hermes/skills/     packs/<name>/
          │                     │
          ▼                     ▼
    EPIC-007 convert ──────► 标准化能力包
          │                     │
          ▼                     ▼
    LLM 分析结果           skill-governance
    (分类/分组/经验)         scan + fix 验证
```

### 复用现有组件清单

| 组件 | 位置 | 用途 |
|:-----|:------|:------|
| `find_skill_dir()` | `scripts/extract-pack.py` | Hermes skill 路径查找 |
| `list_skill_files()` | `scripts/extract-pack.py` | skill 文件枚举 |
| `_parse_frontmatter()` | `adapter/cap_pack_adapter.py` | SKILL.md 解析 |
| `PackManifest.from_file()` | `adapter/cap_pack_adapter.py` | 已有 manifest 解析 |
| `CapPackAdapter.suggest()` | `adapter/cap_pack_adapter.py` | 包匹配推荐 |
| `CapPackAdapter.apply()` | `adapter/cap_pack_adapter.py` | manifest 更新 |
| `BaseScanner` + 所有子类 | `scanner/` | L0-L4 扫描 |
| `FixRule` + 注册规则 | `fixer/` | 自动修复 |
| `CLI framework` | `cli/main.py` | 命令注册 |
| Schema 验证 | `schemas/cap-pack-v3.schema.json` | 输出格式验证 |
| `validate-pack.py` | `scripts/validate-pack.py` | 包完整性验证 |

### 需要新增的文件

| 文件 | 用途 | 模式 | 预计行数 |
|:-----|:------|:----:|:--------:|
| `converter/__init__.py` | 包初始化 | 🛠️ | 10 |
| `converter/scanner.py` | Phase ① 扫描 | 🛠️ | ~100 |
| `converter/llm_analyzer.py` | Phase ② LLM 分析 + prompt 模板 | 🧠 | ~150 |
| `converter/extractor.py` | Phase ③ 文件提取 + 结构生成 | 🛠️ | ~200 |
| `converter/manifest_builder.py` | cap-pack.yaml 生成/合并 | 🛠️ | ~150 |
| `converter/governor.py` | Phase ④ 治理集成 | 🛠️+🧠 | ~100 |
| `converter/reporter.py` | Phase ⑤ 报告输出 | 🛠️ | ~80 |
| `cli/convert_cmd.py` | convert CLI 命令实现 | 🛠️ | ~120 |
| `tests/test_converter.py` | 测试 | 🛠️ | ~200 |
| **总计** | | | **~1,110** |

---

## 五、分阶段实施

### Phase 0: 基础设施 (3 Stories, ~4h)

| Story | 内容 | 产出 |
|:------|:------|:-----|
| STORY-7-0-1 | converter 包结构 + scan 模块 | `converter/` 目录 + Phase ① 实现 |
| STORY-7-0-2 | convert CLI 架子（`--dry-run`） | `skill-governance convert` 命令 |
| STORY-7-0-3 | manifest_builder 模块 | cap-pack.yaml 生成/合并 |

**交付标准**：`cap-pack convert pdf-layout --dry-run` 输出分析报告（不走 LLM，只做脚本分析）

### Phase 1: 单 skill 转换 (4 Stories, ~6h)

| Story | 内容 | 产出 |
|:------|:------|:-----|
| STORY-7-1-1 | LLM analyzer + prompt 工程 | Phase ② 实现 |
| STORY-7-1-2 | Extract 流程（复制文件 + 创建结构） | Phase ③ 实现 |
| STORY-7-1-3 | LLM 经验提取 | EXPERIENCES/ 自动生成 |
| STORY-7-1-4 | end-to-end `convert <skill>` 流程 | 单个 skill 完整转换 |

**交付标准**：`cap-pack convert pdf-layout --pack doc-engine` 走完 ①→⑤ 全流程

### Phase 2: 批量转换 (4 Stories, ~8h)

| Story | 内容 | 产出 |
|:------|:------|:-----|
| STORY-7-2-1 | `convert --all` 批量扫描 + LLM 排队 | 批量处理 50+ skills |
| STORY-7-2-2 | `--auto` 自动分组（LLM 聚类） | 无 pack 的 skill 自动成组 |
| STORY-7-2-3 | `--group-by domain/toolset` 分组模式 | 用户指定分组策略 |
| STORY-7-2-4 | `--interactive` 逐个人工确认 | 低 confidence 暂停机制 |

**交付标准**：`cap-pack convert --all --auto` 一键处理全部未打包 skill

### Phase 3: 治理集成 + 增量同步 (3 Stories, ~6h)

| Story | 内容 | 产出 |
|:------|:------|:-----|
| STORY-7-3-1 | 转换后自动 `scan + fix` | Phase ④ 治理闭环 |
| STORY-7-3-2 | 增量检测（只处理未打包的 skill） | `--unpacked-only` 模式 |
| STORY-7-3-3 | 转换结果报告 + 验证 | Phase ⑤ 报告输出 |

**交付标准**：`cap-pack convert --unpacked-only` 增量同步 + 全自动治理

---

## 六、行业对比与差异化

| 对比维度 | SkillKit | Agent Skill Porter | **EPIC-007** |
|:---------|:--------:|:------------------:|:------------:|
| 核心方向 | 跨 Agent 安装/翻译 | 格式互转 | **Hermes → Cap-Pack 结构化转换** |
| 输入 | 任意 Agent 格式 | 任意 Agent 格式 | **Hermes 原生 skill 目录** |
| 输出 | 任意 Agent 格式 | 任意 Agent 格式 | **标准 Cap-Pack 目录** |
| 分组能力 | ❌ 无 | ❌ 无 | ✅ **LLM 智能分组** |
| 经验提取 | ❌ 无 | ❌ 无 | ✅ **Pitfall/决策树/对比 → EXPERIENCES/** |
| 治理闭环 | ❌ 无 | ❌ 无 | ✅ **自动 scan + fix 验证** |
| 批量转换 | ✅ `--all` | ✅ `--all` | ✅ `convert --all --auto` |
| LLM 使用方式 | 用户自定 | 用户自定 | **内置 prompt 模板** |

---

## 七、风险与缓解

| 风险 | 概率 | 影响 | 缓解 |
|:-----|:----:|:----:|:------|
| LLM 分类不准 | 🟡 中 | 🟡 中 | confidence < 60 自动进待确认池 |
| 大量 skill 批量 LLM 调用成本 | 🟡 中 | 🟢 低 | 批量合并 prompt + 首次全量后续增量 |
| SKILL.md 文件损坏 | 🟢 低 | 🔴 高 | 复制前校验 YAML frontmatter |
| 转换过程中断 | 🟢 低 | 🟡 中 | 每步幂等 + 转换日志 + 可恢复 |
| 与已有包 skill 重复 | 🟡 中 | 🟡 中 | suggest() 检测 + 转换前警告 |

---

## 八、验证标准

| 验证项 | 标准 |
|:-------|:------|
| 单 skill 转换成功率 | ≥ 95%（20 个 skill 测试集） |
| 分类准确率（LLM） | ≥ 80%（人工复核） |
| cap-pack.yaml schema 合规率 | 100% |
| 批量 50 skill 转换时间 | ≤ 5 min |
| 零手工 YAML 编辑 | 全部自动生成 |
| 转换后 `cap-pack scan` 通过 | L0+L1 零错误 |
