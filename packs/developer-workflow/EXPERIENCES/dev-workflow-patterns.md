---

type: best-practice
skill_ref: developer-workflow
keywords: [dev-workflow, patterns]
created: 2026-05-14
---

  - plan
  - writing-plans
  - spike
  - test-driven-development
  - systematic-debugging
  - subagent-driven-development
  - requesting-code-review
  - patch-file-safety
---

# 开发工作流已知陷阱与最佳实践

## Plan & Writing Plans

### 🚩 陷阱：Plan 过于宏观，缺乏具体步骤
**问题**: Plan 只写了目标，没有拆解到可执行的原子步骤（文件级）。
**解决**: 每个 step 应该能直接映射到 `write_file` / `patch` 调用。子步骤不超过 5 行代码的粒度。

### 🚩 陷阱：Plan 不包含回退策略
**问题**: 第一方案失败后，agent 卡住。
**解决**: 每个关键步骤标注 Plan B（如 "如果 pip install 失败，尝试 --no-deps"）。

## Spike

### 🚩 陷阱：Spike 产物被混入主线代码
**问题**: 实验代码忘记清理，遗留 tech debt。
**解决**: Spike 应放在临时目录（`/tmp/` 或 `~/spikes/`），完成后 `git clean` 或删除。Spike 文档记录结论即可。

## TDD

### 🚩 陷阱：Red 阶段写太多实现
**问题**: 没等 Red 确认失败就写实现，失去 TDD 的意义。
**解决**: Red → 确认测试失败（运行测试）→ Green → 最小实现 → Refactor。

### 🚩 陷阱：测试依赖外部资源（网络/DB）
**问题**: 测试不可重复，CI 环境失败。
**解决**: 使用 mock/patch 模拟外部依赖。集成测试单独标记。

## 系统化调试

### 🚩 陷阱：跳过 Phase 1（上下文收集），直接猜根因
**问题**: 浪费时间在错误的方向。
**解决**: 严格执行 4-phase：收集上下文 → 形成假设 → 验证假设 → 修复。Phase 1 至少收集错误信息、最近变更、输入输出。

### 🚩 陷阱：改了一处以为修好了，没跑回归
**问题**: 修复引入新 bug。
**解决**: 修复后一定要跑完整测试套件，至少跑相关模块。

## Subagent-Driven Development

### 🚩 陷阱：Subagent 之间缺乏契约，导致合并冲突
**问题**: 多个 subagent 改同一文件的不同部分，互相覆盖。
**解决**: 在 plan 中明确文件分配，每个文件只分配给一个 subagent。共享接口要提前协商。

### 🚩 陷阱：Subagent 输出不验证
**问题**: subagent 返回的代码可能有语法错误。
**解决**: 主 agent 需要在 merge 前运行 lint + test。

## Code Review

### 🚩 陷阱：Security scan 误报导致 review 疲劳
**问题**: 过多误报让开发者忽略真正的问题。
**解决**: 维护 baseline 文件，只关注 delta。配置 `.semgrepignore` 排除已知误报。

### 🚩 陷阱：Review 只改不测
**问题**: Code review 修改后没有重新验证。
**解决**: Review 修改后必须重新运行测试套件。

## Patch File Safety

### 🚩 陷阱：连续 patch 导致文件累积污染
**问题**: 多次 patch 同一区域，导致缩进错乱或重复内容。
**解决**: 复杂修改优先用 `write_file` 重写整个函数/类，而非多次 patch。patch 后立即 lint。
