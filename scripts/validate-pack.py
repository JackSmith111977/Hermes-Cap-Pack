#!/usr/bin/env python3
"""
validate-pack.py v1.0 — 能力包完整性验证器

检查 cap-pack 的能力包是否完整：
  - manifest (cap-pack.yaml) 格式正确
  - 所有声明的文件实际存在
  - 所有 linked files (references/scripts/templates/checklists) 存在
  - experience_refs 和 skill_refs 交叉引用完整

用法:
  python3 validate-pack.py <pack-dir>     # 验证指定能力包
  python3 validate-pack.py --all           # 验证所有能力包
  python3 validate-pack.py <pack-dir> --fix # 自动修复缺失文件引用
"""

import os, sys, json, yaml, re
from pathlib import Path


def validate_pack(pack_dir, fix=False):
    """验证单个能力包的完整性"""
    pack_dir = Path(pack_dir).expanduser().resolve()
    manifest_path = pack_dir / "cap-pack.yaml"

    print(f"\n{'='*60}")
    print(f"🔍 验证能力包: {pack_dir.name}")
    print(f"{'='*60}")

    issues = []
    warnings = []

    # 1. 检查 manifest 存在
    if not manifest_path.exists():
        issues.append(f"❌ cap-pack.yaml 不存在")
        return False, issues, warnings

    # 2. 解析 manifest
    try:
        with open(manifest_path) as f:
            manifest = yaml.safe_load(f)
    except Exception as e:
        issues.append(f"❌ cap-pack.yaml 解析失败: {e}")
        return False, issues, warnings

    # 3. 基本字段检查
    required_fields = ["name", "version", "type", "description", "created"]
    for field in required_fields:
        if field not in manifest:
            issues.append(f"❌ 缺少必需字段: {field}")

    if manifest.get("type") != "capability-pack":
        issues.append(f"❌ type 必须为 'capability-pack'，当前: {manifest.get('type')}")

    # 4. 检查 compatibility
    compat = manifest.get("compatibility", {})
    agent_types = compat.get("agent_types", [])
    if not agent_types:
        warnings.append("⚠️ 未声明 agent_types")

    # 5. 检查 skills
    skills = manifest.get("skills", [])
    if not skills:
        issues.append("❌ 没有技能声明 (skills 为空)")
    else:
        for skill in skills:
            sid = skill.get("id", "?")
            path = skill.get("path", "")
            full_path = pack_dir / path

            # 检查 SKILL.md
            if not full_path.exists():
                # 也可能是子目录下有 SKILL.md
                alt_path = pack_dir / "SKILLS" / sid / "SKILL.md"
                if alt_path.exists():
                    if fix:
                        skill["path"] = f"SKILLS/{sid}/SKILL.md"
                        print(f"   🔧 修复 {sid}: path = SKILLS/{sid}/SKILL.md")
                else:
                    issues.append(f"❌ {sid}: 文件不存在 ({path})")
            else:
                # 验证 SKILL.md 有 YAML frontmatter
                try:
                    content = full_path.read_text()
                    if not content.startswith("---"):
                        warnings.append(f"⚠️ {sid}: SKILL.md 缺少 YAML frontmatter")
                except:
                    pass

            # 检查 experience_refs 是否存在
            for exp_ref in skill.get("experience_refs", []):
                found = any(e.get("id") == exp_ref for e in manifest.get("experiences", []))
                if not found:
                    issues.append(f"❌ {sid}: experience_ref '{exp_ref}' 在 experiences 中不存在")

            # 检查 files 声明
            for file_cat, file_decl in skill.get("files", {}).items():
                # 提取路径（去掉括号中的计数）
                file_path_str = re.match(r'^(SKILLS/\S+)', str(file_decl))
                if file_path_str:
                    dir_to_check = pack_dir / file_path_str.group(1)
                    if not dir_to_check.exists():
                        issues.append(f"❌ {sid}: files/{file_cat} 目录不存在 ({dir_to_check.name})")

    # 6. 检查 experiences
    experiences = manifest.get("experiences", [])
    if experiences:
        for exp in experiences:
            eid = exp.get("id", "?")
            path = exp.get("path", "")
            full_path = pack_dir / path
            if not full_path.exists():
                issues.append(f"❌ 经验 '{eid}': 文件不存在 ({path})")

            # 检查 skill_refs 是否存在
            for s_ref in exp.get("skill_refs", []):
                found = any(s.get("id") == s_ref for s in skills)
                if not found:
                    issues.append(f"❌ 经验 '{eid}': skill_ref '{s_ref}' 在 skills 中不存在")

    # 7. 检查依赖
    deps = manifest.get("dependencies", {})
    if deps:
        # 检查 python_packages 版本格式
        for pkg in deps.get("python_packages", []):
            if not re.match(r'^[a-zA-Z0-9_.-]+[><=!~]=?\d', pkg) and not re.match(r'^[a-zA-Z0-9_.-]+$', pkg):
                warnings.append(f"⚠️ 可能的无效包格式: {pkg}")

    # 8. 检查 hooks
    hooks = manifest.get("hooks", {})
    for hook_type, hook_list in hooks.items():
        for i, hook in enumerate(hook_list):
            if hook.get("type") == "shell" and not hook.get("command"):
                issues.append(f"❌ hooks.{hook_type}[{i}]: shell 类型但无 command")

    # 输出结果
    if not issues and not warnings:
        print(f"\n✅ 能力包 '{pack_dir.name}' 完美通过验证！")
        print(f"   Skills: {len(skills)} | Experiences: {len(experiences)}")
        return True, [], []
    else:
        if issues:
            print(f"\n❌ 发现 {len(issues)} 个错误:")
            for issue in issues:
                print(f"  {issue}")
        if warnings:
            print(f"\n⚠️  发现 {len(warnings)} 个警告:")
            for warn in warnings:
                print(f"  {warn}")
        return len(issues) == 0, issues, warnings


def validate_all(base_dir=None):
    """验证所有能力包"""
    if not base_dir:
        base_dir = Path.home() / "projects" / "hermes-cap-pack" / "packs"

    base_dir = Path(base_dir).expanduser().resolve()
    if not base_dir.exists():
        print(f"❌ 能力包目录不存在: {base_dir}")
        return False

    packs = sorted([d for d in base_dir.iterdir() if d.is_dir()])
    if not packs:
        print(f"📭 (无能力包)")
        return True

    print(f"\n📋 发现 {len(packs)} 个能力包，开始验证...")
    all_pass = True
    total_issues = 0

    for pack in packs:
        pack_manifest = pack / "cap-pack.yaml"
        if not pack_manifest.exists():
            print(f"⏭️  {pack.name}: 无 cap-pack.yaml，跳过")
            continue
        ok, issues, _ = validate_pack(pack)
        if not ok:
            all_pass = False
            total_issues += len(issues)

    print(f"\n{'='*60}")
    if all_pass:
        print(f"🎉 全部能力包验证通过！")
    else:
        print(f"⚠️  共 {total_issues} 个问题需要修复")
    return all_pass


def main():
    if len(sys.argv) < 2 or sys.argv[1] in ('-h', '--help'):
        print(__doc__)
        sys.exit(0)

    fix = '--fix' in sys.argv

    if sys.argv[1] == '--all':
        validate_all()
    elif sys.argv[1] == '--fix':
        if len(sys.argv) > 2:
            validate_pack(sys.argv[2], fix=True)
        else:
            print("用法: validate-pack.py <pack-dir> --fix")
    else:
        validate_pack(sys.argv[1], fix=fix)

    # 修复后保存 manifest
    if fix:
        pack_dir = Path(sys.argv[2] if sys.argv[1] != '--fix' else sys.argv[2]).expanduser().resolve()
        manifest_path = pack_dir / "cap-pack.yaml"
        if manifest_path.exists():
            with open(manifest_path) as f:
                manifest = yaml.safe_load(f)
            with open(manifest_path, 'w') as f:
                yaml.dump(manifest, f, allow_unicode=True, indent=2, 
                         default_flow_style=False, sort_keys=False)


if __name__ == "__main__":
    main()
