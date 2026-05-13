# 🔗 SPEC-2-3: CAP Pack SRA 适配方案

> **状态**: `draft` · **优先级**: P1 · **创建**: 2026-05-13 · **更新**: 2026-05-13
> **SDD 流程**: `CLARIFY ✅ → RESEARCH ✅ → CREATE ⬜ → QA_GATE ⬜ → REVIEW ⬜`
> **关联 Epic**: EPIC-002-tree-health.md
> **审查人**: 主人
> **外部依赖**: SRA v1.4.0 `~/projects/sra/` (独立 PyPI 项目 `sra-agent`)

---

## 〇、需求澄清 (CLARIFY)

### 要解决的问题

> CAP Pack 解决了技能的「**静态结构管理**」(分类/评分/生命周期)，SRA 解决了技能的「**运行时发现**」(语义匹配/上下文注入)。两者目前相互独立——CAP Pack 不知道 SRA 推荐了什么，SRA 不知道 CAP Pack 的质量分和分类体系。

### 确认的范围

| 包含 | 不包含 |
|:-----|:--------|
| ✅ SRA 消耗 CAP Pack 的 18 模块分类增强类别匹配 | ❌ 合并两个项目（SRA 保持独立 PyPI 包） |
| ✅ SQS 质量分 → SRA 推荐权重修正 | ❌ 重写 SRA 匹配算法核心 |
| ✅ CAP Pack 结构变更时通知 SRA 刷新索引 | ❌ 实时文件监听（SRA EPIC-002 范畴） |
| ✅ skill-tree-index SRA 感知模式 | ❌ SRA 内部重构 |

### 为什么不是合并项目？

SRA (`sra-agent`) 已发布到 PyPI (`pypi.org/project/sra-agent/`)，是**独立可复用的中间件**。Hermes、Claude、Codex 都能消费它。CAP Pack 是**技能管理标准**。两者是互补关系——SRA 消费 CAP Pack 的产物（分类、质量分），但不依赖 CAP Pack 的项目结构。

---

## 一、研究记录 (RESEARCH)

### SRA 现有架构（v1.4.0）

```text
四维匹配引擎：
┌─────────────────────────────────────────────────────┐
│ 词法匹配 (40%)   语义匹配 (25%)   场景 (20%)   类别 (15%) │
│ NAME=30          DESC=10        PATTERN=3     CAT=20  │
│ TRIGGER=25       BODY_KW=5      FREQ=2       TAG=15  │
│ TAG=15                                               │
│ DESC=8                                                │
└─────────────────────────────────────────────────────┘
```

**关键发现**：类别维度（15%）目前匹配方式非常基础——只根据输入关键词命中 `category` 字段。CAP Pack 的 18 模块分类体系是**现成的、经过验证的类别系统**，可直接提升 SRA 类别维度精度。

### SRA 索引格式

```json
{
  "name": "pdf-layout",
  "triggers": ["pdf", "layout", "generate pdf"],
  "tags": ["pdf layout", "pdf-layout"],
  "description": "专业 PDF 排版设计与生成技能...",
  "category": "doc-engine"
}
```

### 现有集成点

| 集成点 | 位置 | 描述 |
|:-------|:-----|:------|
| `hermes-message-injection` skill | Hermes 消息管道 | 每次用户消息调 SRA Proxy :8536 |
| SRA skill index | `~/.sra/data/skill_full_index.json` | 全量技能索引，1h 定时刷新 |
| SRA 适配器 | SRA/adapters/ | Hermes / Claude / Codex 三套适配器 |

---

## 二、适配方案设计

### 2.1 三层适配架构

```text
                     ┌──────────────────────────────┐
                     │     CAP Pack (结构管理层)      │
                     │  18 模块分类 · SQS 质量分 ·    │
                     │  生命周期 · 树状索引           │
                     └──────────┬───────────────────┘
                                │
                    ┌───────────┴───────────┐
                    │   适配层 (Adapter)     │
                    │                       │
                    │ ① 分类映射器           │
                    │   cap-pack 分类 → SRA │
                    │                       │
                    │ ② 质量注入器           │
                    │   SQS 分 → 权重修饰    │
                    │                       │
                    │ ③ 变更通知器           │
                    │   结构变更 → 刷新索引   │
                    └───────────┬───────────┘
                                │
                     ┌──────────┴──────────┐
                     │  SRA (运行时发现层)   │
                     │ 四维匹配 · 场景记忆 ·  │
                     │ 上下文注入 · Proxy    │
                     └─────────────────────┘
```

### 2.2 集成点 1：分类映射 (Category Mapping)

**现状**：SRA 类别维度基本靠 tags 猜测，无体系化分类
**改造**：CAP Pack 提供 18 模块 → SRA 类别映射表

```python
# cap-pack-categories.yaml (SRA 可加载)
categories:
  knowledge-base:     {aliases: ["知识库", "知识管理", "knowledge"], weight: 20}
  learning-engine:    {aliases: ["学习", "研究", "调研", "learning"], weight: 20}
  doc-engine:         {aliases: ["文档", "排版", "pdf", "文档生成", "doc"], weight: 20}
  developer-workflow: {aliases: ["开发", "工作流", "sdd", "tdd", "debug"], weight: 20}
  security-audit:     {aliases: ["安全", "审计", "删除", "secrets"], weight: 20}
  quality-assurance:  {aliases: ["质量", "测试", "qa", "审查", "review"], weight: 20}
  devops-monitor:     {aliases: ["运维", "监控", "docker", "deploy"], weight: 20}
  network-proxy:      {aliases: ["网络", "代理", "clash", "mihomo"], weight: 20}
  messaging:          {aliases: ["消息", "飞书", "微信", "email"], weight: 20}
  agent-orchestration:{aliases: ["agent", "协作", "bmad", "kanban"], weight: 20}
  mcp-integration:    {aliases: ["mcp", "协议", "工具", "plugin"], weight: 20}
  financial-analysis: {aliases: ["金融", "股票", "行情", "akshare"], weight: 20}
  creative-design:    {aliases: ["设计", "创意", "mermaid", "架构图"], weight: 20}
  media-processing:   {aliases: ["媒体", "音频", "视频", "tts"], weight: 20}
  github-ecosystem:   {aliases: ["github", "git", "pr", "ci"], weight: 20}
  news-research:      {aliases: ["新闻", "rss", "arxiv", "trending"], weight: 20}
  metacognition:      {aliases: ["元认知", "自我", "反思", "audit"], weight: 20}
  social-gaming:      {aliases: ["游戏", "社交", "minecraft", "pokemon"], weight: 20}
```

**效果**：SRA 类别维度从「猜测标签」变为「知悉体系化分类」，匹配精度 +15-20%

### 2.3 集成点 2：SQS 质量加权 (Quality Weighting)

**现状**：SRA 推荐分 = 完全基于语义匹配，不管 skill 质量如何
**改造**：推荐分 × 质量修饰因子

```python
# SRA matcher.py 新增质量修饰
def _quality_modifier(sqs_score: float) -> float:
    """SQS 质量修饰因子"""
    if sqs_score >= 80:  return 1.0   # 优秀 → 不降权
    if sqs_score >= 60:  return 0.9   # 良好 → 轻微降权
    if sqs_score >= 40:  return 0.7   # 需改进 → 显著降权
    return 0.4                         # 不合格 → 强烈降权

# 最终推荐分
final_score = raw_match_score * _quality_modifier(skill["sqs_score"])
```

**效果**：低质量 skill 即使语义匹配高也不被优先推荐，引导用户使用高质量技能

### 2.4 集成点 3：树状索引感知 (Tree-Aware Matching)

**现状**：SRA 的类别匹配只匹配单个 skill，不知道簇级关系
**改造**：SRA 加载 `skill-tree-index.py` 的簇结构，实现**簇级推荐**

```json
{
  "cluster": "pdf",
  "pack": "doc-engine",
  "pack_health": 71.8,
  "siblings": ["pdf-layout", "pdf-pro-design", "pdf-render-comparison"]
}
```

**效果**：当用户问「PDF 相关」时，SRA 推荐整个 pdf 簇而非单个技能

### 2.5 变更通知协议 (Change Notification)

**现状**：CAP Pack 合并/重命名 skill 后，SRA 最多等 1h 才刷新
**改造**：CAP Pack 工具链在修改 skill 后通知 SRA

```bash
# 在 install-pack.py / extract-pack.py 末尾添加
curl -s -X POST http://127.0.0.1:8536/refresh > /dev/null
# 或
sra index --rebuild
```

---

## 三、接口契约

### SRA → CAP Pack 接口（SRA 消费 CAP Pack）

| 接口 | 方向 | 频率 | 数据量 | 协议 |
|:-----|:----:|:----:|:------:|:-----|
| 分类映射表加载 | SRA 启动时 | 一次性 | ~2KB | 文件读取 |
| SQS 质量分查询 | 每次推荐 | 高频 | ~100B/skill | HTTP / 本地文件 |
| 树状索引结构 | 索引重建时 | 每周 | ~50KB | 文件读取 |

### CAP Pack → SRA 接口（CAP Pack 通知 SRA）

| 接口 | 触发条件 | 协议 |
|:-----|:---------|:------|
| `POST /refresh` | skill 合并/重命名/删除后 | HTTP REST |
| `sra index --rebuild` | 批量变更后 | CLI |

---

## 四、交付物清单

| # | 交付物 | 类型 | 状态 | 说明 |
|:-:|:-------|:----:|:----:|:------|
| 1 | `packs/sra-adapter/cap-pack.yaml` | 能力包 | ⬜ planned | SRA 适配器能力包 |
| 2 | `packs/categories/cap-pack-categories.yaml` | 配置 | ⬜ planned | 18 模块分类映射表 |
| 3 | `scripts/sra-quality-injector.py` | 脚本 | ⬜ planned | SQS → SRA 质量注入器 |
| 4 | `scripts/sra-index-sync.py` | 脚本 | ⬜ planned | CAP Pack → SRA 索引同步 |
| 5 | skill-tree-index `--sra` 模式 | 功能增强 | ⬜ planned | 输出 SRA 可消费的簇结构 |

---

## 五、验收标准

| ID | 描述 | 验证方式 |
|:---|:-----|:---------|
| AC-01 | SRA 加载 CAP Pack 分类后类别匹配精度提升 | Before/After 对比测试 30 条查询 |
| AC-02 | SQS 质量分影响推荐排序 | 低分 skill 被降权，高分 skill 优先 |
| AC-03 | skill 合并后 SRA 索引自动刷新 | `validate-pack.py` 后调 `POST /refresh` |
| AC-04 | skill-tree-index --sra 输出 SRA 兼容格式 | 输出含 `cluster` + `pack` + `siblings` |
| AC-05 | SRA 适配器能力包可独立安装到其他 Agent | Claude/Codex 适配器测试 |

---

## 六、优先级排序

| 工作项 | 优先级 | 工作量 | 依赖 |
|:-------|:------:|:------:|:-----|
| ① 分类映射表 | P1 | 1 轮 | EPIC-001 分类体系 |
| ② skill-tree-index --sra | P1 | 1 轮 | SPEC-2-1 树索引 |
| ③ SRA 适配器能力包 | P2 | 2 轮 | ①②完成 |
| ④ SQS 质量注入 | P2 | 1 轮 | SQS 引擎稳定 |
| ⑤ 变更通知 | P3 | 1 轮 | install-pack.py 集成 |
