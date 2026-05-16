# Story: Skill Watcher (fingerprint + cron)

> **story_id**: `STORY-5-1-4`
> **status**: `draft`
> **priority**: P1
> **epic**: EPIC-005
> **spec_ref**: SPEC-5-1
> **phase**: Phase-1
> **created**: 2026-05-16
> **owner**: boku (Emma)

---

## 用户故事

> **As a** 治理引擎
> **I want** 通过 fingerprint 快照自动检测 skill 目录的新增/修改，并触发全量扫描
> **So that** 新 skill 加入时自动合规检查，不需要手动触发

## 验收标准

- [x] `skill-governance watcher init` 创建 skills 目录指纹快照（SHA-256） <!-- 验证: test -f .fingerprint.json -->
- [x] `skill-governance watcher check` 检测新增/修改/删除的 skill <!-- 验证: python3 -c "from skill_governance.watcher.fingerprint import FingerprintWatcher; w=FingerprintWatcher('.'); print(w.check())" -->
- [x] 新 skill 检测后自动触发全扫描链 <!-- 验证: grep -q "auto_scan\|trigger_scan\|run_scan" watcher/fingerprint.py -->
- [x] 支持注册 cron 定时任务 <!-- 验证: grep -q "cron\|schedule" watcher/fingerprint.py -->

## 技术方案

详见 SPEC-5-1 §2.5 Watcher 机制。
