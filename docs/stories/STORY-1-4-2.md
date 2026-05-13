# STORY-1-4-2: Hermes 适配器实现（草案）

> **story_id**: `STORY-1-4-2`
> **status**: `draft`
> **priority**: P0
> **epic**: EPIC-001-feasibility
> **spec_ref**: SPEC-1-4
> **created**: 2026-05-13
> **owner**: boku

---

## 用户故事

> **As a** Hermes Agent 用户
> **I want** 将能力包（cap-pack）自动安装到我的 Hermes 环境
> **So that** 无需手动复制文件，一键获得 boku 的领域能力

## 验收标准

- [ ] AC1: `install-pack.py` 能将能力包的 skills 安装到 `~/.hermes/skills/` 下
- [ ] AC2: 安装过程自动备份已存在的 skill（`.bak` 目录）
- [ ] AC3: 安装后执行 `on_activate` 钩子（如 pip install 依赖）
- [ ] AC4: 支持 `--dry-run` 预览安装内容
- [ ] AC5: `remove` 命令可从备份恢复已卸载的 skill

## 技术方案

### 设计思路

利用 Hermes 的 skill 目录结构（`~/.hermes/skills/{name}/SKILL.md`），将能力包中的 `SKILLS/{name}/` 目录直接复制为目标路径。备份机制确保可回滚。

### 实现步骤

1. 解析 cap-pack.yaml 获取 skills 列表和钩子
2. 逐 skill 复制：src=SKILLS/{name}/ → dst=~/.hermes/skills/{name}/
3. 备份已有 skill 到 {name}.bak
4. 执行 on_activate 钩子
5. 记录安装状态到 installed_packs.json

### 涉及文件

- `scripts/install-pack.py` — 安装脚本

## 测试数据契约

```yaml
test_data:
  source: "packs/doc-engine/cap-pack.yaml"
  ci_independent: true
  pattern_reference: "python3 scripts/install-pack.py packs/doc-engine --dry-run"
```

## 引用链

- EPIC-001: [docs/EPIC-001-feasibility.md](../EPIC-001-feasibility.md)
- SPEC-1-4: [docs/SPEC-1-4.md](../SPEC-1-4.md)
- 前序 Story: STORY-003-format-v1（依赖格式定义完成）

## 不做的范围

- ❌ Claude Code 适配器（STORY-010 覆盖）
- ❌ Codex CLI 适配器（Phase 3 覆盖）
- ❌ 在线注册中心集成

---

## 决策日志

| 日期 | 决策 | 理由 |
|:----|:-----|:------|
| 2026-05-13 | 使用 shutil.copytree 而非符号链接 | 符号链接触及 Hermes 的只读预期 |
| 2026-05-13 | 备份到 {name}.bak 而非打包成 tar.gz | 回滚速度快，无需解压 |
