# OpenCode 委托协议 v1.0

> **问题**: OpenCode 集成生硬，没有标准化的委托模式 → 每次临时写 prompt → 结果不可控
> **解决方案**: 标准化的五要素委托协议，每个 OpenCode 任务都走固定结构

---

## 〇、核心原则

```text
Hermes (规划+控制) → OpenCode (编码+执行) → Hermes (审查+合并)

不把 OpenCode 当黑盒：
  1. Hermes 制定精确的任务范围（scope）
  2. OpenCode 按约束执行（bounded execution）
  3. Hermes 验证产出（verification gate）
```

---

## 一、五要素委托协议

每次 OpenCode 任务，必须包含以下五个要素：

### 1.1 任务声明 (Task Declaration)

```text
[任务ID]       ← 唯一标识，与 Story ID 对应
[任务标题]     ← 一句话描述
[任务类型]     ← new_feature | bugfix | refactor | test
[依赖前置]     ← 依赖的任务 ID（如有）
```

### 1.2 输入上下文 (Input Context)

```text
[项目根目录]   ← 绝对路径（--dir 参数）
[参考文件清单]  ← 需要读取的现有文件路径列表
[标准/规则引用] ← 需要遵循的规则文件（如 standards/rules.yaml）
[数据模型]     ← 需要遵循的数据结构定义
```

### 1.3 验收标准 (Acceptance Criteria)

```text
[AC-1]: 具体可验证的标准
[AC-2]: 具体可验证的标准
[验证命令]: 执行后验证的命令
```

### 1.4 约束边界 (Bounded Constraints)

```text
[范围]: 只改什么文件
[不做的]: 明确不改什么
[风格]: 类型标注/docstring/命名规范
[时间盒]: 最大执行分钟数
```

### 1.5 输出产物 (Output Artifacts)

```text
[创建的文件]: 路径列表
[修改的文件]: 路径列表
[验证结果]: 验证命令的输出
```

---

## 二、五种委托模式

### 模式 A: 单文件快速修复 (Bugfix)

```bash
opencode run '
[任务] 修复 #42: login() 返回 500 当 token 过期
[上下文] ~/projects/sra  |  文件: src/auth.py
[AC]  过期 token 返回 401 而非 500
[约束] 只改 auth.py，不修改数据库层
' --dir ~/projects/myapp
```

**超时**: 30s · **验证**: `pytest tests/test_auth.py -q`

### 模式 B: 多文件功能实现 (Feature — 标准模式)

```bash
opencode run '
[任务] 实现用户注册 API
[目标] POST /api/users {email, password} → 201 + token
[文件]
  - 创建: src/api/users.py (路由+handler)
  - 创建: src/models/user.py (ORM model)
  - 修改: src/api/__init__.py (注册路由)
  - 创建: tests/test_users.py (pytest 测试)
[AC-1] POST /api/users 返回 201 + {"token": "..."} 
[AC-2] email 格式验证 (regex)
[AC-3] password 哈希存储 (bcrypt)
[AC-4] POST 重复 email 返回 409
[约束]
  - 遵循现有代码风格 (详见 src/api/auth.py)
  - 所有公共函数写类型标注
  - 测试覆盖正常流 + 异常流
[验证] pytest tests/test_users.py -q
' --thinking --dir ~/projects/myapp
```

**超时**: 120s · **验证**: `pytest tests/test_users.py -q` + `grep -c "def test_" tests/test_users.py`

### 模式 C: 批量并行 (Parallel Tasks)

```bash
# Hermes 先创建 git worktree 隔离
git worktree add -b feat/module-a /tmp/work-a main
git worktree add -b feat/module-b /tmp/work-b main

# 同时委托
opencode run '[任务A] 实现模块 A ...' --dir /tmp/work-a &
opencode run '[任务B] 实现模块 B ...' --dir /tmp/work-b &

# 等全部完成
wait

# Hermes 验证每个 worktree 的测试
pytest /tmp/work-a/tests -q
pytest /tmp/work-b/tests -q

# 合并
git worktree remove /tmp/work-a
git worktree remove /tmp/work-b
```

**超时**: 300s · **验证**: 每个 worktree 独立 pytest

### 模式 D: 代码审查 (Code Review)

```bash
opencode run '
[任务] 审查当前 diff 的安全性和设计模式
[上下文] ~/projects/myapp
[检查点]
  1. 是否有 SQL 注入风险？
  2. 密码/token 是否硬编码？
  3. 错误处理是否完整？
  4. 是否有重复代码？
[输出] 每个检查点: pass/fail + 具体行号 + 改进建议
' --thinking --dir ~/projects/myapp
```

### 模式 E: 测试先行 (TDD — 推荐模式)

```bash
opencode run '
[任务] TDD: 实现 retry 装饰器
[阶段1-RED] 写 test_retry.py 测试 (会失败)
  - test_retry_success: 函数第 2 次重试成功
  - test_retry_max_exceeded: 超过最大重试次数后抛出
  - test_retry_backoff: 指数退避时间正确
[阶段2-GREEN] 实现 retry.py 让测试通过
[阶段3-REFACTOR] 重构代码，确认测试仍通过
[约束] 使用 functools.wraps 保留元数据
[验证] pytest tests/test_retry.py -v
' --thinking --dir ~/projects/myapp
```

---

## 三、超时策略

| 委托模式 | 预估耗时 | 推荐 timeout | 异常处理 |
|:---------|:--------:|:------------:|:---------|
| A (单文件修复) | < 30s | 60s | 超时 → 检查部分输出，手动补完 |
| B (多文件功能) | 1-3min | 300s | 超时 → 用 process log 查看进度，拆分剩余任务 |
| C (批量并行) | 2-5min | 600s | 单个失败不影响其他，最后单独修 |
| D (代码审查) | < 30s | 60s | 超时 → 用 grep 手动检查关键点 |
| E (TDD 三阶段) | 1-3min | 300s | 超时 → 查看已创建的测试文件 |

**经验法则**: 
- 单文件 < 60s · 多文件 < 300s · 全包大任务 < 600s
- 超过 5 分钟的大任务 → 拆分为多个小任务

---

## 四、验证协议

每次 OpenCode 完成后，Hermes 必须执行以下验证：

```python
def verify_opencode_task(task_id: str, expected_files: list[str], verify_cmds: list[str]) -> dict:
    """
    验证 OpenCode 的产出。
    
    Args:
        task_id: 任务标识
        expected_files: 期望创建/修改的文件列表
        verify_cmds: 验证命令列表
    
    Returns:
        {"passed": bool, "created": [str], "missing": [str], "test_results": [...]}
    """
    from pathlib import Path
    import subprocess
    
    result = {"task_id": task_id, "passed": True, "created": [], "missing": [], "test_results": []}
    
    # 检查文件存在性
    for f in expected_files:
        p = Path(f)
        if p.exists():
            result["created"].append(str(p))
        else:
            result["missing"].append(str(p))
            result["passed"] = False
    
    # 运行验证命令
    for cmd in verify_cmds:
        try:
            r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
            result["test_results"].append({
                "command": cmd,
                "passed": r.returncode == 0,
                "output": (r.stdout + r.stderr)[:200],
            })
            if r.returncode != 0:
                result["passed"] = False
        except Exception as e:
            result["test_results"].append({"command": cmd, "passed": False, "output": str(e)})
            result["passed"] = False
    
    return result
```

---

## 五、与工作流链的集成

```text
[工作流链阶段]     [OpenCode 角色]
──────────────────────────────────
SPEC (SDD 完成)    → 不需要 OpenCode
DEV (开发实施)     → Opencode 负责编码 (模式 B/E)
     └── 每个 Task 完成后 → Hermes 验证 (验证协议)
     └── 所有 Task 完成 → chain advance -> QA
QA (质量门禁)      → Opencode 负责修测试 (模式 A)
     └── 门禁通过 → chain advance -> COMMIT
COMMIT (提交)      → 不需要 OpenCode
```

## 六、已知陷阱

| 陷阱 | 表现 | 预防 |
|:-----|:------|:------|
| 超时未完成 | OpenCode 写到一半中断 | 拆小任务 + 设大 timeout |
| 输出截断 | 50KB stdout 上限 | 后台模式 + process log |
| 路径错误 | 文件创建到错误位置 | 强制 --dir 参数 |
| 测试不通过 | OpenCode 说"通过"但实际失败 | 每次必须 Hermes 亲自跑验证 |
| 上下文缺失 | OpenCode 不知道项目约定 | 五要素中的「参考文件」必填 |
