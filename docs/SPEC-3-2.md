# 🎯 SPEC-3-2: 能力包管理器增强 — 升级/技能级操作/搜索/状态

> **状态**: `implemented` · **优先级**: P0 · **创建**: 2026-05-14 · **更新**: 2026-05-14
> **SDD 流程**: `CLARIFY ✅ → RESEARCH ✅ → CREATE ✅ → QA_GATE ✅ → REVIEW ✅`
> **关联 Epic**: EPIC-003-module-extraction.md
> **基础 CLI**: `scripts/cli/main.py` + `scripts/cli/commands.py` + `scripts/adapters/hermes.py`

---

## 〇、需求澄清 (CLARIFY)

### 用户故事

> **As a** 主人
> **I want** 能力包能像 apt/brew 一样通过命令快速安装、升级、卸载、调整具体技能
> **So that** 不需要手动操作文件就能管理能力包的完整生命周期

### 当前状态

现有 CLI 只覆盖了基础 CRUD：

```
✅ cap-pack install   <dir>      # 安装（已有）
✅ cap-pack remove    <name>     # 卸载（已有）
✅ cap-pack verify    <name>     # 验证（已有）
✅ cap-pack list                 # 列出已安装（已有）
✅ cap-pack inspect   <dir>      # 检查包内容（已有）
```

### 需要新增

```
🆕 cap-pack upgrade   <name>              # 升级已安装的包
🆕 cap-pack search    <term>              # 搜索可用能力包
🆕 cap-pack status                        # 显示系统全局状态
🆕 cap-pack skill add    <pack> <source>  # 向包内新增 skill
🆕 cap-pack skill remove <pack> <id>      # 从包内移除 skill
🆕 cap-pack skill list  <pack>            # 列出包内技能
🆕 cap-pack skill update <pack> <id> [src] # 更新包内特定 skill
```

---

## 一、新增命令设计

### 1.1 `cap-pack upgrade <name>`

**用途**: 将已安装的能力包升级到最新版本

```
流程:
  ① 从 installed_packs.json 读取当前版本
  ② 扫描 packs/<name>/ 获取新版本
  ③ 比较版本号
  ④ 备份当前已安装的 skill
  ⑤ 运行 install（更新文件）
  ⑥ 验证安装完整性
  ⑦ 更新 installed_packs.json

命令:
  cap-pack upgrade doc-engine
  cap-pack upgrade doc-engine --dry-run   # 仅预览
  cap-pack upgrade --all                  # 全部升级

输出:
  📦 升级 doc-engine: v1.0.0 → v2.0.0
  ✅ 升级完成！3 个 skill 已更新
```

**AC**: 版本比较正确、备份还原、升级后验证通过。

### 1.2 `cap-pack skill add <pack> <source>`

**用途**: 向现有能力包中添加一个 Hermes skill

```
流程:
  ① 读取 packs/<pack>/cap-pack.yaml
  ② 验证 source 路径的 skill 存在
  ③ 复制 skill 到 SKILLS/<id>/SKILL.md
  ④ 更新 cap-pack.yaml 的 skills 列表
  ⑤ 更新版本号 (minor bump)
  ⑥ 重新验证

命令:
  cap-pack skill add doc-engine ~/.hermes/skills/design/web-ui-ux-design

输出:
  ✅ web-ui-ux-design 已添加到 doc-engine (v2.0.0 → v2.1.0)
```

### 1.3 `cap-pack skill remove <pack> <id>`

**用途**: 从能力包中移除特定 skill

```
流程:
  ① 读取 cap-pack.yaml
  ② 确认 skill 存在
  ③ 备份被删除的 skill
  ④ 从 YAML 中移除条目
  ⑤ 删除 SKILLS/<id>/ 目录
  ⑥ 更新版本号 (minor bump)
  ⑦ 重新验证

命令:
  cap-pack skill remove doc-engine vision-qc-patterns
  cap-pack skill remove doc-engine vision-qc-patterns --dry-run

输出:
  🗑️  vision-qc-patterns 已从 doc-engine 移除 (v2.0.0 → v2.0.1)
  ♻️  备份至 backups/doc-engine/vision-qc-patterns/
```

### 1.4 `cap-pack skill list <pack>`

**用途**: 列出能力包内的所有技能详情

```
命令:
  cap-pack skill list developer-workflow

输出:
  📦 developer-workflow (v1.0.0) — 16 skills
  ─────────────────────────────────────────
  📄 tdd                 TDD 开发流程
  📄 debugging           系统化调试
  📄 plan                实施计划
  ...
```

### 1.5 `cap-pack skill update <pack> <id> [source]`

**用途**: 更新包内特定 skill 的内容

```
无 source 参数 → 从 Hermes 重新同步
有 source 参数 → 从指定路径复制

命令:
  cap-pack skill update doc-engine pdf-layout
  cap-pack skill update doc-engine pdf-layout ~/new-version/SKILL.md
```

### 1.6 `cap-pack search <term>`

**用途**: 搜索 packs/ 目录中可用的能力包

```
命令:
  cap-pack search doc
  cap-pack search --installed   # 只搜已安装的
  cap-pack search --remote      # （预留）从注册中心搜索

输出:
  找到 3 个匹配的能力包:
  📦 doc-engine          📄 文档生成 (13 skills)  ✅ 已安装
  📦 devops-monitor      🔧 运维监控 (9 skills)   ⬜ 可用
  📦 mcp-integration     🔌 MCP 集成 (3 skills)    ⬜ 可用
```

### 1.7 `cap-pack status`

**用途**: 全局状态概览

```
命令:
  cap-pack status

输出:
  ╔════════════════════════════════════════════════╗
  ║   Cap Pack 系统状态                             ║
  ╚════════════════════════════════════════════════╝

  已提取: 3/19 模块
  已安装: 2 个包到 Hermes

  已安装:
  ✅ doc-engine          v2.0.0  13 skills
  ✅ learning-workflow   v5.5.0   1 skill

  可用:
  📦 developer-workflow  (packs/)  16 skills  ⬜ 待安装
  📦 agent-orchestration (packs/)   8 skills  ⬜ 待安装
  ...

  💡 SQS 质量均分: 67.9/70
```

---

## 二、影响范围

| 文件 | 变更 | 
|:-----|:------|
| `scripts/cli/main.py` | 新增 subcommand: upgrade, search, status, skill |
| `scripts/cli/commands.py` | 新增 7 个命令实现 |
| `scripts/adapters/hermes.py` | 新增 upgrade() 方法 |
| `scripts/uca/protocol.py` | 可能需扩展 CapPack 类 |
| `packs/<name>/cap-pack.yaml` | skill add/remove 会修改 |
| `~/.hermes/data/installed_packs.json` | upgrade 会更新 |

---

## 三、验收标准

| AC ID | 描述 | 验证方式 | 优先级 |
|:------|:-----|:---------|:------:|
| AC-01 | `cap-pack upgrade <name>` 成功升级包版本 | 升级后版本号增加 | P0 |
| AC-02 | `cap-pack upgrade --dry-run` 不实际修改 | 升级后回滚验证 | P0 |
| AC-03 | `cap-pack skill add` 成功添加 skill | `skill list` 显示新 skill | P0 |
| AC-04 | `cap-pack skill remove` 成功移除 skill | `skill list` 不含该 skill | P0 |
| AC-05 | `cap-pack skill list` 正确显示包内容 | 输出与 cap-pack.yaml 一致 | P0 |
| AC-06 | `cap-pack search` 能找到匹配包 | 搜索关键词返回正确结果 | P1 |
| AC-07 | `cap-pack status` 显示全局状态 | 输出包含已安装/可用/质量 | P1 |
| AC-08 | 101 测试仍全绿 | `pytest scripts/tests/ -q` | P0 |
