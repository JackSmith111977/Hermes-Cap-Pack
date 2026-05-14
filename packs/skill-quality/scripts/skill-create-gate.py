#!/usr/bin/env python3
"""
skill-create-gate.py — 创建 skill 前质量门禁
作用: 检查目标名称是否冲突、目录是否存在、是否需走 skill-creator 流程
用法:
  python3 skill-create-gate.py "my-new-skill"
  python3 skill-create-gate.py "my-new-skill" --json
  python3 skill-create-gate.py --check "my-new-skill"
退出码: 0=通过, 1=阻塞
"""

import json, os, sys, re
from pathlib import Path


def check_skill_name(name: str) -> dict:
    """Validate skill name and check for conflicts."""
    HERMES_HOME = Path(os.environ.get("HERMES_HOME", Path.home() / ".hermes"))
    issues = []
    warnings = []
    
    # 1. Name validation
    if not re.match(r'^[a-z][a-z0-9._-]*$', name):
        issues.append(f"Skill name '{name}' has invalid characters. Use: [a-z][a-z0-9._-]*")
    if len(name) > 64:
        issues.append(f"Skill name too long ({len(name)} > 64 chars)")
    if len(name) < 2:
        issues.append("Skill name too short (min 2 chars)")
    
    # 2. Check all known skills directories for conflicts
    search_dirs = [HERMES_HOME / "skills"]
    profiles_dir = HERMES_HOME / "profiles"
    if profiles_dir.exists():
        for p in profiles_dir.iterdir():
            if p.is_dir() and not p.name.startswith("."):
                search_dirs.append(p / "skills")
    
    for sd in search_dirs:
        if not sd.exists():
            continue
        for d in sd.iterdir():
            if d.is_dir() and d.name == name:
                issues.append(f"Conflict: skill '{name}' already exists at {d}")
                break
            # Check within category directories
            if d.is_dir():
                for sub in d.iterdir():
                    if sub.is_dir() and sub.name == name:
                        issues.append(f"Conflict: skill '{name}' already exists at {sub}")
                        break
    
    # 3. Check if name resembles existing skills (fuzzy match)
    all_skills = []
    for sd in search_dirs:
        if not sd.exists():
            continue
        for d in sd.iterdir():
            if d.is_dir() and not d.name.startswith("."):
                all_skills.append(d.name)
            if d.is_dir():
                for sub in d.iterdir():
                    if sub.is_dir():
                        all_skills.append(sub.name)
    
    similar = [s for s in all_skills if name in s or s in name]
    if similar:
        warnings.append(f"Similar skills found: {similar[:5]}")
    
    # 4. Check skill-creator availability
    sc_path = HERMES_HOME / "skills" / "skill-creator" / "SKILL.md"
    if not sc_path.exists():
        warnings.append("skill-creator not found — recommend loading it for quality workflow")
    
    # 5. Check for complementary pack
    cap_pack_hints = []
    if "layout" in name or "pdf" in name:
        cap_pack_hints.append("Consider: this skill may belong in 'doc-engine' capability pack")
    if "quality" in name or "audit" in name or "gate" in name:
        cap_pack_hints.append("Consider: this skill may belong in 'skill-quality' capability pack")
    
    return {
        "gate": "skill-create-gate",
        "passed": len(issues) == 0,
        "name": name,
        "issues": issues,
        "warnings": warnings,
        "cap_pack_hints": cap_pack_hints,
        "recommendations": [
            "加载 skill-creator: skill_view(name='skill-creator')",
            "运行依赖扫描: python3 ~/.hermes/skills/skill-creator/scripts/dependency-scan.py",
            "创建后运行 SQS 评分: python3 ~/.hermes/skills/skill-creator/scripts/skill-quality-score.py <name>",
        ] + ([f"💡 {h}" for h in cap_pack_hints] if cap_pack_hints else []),
    }


def main():
    import argparse
    parser = argparse.ArgumentParser(description="skill quality gate: pre-creation check")
    parser.add_argument("name", help="Skill name to check")
    parser.add_argument("--json", action="store_true", help="JSON output")
    parser.add_argument("--check", dest="name2", help="Alias for name")
    args = parser.parse_args()
    
    name = args.name or args.name2 or ""
    if not name:
        parser.print_help()
        sys.exit(1)
    
    result = check_skill_name(name)
    
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(f"{'='*50}")
        print(f"  🔧 Skill Create Gate")
        print(f"{'='*50}")
        print(f"  Name:   {name}")
        print(f"  Status: {'✅ PASS' if result['passed'] else '❌ BLOCKED'}")
        if result["issues"]:
            print(f"\n  🚫 Issues:")
            for i in result["issues"]:
                print(f"    • {i}")
        if result["warnings"]:
            print(f"\n  ⚠️  Warnings:")
            for w in result["warnings"]:
                print(f"    • {w}")
        print(f"\n  📋 Recommendations:")
        for r in result["recommendations"]:
            print(f"    • {r}")
    
    sys.exit(0 if result["passed"] else 1)


if __name__ == "__main__":
    main()
