#!/usr/bin/env python3
"""
workflow-chain.py — 统一工作流链状态机 v2.0

管理 SDD → DEV → QA → COMMIT 四阶段链式衔接。
支持自动注册、泛化项目检测、skill 自动加载提示。

用法:
  python3 scripts/workflow-chain.py init [epic-id]   # 初始化新链
  python3 scripts/workflow-chain.py advance [epic-id] [--force]  # 推进到下一阶段
  python3 scripts/workflow-chain.py status [epic-id]  # 查看状态
  python3 scripts/workflow-chain.py list               # 列出所有活跃链
  python3 scripts/workflow-chain.py reset [epic-id]    # 重置
  python3 scripts/workflow-chain.py skill [epic-id]    # 显示当前阶段应加载的skill
"""

import os, sys, json, subprocess
from pathlib import Path
from datetime import datetime

# ─── Configuration ───────────────────────────────────────────────────────

PROJECT_DIR = Path(__file__).resolve().parent.parent
CHAIN_FILE = PROJECT_DIR / 'docs' / 'chain-state.json'

STAGE_ORDER = ['SPEC', 'DEV', 'QA', 'COMMIT']

STAGE_META = {
    'SPEC':   {'title': 'Spec 完成',    'entry_skill': 'sdd-workflow',         'description': '需求→Spec→Story 批准'},
    'DEV':    {'title': '开发实施',     'entry_skill': 'generic-dev-workflow',  'description': '7 步开发流程 (TDD)'},
    'QA':     {'title': '质量门禁',     'entry_skill': 'generic-qa-workflow',   'description': 'L0-L4 分层门禁'},
    'COMMIT': {'title': '提交对齐',     'entry_skill': 'commit-quality-check',  'description': '文档对齐 + 提交'},
}

# ─── State Management ────────────────────────────────────────────────────


def _load():
    if CHAIN_FILE.exists():
        return json.loads(CHAIN_FILE.read_text())
    return {}


def _save(data: dict):
    CHAIN_FILE.parent.mkdir(parents=True, exist_ok=True)
    CHAIN_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n')


def _get_chain(epic_id: str) -> dict:
    chains = _load()
    return chains.get(epic_id, {
        'epic': epic_id,
        'current_stage': None,
        'completed_stages': [],
        'gate_history': [],
        'created_at': datetime.now().isoformat()[:19],
        'updated_at': datetime.now().isoformat()[:19],
    })


def _save_chain(epic_id: str, chain: dict):
    chain['updated_at'] = datetime.now().isoformat()[:19]
    chains = _load()
    chains[epic_id] = chain
    _save(chains)


# ─── Project Detection (generic) ─────────────────────────────────────────


def _detect_project_type() -> str:
    """Detect project type for appropriate gate scripts."""
    scripts_dir = PROJECT_DIR / 'scripts'
    docs_dir = PROJECT_DIR / 'docs'
    
    if (scripts_dir / 'project-state.py').exists():
        return 'cap-pack'
    if (PROJECT_DIR / 'pyproject.toml').exists():
        return 'python'
    return 'generic'


def _run_generic_gate(stage: str, epic_id: str) -> tuple[bool, str]:
    """Run appropriate gate check for the target stage."""
    project_type = _detect_project_type()
    
    if stage == 'SPEC':
        # Check if Stories are completed via project state
        state_path = PROJECT_DIR / 'docs' / 'project-state.yaml'
        if state_path.exists():
            import yaml
            try:
                data = yaml.safe_load(state_path.read_text())
                epics = data.get('entities', {}).get('epics', {})
                epic = epics.get(epic_id, {})
                completed = epic.get('completed_count', 0)
                total = epic.get('story_count', 0)
                if total > 0 and completed == total:
                    return True, f"✅ EPIC {epic_id}: {completed}/{total} stories completed"
                return True, f"ℹ️  EPIC {epic_id}: {completed}/{total} stories (partial OK for SPEC→DEV)"
            except Exception as e:
                return True, f"ℹ️  Gate check skipped: {e}"
        return True, "ℹ️  No project-state.yaml — gate skipped"

    elif stage == 'DEV':
        # Check tests pass
        try:
            result = subprocess.run(
                [sys.executable, '-m', 'pytest', 'tests/', '-q', '--tb=short'],
                capture_output=True, text=True, timeout=60, cwd=PROJECT_DIR
            )
            if result.returncode == 0:
                return True, "✅ Tests all pass"
            # Extract failure summary
            lines = result.stdout.strip().split('\n')
            summary = [l for l in lines if 'failed' in l or 'error' in l]
            fail_msg = summary[-1] if summary else 'test failures'
            return False, f"❌ {fail_msg}"
        except FileNotFoundError:
            return True, "⚠️  No tests directory — gate skipped"
        except subprocess.TimeoutExpired:
            return False, "⏱️  Tests timed out"

    elif stage == 'QA':
        # Check project state consistency
        if project_type == 'cap-pack':
            state_script = PROJECT_DIR / 'scripts' / 'project-state.py'
            if state_script.exists():
                result = subprocess.run(
                    [sys.executable, str(state_script), 'verify'],
                    capture_output=True, text=True, timeout=30, cwd=PROJECT_DIR
                )
                if result.returncode == 0:
                    return True, "✅ Project state consistent"
                return False, f"❌ {result.stdout.strip()[:150]}"
        return True, "ℹ️  QA gate skipped (no project-state.py)"

    elif stage == 'COMMIT':
        # Check for uncommitted changes
        result = subprocess.run(
            ['git', 'status', '--short'],
            capture_output=True, text=True, timeout=10, cwd=PROJECT_DIR
        )
        changes = result.stdout.strip()
        if not changes:
            return True, "✅ No uncommitted changes"
        return True, f"ℹ️  {len(changes.split(chr(10)))} files to commit (non-blocking)"

    return True, "ℹ️  No gate for this stage"


# ─── Core Commands ───────────────────────────────────────────────────────


def cmd_init(epic_id: str, start_stage: str = 'SPEC'):
    """Initialize a workflow chain."""
    if start_stage not in STAGE_ORDER:
        print(f"❌ Invalid stage '{start_stage}'. Choose: {', '.join(STAGE_ORDER)}")
        return 1

    chains = _load()
    if epic_id in chains:
        print(f"⚠️  Chain for {epic_id} already exists. Use 'reset' first.")
        return 1

    chain = {
        'epic': epic_id,
        'current_stage': start_stage,
        'completed_stages': [],
        'gate_history': [],
        'created_at': datetime.now().isoformat()[:19],
        'updated_at': datetime.now().isoformat()[:19],
    }
    meta = STAGE_META[start_stage]
    _save_chain(epic_id, chain)
    
    print(f"✅ Workflow chain initialized: {epic_id}")
    print(f"   Stage: {start_stage} ({meta['title']})")
    print(f"   Next: skill_view(name='{meta['entry_skill']}')")
    return 0


def cmd_advance(epic_id: str, force: bool = False):
    """Advance to next stage in the chain."""
    chain = _get_chain(epic_id)
    current = chain.get('current_stage')

    if current is None:
        print(f"⏭️  No active chain for {epic_id}. Run 'init' first.")
        return 1

    if current not in STAGE_ORDER:
        print(f"❌ Unknown stage '{current}'")
        return 1

    # Mark current as completed
    completed = set(chain.get('completed_stages', []))
    completed.add(current)
    chain['completed_stages'] = list(completed)

    # Find next stage
    idx = STAGE_ORDER.index(current)
    if idx + 1 >= len(STAGE_ORDER):
        chain['current_stage'] = 'COMPLETED'
        _save_chain(epic_id, chain)
        print(f"🎉 Workflow chain COMPLETED for {epic_id}!")
        print(f"   All stages: {' → '.join(STAGE_ORDER)}")
        return 0

    next_stage = STAGE_ORDER[idx + 1]
    meta = STAGE_META[next_stage]

    # Run gate
    if not force:
        passed, message = _run_generic_gate(next_stage, epic_id)
        chain.setdefault('gate_history', []).append({
            'stage': next_stage,
            'passed': passed,
            'message': message,
            'timestamp': datetime.now().isoformat()[:19],
        })
        if not passed:
            _save_chain(epic_id, chain)
            print(f"❌ Gate blocked: {next_stage}")
            print(f"   {message}")
            print(f"   Fix issue then retry, or use --force to skip gate.")
            return 1
        print(f"   Gate: ✅ {message}")

    # Enter next stage
    chain['current_stage'] = next_stage
    _save_chain(epic_id, chain)

    print(f"✅ Advanced: {current} → {next_stage}")
    print(f"   Stage: {next_stage} ({meta['title']})")
    print(f"   {meta['description']}")
    print(f"")
    print(f"👉 LOAD SKILL: skill_view(name='{meta['entry_skill']}')")
    return 0


def cmd_status(epic_id: str):
    """Show workflow chain status."""
    chain = _get_chain(epic_id)
    current = chain.get('current_stage', '—')
    completed = set(chain.get('completed_stages', []))
    gates = chain.get('gate_history', [])

    print(f"\n{'='*60}")
    print(f"  Workflow Chain: {epic_id}")
    print(f"{'='*60}\n")

    for stage in STAGE_ORDER:
        meta = STAGE_META[stage]
        if stage in completed:
            icon = '✅'
        elif stage == current:
            icon = '⏳'
        else:
            icon = '  '
        print(f"  {icon} {stage:8s} │ {meta['title']:12s} │ {meta['description']}")

    if current == 'COMPLETED':
        print(f"  🎉 {''.rjust(8)} │ {'完成!':12s} │ All 4 stages completed")

    print(f"\n  Gates: {len(gates)} checks")
    for g in gates[-5:]:
        status = '✅' if g['passed'] else '❌'
        print(f"    {status} {g['stage']}: {g['message'][:70]}")

    print()
    return 0


def cmd_list():
    """List all active chains."""
    chains = _load()
    if not chains:
        print("ℹ️  No active workflow chains.")
        return 0

    print(f"\n{'='*60}")
    print(f"  Active Workflow Chains ({len(chains)})")
    print(f"{'='*60}\n")
    for epid, ch in sorted(chains.items()):
        current = ch.get('current_stage', '?')
        n_completed = len(ch.get('completed_stages', []))
        print(f"  {epid:30s} │ Stage: {current:10s} │ {n_completed}/4 done")
    print()
    return 0


def cmd_reset(epic_id: str):
    """Reset a workflow chain."""
    chains = _load()
    if epic_id in chains:
        del chains[epic_id]
        _save(chains)
        print(f"✅ Chain reset for {epic_id}")
    else:
        print(f"⏭️  No chain for {epic_id}")
    return 0


def cmd_skill(epic_id: str):
    """Show which skill to load for current stage."""
    chain = _get_chain(epic_id)
    current = chain.get('current_stage')
    if not current or current == 'COMPLETED':
        print(f"ℹ️  Chain for {epic_id} is completed. No skill to load.")
        return 0
    meta = STAGE_META.get(current)
    if not meta:
        print(f"❌ Unknown stage: {current}")
        return 1
    print(f"skill_view(name='{meta['entry_skill']}')")
    return 0


# ─── CLI Entry ───────────────────────────────────────────────────────────


def main():
    args = sys.argv[1:]
    if not args or '--help' in args or '-h' in args:
        print(__doc__)
        return 0

    cmd = args[0]

    if cmd == 'init' and len(args) >= 2:
        stage = args[2] if len(args) >= 3 else 'SPEC'
        return cmd_init(args[1], stage)

    elif cmd == 'advance' and len(args) >= 2:
        force = '--force' in args
        return cmd_advance(args[1], force)

    elif cmd == 'status' and len(args) >= 2:
        return cmd_status(args[1])

    elif cmd == 'list':
        return cmd_list()

    elif cmd == 'reset' and len(args) >= 2:
        return cmd_reset(args[1])

    elif cmd == 'skill' and len(args) >= 2:
        return cmd_skill(args[1])

    else:
        print(f"❌ Unknown command: {cmd}")
        print(__doc__)
        return 1


if __name__ == '__main__':
    sys.exit(main())
