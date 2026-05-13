# STORY-017: SQS 质量加权 SRA 推荐

> **状态**: `draft` · **优先级**: P2 · **Epic**: EPIC-002 · **Sprint**: 3
> **SDD 状态**: `draft` · **创建**: 2026-05-13 · **预估**: 1 轮
> **标签**: `sra`, `sqs`, `quality-weighting`

---

## 用户故事

**As a** 主人
**I want** SRA 推荐时考虑 skill 的质量分，低质量 skill 即使语义匹配也不优先推荐
**So that** 不会因为 SRA 推荐了低质量 skill 而浪费时间

## 验收标准

- [ ] AC-01: SRA 推荐结果受 SQS 质量分影响
- [ ] AC-02: SQS ≥ 80 → 不降权；SQS 50-79 → 降权 10-30%；SQS < 50 → 降权 60%
- [ ] AC-03: 无 SQS 评分的 skill 使用默认值 50（中性降权）
- [ ] AC-04: 质量加权可开关（`--no-quality` 参数）
- [ ] AC-05: 加权后的推荐列表排序合理（高分高质量 skill 排最前）

## 质量修饰函数

```python
def quality_modifier(sqs: float) -> float:
    if sqs >= 80:  return 1.0
    if sqs >= 60:  return 0.9
    if sqs >= 40:  return 0.7
    return 0.4
```

## 技术方案

1. 在 SRA 侧创建 `scripts/sra-quality-injector.py`：
   - 读取 `~/.hermes/data/skill-quality.db`（SQS 数据库）
   - 建立 skill_name → sqs_score 映射 JSON
   - 输出到 SRA 可读取的位置
2. 通过 cron 每 6 小时更新一次 SQS 映射
3. SRA matcher.py 新增 `_quality_modifier()` 函数

## 不做的

- 实时 SQS 评分（cron 定时同步即可）
- 在 CAP Pack 侧修改 SRA 代码（通过注入文件通信）

## 测试

- 排序测试: 10 个 skill，验证 SQS 加权后的排序是否合理
