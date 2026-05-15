#!/usr/bin/env python3
"""
chain-gate.py — 工作流链门禁检查器

用于 SDD→DEV→QA→COMMIT 各阶段的 gate 检查。
被 chain-state.py 内部调用，也可独立使用。

用法:
  python3 scripts/chain-gate.py check_spec <story-id>
  python3 scripts/chain-gate.py check_dev
  python3 scripts/chain-gate.py check_qa
  python3 scripts/chain-gate.py check_commit
"""
import os, sys, subprocess, json

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def check_spec(story_id=None):
    """检查 Story 是否已批准"""
    if not story_id:
        return False, "缺少 story_id"
    
    state_file = os.path.join(PROJECT_DIR, 'docs', 'project-state.yaml')
    # Check in project-state.yaml
    import yaml
    try:
        with open(state_file) as f:
            data = yaml.safe_load(f)
        stories = data.get('entities', {}).get('stories', {})
        story = stories.get(story_id, {})
        state = story.get('state', 'unknown')
        if state in ('approved', 'completed', 'archived'):
            return True, f"Story {story_id} 状态: {state}"
        else:
            return False, f"Story {story_id} 状态: {state}（需要 approved/completed/archived）"
    except Exception as e:
        return False, f"读取状态失败: {e}"


def check_dev():
    """检查开发完成条件：测试通过"""
    result = subprocess.run(
        ['python3', '-m', 'pytest', 'tests/', '-q', '--tb=short'],
        capture_output=True, text=True,
        cwd=PROJECT_DIR, timeout=60
    )
    if result.returncode == 0:
        return True, "✅ 测试全部通过"
    else:
        # Extract summary
        lines = result.stdout.strip().split('\n')
        summary = [l for l in lines if 'failed' in l or 'passed' in l or 'error' in l]
        return False, f"❌ 测试失败: {summary[-1] if summary else 'unknown'}"


def check_qa():
    """检查 QA 门禁：交叉引用 + 项目状态"""
    checks = []
    all_pass = True
    
    # Check 1: cross-ref
    r1 = subprocess.run(
        ['python3', 'scripts/ci-check-cross-refs.py'],
        capture_output=True, text=True,
        cwd=PROJECT_DIR, timeout=30
    )
    if r1.returncode == 0:
        checks.append(('cross-ref', True, '✅ 交叉引用通过'))
    else:
        checks.append(('cross-ref', False, f"❌ {r1.stdout.strip()[:100]}"))
        all_pass = False
    
    # Check 2: project-state
    r2 = subprocess.run(
        ['python3', 'scripts/project-state.py', 'verify'],
        capture_output=True, text=True,
        cwd=PROJECT_DIR, timeout=30
    )
    if r2.returncode == 0:
        checks.append(('project-state', True, '✅ 项目状态一致'))
    else:
        checks.append(('project-state', False, f"❌ {r2.stdout.strip()[:100]}"))
        all_pass = False
    
    summary = ' | '.join(m for _, _, m in checks)
    return all_pass, summary


def check_commit():
    """检查提交条件"""
    result = subprocess.run(
        ['git', 'status', '--short'],
        capture_output=True, text=True,
        cwd=PROJECT_DIR, timeout=10
    )
    changes = result.stdout.strip()
    if not changes:
        return True, "✅ 无未提交变更"
    else:
        lines = changes.split('\n')
        return True, f"ℹ️ {len(lines)} 个文件待提交"


def main():
    args = sys.argv[1:]
    if not args or '--help' in args:
        print(__doc__)
        return 0
    
    cmd = args[0]
    
    if cmd == 'check_spec':
        story_id = args[1] if len(args) > 1 else None
        ok, msg = check_spec(story_id)
    elif cmd == 'check_dev':
        ok, msg = check_dev()
    elif cmd == 'check_qa':
        ok, msg = check_qa()
    elif cmd == 'check_commit':
        ok, msg = check_commit()
    else:
        print(f"❌ 未知检查: {cmd}")
        return 1
    
    print(msg)
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
