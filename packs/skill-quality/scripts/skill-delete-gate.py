#!/usr/bin/env python3
"""
skill-delete-gate.py — 删除 skill 前引用链分析与安全门禁
作用: 检查目标 skill 是否被其他 skill 引用、是否被能力包声明、是否可安全删除
用法:
  python3 skill-delete-gate.py "my-skill"
  python3 skill-delete-gate.py "my-skill" --json
  python3 skill-delete-gate.py "my-skill" --force   # 跳过非阻塞检查
退出码: 0=安全可删, 1=阻塞, 2=需确认
"""

import json, os, sys, re, shutil
from pathlib import Path


def analyze_delete(name: str, force: bool = False) -> dict:
    """Analyze if a skill can be safely deleted."""
    HERMES_HOME = Path(os.environ.get("HERMES_HOME", Path.home() / ".hermes"))
    blocks = []
    warnings = []
    
    # 1. Find the skill directory
    skill_dir = None
    for base in [HERMES_HOME / "skills"]:
        if not base.exists():
            continue
        # Direct match
        d = base / name
        if d.exists() and (d / "SKILL.md").exists():
            skill_dir = d
            break
        # Category match
        for cat in base.iterdir():
            if cat.is_dir():
                d = cat / name
                if d.exists() and (d / "SKILL.md").exists():
                    skill_dir = d
                    break
        if skill_dir:
            break
    
    if not skill_dir:
        return {
            "gate": "skill-delete-gate",
            "passed": True,
            "name": name,
            "found": False,
            "blocks": [],
            "warnings": ["Skill not found — nothing to delete"],
            "actions": [],
        }
    
    # 2. Scan all frontmatter for cross-references
    referrers = []
    for root, dirs, files in os.walk(HERMES_HOME / "skills"):
        if ".archive" in root:
            continue
        if "SKILL.md" in files:
            fp = Path(root) / "SKILL.md"
            content = fp.read_text(encoding="utf-8", errors="replace")
            # Check depends_on, related_skills, referenced_by
            patterns = [
                rf'depends_on\s*:.*?{re.escape(name)}',
                rf'related_skills\s*:.*?{re.escape(name)}',
                rf'referenced_by\s*:.*?{re.escape(name)}',
                rf'\[.*?\]\(.*?{re.escape(name)}.*?\)',
                rf'~/.hermes/skills/{re.escape(name)}',
            ]
            for pat in patterns:
                if re.search(pat, content, re.DOTALL | re.IGNORECASE):
                    referrers.append({
                        "skill": fp.parent.name,
                        "file": str(fp),
                        "pattern": pat,
                    })
                    break
    
    # 3. Check cap-pack declarations
    cap_pack_refs = []
    for root, dirs, files in os.walk(HERMES_HOME.parent / "projects" / "hermes-cap-pack" / "packs"):
        if "cap-pack.yaml" in files:
            fp = Path(root) / "cap-pack.yaml"
            content = fp.read_text(encoding="utf-8", errors="replace")
            if name in content:
                pack_name = fp.parent.name
                cap_pack_refs.append({"pack": pack_name, "file": str(fp)})
    
    # 4. Check curator state
    curator_tracking = False
    usage_path = HERMES_HOME / "skills" / ".usage.json"
    if usage_path.exists():
        try:
            usage = json.loads(usage_path.read_text())
            if name in usage:
                curator_tracking = True
        except Exception:
            pass
    
    # 5. Build recommendations
    if referrers:
        blocks.append(f"Skill '{name}' is referenced by {len(referrers)} other skill(s)")
    if cap_pack_refs:
        blocks.append(f"Skill '{name}' is declared in {len(cap_pack_refs)} capability pack(s)")
    if curator_tracking:
        warnings.append("Skill is tracked by curator (in .usage.json)")
    
    # Check if skill has been modified recently
    if skill_dir:
        mtime = os.path.getmtime(skill_dir / "SKILL.md")
        from datetime import datetime
        days_ago = (datetime.now() - datetime.fromtimestamp(mtime)).days
        if days_ago < 7:
            warnings.append(f"Skill was modified {days_ago} days ago — verify deletion intent")
    
    # Build safe-delete actions
    actions = []
    if blocks:
        actions.append(f"Before deleting, update these referrers: {', '.join(r['skill'] for r in referrers)}")
    if cap_pack_refs:
        actions.append(f"Update cap-pack.yaml files to remove references: {', '.join(r['pack'] for r in cap_pack_refs)}")
    actions.append("Create backup: cp -r <skill_dir> ~/.hermes/skills/.archive/<name>")
    
    passed = len(blocks) == 0 or force
    
    return {
        "gate": "skill-delete-gate",
        "passed": passed,
        "name": name,
        "found": True,
        "skill_dir": str(skill_dir),
        "blocks": blocks,
        "warnings": warnings,
        "referrers": referrers,
        "cap_pack_refs": cap_pack_refs,
        "curator_tracking": curator_tracking,
        "modified_days_ago": days_ago,
        "actions": actions,
    }


def main():
    import argparse
    parser = argparse.ArgumentParser(description="skill quality gate: pre-deletion analysis")
    parser.add_argument("name", help="Skill name to analyze for deletion")
    parser.add_argument("--json", action="store_true", help="JSON output")
    parser.add_argument("--force", action="store_true", help="Skip non-blocking checks")
    args = parser.parse_args()
    
    result = analyze_delete(args.name, args.force)
    
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(f"{'='*50}")
        print(f"  🗑️  Skill Delete Gate")
        print(f"{'='*50}")
        print(f"  Name:   {args.name}")
        print(f"  Found:  {'✅' if result['found'] else '❌'} at {result.get('skill_dir', '?')}")
        print(f"  Status: {'✅ SAFE' if result['passed'] else '❌ BLOCKED'}")
        
        if result["blocks"]:
            print(f"\n  🚫 Blocks ({len(result['blocks'])}):")
            for b in result["blocks"]:
                print(f"    • {b}")
        if result["referrers"]:
            print(f"\n  🔗 Referrers ({len(result['referrers'])}):")
            for r in result["referrers"]:
                print(f"    • {r['skill']}")
        if result["cap_pack_refs"]:
            print(f"\n  📦 Cap-pack references:")
            for r in result["cap_pack_refs"]:
                print(f"    • {r['pack']}")
        if result["warnings"]:
            print(f"\n  ⚠️  Warnings:")
            for w in result["warnings"]:
                print(f"    • {w}")
        if result["actions"]:
            print(f"\n  📋 Recommended actions:")
            for a in result["actions"]:
                print(f"    • {a}")
    
    sys.exit(0 if result["passed"] else 1)


if __name__ == "__main__":
    main()
