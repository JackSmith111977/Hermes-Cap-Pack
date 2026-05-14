# STORY-4-5: L2/L3 模板标准化 + validate-layers.py

> **状态**: `completed` · **Epic**: EPIC-004 · **Spec**: SPEC-4-2
> **SDD 状态**: `completed` · **创建**: 2026-05-14

---

## 用户故事

**As a** 主人
**I want** L2/L3 有标准模板和自动检查脚本
**So that** 后续补充的 L2/L3 质量一致，且可被自动验证

## 验收标准

- [ ] AC-01: `scripts/validate-layers.py` 存在且可运行
- [ ] AC-02: 脚本检查每个 pack 的 L2/L3 完整性（≥ 1 篇）
- [ ] AC-03: 脚本验证 YAML frontmatter 字段完整
- [ ] AC-04: doc-engine 旧格式 L2（11 篇）已迁移到新 YAML frontmatter 格式
- [ ] AC-05: 迁移后 doc-engine 功能不受影响
- [ ] AC-06: project-state.py verify 通过

## 执行步骤

1. 编写 `scripts/validate-layers.py`
   - `--layers` 检查每包 L2/L3 存在性
   - `--frontmatter` 验证 YAML 字段完整
   - `--all` 全量检查
2. 迁移 doc-engine EXPERIENCES 11 篇到 YAML frontmatter 格式
3. 运行验证

## 估算：1h

## validate-layers.py 设计

```bash
python3 scripts/validate-layers.py                     # 全量检查
python3 scripts/validate-layers.py --pack creative-design # 单包检查
python3 scripts/validate-layers.py --ci                # CI 模式（exit code）
```

检查项：
- 每包 `EXPERIENCES/` 至少 1 个 `.md` 文件
- 每包 `KNOWLEDGE/` 至少 1 个 `.md` 文件
- 每个 `.md` 文件有完整 YAML frontmatter（type/...）
