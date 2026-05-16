# 🤖 SPEC-6-2: LLM 辅助修复 — Phase 2

> **spec_id**: `SPEC-6-2`
> **status**: `completed`
> **epic**: `EPIC-006`
> **phase**: `Phase-2`
> **created**: 2026-05-16
> **updated**: 2026-05-16
> **owner**: boku (Emma)
> **优先级**: P2
> **估算**: ~4h（3 Stories）
> **前置**: Phase 0+1 ✅ Fix 基础设施 + 确定性修复规则

---

## 〇、需求澄清

### 用户故事

> **As a** 主人
> **I want** 对于需要语义理解的扫描问题（classification 推断、SRA 元数据、断链修复），LLM 能辅助生成精确的修复建议
> **So that** 确定性规则覆盖不到的 30% 问题也能自动修复

### 范围

| 包含 | 不包含 |
|:-----|:-------|
| LLM 辅助修复框架（接口抽象 + prompt 模板） | Web UI |
| F006 增强：LLM 辅助 classification 推断 | 自动 git commit |
| E001: 生成 SRA 友好的 triggers 和描述 | 修改 SKILL.md 正文 |
| E002: 补充 cross-platform agent_types 声明 | 与非 cap-pack 生态集成 |
| E005: 检测并修复断裂链接 | |

---

## 一、技术方案

### LLM 辅助框架

```python
# fixer/llm_assist.py

class LLMAssistRule(FixRule):
    """LLM 辅助修复规则的基类。
    
    对于需要语义理解的规则，继承此类：
    1. 收集上下文: pack_path, SKILL.md 内容, 扫描细节
    2. 构建 prompt: 包含 SKILL.md 内容 + 规则要求 + 输出格式
    3. 调用 LLM: 通过命令行或 API 获取建议
    4. 解析结果: 提取结构化修复建议
    5. 应用修复: 通过 FixRule.apply() 执行
    """
    
    LLM_COMMAND = "opencode run"  # 可配置
    
    def _call_llm(self, prompt: str) -> str:
        """调用 LLM 生成建议"""
        import subprocess
        result = subprocess.run(
            ["opencode", "run", prompt, "--dir", "."],
            capture_output=True, text=True, timeout=60
        )
        return result.stdout
```

### E001: SRA 元数据

检测到 SRA 发现性不足时，LLM 分析 SKILL.md 内容，生成：
- 3-5 个精确的 triggers（提升 SRA 召回）
- 1-2 句简洁的 description（提升匹配质量）

### E002: 跨平台声明

检测到 agent_types < 2 时，LLM 根据 skill 内容推断：
- 适用哪些 Agent 平台（hermes/opencode/claude/openclaw）
- 更新 compatibility.agent_types

### E005: 断裂链接

从扫描结果的断裂链接列表，LLM 逐个：
1. 验证链接是否真的失效（通过 curl --head）
2. 如失效 → 搜索替代 URL
3. 提供替换建议

---

## 二、Story 分解

| ID | 标题 | 内容 | 估算 | 产出物 |
|:---|:-----|:-----|:----:|:-------|
| STORY-6-2-1 | **LLM 辅助修复框架 + F006 增强** | LLMAssistRule 基类 + F006 LLM 增强 | 1.5h | `fixer/llm_assist.py` |
| STORY-6-2-2 | **E001 SRA 元数据 + E002 跨平台** | LLM 生成 triggers/agent_types | 1.5h | `fixer/rules/e001_sra.py`, `e002_cross_platform.py` |
| STORY-6-2-3 | **E005 断裂链接检测与修复** | curl 验证 + LLM 搜索替代 | 1h | `fixer/rules/e005_broken_links.py` |

---

## 三、验收标准

- [x] LLMAssistRule 基类定义 _call_llm() 调用 opencode run <!-- 验证: grep -q "LLMAssistRule\|_call_llm" fixer/llm_assist.py -->
- [x] E001: 生成 3-5 个 SRA triggers + 优化 description <!-- 验证: grep -q "E001\|sra\|triggers" fixer/rules/e001_sra.py -->
- [x] E002: 推断并补充 agent_types 声明 <!-- 验证: grep -q "E002\|agent_types\|cross-platform\|compatibility" fixer/rules/e002_cross_platform.py -->
- [x] E005: 检测断裂链接 + 请求 LLM 替代建议 <!-- 验证: grep -q "E005\|broken_links\|curl.*head" fixer/rules/e005_broken_links.py -->
- [x] 全部测试通过 <!-- 验证: python3 -m pytest packages/skill-governance/tests/ -q -->
