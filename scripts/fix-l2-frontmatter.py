#!/usr/bin/env python3
"""
fix-l2-frontmatter.py — 为已有 L2 文件添加 YAML frontmatter
"""
import os, re, sys

PACKS = "packs"
L2_TYPES = {
    "quick-ref": "tutorial",
    "pitfall": "pitfall",
    "pitfalls": "pitfall",
    "tips": "best-practice",
    "guide": "tutorial",
    "decision-tree": "decision-tree",
    "patterns": "best-practice",
    "encoding": "lesson-learned",
    "fallback": "lesson-learned",
    "comparison": "lesson-learned",
    "failure": "pitfall",
    "usage": "tutorial",
}

def detect_type(filename, content):
    for keyword, l2type in L2_TYPES.items():
        if keyword in filename.lower():
            return l2type
    if "pitfall" in content.lower():
        return "pitfall"
    if "comparison" in content.lower():
        return "lesson-learned"
    return "best-practice"

def detect_skill_ref(filename, content):
    for line in content.split("\n")[:5]:
        m = re.search(r"关联技能[：:](\S+)", line)
        if m: return m.group(1).strip()
        m = re.search(r"skill_ref[：:]\s*(\S+)", line)
        if m: return m.group(1).strip()
    return filename.replace(".md", "").replace("-", " ")

fixed = 0
for pack in sorted(os.listdir(PACKS)):
    exp_dir = os.path.join(PACKS, pack, "EXPERIENCES")
    if not os.path.isdir(exp_dir):
        continue
    for fname in sorted(os.listdir(exp_dir)):
        if not fname.endswith(".md"):
            continue
        fpath = os.path.join(exp_dir, fname)
        with open(fpath) as f:
            content = f.read()
        if content.startswith("---"):
            continue
        l2type = detect_type(fname, content)
        skill_ref = detect_skill_ref(fname, content)
        name = fname.replace(".md", "")
        frontmatter = (
            "---\n"
            f'type: {l2type}\n'
            f'skill_ref: "{skill_ref}"\n'
            f'keywords: [{name}]\n'
            f'created: 2026-05-14\n'
            "---\n"
            "\n"
        )
        with open(fpath, "w") as f:
            f.write(frontmatter + content.lstrip())
        fixed += 1
        print(f"  [{pack}] {fname} -> {l2type}")

print(f"\nDone: {fixed} files fixed")
