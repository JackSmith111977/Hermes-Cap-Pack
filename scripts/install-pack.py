#!/usr/bin/env python3
"""
install-pack.py v2.0 — 将能力包安装到目标 Agent

支持多 Agent 安装，通过 --target 指定目标。
基于 AgentAdapter Protocol 统一接口。

用法:
  python3 install-pack.py <pack-dir>                          # 默认→Hermes
  python3 install-pack.py <pack-dir> --target hermes          # 安装到 Hermes
  python3 install-pack.py <pack-dir> --target opencode        # 安装到 OpenCode
  python3 install-pack.py <pack-dir> --target auto            # 自动检测可用 Agent
  python3 install-pack.py <pack-dir> --dry-run                # 预览
  python3 install-pack.py <pack-dir> --skip-deps              # 跳过依赖检查
  python3 install-pack.py status                              # 查看已安装
  python3 install-pack.py status --target opencode            # 查看 OpenCode 状态
  python3 install-pack.py remove <pack-name>                  # 卸载
  python3 install-pack.py remove <pack-name> --target opencode # 从 OpenCode 卸载
  python3 install-pack.py verify <pack-name>                  # 验证已安装的包
"""

import sys
import json
import yaml
from pathlib import Path

# ── 项目路径 ──
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from scripts.uca.parser import PackParser
from scripts.adapters.hermes import HermesAdapter
from scripts.adapters.opencode import OpenCodeAdapter


# ── 适配器注册表 ──

ADAPTERS = {
    "hermes": HermesAdapter,
    "opencode": OpenCodeAdapter,
}


def get_adapter(name: str):
    cls = ADAPTERS.get(name)
    if cls is None:
        print(f"❌ 未知目标: {name} (可选: {', '.join(ADAPTERS.keys())}, auto)")
        sys.exit(1)
    return cls()


def detect_available() -> list[str]:
    """自动检测可用的 Agent 环境"""
    available = []
    for name, cls in ADAPTERS.items():
        adapter = cls()
        if adapter.is_available:
            available.append(name)
    return available


def cmd_install(pack_dir: str, target: str, dry_run: bool, skip_deps: bool):
    """安装能力包到指定目标"""
    pack_path = Path(pack_dir).expanduser().resolve()
    if not pack_path.exists():
        print(f"❌ 目录不存在: {pack_path}")
        sys.exit(1)

    parser = PackParser()
    try:
        pack = parser.parse(pack_path)
    except Exception as e:
        print(f"❌ 解析失败: {e}")
        sys.exit(1)

    targets = []
    if target == "auto":
        targets = detect_available()
        if not targets:
            print("❌ 未检测到可用的 Agent 环境")
            sys.exit(1)
        print(f"🔍 自动检测到: {', '.join(targets)}")
    else:
        targets = [target]

    all_ok = True
    for tgt in targets:
        adapter = get_adapter(tgt)
        if not adapter.is_available and not dry_run:
            print(f"   ⚠️  {tgt} 环境不可用，跳过")
            all_ok = False
            continue

        print(f"\n📦 安装能力包 '{pack.name}' v{pack.version} → {tgt}")
        result = adapter.install(pack, dry_run=dry_run, skip_deps=skip_deps)

        if result.success:
            print(f"   ✅ 安装成功")
            if result.details.get("installed_skills"):
                skills = result.details["installed_skills"]
                print(f"     Skills: {len(skills)} 个: {', '.join(skills[:5])}{'...' if len(skills) > 5 else ''}")
            if result.details.get("installed_scripts"):
                print(f"     Scripts: {len(result.details['installed_scripts'])} 个")
            if result.details.get("verification") and result.details["verification"].get("passed"):
                print(f"     ✅ 验证门禁通过 ({result.details['verification']['check_count']} 项检查)")
        else:
            print(f"   ❌ 安装失败")
            all_ok = False

        for w in result.warnings:
            print(f"   ⚠️  {w}")
        for e in result.errors:
            print(f"   ❌ {e}")

    if all_ok:
        print(f"\n✅ 全部完成！")
    else:
        print(f"\n⚠️  部分操作未成功，见上")
        sys.exit(1)


def cmd_status(target: str):
    """查看已安装的能力包"""
    if target == "auto":
        targets = detect_available() or ["hermes"]
    else:
        targets = [target]

    for tgt in targets:
        adapter = get_adapter(tgt)
        if not adapter.is_available:
            print(f"📭 [{tgt}] 环境不可用")
            continue

        packs = adapter.list_installed()
        if not packs:
            print(f"📭 [{tgt}] (无已安装的能力包)")
            continue

        print(f"\n📋 [{tgt}] 已安装的能力包 ({len(packs)} 个):")
        print(f"{'=' * 60}")
        for p in packs:
            print(f"  📦 {p['name']:20s} v{p.get('version', '?'):8s} [{p.get('installed_at', '')[:19]}]"
                  f"  skills: {p.get('skill_count', 0)}")


def cmd_remove(pack_name: str, target: str):
    """卸载能力包"""
    if target == "auto":
        targets = detect_available() or ["hermes"]
    else:
        targets = [target]

    for tgt in targets:
        adapter = get_adapter(tgt)
        if not adapter.is_available:
            print(f"   ⚠️  [{tgt}] 环境不可用，跳过")
            continue

        print(f"🗑️  从 {tgt} 卸载 '{pack_name}'")
        result = adapter.uninstall(pack_name)
        if result.success:
            print(f"   ✅ 已卸载")
        else:
            for e in result.errors:
                print(f"   ❌ {e}")


def cmd_verify(pack_name: str, target: str):
    """验证已安装的能力包"""
    if target == "auto":
        targets = detect_available() or ["hermes"]
    else:
        targets = [target]

    for tgt in targets:
        adapter = get_adapter(tgt)
        if not adapter.is_available:
            print(f"   ⚠️  [{tgt}] 环境不可用，跳过")
            continue

        print(f"🔍 验证 [{tgt}] {pack_name}")
        result = adapter.verify(pack_name)
        if result.success:
            print(f"   ✅ 验证通过")
            print(f"     Skills: {result.details.get('valid_skills', 0)}/{result.details.get('total_skills', 0)}")
            if "script_count" in result.details:
                print(f"     Scripts: {result.details['script_count']} 个")
        else:
            print(f"   ❌ 验证失败")
        for w in result.warnings:
            print(f"   ⚠️  {w}")
        for e in result.errors:
            print(f"   ❌ {e}")


def main():
    import argparse

    # 兼容旧用法: install-pack.py <pack-dir> [--dry-run]
    if len(sys.argv) >= 2 and sys.argv[1] not in ("status", "remove", "verify", "-h", "--help") and not sys.argv[1].startswith("-"):
        # 直接安装模式
        pack_dir = sys.argv[1]
        target = "hermes"
        dry_run = False
        skip_deps = False
        i = 2
        while i < len(sys.argv):
            if sys.argv[i] == "--target" and i + 1 < len(sys.argv):
                target = sys.argv[i + 1]
                i += 2
            elif sys.argv[i] == "--dry-run":
                dry_run = True
                i += 1
            elif sys.argv[i] == "--skip-deps":
                skip_deps = True
                i += 1
            else:
                i += 1
        cmd_install(pack_dir, target, dry_run, skip_deps)
        return

    # 子命令模式
    parser = argparse.ArgumentParser(description="能力包安装工具 v2.0")
    subparsers = parser.add_subparsers(dest="command", help="子命令")

    # status
    p_status = subparsers.add_parser("status", help="查看已安装的包")
    p_status.add_argument("--target", default="hermes", help="目标 Agent")

    # remove
    p_remove = subparsers.add_parser("remove", help="卸载能力包")
    p_remove.add_argument("pack_name", help="能力包名称")
    p_remove.add_argument("--target", default="hermes", help="目标 Agent")

    # verify
    p_verify = subparsers.add_parser("verify", help="验证已安装的能力包")
    p_verify.add_argument("pack_name", help="能力包名称")
    p_verify.add_argument("--target", default="hermes", help="目标 Agent")

    args = parser.parse_args()

    if args.command == "status":
        cmd_status(args.target)
    elif args.command == "remove":
        cmd_remove(args.pack_name, args.target)
    elif args.command == "verify":
        cmd_verify(args.pack_name, args.target)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
