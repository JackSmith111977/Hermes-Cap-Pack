# Story: cron 定时扫描 + 飞书推送

> **story_id**: `STORY-5-2-4`
> **status**: `draft`
> **priority**: P1
> **epic**: EPIC-005
> **spec_ref**: SPEC-5-2
> **phase**: Phase-2
> **created**: 2026-05-16
> **owner**: boku (Emma)

---

## 用户故事

> **As a** 主人
> **I want** 每天自动收到 cap-pack 合规报告
> **So that** 不需要手动触发扫描就知道 skill 健康状况

## 验收标准

- [x] `integration/cron_reporter.py` — 定时扫描 + 飞书推送 <!-- 验证: python3 -c "from skill_governance.integration.cron_reporter import setup_cron; print('OK')" -->
- [x] 每日 6:00 全量扫描 <!-- 验证: grep -q "6:00\|daily\|0 6" integration/cron_reporter.py -->
- [x] 降级检测 — 对比前次结果 <!-- 验证: grep -q "previous\|diff\|compare\|delta" integration/cron_reporter.py -->
- [x] 飞书推送 — 合规报告卡片 <!-- 验证: grep -q "feishu\|send\|report\|notify" integration/cron_reporter.py -->

## 技术方案

使用 Hermes cronjob 注册定时任务，每日扫描后通过 feishu API 发送报告。
