# Story: machine-checkable 规则集

> **story_id**: `STORY-5-0-2`
> **status**: `draft`
> **priority**: P1
> **epic**: EPIC-005
> **spec_ref**: SPEC-5-0
> **phase**: Phase-0
> **created**: 2026-05-16
> **owner**: boku (Emma)

---

## 用户故事

> **As a** 治理引擎
> **I want** 有一套结构化（JSON/YAML）的可编程规则集，对照 CAP-PACK-STANDARD.md
> **So that** 检测器不需要硬编码检查逻辑，规则变更只需修改配置文件

## 验收标准

- [x] v3 schema 文件 `schemas/cap-pack-v3.schema.json` 已创建，兼容 v2 <!-- 验证: python3 -c "import json; json.load(open('schemas/cap-pack-v3.schema.json')); print('OK')" -->
- [x] `standards/rules.yaml` 包含 L0-L4 各层的规则条目 <!-- 验证: python3 -c "import yaml; r=yaml.safe_load(open('standards/rules.yaml')); print(len(r.get('layers',[])), 'layers')" -->
- [x] 每层至少 3 条 machine-checkable 规则 <!-- 验证: python3 -c "import yaml; r=yaml.safe_load(open('standards/rules.yaml')); [print(l['name'], len(l['rules'])) for l in r['layers']]" -->
- [x] 规则含 `id`、`description`、`check` 类型、`severity`（blocking/warning/info） <!-- 验证: python3 -c "import yaml; r=yaml.safe_load(open('standards/rules.yaml')); all('id' in rule for l in r['layers'] for rule in l['rules'])" -->

## 技术方案

### 设计思路

将 `CAP-PACK-STANDARD.md` 中的各层规则翻译为结构化格式：

```yaml
# standards/rules.yaml 结构
layers:
  - level: 0
    name: compatibility
    rules:
      - id: C001
        description: "SKILL.md 目录结构符合 Agent Skills Spec"
        check: "dir_structure"
        path: "SKILLS/{id}/SKILL.md"
        severity: blocking
  
  - level: 1
    name: foundation
    rules:
      - id: F001
        description: "YAML frontmatter 含 name/description"
        check: "frontmatter_fields"
        fields: ["name", "description"]
        severity: blocking
```

v3 Schema 在 v2 基础上新增 `compliance_levels` 和 `workflows` 字段，保持向后兼容。

### 涉及文件

- `schemas/cap-pack-v3.schema.json` — 新增（兼容 v2）
- `standards/rules.yaml` — 新增

## 引用链

- EPIC-005: `docs/EPIC-005-skill-governance-engine.md`
- SPEC-5-0: `docs/SPEC-5-0.md`
- 前序 Story: STORY-5-0-1（标准文档定稿后才有规则来源）

## 不做的范围

- Workflow 编排模式定义（STORY-5-0-3）
- 检测器代码实现

---

## 决策日志

| 日期 | 决策 | 理由 |
|:-----|:-----|:------|
| 2026-05-16 | YAML 作为主规则格式，JSON 作为编译输出 | YAML 更可读，适合手写维护 |
