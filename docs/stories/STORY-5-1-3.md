# Story: CLI 工具 + JSON/HTML 报告

> **story_id**: `STORY-5-1-3`
> **status**: `draft`
> **priority**: P1
> **epic**: EPIC-005
> **spec_ref**: SPEC-5-1
> **phase**: Phase-1
> **created**: 2026-05-16
> **owner**: boku (Emma)

---

## 用户故事

> **As a** 主人/运维
> **I want** 一条 `skill-governance scan` 命令即可对任意 skill 执行 L0-L4 四层检测，并可 --json 或 --html 输出
> **So that** 不打开文件就能知道 skill 的健康状况

## 验收标准

- [x] `skill-governance scan <path>` 输出带颜色的 CLI 摘要 <!-- 验证: skill-governance scan . --help -->
- [x] `--json` 输出可被程序解析的完整 L0-L4 分层结果 <!-- 验证: skill-governance scan . --json | python3 -c "import json,sys; json.load(sys.stdin)" -->
- [x] `--html` 输出美观的可视化报告（暗色主题） <!-- 验证: test -f report.html -->
- [x] exit code 反映检测结果（0=全通过, 1=有失败） <!-- 验证: skill-governance scan . --json; echo $? -->

## 技术方案

详见 SPEC-5-1 §2.4 CLI 接口设计。
