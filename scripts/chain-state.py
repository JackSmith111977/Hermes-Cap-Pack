#!/usr/bin/env python3
"""
chain-state.py — 工作流链状态机 (Workflow Chain Protocol v1.0)

链式衔接 SDD → DEV → QA → COMMIT 四个阶段。
每个 transition 通过 gate 检查后才能进入下一阶段。

用法:
  python3 scripts/chain-state.py status [epic-id]
      # 查看当前工作流链状态
  python3 scripts/chain-state.py list
      # 列出所有活跃链
  python3 scripts/chain-state.py start <epic-id> <stage>
      # 启动一个链的阶段
  python3 scripts/chain-state.py advance <epic-id>
      # 尝试推进到下一阶段（会跑 gate）
  python3 scripts/chain-state.py check <epic-id> <stage>
      # 检查是否可以进入某个阶段
  python3 scripts/chain-state.py reset <epic-id>
      # 重置链状态
"""
import os, sys, json, yaml, subprocess

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHAIN_FILE = os.path.join(PROJECT_DIR, 'docs', 'chain-state.json')


# ——— 默认链定义 ———
STAGE_ORDER = ['SPEC', 'DEV', 'QA', 'COMMIT']

STAGE_META = {
    'SPEC':   {'title': 'Spec 完成',    'entry_skill': 'sdd-workflow'},
    'DEV':    {'title': '开发实施',      'entry_skill': 'generic-dev-workflow'},
    'QA':     {'title': '质量门禁',      'entry_skill': 'generic-qa-workflow'},
    'COMMIT': {'title': '提交对齐',      'entry_skill': 'generic-dev-workflow'},
}

GATE_SCRIPTS = {
    'SPEC':   'scripts/spec-state.py',
    'DEV':    'scripts/chain-gate.py',
    'QA':     'scripts/ci-check-cross-refs.py',
}


def load_chain():
    if os.path.isfile(CHAIN_FILE):
        with open(CHAIN_FILE) as f:
            return json.load(f)
    return {}


def save_chain(data):
    os.makedirs(os.path.dirname(CHAIN_FILE), exist_ok=True)
    with open(CHAIN_FILE, 'w') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"✅ 已写入 {CHAIN_FILE}")


def get_chain(epic_id):
    chains = load_chain()
    return chains.get(epic_id, {
        'epic': epic_id,
        'current_stage': None,
        'completed_stages': [],
        'gate_history': [],
    })


def status(epic_id):
    chain = get_chain(epic_id)
    current = chain['current_stage']
    completed = set(chain['completed_stages'])
    gates = chain.get('gate_history', [])
    
    print(f"\n{'='*55}")
    print(f"  Workflow Chain: {epic_id}")
    print(f"{'='*55}\n")
    
    for stage in STAGE_ORDER:
        meta = STAGE_META[stage]
        if stage in completed:
            icon = '✅'
        elif stage == current:
            icon = '⏳'
        else:
            icon = '⏭️'
        
        print(f"  {icon} {stage:8s} | {meta['title']:12s} | skill: {meta['entry_skill']}")
    
    print(f"\n  门禁历史: {len(gates)} 次")
    for g in gates[-3:]:  # 最近 3 条
        print(f"    {g['stage']}: {'✅' if g['passed'] else '❌'} {g.get('message', '')}")
    
    return chain


def advance(epic_id, force=False):
    """尝试推进到下一阶段"""
    chain = get_chain(epic_id)
    current = chain['current_stage']
    completed = set(chain['completed_stages'])
    
    # 如果当前无阶段 → 从 SPEC 开始
    if current is None:
        return start(epic_id, 'SPEC')
    
    # 找到当前阶段索引
    if current not in STAGE_ORDER:
        print(f"❌ 未知阶段 '{current}'")
        return False
    
    idx = STAGE_ORDER.index(current)
    
    # 标记当前阶段完成
    if current not in completed:
        completed.add(current)
        chain['completed_stages'] = list(completed)
    
    # 进入下一阶段
    if idx + 1 < len(STAGE_ORDER):
        next_stage = STAGE_ORDER[idx + 1]
        
        # 跑 gate 检查
        if not force:
            ok, msg = run_gate(epic_id, next_stage)
            track_gate(chain, next_stage, ok, msg)
            if not ok:
                print(f"❌ Gate 阻止进入 {next_stage}: {msg}")
                print(f"   使用 --force 跳过 gate")
                save_chain({**load_chain(), epic_id: chain})
                return False
        
        chain['current_stage'] = next_stage
        meta = STAGE_META[next_stage]
        print(f"✅ 进入 {next_stage}: {meta['title']}")
        print(f"👉 加载 skill: {meta['entry_skill']}")
        print(f"   skill_view(name='{meta['entry_skill']}')")
    else:
        # 已经是 COMMIT，全部完成
        chain['current_stage'] = 'COMPLETED'
        print(f"🎉 工作流链全部完成！")
    
    save_chain({**load_chain(), epic_id: chain})
    return True


def run_gate(epic_id, stage):
    """运行指定阶段的 gate 检查"""
    if stage == 'SPEC':
        # 检查 spec-state
        result = subprocess.run(
            ['python3', 'scripts/spec-state.py', 'status', epic_id],
            capture_output=True, text=True,
            cwd=PROJECT_DIR, timeout=15
        )
        output = result.stdout + result.stderr
        if 'approved' in output or 'completed' in output or 'archived' in output:
            return True, "Spec/Story 已批准"
        return False, f"Spec 未批准: {output[:200]}"
    
    elif stage == 'DEV':
        # 检查测试
        result = subprocess.run(
            ['python3', '-m', 'pytest', 'tests/', '-q', '--tb=short'],
            capture_output=True, text=True,
            cwd=PROJECT_DIR, timeout=60
        )
        output = result.stdout + result.stderr
        if result.returncode == 0:
            return True, "测试全部通过"
        return False, f"测试失败: {output[:200]}"
    
    elif stage == 'QA':
        # 检查交叉引用
        result = subprocess.run(
            ['python3', 'scripts/ci-check-cross-refs.py'],
            capture_output=True, text=True,
            cwd=PROJECT_DIR, timeout=30
        )
        if result.returncode == 0:
            return True, "交叉引用检查通过"
        return False, f"交叉引用检查失败: {(result.stdout+result.stderr)[:200]}"
    
    elif stage == 'COMMIT':
        # 检查 project-state
        result = subprocess.run(
            ['python3', 'scripts/project-state.py', 'verify'],
            capture_output=True, text=True,
            cwd=PROJECT_DIR, timeout=30
        )
        if result.returncode == 0:
            return True, "项目状态一致"
        return False, f"状态不一致: {(result.stdout+result.stderr)[:200]}"
    
    return True, "无 gate 检查"


def track_gate(chain, stage, passed, message):
    """记录门禁检查结果"""
    chain.setdefault('gate_history', []).append({
        'stage': stage,
        'passed': passed,
        'message': message,
        'timestamp': __import__('datetime').datetime.now().isoformat()[:19]
    })


def start(epic_id, stage='SPEC'):
    """启动工作流链"""
    if stage not in STAGE_ORDER:
        print(f"❌ 无效阶段 '{stage}'，可选: {', '.join(STAGE_ORDER)}")
        return False
    
    chain = get_chain(epic_id)
    chain['current_stage'] = stage
    chain['completed_stages'] = []
    chain['gate_history'] = []
    
    meta = STAGE_META[stage]
    print(f"✅ 工作流链已启动: {epic_id} → {stage}")
    print(f"👉 加载 skill: skill_view(name='{meta['entry_skill']}')")
    
    save_chain({**load_chain(), epic_id: chain})
    return True


def check(epic_id, stage):
    """检查是否可以进入某个阶段"""
    idx = STAGE_ORDER.index(stage) if stage in STAGE_ORDER else -1
    if idx == -1:
        print(f"❌ 未知阶段 '{stage}'")
        return False
    
    if idx == 0:
        ok, msg = True, "阶段 0 无前置检查"
    else:
        ok, msg = run_gate(epic_id, stage)
    
    print(f"{'✅' if ok else '❌'} {stage}: {msg}")
    return ok


def reset(epic_id):
    """重置链状态"""
    chains = load_chain()
    if epic_id in chains:
        del chains[epic_id]
        save_chain(chains)
        print(f"✅ {epic_id} 链已重置")
    else:
        print(f"⏭️ {epic_id} 没有活跃链")
    return True


def list_chains():
    chains = load_chain()
    if not chains:
        print("ℹ️ 没有活跃的工作流链")
        return
    print(f"\n{'='*55}")
    print(f"  活跃工作流链 ({len(chains)} 条)")
    print(f"{'='*55}\n")
    for epic_id, chain in chains.items():
        current = chain.get('current_stage', '?')
        completed = len(chain.get('completed_stages', []))
        print(f"  {epic_id:25s} | 当前: {current:10s} | 已完成: {completed}/4")


def main():
    args = sys.argv[1:]
    if not args or '--help' in args:
        print(__doc__)
        return 0
    
    cmd = args[0]
    
    if cmd == 'status' and len(args) >= 2:
        status(args[1])
        return 0
    
    elif cmd == 'list':
        list_chains()
        return 0
    
    elif cmd == 'start' and len(args) >= 2:
        stage = args[2] if len(args) >= 3 else 'SPEC'
        return 0 if start(args[1], stage) else 1
    
    elif cmd == 'advance' and len(args) >= 2:
        force = '--force' in args
        return 0 if advance(args[1], force) else 1
    
    elif cmd == 'check' and len(args) >= 3:
        return 0 if check(args[1], args[2]) else 1
    
    elif cmd == 'reset' and len(args) >= 2:
        return 0 if reset(args[1]) else 1
    
    else:
        print(f"用法错误: {cmd}")
        print(__doc__)
        return 1


if __name__ == '__main__':
    sys.exit(main())
