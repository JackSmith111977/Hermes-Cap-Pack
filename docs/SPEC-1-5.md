# 🔧 SPEC-1-5: 能力包安装引擎

> **状态**: `clarify` · **优先级**: P0 · **创建**: 2026-05-14
> **SDD 流程**: `CLARIFY ⬜ → RESEARCH ⬜ → CREATE ⬜ → QA_GATE ⬜ → REVIEW ⬜`
> **关联 Epic**: EPIC-001-feasibility.md
> **审查人**: 主人

---

## 〇、需求澄清 (CLARIFY)

### 用户故事

> **As a** 系统维护者（主人）
> **I want** 能力包安装引擎能完整利用 cap-pack.yaml 的 install 配置
> **So that** 安装一个包 = 一步到位：skill 复制 + 脚本链接 + MCP 注入 + 验证

### 确认的需求范围

| 维度 | 包含 | 不包含 |
|:-----|:------|:-------|
| **安装引擎** | HermesAdapter 支持 install.scripts/skills/references/post_install | 非 Agent 平台部署 |
| **集成测试** | learning-workflow 包端到端安装验证 | 全部 18 模块的测试 |
| **验证门禁** | 安装后自动验证 skill 可加载、脚本可执行 | 运行时性能监控 |
| **依赖管理** | depends_on 检查并提示缺失依赖 | 自动安装依赖包 |
| **多 Agent** | hermes + opencode 双适配器 | Codex/Claude 适配器 |

### out_of_scope

- 在线包注册中心（仍为本地目录安装）
- 依赖包的自动递归安装（仅检测并提示）
- Agent 运行时热加载（需重启）

---

## 一、架构概览

### 当前流程（有缺口）

```
cap-pack.yaml  ──→  PackParser  ──→  CapPack 对象
                                         │
                    HermesAdapter.install(pack)
                         │
                    ┌────┴────┐
                    ↓         ↓
              SKILLS/ 复制  MCP 注入
              ✗ 脚本不链接  ✓ config.yaml
              ✗ 依赖不检查
              ✗ post_install 不执行
```

### 目标流程

```
cap-pack.yaml  ──→  PackParser  ──→  CapPack 对象
                                         │
                    HermesAdapter.install(pack, options)
                         │
               ┌────────┼────────┐
               ↓        ↓        ↓
         ① Skill 复制  ② 脚本链接  ③ MCP 注入
               │        │        │
         ④ 引用复制 ←──┘        │
               │                 │
         ⑤ post_install ─────────┘
               │
         ⑥ 验证门禁（skill 存在、脚本可执行、config 完整）
               │
         ⑦ 追踪记录 → installed_packs.json
```

---

## 二、验收标准 (AC)

### AC-1: install 配置完整消费
- [ ] `install.scripts` 中的文件复制到 `~/.hermes/scripts/`
- [ ] `install.skills` 中的 skill 文件复制到 `~/.hermes/skills/{id}/`
- [ ] `install.references` 中的引用文件复制到目标目录
- [ ] `install.post_install` 中的命令依次执行
- [ ] 所有路径自动创建父目录

### AC-2: 依赖检查
- [ ] `depends_on` 中声明的依赖包已安装（检查 installed_packs.json）
- [ ] 缺失依赖时输出清晰提示，不阻塞安装
- [ ] 依赖检查可通过 `--skip-deps` 跳过

### AC-3: 端到端集成测试
- [ ] `learning-workflow` 包可通过 `cap-pack install` 实际安装到本地 Hermes
- [ ] 安装后 skill 在 `skill_view(name='learning-workflow')` 中可加载
- [ ] 安装后脚本在 `~/.hermes/scripts/` 下可执行
- [ ] `validate-pack.py` 在安装后验证通过
- [ ] 卸载后恢复到安装前状态（快照回滚验证）

### AC-4: 验证门禁
- [ ] 安装后自动执行 `chmod +x` 所有脚本
- [ ] 自动验证 skill YAML frontmatter 完整性
- [ ] 自动验证脚本文件可执行（`--help` 或 `--version`）
- [ ] 失败时自动回滚

### AC-5: 多 Agent 适配
- [ ] `--target hermes` 安装到 Hermes
- [ ] `--target opencode` 安装到 OpenCode
- [ ] `--target auto` 自动检测可用环境

---

## 三、初步 Story 分解

| Story | 标题 | AC | 预估 |
|:------|:-----|:---|:----:|
| **STORY-1-5-1** | HermesAdapter install 配置完整消费 | AC-1 | 1 轮 |
| **STORY-1-5-2** | 依赖检查与验证门禁 | AC-2, AC-4 | 1 轮 |
| **STORY-1-5-3** | 端到端集成测试（learning-workflow 包） | AC-3 | 1 轮 |
| **STORY-1-5-4** | 多 Agent 安装与自动检测 | AC-5 | 1 轮 |
| **STORY-1-5-5** | 卸载增强与快照回滚测试 | AC-3（卸载部分） | 1 轮 |

---

## 四、实施顺序

```
Phase 1: 核心安装引擎
  STORY-1-5-1 → 让 HermesAdapter 使用 cap-pack.yaml 的 install 配置
  STORY-1-5-2 → 依赖检查 + 安装后验证门禁
  
Phase 2: 集成验证
  STORY-1-5-3 → learning-workflow 包端到端安装测试
  
Phase 3: 多 Agent + 卸载
  STORY-1-5-4 → OpenCode + auto 检测
  STORY-1-5-5 → 卸载增强
```
