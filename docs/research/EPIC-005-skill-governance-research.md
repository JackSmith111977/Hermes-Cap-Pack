# 深度调研：Skill 治理引擎（EPIC-005 研究支撑文档）

> **背景**: 2026-05-16 深度循环学习产出，支撑 EPIC-005 的可行性论证
> **方法**: 三轮搜索（Tavily + Web Search），覆盖学术论文 + 开源项目 + 行业动态
> **来源**: 详见下方参考文献

## 一、行业生态全览

### 已有工具矩阵

| 工具 | 类型 | 语言 | 关注度 | 官网/仓库 |
|:-----|:-----|:-----|:------:|:----------|
| **skill-validator** | 质量验证 | Go | ⭐102 | agent-ecosystem/skill-validator |
| **skill-guard** | 质量门禁 | Python | ⭐3 | vaibhavtupe/skill-guard (v0.7.2) |
| **SkillCompass** | 质量评估 | Claude 插件 | — | skillsllm.com/skill/skillcompass |
| **skills-check** | 质量工具包 | — | — | skillscheck.ai |
| **skillctl** | 包管理+lint | — | — | skillctl.xyz |
| **skill-tree** | 树状路由 | Python | — | danielbrodie/skill-tree |
| **Skilldex** | 包管理+验证 | TypeScript | 学术 | Pandemonium-Research/Skilldex (arxiv 2604.16911) |
| **AgentVerus** | 安全认证 | — | — | agentverus.ai |
| **Cisco skill-scanner** | 安全扫描 | Python | 企业级 | cisco-ai-defense/skill-scanner |
| **skilltree (npm)** | 依赖管理 | Rust | — | imarios/skilltree |
| **CAPA** | 能力管理 | Go | — | infragate/capa |
| **Skilgen** | 自动生成 | — | — | skilgen/skilgen |

### 学术前沿

| 论文 | 会议/年份 | 核心贡献 |
|:-----|:----------|:---------|
| **Skilldex** (arxiv 2604.16911) | 2026-04 | 编译器式格式合规评分+skillset抽象+三作用域+MCP |
| **SkillRouter** (arxiv 2603.22455) | 2026-03 | 1.2B 全文本 Skill 路由，74% Hit@1 在 80K 规模 |
| **SkillOrchestra** (arxiv 2602.19672) | 2026-02 | Skill-aware agent routing，技能手册+能力感知路由 |

## 二、差距分析详情

### 7 维需求 vs 现有覆盖

| 需求 | 最佳已有工具 | 差距描述 | 差距等级 |
|:-----|:------------|:---------|:--------:|
| 原子性扫描 | skill-guard (validate) | 检查结构完整性但不判断原子性 | 🟡 部分 |
| 树状结构 | skill-tree | 做聚类但不关联质量和合规 | 🟡 部分 |
| 工作流编排 | **无** | 完全空白 | 🔴 空白 |
| Cap-Pack 合规 | **无** | cap-pack v2 schema 已有但无检测工具 | 🔴 空白 |
| 新增检测 | skill-guard (pre-commit) | event 触发而非持续 watcher | 🟡 部分 |
| 自动质量测试 | skill-guard (test) | on-demand 非自动触发 | 🟡 部分 |
| 自动适配改造 | **无** | 完全空白 | 🔴 空白 |

### 独特价值

> **其他工具**: "发现 Skill 不符合标准，报告问题"
> **本工具**: "发现 Skill 不符合 Cap-Pack 标准，报告问题，自动生成适配方案（dry-run），确认后执行"

## 三、技术可行性验证

### Hermes 集成点已验证

| 集成点 | 验证方式 | 结论 |
|:-------|:---------|:-----|
| pre_flight gate | v2.0 已支持多门禁扩展 | ✅ 直接可用 |
| cron 定时任务 | cronjob 系统已运行多次 | ✅ 直接可用 |
| SRA 质量注入 | sqs-sync.py 已验证 SQS→SRA 通道 | ✅ 可直接扩展 |
| skill-creator 门禁 | SQS 门禁已集成 | ✅ 可直接扩展 |
| cap-pack schema | v2 schema 已有且通过验证 | ✅ 可用作合规标准 |

### 适配层可行性

| 目标 | 方法 | 难度 |
|:-----|:------|:----:|
| Hermes | pre_flight + cron + file system | 🟢 低 |
| OpenCode | Plugin hooks + skill 目录扫描 | 🟢 低 |
| OpenClaw | Plugin system + disable-model-invocation 机制 | 🟢 低 |
| Claude Code | Plugin + CLAUDE.md + file ops | 🟡 中 |
| MCP Server | stdio MCP server 暴露治理工具 | 🟢 低（Skilldex 已验证此模式） |

## 四、参考文献

- [skill-validator](https://github.com/agent-ecosystem/skill-validator) — Go CLI 验证工具，102 stars
- [skill-guard](https://github.com/vaibhavtupe/skill-guard) — Python 质量门禁，3 stars
- [SkillCompass](https://skillsllm.com/skill/skillcompass) — Claude 插件式 Skill 质量评估
- [skills-check](https://skillscheck.ai/) — 10 命令质量工具包
- [skill-tree](https://github.com/danielbrodie/skill-tree) — 双跳路由架构，跨平台
- [Skilldex (arxiv 2604.16911)](https://arxiv.org/abs/2604.16911) — 包管理+格式合规评分
- [SkillRouter (arxiv 2603.22455)](https://arxiv.org/abs/2603.22455) — 全文本 Skill 路由
- [SkillOrchestra (arxiv 2602.19672)](https://arxiv.org/abs/2602.19672) — Skill-aware agent routing
- [AgentVerus](https://agentverus.ai/) — Skill 安全认证
- [Cisco skill-scanner](https://github.com/cisco-ai-defense/skill-scanner) — 企业级安全扫描
- [MCP Registry](https://registry.modelcontextprotocol.io/) — MCP 官方注册中心
- [skillctl](https://skillctl.xyz/) — 包管理器+lint
