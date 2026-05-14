#!/usr/bin/env python3
"""
project-state.py v1.0 — 项目统一状态机管理器

用法:
  python3 scripts/project-state.py status              # 显示当前状态
  python3 scripts/project-state.py scan                # 扫描 SDD 文档，检测漂移
  python3 scripts/project-state.py verify              # 一致性验证 (exit code)
  python3 scripts/project-state.py list                # 列出所有实体及状态
  python3 scripts/project-state.py list --by-state     # 按状态分组
  python3 scripts/project-state.py list --by-type      # 按类型分组
  python3 scripts/project-state.py gate <entity> <to>  # 门禁检查（不执行）
  python3 scripts/project-state.py transition <entity> <to> [reason]  # 状态转换 + 门禁
  python3 scripts/project-state.py sync                # 同步 SDD 文档状态到 YAML
  python3 scripts/project-state.py history             # 查看变更历史
"""

import sys
import os
import re
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
STATE_FILE = PROJECT_DIR / "docs" / "project-state.yaml"
SDD_DIR = PROJECT_DIR / "docs"
STORY_DIR = SDD_DIR / "stories"

# 有效状态列表（按工作流类型分组）
SDD_STATES = [
    "draft", "review", "approved",
    "architect", "plan", "implement",
    "completed", "archived"
]
EPIC_STATES = ["draft", "create", "qa_gate", "review", "approved"]
SPRINT_STATES = ["planning", "in_progress", "released"]


def load_state():
    """加载 project-state.yaml"""
    import yaml
    if not STATE_FILE.exists():
        print(f"❌ STATE_FILE not found: {STATE_FILE}")
        print("   运行 python3 scripts/project-state.py init 创建")
        sys.exit(1)
    with open(STATE_FILE, "r") as f:
        return yaml.safe_load(f)


def save_state(state):
    """保存 project-state.yaml（保持可读性）"""
    import yaml
    with open(STATE_FILE, "w") as f:
        yaml.dump(state, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
    print(f"✅ 已保存状态到 {STATE_FILE}")


def get_doc_states():
    """扫描 SDD 文档，提取实际状态"""
    doc_states = {"epics": {}, "specs": {}, "stories": {}}

    # 扫描 EPICs
    for f in sorted(SDD_DIR.glob("EPIC-*.md")):
        text = f.read_text()
        m = re.search(r'\*\*状态\*\*:\s*`(\w+)`', text) or re.search(r'\*\*status\*\*:\s*`(\w+)`', text)
        if m:
            eid = f.stem.split("-")[0] + "-" + f.stem.split("-")[1]
            doc_states["epics"][eid] = m.group(1)

    # 扫描 SPECs
    for f in sorted(SDD_DIR.glob("SPEC-*.md")):
        text = f.read_text()
        m = re.search(r'\*\*状态\*\*:\s*`(\w+)`', text) or re.search(r'\*\*status\*\*:\s*`(\w+)`', text)
        if m:
            sid = f.stem
            doc_states["specs"][sid] = m.group(1)

    # 扫描 STORYS
    for f in sorted(STORY_DIR.glob("STORY-*.md")):
        text = f.read_text()
        m = re.search(r'\*\*状态\*\*:\s*`(\w+)`', text) or re.search(r'\*\*status\*\*:\s*`(\w+)`', text)
        if m:
            stid = f.stem
            doc_states["stories"][stid] = m.group(1)

    return doc_states


# ─── 命令实现 ───

def cmd_status():
    state = load_state()
    p = state["project"]
    q = state["quality"]
    print(f"\n{'='*60}")
    print(f"  📊 {p['name']} v{p['version']} — 统一状态机")
    print(f"  Phase: {p['current_phase']} · 总体状态: {p['overall_state']}")
    print(f"{'='*60}")

    # Epics
    print(f"\n📋 Epics:")
    for eid, e in state["entities"]["epics"].items():
        ratio = f"{e['completed_count']}/{e['story_count']}"
        print(f"  {eid:12s} [{e['state']:10s}] {e['title'][:50]} ({ratio})")

    # Specs
    print(f"\n📄 Specs:")
    for sid, s in state["entities"]["specs"].items():
        print(f"  {sid:12s} [{s['state']:10s}] {s['epic']} · {len(s.get('stories',[]))} stories")

    # Sprints
    print(f"\n🏃 Sprints:")
    for spid, sp in state.get("sprints", {}).items():
        r = f"{sp['stories_completed']}/{sp['stories_planned']}"
        print(f"  {spid:12s} [{sp['state']:10s}] {sp.get('title','')} ({r})")

    # Quality
    print(f"\n📈 质量指标:")
    print(f"  SQS: {q['sqs']['avg']}/{q['sqs']['target']}  "
          f"Tests: {q['tests']['passing']}/{q['tests']['count']}  "
          f"CHI: {q['chi']['value']}/{q['chi']['target']}")

    print()


def cmd_verify():
    """验证 YAML 状态 vs 文档实际状态的一致性"""
    state = load_state()
    doc_states = get_doc_states()
    errors = []
    warnings = []

    # 检查 Epics
    for eid, e in state["entities"]["epics"].items():
        doc_s = doc_states["epics"].get(eid)
        if doc_s and doc_s != e["state"]:
            errors.append(f"🔴 EPIC {eid}: YAML={e['state']}, DOC={doc_s} 状态不一致")
        elif not doc_s:
            warnings.append(f"🟡 EPIC {eid}: YAML 中有记录但未找到文档文件")

    # 检查 Specs
    for sid, s in state["entities"]["specs"].items():
        doc_s = doc_states["specs"].get(sid)
        if doc_s and doc_s != s["state"]:
            errors.append(f"🔴 SPEC {sid}: YAML={s['state']}, DOC={doc_s} 状态不一致")
        elif not doc_s:
            warnings.append(f"🟡 SPEC {sid}: YAML 中有记录但未找到文档文件")

    # 检查 Stories
    for stid, st in state["entities"]["stories"].items():
        doc_s = doc_states["stories"].get(stid)
        if doc_s and doc_s != st["state"]:
            errors.append(f"🔴 STORY {stid}: YAML={st['state']}, DOC={doc_s} 状态不一致")
        elif not doc_s:
            warnings.append(f"🟡 STORY {stid}: YAML 中有记录但未找到文档文件")

    # 检查文档有的但 YAML 缺失
    for eid in doc_states["epics"]:
        if eid not in state["entities"]["epics"]:
            errors.append(f"🔴 EPIC {eid}: 文档存在但 YAML 中未注册")
    for sid in doc_states["specs"]:
        if sid not in state["entities"]["specs"]:
            errors.append(f"🔴 SPEC {sid}: 文档存在但 YAML 中未注册")
    for stid in doc_states["stories"]:
        if stid not in state["entities"]["stories"]:
            errors.append(f"🔴 STORY {stid}: 文档存在但 YAML 中未注册")

    if warnings:
        print(f"🟡 警告 ({len(warnings)}):\n")
        for w in warnings:
            print(f"  {w}")
    if errors:
        print(f"\n❌ 状态不一致 ({len(errors)}):\n")
        for e in errors:
            print(f"  {e}")
        sys.exit(1)
    if not errors and not warnings:
        print(f"✅ 一致性验证通过 — {len(state['entities']['epics'])} Epics, "
              f"{len(state['entities']['specs'])} Specs, "
              f"{len(state['entities']['stories'])} Stories 全一致")
    else:
        print(f"\n✅ 关键状态一致性通过，{len(warnings)} 个警告 (非 blocking)")
    return True


def cmd_scan():
    """扫描文档状态，对比 YAML"""
    state = load_state()
    doc_states = get_doc_states()

    print(f"\n{'='*60}")
    print("  扫描结果: 文档实际状态 vs YAML 记录状态")
    print(f"{'='*60}")

    total = drift = 0

    for eid, e in sorted(state["entities"]["epics"].items()):
        total += 1
        doc_s = doc_states["epics"].get(eid, "—")
        mark = "⚠️" if doc_s != "—" and doc_s != e["state"] else " ✅"
        if doc_s != "—" and doc_s != e["state"]:
            drift += 1
        print(f"  {mark} EPIC {eid:12s} YAML={e['state']:10s} DOC={doc_s}")

    for sid, s in sorted(state["entities"]["specs"].items()):
        total += 1
        doc_s = doc_states["specs"].get(sid, "—")
        mark = "⚠️" if doc_s != "—" and doc_s != s["state"] else " ✅"
        if doc_s != "—" and doc_s != s["state"]:
            drift += 1
        print(f"  {mark} SPEC {sid:12s} YAML={s['state']:10s} DOC={doc_s}")

    for stid, st in sorted(state["entities"]["stories"].items()):
        total += 1
        doc_s = doc_states["stories"].get(stid, "—")
        mark = "⚠️" if doc_s != "—" and doc_s != st["state"] else " ✅"
        if doc_s != "—" and doc_s != st["state"]:
            drift += 1
        print(f"  {mark} STORY {stid:12s} YAML={st['state']:10s} DOC={doc_s}")

    print(f"\n总计: {total} 个实体, 漂移: {drift} 个")
    return drift


def cmd_gate(entity, target_state):
    """检查状态转换是否允许"""
    state = load_state()

    # 查找实体当前状态
    current = None
    for etype in ["epics", "specs", "stories"]:
        if entity in state["entities"].get(etype, {}):
            current = state["entities"][etype][entity]["state"]
            break

    if not current:
        # 可能是 sprint
        if entity in state.get("sprints", {}):
            current = state["sprints"][entity]["state"]

    if not current:
        print(f"❌ 未找到实体: {entity}")
        sys.exit(1)

    # 检查是否在有效状态列表中
    all_valid = SDD_STATES + EPIC_STATES + SPRINT_STATES
    if target_state not in all_valid:
        print(f"❌ 无效目标状态: {target_state}")
        print(f"   有效状态: {', '.join(all_valid)}")
        sys.exit(1)

    print(f"🔍 门禁检查: {entity}: {current} → {target_state}")
    print(f"  ✅ 当前状态有效: {current}")
    print(f"  ✅ 目标状态有效: {target_state}")

    # 门禁预检（不执行外部脚本，只做软检查）
    if target_state == "qa_gate" and current in ("draft", "create"):
        print(f"  ⚠️  需要先经过 REVIEW 才能进入 QA_GATE")
        print(f"  ℹ️  实际通过: 手动验证前置条件")

    if target_state == "completed":
        print(f"  ⚠️  需要检查: pytest 通过 + AC 验证 + doc-alignment")

    if target_state == "archived":
        print(f"  ⚠️  需要检查: 漂移=0 + HTML 已生成")

    print(f"\n✅ 门禁预检通过 (软检查)")
    print(f"  执行 transition: python3 scripts/project-state.py transition {entity} {target_state} \"<reason>\"")
    return True


def cmd_transition(entity, target_state, reason=""):
    """执行状态转换"""
    # 先跑门禁
    try:
        cmd_gate(entity, target_state)
    except SystemExit as e:
        if e.code != 0:
            print(f"🛑 门禁拦截: 转换被拒绝")
            sys.exit(1)

    state = load_state()

    # 更新状态
    found = False
    old_state = None
    for etype in ["epics", "specs", "stories"]:
        if entity in state["entities"].get(etype, {}):
            old_state = state["entities"][etype][entity]["state"]
            state["entities"][etype][entity]["state"] = target_state
            found = True
            break

    if not found:
        if entity in state.get("sprints", {}):
            old_state = state["sprints"][entity]["state"]
            state["sprints"][entity]["state"] = target_state
            found = True

    if not found:
        print(f"❌ 未找到实体: {entity}")
        sys.exit(1)

    # 记录历史
    log_entry = {
        "date": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "entity": entity,
        "from": old_state,
        "to": target_state,
        "action": "transition",
        "reason": reason or f"{entity}: {old_state} → {target_state}",
        "gate": "pre_flight"
    }
    if "history" not in state:
        state["history"] = []
    state["history"].append(log_entry)

    # 更新 project.updated
    state["project"]["updated"] = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    save_state(state)
    print(f"✅ 状态转换完成: {entity}: {old_state} → {target_state}")
    return True


def cmd_sync():
    """从文档同步状态到 YAML"""
    state = load_state()
    doc_states = get_doc_states()
    changes = []

    for eid, doc_s in doc_states["epics"].items():
        if eid in state["entities"]["epics"]:
            if state["entities"]["epics"][eid]["state"] != doc_s:
                changes.append(f"EPIC {eid}: {state['entities']['epics'][eid]['state']} → {doc_s}")
                state["entities"]["epics"][eid]["state"] = doc_s
        else:
            changes.append(f"EPIC {eid}: (新增) → {doc_s}")
            state["entities"]["epics"][eid] = {"state": doc_s, "title": "", "spec_count": 0,
                                                "story_count": 0, "completed_count": 0,
                                                "priority": "", "qa_gate_date": None, "review_date": None}

    for sid, doc_s in doc_states["specs"].items():
        if sid in state["entities"]["specs"]:
            if state["entities"]["specs"][sid]["state"] != doc_s:
                changes.append(f"SPEC {sid}: {state['entities']['specs'][sid]['state']} → {doc_s}")
                state["entities"]["specs"][sid]["state"] = doc_s
        else:
            changes.append(f"SPEC {sid}: (新增) → {doc_s}")
            state["entities"]["specs"][sid] = {"state": doc_s, "epic": "?", "stories": []}

    for stid, doc_s in doc_states["stories"].items():
        if stid in state["entities"]["stories"]:
            if state["entities"]["stories"][stid]["state"] != doc_s:
                changes.append(f"STORY {stid}: {state['entities']['stories'][stid]['state']} → {doc_s}")
                state["entities"]["stories"][stid]["state"] = doc_s
        else:
            changes.append(f"STORY {stid}: (新增) → {doc_s}")
            state["entities"]["stories"][stid] = {"state": doc_s, "epic": "?", "spec": "?"}

    if changes:
        print(f"📝 同步了 {len(changes)} 个变更:")
        for c in changes:
            print(f"  - {c}")
        save_state(state)
    else:
        print("✅ 已是最新，无需同步")
    return changes


def cmd_list(by_state=False, by_type=False):
    state = load_state()

    if by_state:
        # 按状态分组
        groups = {}
        for etype in ["epics", "specs", "stories"]:
            for eid, e in state["entities"].get(etype, {}).items():
                s = e["state"]
                if s not in groups:
                    groups[s] = []
                groups[s].append(f"{etype[:-1].upper()} {eid}")
        for s in sorted(groups.keys()):
            print(f"\n[{s}]")
            for item in sorted(groups[s]):
                print(f"  {item}")
    elif by_type:
        # 按类型分组
        for etype in ["epics", "specs", "stories"]:
            print(f"\n--- {etype.upper()} ---")
            for eid, e in sorted(state["entities"].get(etype, {}).items()):
                print(f"  {eid:14s} [{e['state']:10s}]")
    else:
        # 平铺
        for etype in ["epics", "specs", "stories"]:
            for eid, e in sorted(state["entities"].get(etype, {}).items()):
                print(f"{etype[:-1].upper():5s} {eid:14s} [{e['state']:10s}]")


def cmd_history():
    state = load_state()
    hist = state.get("history", [])
    if not hist:
        print("暂无历史记录")
        return
    for h in hist:
        frm = h.get('from') or '—'
        print(f"  {h.get('date','')} | {h['entity']:14s} | {frm:10s} → {h['to']:10s} | {h.get('reason','')}")


def init_state():
    """初始化状态文件"""
    if STATE_FILE.exists():
        print(f"⚠️  文件已存在: {STATE_FILE}")
        yn = input("  覆盖? (y/N): ")
        if yn.lower() != "y":
            print("  取消")
            return
    # 自动扫描文档
    doc_states = get_doc_states()
    print(f"  扫描到 {len(doc_states['epics'])} EPICs, {len(doc_states['specs'])} SPECs, {len(doc_states['stories'])} STORYS")
    print("  请使用 python3 scripts/project-state.py scan 同步状态")
    print("  或手动创建 docs/project-state.yaml")


# ─── 入口 ───

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(0)

    cmd = sys.argv[1]

    if cmd == "status":
        cmd_status()
    elif cmd == "verify":
        cmd_verify()
    elif cmd == "scan":
        drift = cmd_scan()
        sys.exit(1 if drift > 0 else 0)
    elif cmd == "gate":
        if len(sys.argv) < 4:
            print("用法: python3 scripts/project-state.py gate <entity> <target_state>")
            sys.exit(1)
        cmd_gate(sys.argv[2], sys.argv[3])
    elif cmd == "transition":
        if len(sys.argv) < 4:
            print("用法: python3 scripts/project-state.py transition <entity> <target_state> [reason]")
            sys.exit(1)
        reason = " ".join(sys.argv[4:]) if len(sys.argv) > 4 else ""
        cmd_transition(sys.argv[2], sys.argv[3], reason)
    elif cmd == "sync":
        cmd_sync()
    elif cmd == "list":
        kwargs = {}
        if "--by-state" in sys.argv:
            kwargs["by_state"] = True
        if "--by-type" in sys.argv:
            kwargs["by_type"] = True
        cmd_list(**kwargs)
    elif cmd == "history":
        cmd_history()
    elif cmd == "init":
        init_state()
    else:
        print(f"未知命令: {cmd}")
        print(__doc__)
        sys.exit(1)
