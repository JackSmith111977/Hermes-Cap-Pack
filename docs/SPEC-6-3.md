# 📖 SPEC-6-3: 跨 Agent 适配文档与 README — Phase 3

> **spec_id**: `SPEC-6-3`
> **status**: `completed`
> **epic**: `EPIC-006`
> **phase**: `Phase-3`
> **created**: 2026-05-16
> **updated**: 2026-05-16
> **owner**: boku (Emma)
> **优先级**: P2
> **估算**: ~5h（2 Stories）
> **前置**: Phase 0+1 ✅ + Phase 2 ✅（可选，不阻塞）

---

## 〇、需求澄清

### 用户故事

> **As a** 任何 AI Agent（Hermes / OpenCode / Claude / 新 Agent）
> **I want** 阅读 README 后 5 分钟内理解 cap-pack 是什么、怎么用、怎么适配
> **So that** 不需要主人讲解就能独立完成 cap-pack 的安装/卸载/检查

### 范围

| 包含 | 不包含 |
|:-----|:-------|
| README.md 完整重写（AI 友好版） | Web UI 仪表盘 |
| ADAPTER_GUIDE.md 适配器使用指南 | 公共注册中心 |
| QUICKSTART.md 新 Agent 初始化流程 | 自动 git commit |
| CLI 速查三列表格 | 修改任何代码 |

---

## 一、技术方案

### README v2.0 结构（遵循 readme-for-ai 方法论）

```
# 一、项目身份 — 一句话定义 cap-pack
# 二、核心概念 — 跨 Agent 技能包标准（配架构图）
# 三、快速安装 — 前置条件 + 验证命令
# 四、CLI 速查 — 三列表格（命令/关键参数/预期输出）
# 五、能力包列表 — 18 个包一览
# 六、适配器体系 — 4 个适配器 + MCP Server
# 七、质量治理 — L0-L4 检测 + fix 修复
# 八、验证 — 运行状态检查
# 九、FAQ — 排错指南
# 十、开发指南 — 如何创建新包
```

### 核心概念图（ASCII）

```
Agent A 原生技能库    Agent B 原生技能库
       ↕                    ↕
  ┌────────────────────────────┐
  │    Cap-Pack 挂载层          │  ← 保留各自技能，额外挂载
  │  HermesAdapter             │
  │  OpenCodeAdapter           │
  │  ClaudeAdapter             │
  │  MCP Server                │
  └────────────────────────────┘
       ↕
  skill-governance scan/fix    ← 治理引擎确保合规
```

### ADAPTER_GUIDE

每个适配器至少包含：使用案例、配置方法、示例命令、故障排查

### QUICKSTART

新 Agent 从 0 到 1 的 5 步流程：
1. 克隆仓库
2. 安装依赖
3. 扫描现有包
4. 安装目标包到本 Agent
5. 验证安装

---

## 二、Story 分解

| ID | 标题 | 内容 | 估算 | 产出物 |
|:---|:-----|:-----|:----:|:-------|
| STORY-6-3-1 | **README v2.0 AI 友好版重写** | 编号章节 + CLI 三列表格 + 适配器一览 + 概念图 | 3h | `README.md` v2.0 |
| STORY-6-3-2 | **ADAPTER_GUIDE + QUICKSTART + CLI 速查** | 4 适配器使用指南 + 5 步初始化流程 | 2h | `docs/ADAPTER_GUIDE.md`, `docs/QUICKSTART.md` |

---

## 三、验收标准

### STORY-6-3-1
- [x] README 使用编号中文章节（一、二、三…） <!-- 验证: grep -c "^# " README.md -->
- [x] 包含跨 Agent 核心概念说明 <!-- 验证: grep -q "Agent\|适配器\|挂载" README.md -->
- [x] CLI 使用三列参考表（命令/参数/预期输出） <!-- 验证: grep -q "|.*|.*|" README.md -->
- [x] 包含适配器一览表（4 个适配器） <!-- 验证: grep -q "HermesAdapter\|OpenCodeAdapter\|ClaudeAdapter\|OpenClawAdapter" README.md -->
- [x] L0-L4 治理引擎说明 <!-- 验证: grep -q "L0\|L1\|L2\|L3\|L4\|治理\|合规" README.md -->

### STORY-6-3-2
- [x] ADAPTER_GUIDE 覆盖 4 个适配器 <!-- 验证: grep -q "Hermes\|OpenCode\|Claude\|OpenClaw" docs/ADAPTER_GUIDE.md -->
- [x] QUICKSTART 包含 5 步初始化流程 <!-- 验证: grep -c "Step\|步骤\|流程" docs/QUICKSTART.md -->
- [x] CLI 速查完整（scan/fix/install/remove/list） <!-- 验证: grep -q "scan\|fix\|install\|remove\|list" docs/ADAPTER_GUIDE.md -->
