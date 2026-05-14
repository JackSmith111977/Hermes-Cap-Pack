#!/usr/bin/env python3
"""
complete-extraction.py — 能力包提取完成仪式

当模块提取完成后，统一更新所有文档制品：
1. project-state.yaml — 设置 Story 状态为 completed
2. STORY-3-*.md — 更新 frontmatter 状态为 completed
3. project-state.py verify — 验证一致性
4. validate-readme.py — 验证 README 对齐

用法:
    python3 scripts/complete-extraction.py <module-name>
    python3 scripts/complete-extraction.py list           # 列出待完成的模块

示例:
    python3 scripts/complete-extraction.py media-processing
    python3 scripts/complete-extraction.py --all          # 全部完成
"""

import sys
import re
import os
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
STATE_FILE = PROJECT_DIR / "docs" / "project-state.yaml"
STORY_DIR = PROJECT_DIR / "docs" / "stories"

# ── 已知的 Story 编号映射 ──
# 从 EPIC-003 全景路线图提取
STORY_MAP = {
    "agent-orchestration": "STORY-3-7",
    "devops-monitor":      "STORY-3-8",
    "security-audit":      "STORY-3-9",
    "media-processing":    "STORY-3-10",
    "mcp-integration":     "STORY-3-11",
    "network-proxy":       "STORY-3-12",
    "news-research":       "STORY-3-13",
    "financial-analysis":  "STORY-3-14",
    "social-gaming":       "STORY-3-15",
}


def load_state():
    import yaml
    with open(STATE_FILE) as f:
        return yaml.safe_load(f)


def save_state(state):
    import yaml
    with open(STATE_FILE, "w") as f:
        yaml.dump(state, f, default_flow_style=False, allow_unicode=True, sort_keys=False)


def list_pending():
    """列出 project-state 中仍为 approved 的 Story"""
    state = load_state()
    pending = []
    for stid, st in state["entities"]["stories"].items():
        if st["state"] == "approved":
            pending.append((stid, st.get("spec", "?"), st.get("epic", "?")))
    return pending


def complete_module(module_name, dry_run=False):
    """完成一个模块的提取仪式"""
    story_id = STORY_MAP.get(module_name)
    if not story_id:
        print(f"❌ 未知模块: {module_name}")
        print(f"   已知模块: {', '.join(sorted(STORY_MAP.keys()))}")
        return False

    changes = []

    # 1. 更新 project-state.yaml
    state = load_state()
    if story_id in state["entities"]["stories"]:
        old_state = state["entities"]["stories"][story_id]["state"]
        if old_state in ("approved", "implemented"):
            state["entities"]["stories"][story_id]["state"] = "completed"
            changes.append(f"📋 project-state: {story_id} {old_state} → completed")
    else:
        changes.append(f"⚠️  project-state: {story_id} 未注册")

    # 2. 更新 story doc 文件 frontmatter
    story_file = STORY_DIR / f"{story_id}.md"
    if story_file.exists():
        content = story_file.read_text()
        new_content, count = re.subn(
            r'(\*\*状态\*\*:\s*)`(\w+)`',
            r'\1`completed`',
            content
        )
        if count > 0:
            changes.append(f"📝 {story_id}.md: 状态 → completed")
            if not dry_run:
                story_file.write_text(new_content)
    else:
        changes.append(f"⚠️  {story_id}.md 文件不存在")

    # 保存 state
    if not dry_run:
        save_state(state)

    # 报告
    for c in changes:
        print(f"  {c}")
    print(f"  {'✅' if not dry_run else '🔍'} 完成")

    return True


def cmd_verify():
    """运行一致性验证"""
    print("\n  🔍 运行 project-state.py verify...\n")
    import subprocess
    r = subprocess.run(
        [sys.executable, "scripts/project-state.py", "verify"],
        cwd=PROJECT_DIR,
        capture_output=True, text=True
    )
    print(r.stdout)
    if r.returncode != 0:
        print(r.stderr)
        print("  ❌ 验证失败")
        return False
    print("  ✅ 一致性验证通过")
    return True


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "list":
        pending = list_pending()
        if pending:
            print(f"📋 待完成的 Story ({len(pending)}):")
            for stid, spec, epic in pending:
                print(f"  {stid} (spec={spec}, epic={epic})")
        else:
            print("✅ 所有 Story 状态已对齐")
        return

    if cmd == "--all":
        pending = [s[0] for s in list_pending()]
        if not pending:
            print("✅ 没有待完成的模块")
            return
        # 反向映射 story_id → module_name
        reverse_map = {v: k for k, v in STORY_MAP.items()}
        for stid in pending:
            module = reverse_map.get(stid, stid)
            print(f"\n{'='*50}")
            print(f"  完成 {module} ({stid})")
            print(f"{'='*50}")
            complete_module(module)
        cmd_verify()
        return

    if cmd in ("--help", "-h"):
        print(__doc__)
        return

    # 完成指定模块
    module_name = cmd
    if module_name not in STORY_MAP:
        print(f"❌ 未知模块: {module_name}")
        print(f"   已知: {', '.join(sorted(STORY_MAP.keys()))}")
        sys.exit(1)

    print(f"\n{'='*50}")
    print(f"  完成模块: {module_name}")
    print(f"{'='*50}")
    complete_module(module_name)
    cmd_verify()


if __name__ == "__main__":
    main()
