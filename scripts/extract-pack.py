#!/usr/bin/env python3
"""
extract-pack.py v1.0 — 从 Hermes Skill 库提取技能到能力包格式

将 ~/.hermes/skills/<name>/ 下的完整 skill（SKILL.md + 关联文件）
提取到 cap-pack 目录结构中。

用法:
  python3 extract-pack.py <skill-name>                      # 提取到 packs/<skill-name>/
  python3 extract-pack.py <skill-name> --pack <pack-name>   # 指定目标能力包
  python3 extract-pack.py <skill-name> --dest <path>        # 指定目标路径
  python3 extract-pack.py <skill-name> --update-manifest    # 同时更新 cap-pack.yaml
  python3 extract-pack.py --list                            # 列出可提取的 skill

示例:
  python3 extract-pack.py pdf-layout --pack doc-engine --update-manifest
  python3 extract-pack.py pdf-layout --dest ~/projects/hermes-cap-pack/packs/doc-engine
"""

import os, sys, shutil, re, json
from datetime import datetime

SKILLS_DIR = os.path.expanduser("~/.hermes/skills")
PACK_BASE = os.path.expanduser("~/projects/hermes-cap-pack/packs")


def find_skill_dir(skill_name):
    """查找 skill 目录，支持模糊匹配"""
    # 精确匹配
    path = os.path.join(SKILLS_DIR, skill_name)
    if os.path.isdir(path) and os.path.exists(os.path.join(path, "SKILL.md")):
        return path

    # 模糊匹配（在子目录中查找）
    for root, dirs, files in os.walk(SKILLS_DIR):
        if os.path.basename(root) == skill_name:
            if "SKILL.md" in files:
                return root
        # 检查子目录
        for d in dirs:
            if d == skill_name:
                sub = os.path.join(root, d)
                if os.path.exists(os.path.join(sub, "SKILL.md")):
                    return sub

    return None


def get_skill_metadata(skill_path):
    """解析 SKILL.md 的 YAML frontmatter"""
    sk_path = os.path.join(skill_path, "SKILL.md")
    if not os.path.exists(sk_path):
        return None
    with open(sk_path) as f:
        content = f.read()
    match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
    if not match:
        return {"name": os.path.basename(skill_path)}
    import yaml
    try:
        return yaml.safe_load(match.group(1)) or {}
    except:
        return {"name": os.path.basename(skill_path)}


def list_skill_files(skill_path):
    """列出 skill 目录中所有文件（排除隐藏/缓存）"""
    files = []
    for root, dirs, fnames in os.walk(skill_path):
        # 排除隐藏目录和缓存
        dirs[:] = [d for d in dirs if not d.startswith('.') and d != '__pycache__']
        for fname in fnames:
            if fname.endswith(('.pyc', '.swp', '~')):
                continue
            full = os.path.join(root, fname)
            rel = os.path.relpath(full, skill_path)
            files.append(rel)
    return sorted(files)


def categorize_file(rel_path):
    """将文件分类到 cap-pack 的子目录"""
    parts = rel_path.split(os.sep)
    if len(parts) == 1:
        # SKILL.md 本身
        return ("SKILLS", parts[-1])
    elif parts[0] == "SKILL.md":
        return ("SKILLS", parts[-1])
    else:
        # 其他文件按原目录结构放入 SKILLS/<skill>/<category>/
        return ("SKILLS", rel_path)


def extract_skill(skill_name, pack_name=None, dest_dir=None, update_manifest=False):
    """提取 skill 到能力包格式"""
    print(f"\n🔍 查找 skill: {skill_name}")

    skill_path = find_skill_dir(skill_name)
    if not skill_path:
        print(f"❌ Skill '{skill_name}' 未找到")
        # 相近名称建议
        all_skills = []
        for root, dirs, files in os.walk(SKILLS_DIR):
            if "SKILL.md" in files:
                all_skills.append(os.path.basename(root))
        close = [s for s in all_skills if skill_name in s or s in skill_name]
        if close:
            print(f"💡 相近 skill: {', '.join(close[:10])}")
        return False

    print(f"   📍 源路径: {skill_path}")

    # 读取元数据
    meta = get_skill_metadata(skill_path)
    meta_name = meta.get("name", skill_name)

    # 确定目标
    if not pack_name:
        pack_name = skill_name  # 单 skill 包
    if not dest_dir:
        dest_dir = os.path.join(PACK_BASE, pack_name)

    # 源数据
    # 列出所有文件
    all_files = list_skill_files(skill_path)
    print(f"   📦 Skill 文件数: {len(all_files)}")

    # 复制文件
    copied = []
    for rel_path in all_files:
        src = os.path.join(skill_path, rel_path)
        # 目标路径：SKILLS/<skill-name>/... (保留原目录结构)
        dst = os.path.join(dest_dir, "SKILLS", skill_name, rel_path)
        os.makedirs(os.path.dirname(dst), exist_ok=True)

        if os.path.isdir(src):
            continue

        # 复制文件
        shutil.copy2(src, dst)
        copied.append(os.path.join("SKILLS", skill_name, rel_path))

    print(f"   ✅ 已复制 {len(copied)} 个文件")

    # 更新 cap-pack.yaml（如果指定了 --update-manifest）
    if update_manifest:
        manifest_path = os.path.join(dest_dir, "..", "cap-pack.yaml")
        if not os.path.exists(manifest_path):
            manifest_path = os.path.join(dest_dir, "cap-pack.yaml")

        if os.path.exists(manifest_path):
            import yaml
            with open(manifest_path) as f:
                manifest = yaml.safe_load(f) or {}

            # 更新技能条目
            skills = manifest.get("skills", [])
            existing = None
            for s in skills:
                if s.get("id") == skill_name:
                    existing = s
                    break

            entry = {
                "id": skill_name,
                "path": f"SKILLS/{skill_name}/SKILL.md",
                "version": meta.get("version", "1.0.0"),
                "description": meta.get("description", ""),
                "tags": meta.get("tags", meta.get("triggers", []))[:5],
            }

            if existing:
                existing.update(entry)
                print(f"   📝 已更新 manifest 中的 '{skill_name}'")
            else:
                skills.append(entry)
                manifest["skills"] = skills
                print(f"   📝 已添加 '{skill_name}' 到 manifest")

            # 检查是否有 references/scripts 等资源需要声明
            linked_types = []
            for rel_path in all_files:
                parts = rel_path.split(os.sep)
                if len(parts) > 1 and parts[0] in (
                        "references", "scripts", "templates", "checklists", "assets"):
                    if parts[0] not in linked_types:
                        linked_types.append(parts[0])

            if linked_types:
                # 确保 skills 条目的 files 字段
                for s in skills:
                    if s.get("id") == skill_name:
                        if "files" not in s:
                            s["files"] = {}
                        for lt in linked_types:
                            count = sum(1 for f in all_files if f.startswith(lt + "/"))
                            s["files"][lt] = f"SKILLS/{skill_name}/{lt}/ ({count} files)"
                        break

            with open(manifest_path, 'w') as f:
                yaml.dump(manifest, f, allow_unicode=True, indent=2, 
                         default_flow_style=False, sort_keys=False)
            print(f"   💾 已更新 manifest: {manifest_path}")
        else:
            print(f"   ⚠️  manifest 不存在 ({manifest_path})，跳过更新")

    # 结果摘要
    print(f"\n{'='*60}")
    print(f"✅ 提取完成: {skill_name}")
    print(f"   源: {skill_path}")
    print(f"   目标: {dest_dir}/SKILLS/{skill_name}/")
    print(f"   文件: {len(copied)} 个")
    print(f"{'='*60}")
    return True


def list_extractable_skills():
    """列出所有可提取的 skill（有 SKILL.md 的）"""
    skills = []
    for root, dirs, files in os.walk(SKILLS_DIR):
        if "SKILL.md" in files:
            name = os.path.basename(root)
            meta = get_skill_metadata(root)
            desc = meta.get("description", "")[:80]
            version = meta.get("version", "?")
            # 检查引用
            refs = sum(1 for d in dirs if d in ("references", "scripts", "templates", "checklists", "assets"))
            skills.append((name, version, desc, refs))

    skills.sort(key=lambda x: x[0])
    print(f"\n📋 可提取的 Skill ({len(skills)} 个):")
    print(f"{'='*70}")
    for name, ver, desc, refs in skills:
        has_extras = " 📎" if refs > 0 else ""
        print(f"  {name:30s} v{ver:8s}{has_extras} {desc[:50]}")
    print(f"\n💡 提取: python3 extract-pack.py <skill-name>")


def main():
    if len(sys.argv) < 2 or sys.argv[1] in ('-h', '--help'):
        print(__doc__)
        sys.exit(0)

    if sys.argv[1] == '--list':
        list_extractable_skills()
        sys.exit(0)

    skill_name = sys.argv[1]
    pack_name = None
    dest_dir = None
    update_manifest = False

    args = sys.argv[2:]
    for i, arg in enumerate(args):
        if arg == '--pack' and i + 1 < len(args):
            pack_name = args[i + 1]
        elif arg == '--dest' and i + 1 < len(args):
            dest_dir = os.path.abspath(args[i + 1])
        elif arg == '--update-manifest':
            update_manifest = True

    success = extract_skill(skill_name, pack_name, dest_dir, update_manifest)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
