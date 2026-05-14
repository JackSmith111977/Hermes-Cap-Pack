#!/usr/bin/env python3
"""
pre-flight-enhancer.py — skill-quality 前置检测增强器

作用: 增强 pre_flight.py 的 skill 操作检测能力
- 通过任务描述分析是否涉及 skill 文件操作
- 检测 write_file/patch 路径是否指向 skill 目录
- 输出结构化结果供 pre_flight.py 或 boku 消费

用法:
  python3 pre-flight-enhancer.py "更新 pdf-layout skill 的字体配置"
  python3 pre-flight-enhancer.py --task "写一个新 skill" --json

集成方式:
  从 pre_flight.py 调用: python3 pre-flight-enhancer.py "$TASK" --json
  作为独立预检: python3 pre-flight-enhancer.py "删除 skill xxx" --gate
"""

import json, os, sys, re, subprocess
from pathlib import Path


def find_skill_quality_scripts() -> Path:
    """Locate the skill-quality scripts directory."""
    candidates = [
        Path(__file__).parent,                                   # same dir
        Path.home() / ".hermes" / "cap-packs" / "skill-quality" / "scripts",
        Path.home() / "projects" / "hermes-cap-pack" / "packs" / "skill-quality" / "scripts",
    ]
    for c in candidates:
        if (c / "hermes-locate.py").exists():
            return c
    return Path(__file__).parent


def detect_skill_path_patterns(task: str) -> dict:
    """Analyze task description for skill-related path patterns.

    Returns structured info about what kind of skill operation is detected.
    """
    task_lower = task.lower()
    result = {
        "is_skill_operation": False,
        "operation_type": None,       # create | edit | delete | install | unknown
        "detected_skill_name": None,
        "detected_paths": [],
        "matches_skill_dir": False,
        "confidence": 0.0,           # 0.0 - 1.0
    }

    # ---- Pattern 1: Explicit skill_manage keywords ----
    crud_patterns = [
        (r'(?:create|新建|创建|编辑|更新|修改).*?(?:skill|技能)', "edit"),
        (r'(?:delete|删除|移除).*?(?:skill|技能)', "delete"),
        (r'skill_manage', "unknown"),
        (r'(?:patch|fix|优化).*skill', "edit"),
    ]

    for pattern, op_type in crud_patterns:
        if re.search(pattern, task_lower):
            result["is_skill_operation"] = True
            if result["operation_type"] in (None, "unknown"):
                result["operation_type"] = op_type
            result["confidence"] = max(result["confidence"], 0.8)
            break

    # ---- Pattern 2: Skill name detection ----
    skill_name_patterns = [
        r'(?:skill|技能)\s*[`\'】]?\s*([a-z][a-z0-9-]+(?:skill)?)',
        r'(?:更新|编辑|修改|优化|创建|删除)\s*([a-z][a-z0-9-]{3,48}[a-z0-9])',
        r'([a-z][a-z0-9-]{3,48}[a-z0-9])',
    ]
    for pattern in skill_name_patterns:
        match = re.search(pattern, task_lower)
        if match:
            candidate = match.group(1)
            # Verify it looks like a real skill name
            if re.match(r'^[a-z][a-z0-9-]+$', candidate) and len(candidate) > 2:
                # Check if skill directory exists
                for base in [
                    Path.home() / ".hermes" / "skills",
                    Path.home() / ".hermes" / "profiles",
                ]:
                    for sk_dir in [base / candidate] + list(base.glob(f"*/{candidate}")):
                        if sk_dir.exists() and (sk_dir / "SKILL.md").exists():
                            result["detected_skill_name"] = candidate
                            result["detected_paths"].append(str(sk_dir / "SKILL.md"))
                            result["matches_skill_dir"] = True
                            result["confidence"] = max(result["confidence"], 0.9)
                            break
                    if result["detected_skill_name"]:
                        break
            if result["detected_skill_name"]:
                break

    # ---- Pattern 3: Path-level detection ----
    path_patterns = [
        r'(?:~/?\.hermes|\.hermes)/skills/[\w/-]+/SKILL\.md',
        r'(?:~/?\.hermes|\.hermes)/skills/[\w/-]+(?:/SKILL\.md)?',
        r'skills/[\w/-]+/SKILL\.md',
    ]
    for pattern in path_patterns:
        match = re.search(pattern, task)
        if match:
            result["detected_paths"].append(match.group(0))
            result["matches_skill_dir"] = True
            result["is_skill_operation"] = True
            if result["operation_type"] is None:
                result["operation_type"] = "edit"
            result["confidence"] = max(result["confidence"], 0.85)

    # ---- Pattern 4: File write to skill dir (from write_file/patch args) ----
    write_patterns = [
        r'write_file\([\s\S]{0,50}hermes/skills/',
        r'patch\([\s\S]{0,50}hermes/skills/',
        r'SKILL\.md',
    ]
    for pattern in write_patterns:
        if re.search(pattern, task):
            result["matches_skill_dir"] = True
            result["is_skill_operation"] = True
            result["confidence"] = max(result["confidence"], 0.9)
            break

    return result


def check_existing_detection(task: str) -> dict:
    """Check what the current pre_flight.py would detect (simulate its regex)."""
    # Replicate pre_flight patterns
    pattern_map = {
        "skill_create": r'skill.*(?:create|新建|创建)',
        "skill_edit": r'skill.*(?:edit|编辑|更新|修改)',
        "skill_delete": r'skill.*(?:delete|删除)',
        "skill_manage": r'skill_manage',
        "skill_optimize": r'优化.*skill|skill.*优化',
        "skill_eval": r'评估.*skill|skill.*eval',
    }
    found = []
    for op_type, pattern in pattern_map.items():
        if re.search(pattern, task.lower()):
            found.append(op_type)
    return {"pre_flight_would_detect": found, "would_miss": []}


def get_recommendation(analysis: dict, preflight: dict) -> dict:
    """Generate actionable recommendation."""
    ops = []
    if analysis["is_skill_operation"]:
        if analysis["operation_type"] in ("create", "edit"):
            ops.append("加载 skill-creator: skill_view(name='skill-creator')")
            ops.append("运行依赖扫描: python3 scripts/dependency-scan.py")
        if analysis["operation_type"] == "delete":
            ops.append("加载 skill-creator 检查引用链")
            ops.append("运行引用分析: python3 scripts/dependency-scan.py --target <name>")
        if analysis.get("matches_skill_dir"):
            ops.append("检测到 skill 目录路径操作 — 建议使用 skill_manage 而非直接 write_file/patch")
    
    # Missing detection? 
    misses = []
    if "skill_manage" in analysis.get("detected_paths", []) and "skill_manage" not in preflight.get("pre_flight_would_detect", []):
        misses.append("pre_flight 未匹配到 skill_manage 操作")
    if analysis.get("matches_skill_dir") and not preflight.get("pre_flight_would_detect"):
        misses.append("pre_flight 未检测到 skill 目录操作（路径级别）")
    
    return {
        "needs_intervention": len(ops) > 0,
        "actions": ops,
        "pre_flight_gaps": misses,
        "severity": "high" if analysis.get("matches_skill_dir") else "medium",
    }


def gate_check(task: str) -> dict:
    """Gate mode: return actionable pass/fail with suggestions.
    
    This is the main entry point for integration.
    """
    analysis = detect_skill_path_patterns(task)
    preflight = check_existing_detection(task)
    recommendation = get_recommendation(analysis, preflight)
    
    return {
        "gate": "pre-flight-enhancer",
        "passed": not analysis["is_skill_operation"] or analysis["detected_skill_name"] is not None,
        "analysis": analysis,
        "pre_flight_simulation": preflight,
        "recommendation": recommendation,
    }


def main():
    import argparse
    parser = argparse.ArgumentParser(description="skill-quality pre-flight enhancer")
    parser.add_argument("task", nargs="?", default="", help="Task description to analyze")
    parser.add_argument("--task", dest="task2", help="Alternative task argument")
    parser.add_argument("--json", action="store_true", help="JSON output")
    parser.add_argument("--gate", action="store_true", help="Gate mode (exit 1 if blocked)")
    args = parser.parse_args()

    task = args.task or args.task2 or ""
    if not task:
        parser.print_help()
        sys.exit(1)

    result = gate_check(task)

    if args.json or args.gate:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        a = result["analysis"]
        print(f"{'='*50}")
        print(f"  🔍 Pre-flight Enhancer")
        print(f"{'='*50}")
        print(f"  Skill Operation: {'✅ Yes' if a['is_skill_operation'] else '❌ No'}")
        print(f"  Type:            {a.get('operation_type', '?')}")
        print(f"  Skill Name:      {a.get('detected_skill_name', '?')}")
        print(f"  Confidence:      {a['confidence']:.0%}")
        print(f"  Path Match:      {'✅' if a.get('matches_skill_dir') else '❌'}")
        print(f"\n  📋 Recommended Actions:")
        for action in result["recommendation"]["actions"]:
            print(f"    • {action}")
        if result["recommendation"]["pre_flight_gaps"]:
            print(f"\n  ⚠️  pre_flight Gaps:")
            for gap in result["recommendation"]["pre_flight_gaps"]:
                print(f"    • {gap}")

    if args.gate and result["recommendation"]["needs_intervention"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
