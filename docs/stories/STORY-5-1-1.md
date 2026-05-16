# Story: 原子性 + 树状 + 工作流检测器

> **story_id**: `STORY-5-1-1`
> **status**: `completed`
> **priority**: P1
> **epic**: EPIC-005
> **spec_ref**: SPEC-5-1
> **phase**: Phase-1
> **created**: 2026-05-16
> **owner**: boku (Emma)

---

## 用户故事

> **As a** 治理引擎
> **I want** 原子性/树状结构/工作流编排三个检测器，从 `standards/rules.yaml` 加载 L2+H 和 L4+W 规则
> **So that** skill 的组织结构和编排声明可被自动检测

## 验收标准

- [x] `scanner/base.py` — 规则加载基础类，从 `standards/rules.yaml` 加载规则并按层分组 <!-- 验证: python3 -c "from skill_governance.scanner.base import RuleLoader; print('OK')" -->
- [x] `scanner/atomicity.py` — 检测 skill 行数/主题数/依赖数并给出原子性评分 <!-- 验证: pytest tests/test_atomicity.py -q -->
- [x] `scanner/tree_validator.py` — 读取 skill-tree-index 输出并判断簇归属和簇大小 <!-- 验证: pytest tests/test_tree_validator.py -q -->
- [x] `scanner/workflow_detector.py` — 检测 SKILL.md 中的编排声明，验证 W001-W005 <!-- 验证: pytest tests/test_workflow_detector.py -q -->

## 技术方案

详见 SPEC-5-1 §2.3。
