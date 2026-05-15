#!/usr/bin/env python3
"""
phase-gate.py — SDD Phase 门禁检查器

用途: 确保 SDD 流程中的 Phase 按顺序推进，禁止跳过未完成的 Phase。

用法:
  python3 scripts/phase-gate.py check <epic-id> <target-phase>
      # 检查是否可以从当前 Phase 进入 target-phase
  python3 scripts/phase-gate.py list <epic-id>
      # 列出指定 Epic 的所有 Phase 状态
  python3 scripts/phase-gate.py complete <epic-id> <phase>
      # 标记某个 Phase 为已完成
  python3 scripts/phase-gate.py start <epic-id> <phase>
      # 开始某个 Phase（会先执行 check）

依赖:
  - docs/project-state.yaml (phases 字段)
  - spec-state.py (检查 Spec/Story 完成度)
"""
import os, sys, yaml, json

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATE_PATH = os.path.join(PROJECT_DIR, 'docs', 'project-state.yaml')
WORKFLOW = os.path.join(PROJECT_DIR, 'docs', 'project-state.yaml')


def load_yaml():
    with open(STATE_PATH) as f:
        return yaml.safe_load(f)


def save_yaml(data):
    with open(STATE_PATH, 'w') as f:
        yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)


def get_epic_phases(data, epic_id):
    """获取 Epic 的 phases 定义"""
    epics = data.get('entities', {}).get('epics', {})
    epic = epics.get(epic_id)
    if not epic:
        return None, f"Epic {epic_id} 不存在"
    
    # Get phases from epic definition or from project-level phases block
    all_phases = data.get('phases', {})
    epic_phases_config = all_phases.get(epic_id)
    
    return epic, epic_phases_config


def check_phase_transition(data, epic_id, target_phase):
    """检查是否可以从当前状态进入目标 Phase"""
    epic = data.get('entities', {}).get('epics', {}).get(epic_id)
    if not epic:
        return False, f"Epic {epic_id} 不存在"
    
    all_phases = data.get('phases', {})
    phase_config = all_phases.get(epic_id)
    if not phase_config:
        return False, f"Epic {epic_id} 没有 Phase 配置"
    
    phases = phase_config.get('phases', [])
    completed_phases = set(phase_config.get('completed_phases', []))
    
    # 检查目标 Phase 是否存在
    phase_names = [p.get('name', p.get('id', '')) for p in phases]
    if target_phase not in phase_names:
        return False, f"Phase '{target_phase}' 不在 Epic {epic_id} 的定义中 (可用: {', '.join(phase_names)})"
    
    # 找到目标 Phase 的索引
    target_idx = phase_names.index(target_phase)
    
    # 前置检查：上一个 Phase 必须已完成
    # 只有 Phase 0 可以没有前置
    if target_idx > 0:
        prev_phase = phase_names[target_idx - 1]
        if prev_phase not in completed_phases:
            return False, f"前置 Phase '{prev_phase}' 未完成！必须先完成该 Phase"
    
    # 检查目标 Phase 是否已全部完成（跳过已完成）
    if target_phase in completed_phases:
        return False, f"Phase '{target_phase}' 已经完成"
    
    return True, f"允许进入 Phase '{target_phase}'"


def get_current_phase(phase_config):
    """计算当前处于哪个 Phase"""
    phases = phase_config.get('phases', [])
    completed = set(phase_config.get('completed_phases', []))
    current_idx = -1
    for i, p in enumerate(phases):
        pname = p.get('name', p.get('id', ''))
        if pname not in completed:
            current_idx = i
            break
    if current_idx == -1:
        return 'all_completed'
    return phases[current_idx].get('name', phases[current_idx].get('id', ''))


def list_phases(data, epic_id):
    """列出 Epic 的所有 Phase 状态"""
    epic = data.get('entities', {}).get('epics', {}).get(epic_id)
    if not epic:
        return f"Epic {epic_id} 不存在"
    
    all_phases = data.get('phases', {})
    phase_config = all_phases.get(epic_id)
    if not phase_config:
        return f"Epic {epic_id} 没有 Phase 配置"
    
    phases = phase_config.get('phases', [])
    completed = set(phase_config.get('completed_phases', []))
    current = get_current_phase(phase_config)
    
    lines = [f"Epic {epic_id}: {epic.get('title', '')}"]
    lines.append(f"状态: {epic.get('state', '?')}")
    lines.append(f"当前 Phase: {current}")
    lines.append("")
    
    for i, p in enumerate(phases):
        pname = p.get('name', p.get('id', ''))
        status = '✅' if pname in completed else ('⏳' if pname == current else '⏭️')
        ac = p.get('acceptance_criteria', [])
        lines.append(f"  {status} Phase {i}: {pname}")
        for a in ac:
            lines.append(f"       AC: {a}")
    
    return '\n'.join(lines)


def mark_phase_complete(data, epic_id, phase_name):
    """标记 Phase 为已完成"""
    all_phases = data.get('phases', {})
    phase_config = all_phases.get(epic_id)
    if not phase_config:
        return False, f"Epic {epic_id} 没有 Phase 配置"
    
    phases = phase_config.get('phases', [])
    phase_names = [p.get('name', p.get('id', '')) for p in phases]
    
    if phase_name not in phase_names:
        return False, f"Phase '{phase_name}' 不在定义中"
    
    completed = set(phase_config.get('completed_phases', []))
    if phase_name in completed:
        return False, f"Phase '{phase_name}' 已完成"
    
    # 前置检查
    ok, msg = check_phase_transition(data, epic_id, phase_name)
    if not ok:
        return False, msg
    
    # 检查 AC
    idx = phase_names.index(phase_name)
    phase_def = phases[idx]
    ac_list = phase_def.get('acceptance_criteria', [])
    unchecked = [a for a in ac_list if not a.get('done', False)]
    if unchecked:
        return False, f"Phase '{phase_name}' 有未完成的 AC: {', '.join(unchecked)}"
    
    # 标记完成
    phase_config.setdefault('completed_phases', []).append(phase_name)
    data['phases'][epic_id] = phase_config
    save_yaml(data)
    return True, f"Phase '{phase_name}' 已完成"


def start_phase(data, epic_id, phase_name):
    """开始一个 Phase（先检查再标记）"""
    ok, msg = check_phase_transition(data, epic_id, phase_name)
    if not ok:
        return False, msg
    
    all_phases = data.get('phases', {})
    phase_config = all_phases.get(epic_id)
    phases = phase_config.get('phases', [])
    phase_names = [p.get('name', p.get('id', '')) for p in phases]
    idx = phase_names.index(phase_name)
    phase_def = phases[idx]
    
    return True, f"Phase '{phase_name}' 已就绪，可以开始。本 Phase 需要: {', '.join(phase_def.get('requires', []))}"


def main():
    args = sys.argv[1:]
    if not args or '--help' in args:
        print(__doc__)
        return 0
    
    cmd = args[0]
    data = load_yaml()
    
    if cmd == 'check' and len(args) >= 3:
        ok, msg = check_phase_transition(data, args[1], args[2])
        print('✅' if ok else '❌', '—' if ok else '', msg)
        return 0 if ok else 1
    
    elif cmd == 'list' and len(args) >= 2:
        print(list_phases(data, args[1]))
        return 0
    
    elif cmd == 'complete' and len(args) >= 3:
        ok, msg = mark_phase_complete(data, args[1], args[2])
        print('✅' if ok else '❌', msg)
        return 0 if ok else 1
    
    elif cmd == 'start' and len(args) >= 3:
        ok, msg = start_phase(data, args[1], args[2])
        print('✅' if ok else '❌', msg)
        return 0 if ok else 1
    
    else:
        print(f"用法错误: {cmd}")
        print(__doc__)
        return 1


if __name__ == '__main__':
    sys.exit(main())
