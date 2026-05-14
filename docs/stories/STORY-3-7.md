# STORY-3-7: learning-engine 能力包提取

> **状态**: `approved` · **优先级**: P1 · **Epic**: EPIC-003 · **Spec**: SPEC-3-3
> **SDD 状态**: `approved` · **创建**: 2026-05-14
> **标签**: `extraction`, `learning-engine`

## 用户故事

**As a** 主人
**I want** research/learning/knowledge 领域的技能被提取为 `learning-engine` 能力包
**So that** 跨 Agent 复用深度调研、论文搜索、知识沉淀能力

## 验收标准

- [ ] AC-01: `packs/learning-engine/cap-pack.yaml` 创建，通过 v2 schema 验证
- [ ] AC-02: 每个 skill 复制到 `SKILLS/<id>/SKILL.md`（或 symlink）
- [ ] AC-03: SQS ≥ 50 的 skill 全部纳入，< 50 的记录到 exceptions
- [ ] AC-04: depends_on/referenced_by 交叉引用完整
- [ ] AC-05: 覆盖率统计: HERMES_SKILLS_DIR → packs/ 的映射表

## 执行 SOP

### Step 1: 盘点
- 扫描 research/, learning/, knowledge-* 等目录
- 确认每个 skill 的实际文件位置和状态
- 生成映射表

### Step 2: SQS 质检
- 对每个 skill 运行 SQS 评分
- 记录基线（用于后续健康度追踪）

### Step 3: 提取
- 创建 `packs/learning-engine/` 目录结构
- 编写 `cap-pack.yaml`（v2 schema）
- 复制 skill 文件

### Step 4: 验证
- v2 schema 验证
- 依赖完整性检查
- 交叉引用一致性
