# 📋 SPEC-1-2: 模块生命周期管理

> **状态**: `approved` · **优先级**: P1 · **创建**: 2026-05-12 · **更新**: 2026-05-12
> **SDD 流程**: `CLARIFY ✅ → RESEARCH ✅ → CREATE ✅ → QA_GATE ✅ → REVIEW ✅`
> **关联 Epic**: EPIC-001-feasibility.md
> **审查人**: 主人

---

## 〇、需求澄清记录 (CLARIFY)

### 要解决的核心问题

> 能力包从创建到废弃的完整生命周期如何管理？版本号、依赖关系、CRUD 操作如何规范化？

### 确认的范围

| 包含 | 不包含 |
|:-----|:--------|
| ✅ 模块生命周期的六个阶段模型 | ❌ 注册中心后端服务 |
| ✅ 版本号规范（语义版本） | ❌ 自动化依赖解析引擎 |
| ✅ 依赖关系声明与管理 | ❌ 模块市场/商店 |
| ✅ CRUD 操作定义（安装/查看/更新/卸载） | ❌ 分布式存储方案 |

---

## 一、RESEARCH — 深度调研

### 1.1 业界参考

| 来源 | 要点 | 可借鉴 |
|:-----|:------|:-------|
| **Hermes Curator** | Agent 创建技能的生命周期管理 / 自动归档 | 模块自动废弃机制 |
| **NPM (Node.js)** | 语义版本 + 依赖解析树 + 锁文件 | 版本号规范 + semver 范围 |
| **MCP Registry** | Server 发现和认证 | 注册中心设计参考 |
| **Homebrew** | 本地 Formula + 远程 Tap | 模块源的多级发现 |

### 1.2 关键设计原则

1. **渐进式成熟** — 模块从草稿到稳定再到归档，每步有明确的转换条件
2. **语义版本优先** — 版本号反映兼容性变化，让依赖解析可预测
3. **CRUD 完备** — 每个操作有标准流程和回滚路径
4. **依赖显式声明** — 模块间的依赖关系在 cap-pack.yaml 中声明，运行时检查

---

## 二、模块生命周期状态机

### 六阶段模型

```text
         ┌─────────────────────────────────┐
         │  DRAFT                          │
         │  草稿阶段                        │
         │  初步定义模块边界与内容            │
         └─────────┬───────────────────────┘
                   │ submit (验证完整性)
                   ▼
         ┌─────────────────────────────────┐
         │  ACTIVE                         │
         │  活跃阶段                        │
         │  可被安装和使用                    │
         └─────────┬───────────────────────┘
                   │ updates / patches
                   ▼
         ┌─────────────────────────────────┐
         │  MATURING                       │
         │  成熟阶段                        │
         │  迭代优化 + 新增经验               │
         └─────────┬───────────────────────┘
                   │ stabilize
                   ▼
         ┌─────────────────────────────────┐
         │  STABLE                         │
         │  稳定阶段                        │
         │  经过验证，推荐使用                │
         └─────────┬───────────────────────┘
                   │ deprecate
                   ▼
         ┌─────────────────────────────────┐
         │  DEPRECATED                     │
         │  废弃阶段                        │
         │  有替代模块，不再推荐新装           │
         └─────────┬───────────────────────┘
                   │ archive
                   ▼
         ┌─────────────────────────────────┐
         │  ARCHIVED                       │
         │  归档阶段                        │
         │  仅保留文档，不可安装              │
         └─────────────────────────────────┘
```

### 阶段转换条件

| 转换 | 前置条件 | 操作 | 副作用 |
|:-----|:---------|:-----|:-------|
| DRAFT → ACTIVE | 模块清单完整、至少 1 个技能 | `cap-pack review` | 加入可用索引 |
| ACTIVE → MATURING | ≥ 3 次安装反馈 / ≥ 1 次更新 | 自动判断 | 允许 breaking change |
| MATURING → STABLE | ≥ 10 次安装、≤ 2 个已知 Issue | `cap-pack stabilize` | 锁定 API |
| STABLE → DEPRECATED | 有替代模块 | `cap-pack deprecate` | 安装时提示迁移 |
| DEPRECATED → ARCHIVED | 已废弃 ≥ 90 天 | 自动归档 | 移出索引 |

---

## 三、版本号规范（语义版本）

### 格式

```
MAJOR.MINOR.PATCH
```

| 层级 | 何时增加 | 示例 |
|:-----|:---------|:------|
| **MAJOR** | 不兼容的格式变更、技能移除、MCP 配置结构变化 | `1.0.0` → `2.0.0` |
| **MINOR** | 新增技能、新增经验、新增 MCP 工具 | `1.0.0` → `1.1.0` |
| **PATCH** | 经验修正、技能步骤优化、文档改进 | `1.0.0` → `1.0.1` |

### 版本约束声明

```yaml
dependencies:
  - name: mcp-hub
    version: ">= 1.0.0, < 2.0.0"
    optional: false
  - name: basic-tools
    version: "~1.2"
    optional: true
```

### 预发布标签

```yaml
version: 1.0.0-alpha.1
version: 1.0.0-beta.2
version: 1.0.0-rc.1
```

---

## 四、CRUD 操作定义

### 安装 (Create)

```bash
cap-pack install ./packs/doc-engine.yaml --agent hermes
cap-pack install doc-engine --version ">= 1.0.0"
```

**安装流程**: 解析 YAML → 检查依赖 → 写入技能目录 → 注册 MCP → 执行 `on_activate` → 写入安装清单

### 查看 (Read)

```bash
cap-pack list                          # 列出所有已安装模块
cap-pack show doc-engine               # 查看模块详情
cap-pack inspect doc-engine SKILLS/    # 查看模块文件
```

### 更新 (Update)

```bash
cap-pack check-updates                 # 检查可用更新
cap-pack update doc-engine --to 1.2.0  # 更新特定模块
cap-pack upgrade                       # 全部升级
```

**更新流程**: 备份 → diff → MAJOR 需确认 → 技能/经验/MCP 顺序执行 → `on_activate` → 日志

### 卸载 (Delete)

```bash
cap-pack remove doc-engine
cap-pack remove doc-engine --keep-config
cap-pack remove doc-engine --force
```

**卸载流程**: 依赖检查 → `on_deactivate` → 移除文件 → 移除 MCP → 备份保留 7 天

---

## 五、依赖管理

### 依赖类型

| 类型 | 说明 | 示例 |
|:-----|:-----|:------|
| **模块依赖** | 依赖另一个能力包 | `mcp-hub` → `doc-engine` |
| **工具依赖** | 依赖 Agent 的内置工具 | `web_search`, `terminal` |
| **MCP 依赖** | 依赖外部 MCP 服务 | OCR 服务、翻译 API |
| **环境依赖** | 依赖运行时环境 | Python ≥ 3.10, 系统字体 |

### 版本冲突解决

| 场景 | 策略 | 用户提示 |
|:-----|:-----|:---------|
| A 要 v1.x，B 要 v2.x | 不可兼容 | ❌ 需人工介入 |
| A 要 ≥1.0，已装 1.2 | 自动满足 | ✅ 静默通过 |
| A 要 =1.0，已装 1.1 | 不满足 | ⚠️ 提示可降级或升级 |

---

## 六、模块存储与发现

### 本地存储结构

```text
~/.hermes/cap-packs/
├── installed.json         # 已安装模块清单
├── registry.json          # 已知模块源
├── backups/               # 更新前的自动备份
└── packs/                 # 缓存的模块定义
    └── doc-engine/
        ├── cap-pack.yaml
        ├── SKILLS/
        ├── EXPERIENCES/
        └── MCP/
```

### 发现方式

| 方式 | 范围 | 命令 |
|:-----|:-----|:------|
| 本地文件 | 本机 | `cap-pack list --local` |
| 本地注册表 | `registry.json` 中的源 | `cap-pack search pdf` |
| 远程注册中心 | 互联网 | `cap-pack search --remote` |
| GitHub 仓库 | 指定仓库 | `cap-pack install github:user/repo` |
| Hermes Skills Hub | 已有技能生态 | `cap-pack import-from-skills` |

---

## 七、验收标准 (Acceptance Criteria)

- [ ] 六阶段状态机经主人确认
- [ ] 每个阶段转换条件可执行（可脚本化）
- [ ] 版本号规范覆盖全部 3 种变化类型
- [ ] CRUD 操作流程完整，含回滚路径
- [ ] 依赖冲突的 3 种场景都有处理策略
- [ ] 存储结构可实际部署到 `~/.hermes/cap-packs/`

---

## 八、开放问题

- [ ] Q1: MATURING → STABLE 是否需要人工审批？
- [ ] Q2: 依赖冲突时，是否允许自动降级某个模块？
- [ ] Q3: 多个模块共享同一个 MCP Server，卸载一个模块是否影响另一个？

---

## 九、QA_GATE 检查清单

- [x] Spec ID 格式正确（SPEC-1-2）
- [x] 关联 Epic 引用完整
- [x] CLARIFY 章节记录了需求澄清
- [x] RESEARCH 章节有业界参考
- [x] 状态机有明确的阶段和转换条件
- [x] CRUD 操作有完整流程
- [x] 依赖管理覆盖所有类型
- [x] AC 每项可独立验证
- [x] 开放问题已记录
- [x] 主人 REVIEW 批准
