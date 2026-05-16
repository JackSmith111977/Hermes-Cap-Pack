# Story: H001+H002 — 树簇归属 + 簇大小优化

> **story_id**: `STORY-6-1-3`
> **status**: `completed`
> **priority**: P1
> **epic**: EPIC-006
> **spec_ref**: SPEC-6-1
> **phase**: Phase-1
> **created**: 2026-05-16
> **owner**: boku (Emma)

## 用户故事
**As a** 包维护者
**I want** 自动将未归属的 skill 分配到最佳簇，并优化过小簇
**So that** 满足 L2 树状结构合规

## 验收标准
- [x] H001: Jaccard 相似度匹配 skill → 最佳簇 <!-- 验证: grep -q "jaccard\|similarity" fixer/rules/h001_cluster.py -->
- [x] H001: 更新 cap-pack.yaml 的 cluster 字段 <!-- 验证: grep -q "cluster" fixer/rules/h001_cluster.py -->
- [x] H002: 检测簇 < 3 skill → 建议合并目标 <!-- 验证: grep -q "size\|merge" fixer/rules/h002_cluster_size.py -->
- [x] H002: 只建议不自动执行（dry_run） <!-- 验证: grep -q "suggest\|recommend" fixer/rules/h002_cluster_size.py -->

## 技术方案
- 模块: `fixer/rules/h001_cluster.py`, `fixer/rules/h002_cluster_size.py`
- H001 复用 `adapter/cap_pack_adapter.py` 的 `_jaccard_similarity()` 算法
- H002 统计每个簇的 skill 数量，小于 3 时查找 Jaccard 最接近的簇
