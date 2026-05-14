# STORY-2-4-1: project-report-generator skill 创建与 SDD 工作流集成

> **状态**: `implemented` · **优先级**: P1 · **Epic**: EPIC-002 · **Sprint**: 4
> **SDD 状态**: `implemented` · **创建**: 2026-05-14 · **预估**: 1 轮
> **标签**: `reporting`, `sdd-integration`, `workflow`
> **关联 Spec**: SPEC-2-4

---

## 用户故事

**As a** 主人
**I want** 项目状态报告由 LLM 驱动的 Hermes Skill 按五阶段深度循环创作生成
**So that** 每份报告都是根据项目特点定制的，有独特的设计语言和叙事结构，而非模板填充

## 验收状态

- [x] AC-01: project-report-generator skill 已创建并存于 `~/.hermes/skills/documentation/`
- [x] AC-02: skill 包含完整的五阶段创作工作流（Phase 0 ~ Phase 4）
- [x] AC-03: skill 包含三层门禁机制（R1/R2/R3 + QG）
- [x] AC-04: skill 包含 CSS 模式库引用（`references/css-patterns.md`）
- [x] AC-05: 可配合 `web-ui-ux-design` + `visual-aesthetics` skill 协同使用
- [x] AC-06: SDD 流程图中标注了报告生成步骤
- [x] AC-07: 使用本 skill 成功生成一份符合质量标准的 HTML 报告

## 交付物

| 文件 | 说明 |
|:-----|:------|
| `~/.hermes/skills/documentation/project-report-generator/SKILL.md` | 五阶段工作流 + 三层门禁 + 设计原则 |
| `~/.hermes/skills/documentation/project-report-generator/references/css-patterns.md` | 10 个 CSS 模式参考 |
| `docs/SPEC-2-4.md` | 项目报告生成器工作流集成规范 |
| `docs/STORY-2-4-1.md` | 本 Story 文档 |
| `docs/EPIC-002-tree-health.md` | 更新: 新增 SPEC-2-4 和 STORY-2-4-1 引用 |

## 实施记录

| 日期 | 操作 | 说明 |
|:----|:-----|:------|
| 2026-05-14 | skill_manage(action='create') | 创建 project-report-generator skill + css-patterns.md |
| 2026-05-14 | write_file SPEC-2-4.md | 创建 SDD 工作流集成规范 |
| 2026-05-14 | write_file STORY-2-4-1.md | 本 Story 文档 |
| 2026-05-14 | 加载 skill + 生成 HTML | 验证五阶段流程可执行 |

## 使用说明

在需要生成项目报告时，按以下顺序加载技能：

```bash
# 三步装
skill_view(name='project-report-generator')     # 加载本 skill（含完整的五阶段指令）
skill_view(name='web-ui-ux-design')              # 加载 UI/UX 设计知识
skill_view(name='visual-aesthetics')             # 加载视觉审美标准

# 然后按 skill 中的 Phase 0 → 1 → 2 → 3 → 4 顺序执行
```

## 关联文档

- SPEC-2-4: 项目报告生成器工作流集成规范
- EPIC-002: Skill 树状层次管理与健康度优化系统
