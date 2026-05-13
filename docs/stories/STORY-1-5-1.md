# STORY-1-5-1: HermesAdapter install 配置完整消费

> **story_id**: `STORY-1-5-1`
> **status**: `implemented`
> **priority**: P0
> **epic**: EPIC-001-feasibility
> **spec_ref**: SPEC-1-5
> **created**: 2026-05-14
> **owner**: boku

---

## 用户故事

> **As a** 系统维护者
> **I want** 安装能力包时 cap-pack.yaml 的 `install.scripts`、`install.references`、`install.post_install` 被完整消费
> **So that** 安装一个包 = 一步到位，不需要手动复制脚本或执行 chmod

## 验收标准

### AC-1: install.scripts 完整消费
- [x] `install.scripts` 中的 source→target 文件被复制到 `~/.hermes/scripts/`
- [x] 目标文件已存在时自动备份为 `.bak`
- [x] 目标目录不存在时自动创建父目录
- [x] dry_run 模式只预览不复制

### AC-2: install.references 完整消费
- [x] `install.references` 中的 source→target 被复制
- [x] 支持目录批量复制和单文件复制
- [x] dry_run 模式只预览不复制

### AC-3: install.post_install 完整消费
- [x] `install.post_install` 中的 shell 命令被顺序执行
- [x] 单条命令失败时不影响后续命令
- [x] 超时 30 秒保护
- [x] 非零退出码记录警告不阻塞安装

### AC-4: 向前兼容
- [x] 没有 `install` 配置的旧包不受影响
- [x] 所有 14 个已有测试通过

## 技术方案

### 修改文件

`scripts/adapters/hermes.py` — HermesAdapter 类

### 新增方法

| 方法 | 输入 | 输出 | 说明 |
|:-----|:-----|:-----|:------|
| `_install_scripts()` | pack, dry_run | list[str] | 从 install.scripts 复制脚本到目标路径 |
| `_install_references()` | pack, dry_run | list[str] | 从 install.references 复制引用文档 |
| `_run_post_install()` | pack | bool | 执行 install.post_install shell 命令 |

### 修改方法

`install()` — 安装流程从 5 步扩展为 8 步：

```
Step 1: 创建快照
Step 2: _install_skills()     ← 不变
Step 3: _install_scripts()    ← 新增
Step 4: _install_references() ← 新增
Step 5: _install_mcp()        ← 不变
Step 6: _run_post_install()   ← 新增
Step 7: 记录追踪
Step 8: 清理快照
```

### 设计决策

- 使用 `pack.manifest`（原始 dict）读取 install 配置，不修改 CapPack 数据类
- 文件复制含备份（`.bak` 后缀），与现有 skill 备份策略一致
- post_install 使用 `subprocess.run` 而非 `os.system`，可控性更高
