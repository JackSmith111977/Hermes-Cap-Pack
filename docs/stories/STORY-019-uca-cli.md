# Story: UCA CLI 命令行工具

> **story_id**: `STORY-019-uca-cli`
> **status**: `implemented`
> **priority**: P0
> **epic**: EPIC-001-feasibility
> **spec_ref**: SPEC-004-adaptation
> **created**: 2026-05-13
> **implemented**: 2026-05-13
> **owner**: boku

---

## 用户故事

> **As a** 能力包使用者
> **I want** 通过 `cap-pack` 命令行安装/卸载/验证/列出能力包
> **So that** 无需手动复制文件，一键管理能力包

## 验收标准

- [ ] AC1: `cap-pack install <pack-dir>` 安装能力包（调用对应适配器）
- [ ] AC2: `cap-pack remove <pack-name>` 卸载已安装的能力包
- [ ] AC3: `cap-pack verify <pack-name>` 验证已安装的包是否完整
- [ ] AC4: `cap-pack list` 列出所有已安装的能力包及状态
- [ ] AC5: `cap-pack --help` 显示完整的帮助信息
- [ ] AC6: CLI 返回合适的 exit code（0=成功, 1=错误）

## 技术方案

### 设计思路

用 `argparse` 实现 CLI（项目中尚无 click 依赖）。CLI 作为入口，调用 `uca/` 包的 Parser 解析能力包，根据 `compatibility` 字段自动选择适配器，然后执行安装/卸载/验证。

### 架构

```text
cap-pack install doc-engine
    ↓
CLI 入口 (cli/main.py)
    ↓
PackParser.parse("packs/doc-engine/cap-pack.yaml")
    ↓
CapPack 对象 (含 compatibility 声明)
    ↓
Auto-select adapter: HermesAdapter (因为运行在 Hermes 上)
    ↓
HermesAdapter.install(cap_pack)
    ↓
AdapterResult { success, details, warnings, backup_path }
    ↓
CLI 展示结果
```

### 涉及文件

| 文件 | 操作 | 说明 |
|:-----|:-----|:------|
| `scripts/cli/__init__.py` | 新建 | CLI 包 |
| `scripts/cli/main.py` | 新建 | 主入口 + argparse 参数解析 |
| `scripts/cli/commands.py` | 新建 | install/remove/verify/list 命令实现 |

## 测试数据契约

```yaml
test_data:
  source: "packs/doc-engine/"
  ci_independent: true
  pattern_reference: "python3 scripts/cli/main.py install packs/doc-engine --dry-run"
```

## 引用链

- SPEC-004: [docs/SPEC-004-adaptation.md](../SPEC-004-adaptation.md)
- 前序 Story: STORY-018-uca-core
- 后序 Story: STORY-020-hermes-adapter

## 不做的范围

- ❌ 在线注册中心集成
- ❌ 图形化界面
- ❌ 包依赖解析（DependencyChecker 由 STORY-018 提供）

---

## 决策日志

| 日期 | 决策 | 理由 |
|:----|:-----|:------|
| 2026-05-13 | 用 argparse 而非 click | 零依赖，项目中已有 pyyaml 但无 click |
| 2026-05-13 | CLI 自动检测适配器 | 降低用户心智负担，适配器选择透明 |
