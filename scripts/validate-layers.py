#!/usr/bin/env python3
"""
validate-layers.py — 能力包三层结构完整性检查 (L2/L3)

检查每个能力包是否具备完整的 L2 Experiences 和 L3 Knowledge。

用法:
  python3 scripts/validate-layers.py                  # 全量检查
  python3 scripts/validate-layers.py --pack doc-engine # 单包检查
  python3 scripts/validate-layers.py --ci             # CI 模式 (exit code)
  python3 scripts/validate-layers.py --fix-frontmatter # 自动修复缺失 frontmatter
"""

import os, sys, re, yaml
from pathlib import Path

PACKS_DIR = Path(__file__).resolve().parent.parent / "packs"

# Required frontmatter fields
L2_REQUIRED = ["type", "skill_ref"]
L3_REQUIRED = ["type", "domain"]
L2_OPTIONAL = ["keywords", "created"]
L3_OPTIONAL = ["keywords", "created"]
VALID_L2_TYPES = ["best-practice", "lesson-learned", "tutorial", "case-study", "decision-tree", "pitfall"]
VALID_L3_TYPES = ["concept", "entity", "summary"]


def check_pack(pack_name, ci_mode=False):
    """检查单个包的三层结构"""
    pack_dir = PACKS_DIR / pack_name
    if not pack_dir.is_dir():
        return {"pack": pack_name, "errors": [f"包目录不存在"], "warnings": []}
    
    errors = []
    warnings = []
    
    # Check L2: EXPERIENCES/
    exp_dir = pack_dir / "EXPERIENCES"
    if not exp_dir.is_dir():
        warnings.append("❌ 缺少 EXPERIENCES/ 目录")
        l2_files = []
    else:
        l2_files = sorted(exp_dir.glob("*.md"))
        if not l2_files:
            warnings.append("❌ EXPERIENCES/ 为空")
    
    # Check L3: KNOWLEDGE/
    kn_dir = pack_dir / "KNOWLEDGE"
    if not kn_dir.is_dir():
        warnings.append("❌ 缺少 KNOWLEDGE/ 目录")
        l3_files = []
    else:
        l3_files = sorted(kn_dir.glob("**/*.md"))
        if not l3_files:
            warnings.append("❌ KNOWLEDGE/ 为空")
    
    # Validate frontmatter
    bad_frontmatter_l2 = 0
    bad_frontmatter_l3 = 0
    
    for f in l2_files:
        if not validate_frontmatter(f, L2_REQUIRED, VALID_L2_TYPES):
            bad_frontmatter_l2 += 1
            warnings.append(f"  ⚠️ {f.name}: frontmatter 不完整或类型无效")
    
    for f in l3_files:
        if not validate_frontmatter(f, L3_REQUIRED, VALID_L3_TYPES):
            bad_frontmatter_l3 += 1
            warnings.append(f"  ⚠️ {f.name}: frontmatter 不完整或类型无效")
    
    return {
        "pack": pack_name,
        "l2_count": len(l2_files),
        "l3_count": len(l3_files),
        "bad_fm_l2": bad_frontmatter_l2,
        "bad_fm_l3": bad_frontmatter_l3,
        "has_l2": len(l2_files) > 0,
        "has_l3": len(l3_files) > 0,
        "errors": errors,
        "warnings": warnings,
    }


def validate_frontmatter(filepath, required_fields, valid_types):
    """验证单个文件的 YAML frontmatter"""
    text = filepath.read_text()
    
    # Check for YAML frontmatter
    if not text.startswith("---"):
        return False
    
    # Extract frontmatter
    parts = text.split("---", 2)
    if len(parts) < 3:
        return False
    
    try:
        fm = yaml.safe_load(parts[1])
    except yaml.YAMLError:
        return False
    
    if not isinstance(fm, dict):
        return False
    
    # Check required fields
    for field in required_fields:
        if field not in fm:
            return False
    
    # Check type validity
    if "type" in fm and valid_types:
        if fm["type"] not in valid_types:
            return False
    
    return True


def main():
    args = sys.argv[1:]
    ci_mode = "--ci" in args
    pack_filter = None
    
    for i, arg in enumerate(args):
        if arg == "--pack" and i + 1 < len(args):
            pack_filter = args[i + 1]
        elif arg == "--help":
            print(__doc__)
            return
    
    if pack_filter:
        packs = [pack_filter]
    else:
        packs = sorted([d.name for d in PACKS_DIR.iterdir() if d.is_dir() and d.name != "categories"])
    
    all_ok = True
    summary = []
    
    print(f"{'包名':25s} L2  L3  FM✗  状态")
    print("-" * 50)
    
    for pack_name in packs:
        result = check_pack(pack_name, ci_mode)
        summary.append(result)
        
        l2 = f"{'✅' if result['has_l2'] else '❌'}{result['l2_count']}"
        l3 = f"{'✅' if result['has_l3'] else '❌'}{result['l3_count']}"
        fm_bad = result["bad_fm_l2"] + result["bad_fm_l3"]
        status = "✅" if (result["has_l2"] and result["has_l3"] and fm_bad == 0) else "⚠️"
        
        print(f"{pack_name:25s} {l2:3s} {l3:3s} {fm_bad:2d}   {status}")
        
        if result["warnings"]:
            for w in result["warnings"]:
                print(f"  {w}")
            all_ok = False
    
    # Summary
    ok_count = sum(1 for r in summary if r["has_l2"] and r["has_l3"] and r["bad_fm_l2"] == 0 and r["bad_fm_l3"] == 0)
    print(f"\n{'='*50}")
    print(f"总计: {len(packs)} 包 | L2完整: {sum(1 for r in summary if r['has_l2'])}/{len(packs)} | L3完整: {sum(1 for r in summary if r['has_l3'])}/{len(packs)} | frontmatter异常: {sum(r['bad_fm_l2']+r['bad_fm_l3'] for r in summary)}")
    
    if not all_ok:
        print("⚠️ 部分包需要补充 L2/L3 或修复 frontmatter")
        if ci_mode:
            sys.exit(1)
    else:
        print("✅ 全部包三层结构完整")


if __name__ == "__main__":
    main()
