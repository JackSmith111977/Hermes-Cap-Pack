#!/usr/bin/env python3
"""
install-pack.py v1.0 — 将能力包安装到 Hermes Agent

从 cap-pack 格式安装到 ~/.hermes/skills/，支持：
  - 安装完整 skill（含 references/scripts/templates/checklists）
  - 只安装未安装的（增量模式）
  - 卸载已安装的包
  - 查看已安装状态

用法:
  python3 install-pack.py <pack-dir>              # 安装到 Hermes
  python3 install-pack.py <pack-dir> --dry-run    # 预览安装
  python3 install-pack.py status                  # 查看已安装的包
  python3 install-pack.py remove <pack-name>      # 卸载
"""

import os, sys, shutil, json, yaml
from pathlib import Path

HERMES_SKILLS = Path.home() / ".hermes" / "skills"
PACK_BASE = Path.home() / "projects" / "hermes-cap-pack" / "packs"
TRACK_FILE = Path.home() / ".hermes" / "installed_packs.json"


def load_tracked():
    if TRACK_FILE.exists():
        try:
            return json.loads(TRACK_FILE.read_text())
        except:
            return {}
    return {}


def save_tracked(tracked):
    TRACK_FILE.write_text(json.dumps(tracked, indent=2, ensure_ascii=False) + "\n")


def install_pack(pack_dir, dry_run=False):
    pack_dir = Path(pack_dir).expanduser().resolve()
    manifest_path = pack_dir / "cap-pack.yaml"

    if not manifest_path.exists():
        print(f"❌ {pack_dir.name}: 无 cap-pack.yaml")
        return False

    with open(manifest_path) as f:
        manifest = yaml.safe_load(f)

    pack_name = manifest.get("name", pack_dir.name)
    skills = manifest.get("skills", [])
    hooks = manifest.get("hooks", {}).get("on_activate", [])

    print(f"\n📦 安装能力包: {pack_name}")
    print(f"   技能数: {len(skills)}")
    print(f"   依赖: {len(manifest.get('dependencies', {}).get('python_packages', []))} Python 包")

    if dry_run:
        print("\n   [DRY RUN] 将安装以下 skill:")
        for skill in skills:
            sid = skill.get("id", "?")
            path = skill.get("path", "")
            src = pack_dir / path
            dst = HERMES_SKILLS / sid / "SKILL.md"
            print(f"     📄 {sid} → {dst}")
            # 检查 linked files
            skill_dir = src.parent if src.name == "SKILL.md" else src
            skill_pack_dir = pack_dir / "SKILLS" / sid
            if skill_pack_dir.exists():
                for f in skill_pack_dir.rglob("*"):
                    if f.is_file() and f.name != "SKILL.md":
                        rel = f.relative_to(skill_pack_dir)
                        print(f"     📎   {rel}")
        print("\n   ✅ 预览完成")
        return True

    # 实际安装
    installed = []
    for skill in skills:
        sid = skill.get("id", "?")
        path = skill.get("path", "")

        # 确定源目录（skill 的完整目录）
        skill_src = pack_dir / "SKILLS" / sid
        skill_dst = HERMES_SKILLS / sid

        if not skill_src.exists():
            print(f"   ⚠️  {sid}: SKILLS/{sid}/ 不存在，跳过")
            continue

        # 安装
        if skill_dst.exists():
            # 备份
            bak = skill_dst.parent / f"{sid}.bak"
            if bak.exists():
                shutil.rmtree(bak)
            shutil.copytree(skill_dst, bak)
            shutil.rmtree(skill_dst)

        shutil.copytree(skill_src, skill_dst)
        installed.append(sid)
        print(f"   ✅ {sid}: installed")

    # 记录已安装
    tracked = load_tracked()
    tracked[pack_name] = {
        "path": str(pack_dir),
        "installed_at": __import__("datetime").datetime.now().isoformat(),
        "skills": installed,
        "version": manifest.get("version", "1.0.0"),
    }
    save_tracked(tracked)

    # 执行钩子
    for hook in hooks:
        if hook.get("type") == "shell":
            cmd = hook.get("command", "")
            print(f"   ⚡ 执行钩子: {cmd[:60]}...")
            if not dry_run:
                os.system(cmd)

    print(f"\n✅ 能力包 '{pack_name}' 安装完成！")
    print(f"   已安装 {len(installed)} 个 skill: {', '.join(installed[:5])}{'...' if len(installed) > 5 else ''}")
    return True


def cmd_status():
    tracked = load_tracked()
    if not tracked:
        print("📭 (无已安装的能力包)")
        return

    print(f"\n📋 已安装的能力包 ({len(tracked)} 个):")
    print(f"{'='*60}")
    for name, info in sorted(tracked.items()):
        skills = info.get("skills", [])
        version = info.get("version", "?")
        installed_at = info.get("installed_at", "")[:19]
        print(f"  📦 {name:20s} v{version:8s} [{installed_at}]")
        print(f"     Skills: {', '.join(skills[:6])}{'...' if len(skills) > 6 else ''}")
    print()


def cmd_remove(pack_name):
    tracked = load_tracked()
    if pack_name not in tracked:
        print(f"❌ 能力包 '{pack_name}' 未安装")
        return False

    info = tracked[pack_name]
    skills = info.get("skills", [])

    print(f"\n🗑️  卸载能力包: {pack_name}")
    for sid in skills:
        skill_dir = HERMES_SKILLS / sid
        bak_dir = HERMES_SKILLS / f"{sid}.bak"
        if skill_dir.exists():
            shutil.rmtree(skill_dir)
            print(f"   🗑️  {sid}: 已删除")
        if bak_dir.exists():
            shutil.copytree(bak_dir, skill_dir)
            shutil.rmtree(bak_dir)
            print(f"   ♻️  {sid}: 已从备份恢复")
        else:
            print(f"   ⚠️  {sid}: 无备份")

    del tracked[pack_name]
    save_tracked(tracked)
    print(f"✅ 已卸载 '{pack_name}'")
    return True


def main():
    if len(sys.argv) < 2 or sys.argv[1] in ('-h', '--help'):
        print(__doc__)
        sys.exit(0)

    if sys.argv[1] == "status":
        cmd_status()
    elif sys.argv[1] == "remove":
        if len(sys.argv) < 3:
            print("用法: install-pack.py remove <pack-name>")
            sys.exit(1)
        cmd_remove(sys.argv[2])
    else:
        pack_dir = sys.argv[1]
        dry_run = "--dry-run" in sys.argv
        install_pack(pack_dir, dry_run)


if __name__ == "__main__":
    main()
