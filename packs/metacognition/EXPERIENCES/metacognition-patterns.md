---
type: best-practice
skill_ref: "metacognition patterns"
keywords: [metacognition-patterns]
created: 2026-05-14
---

# Metacognition Patterns — Skill Lifecycle & Capability Mapping Best Practices

> 元认知系统经验沉淀。涵盖 Skill 生命周期管理、能力认知审计、设计哲学迁移等核心模式。

---

## 1. Skill 生命周期管理

### 核心模式

```
CREATE → QA GATE → DEPLOY → MAINTAIN → AUDIT → DEPRECATE
```

每个阶段的关键动作：

| 阶段 | 操作 | 工具/参考 |
|:-----|:------|:-----------|
| **创建 (CREATE)** | S1-S9 逐阶段走；或快速通道 | `skill-creator` |
| **质量门禁 (QA GATE)** | SQS >= 50, 依赖无断裂, YAML frontmatter 完整 | `skill-quality-score.py`, `dependency-scan.py` |
| **部署 (DEPLOY)** | `skill_manage(action='create')` | pre_flight v2.0 |
| **维护 (MAINTAIN)** | 版本更新 → 依赖同步 → 质量重检 | 按 semver 更新版本号 |
| **审计 (AUDIT)** | SQS 定期扫描 + 新鲜度检查 | `skill-lifecycle-audit.py` |
| **退役 (DEPRECATE)** | 影响分析 → 通知引用者 → 标记退役 → 30天后归档 | `skill-lifecycle-audit.py` |

### 关键教训

1. **永远不要绕过 skill-creator 直接调用 skill_manage** — 这是 P0 违规，会导致引用链断裂和质量失控。
2. **修改/删除前必须运行 `dependency-scan.py`** — 检查哪些技能引用了目标技能，防止连锁失败。
3. **SQS 质量分 < 50 时禁止部署** — 不合格的技能会污染整体能力生态。
4. **快速更新通道仅适用于错别字/描述优化** — 任何逻辑变更必须走完整 9 阶段流程。
5. **pre_flight v2.0 自动检测技能操作** — 但仍需手动 `skill_view(name='skill-creator')` 加载完整流程。

### 版本管理规范

- **主版本 (X.0.0)**: 破坏性变更（改变了 Skill 类型或核心逻辑）
- **次版本 (0.X.0)**: 增加新功能、新用例或新的 References
- **修订号 (0.0.X)**: 修复错别字、优化指令清晰度、瘦身

---

## 2. 能力认知与审计 (Capability Mapping)

### 核心模式：Inversion（从结果反推执行步骤）

能力审计不是罗列「有什么工具」，而是从「能解决什么问题」反推能力边界。

### 正确的能力审计流程

```bash
# Step 1: 穷举所有技能
find ~/.hermes/skills -name "SKILL.md" -maxdepth 3 | wc -l

# Step 2: 逐项读取 name + description + tags
for f in $(find ~/.hermes/skills -name "SKILL.md" -maxdepth 3); do
  dir=$(dirname "$f")
  cat "$f" | head -5 | grep -E "^name:|^description:|tags:" | sed 's/name: //'
  echo "  └─ $dir"
done

# Step 3: 按领域归类（不预设分类，让技能自己告诉你它属于哪）
# Step 4: 检查隐性知识体系（experiences/ 和 brain/）
```

### 常见陷阱

| 陷阱 | 后果 | 预防 |
|:-----|:------|:------|
| **仅依赖 `self-capabilities-map` 的领域列表** | 遗漏整个能力类别 | 必须同时穷举扫描 + 手动归类 |
| **按「工具/平台」而非「领域」分类** | 分类碎片化 | 按「解决什么问题」分类 |
| **忽略隐性知识体系** | 看不到 experiences/ brain/ 等非技能知识 | 审计时检查所有知识目录 |
| **只计已安装技能** | 声称某模块完整但技能未安装 | 审计时注明「已安装/可用」状态 |

### 架构三难抉择决策树

当需要决定一个组件属于哪种扩展机制时：

```
是常驻服务，需要 7x24 运行？
  ├─ ✅ → 运行时（Runtime）— 独立守护进程，HTTP API
  └─ ❌ → Agent 按需使用？
      ├─ 是原子操作（一个函数/一个命令）？
      │  ├─ ✅ → 工具（Tool）— Hermes 内置
      │  └─ ❌ → 技能（Skill）— SKILL.md 知识单元
```

一句话原则：**技能告诉 Agent "怎么做"，运行时告诉 Agent "去哪问"，工具替 Agent "直接做"。**

---

## 3. 设计哲学迁移模式

当需要从优秀项目中学习设计模式时，走 6 步法：

1. **全量文件扫描** — 了解目标项目结构（文件数量和结构比内容更重要）
2. **关键文件深度提取** — README.md, SKILL.md, check-deps 优先级最高
3. **设计哲学提炼** — 问 5 个元问题，输出 6~8 条设计哲学
4. **对比分析** — 差距表格，按 🔴→🟡→🟢 排序
5. **实施改进** — 独立分支，逐项 commit
6. **提交与验证** — 推送到远程

**核心原则**：复制哲学而非复制代码。理解「为什么好」而不是「做了什么」。

---

## 4. Skill → PyPI 独立打包决策树

```
组件是 Hermes 特有的吗？
├─ 是 → ❌ 不适合开源，保持为 skill
└─ 否 → 有独立价值吗？
    ├─ 否 → 保持为 skill
    └─ 是 → 能脱离 Hermes 环境运行吗？
        ├─ 否 → 保持为 skill
        └─ 是 → ✅ 适合独立打包！
```

---

## 5. 运维最佳实践摘要

| 场景 | 推荐实践 |
|:-----|:---------|
| **Hermes 升级** | 国内服务器用 GitHub Release tarball + rsync 替代 git pull |
| **升级后恢复** | 文件存在 ≠ 代码集成 — 必须验证 import 链路 |
| **Gateway 重启** | 优先用 `hermes gateway restart`（优雅重启）而非 `systemctl restart` |
| **Memory 溢出** | 优先替换旧条目，其次保存为 Markdown 文件并记录路径 |
| **SRA 管理** | 优先用内置 `sra upgrade` / `sra uninstall` 命令 |
| **Vision 配置** | 国内服务器用 OpenRouter + Qwen3-VL 替代 Gemini |
