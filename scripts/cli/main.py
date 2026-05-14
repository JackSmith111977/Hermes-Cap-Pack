"""
cap-pack CLI — 能力包管理命令行工具

用法:
    cap-pack install <pack-dir>             安装能力包
    cap-pack remove <pack-name>             卸载能力包
    cap-pack verify <pack-name>             验证已安装的能力包
    cap-pack list                           列出已安装的能力包
    cap-pack inspect <pack-dir>             检查能力包内容（不安装）
    cap-pack upgrade <name>                 升级能力包
    cap-pack upgrade --all                  升级所有已安装的能力包
    cap-pack status                         显示能力包状态概览
    cap-pack search <term>                  搜索能力包
    cap-pack skill add <pack> <source>      添加 skill 到能力包
    cap-pack skill remove <pack> <id>       从能力包移除 skill
    cap-pack skill list <pack>              列出能力包中的 skill
    cap-pack skill update <pack> <id> [src] 更新能力包中的 skill
    cap-pack --help                         显示帮助
"""

import sys
import argparse
from pathlib import Path

# ── 确保项目根目录在 Python 路径中 ──
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from scripts.cli.commands import (
    cmd_install,
    cmd_remove,
    cmd_verify,
    cmd_list,
    cmd_inspect,
    cmd_upgrade,
    cmd_status,
    cmd_search,
    cmd_skill_add,
    cmd_skill_remove,
    cmd_skill_list,
    cmd_skill_update,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="cap-pack",
        description="能力包管理工具 — 安装/卸载/验证/列出/升级/状态/搜索 Hermes 能力包",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
    cap-pack install packs/doc-engine             安装 doc-engine 能力包
    cap-pack install packs/doc-engine --dry-run   预览安装
    cap-pack remove doc-engine                    卸载 doc-engine
    cap-pack verify doc-engine                    验证 doc-engine
    cap-pack list                                 列出所有已安装
    cap-pack inspect packs/doc-engine             查看包内容
    cap-pack upgrade doc-engine                   升级 doc-engine
    cap-pack upgrade --all                        升级所有已安装
    cap-pack status                               显示状态概览
    cap-pack search pdf                           搜索含 "pdf" 的包
    cap-pack skill add my-pack ~/skills/my-skill  添加 skill
    cap-pack skill remove my-pack my-skill        移除 skill
    cap-pack skill list my-pack                   列出 skill
    cap-pack skill update my-pack my-skill [src]  更新 skill
        """,
    )

    sub = parser.add_subparsers(dest="command", help="可用命令")

    # install
    p_install = sub.add_parser("install", help="安装能力包到 Hermes 或 OpenCode")
    p_install.add_argument("pack_dir", type=str, help="能力包目录路径")
    p_install.add_argument("--dry-run", action="store_true", help="仅预览，不实际安装")
    p_install.add_argument("--target", choices=["hermes", "opencode", "auto"],
                          default="auto", help="目标 Agent (默认: auto 检测)")

    # remove
    p_remove = sub.add_parser("remove", help="卸载能力包")
    p_remove.add_argument("pack_name", type=str, help="能力包名称")
    p_remove.add_argument("--target", choices=["hermes", "opencode"], default=None,
                         help="目标 Agent (默认: auto 检测)")

    # verify
    p_verify = sub.add_parser("verify", help="验证已安装的能力包")
    p_verify.add_argument("pack_name", type=str, help="能力包名称")
    p_verify.add_argument("--target", choices=["hermes", "opencode"], default=None,
                         help="目标 Agent (默认: auto 检测)")

    # list
    p_list = sub.add_parser("list", help="列出已安装的能力包")
    p_list.add_argument("--target", choices=["hermes", "opencode"], default=None,
                       help="目标 Agent (默认: auto 检测)")

    # inspect
    p_inspect = sub.add_parser("inspect", help="检查能力包内容（不安装）")
    p_inspect.add_argument("pack_dir", type=str, help="能力包目录路径")

    # ── upgrade ──
    p_upgrade = sub.add_parser("upgrade", help="升级能力包")
    p_upgrade.add_argument("name", type=str, nargs="?", default="",
                          help="能力包名称")
    p_upgrade.add_argument("--all", action="store_true", dest="all_packs",
                          help="升级所有已安装的能力包")
    p_upgrade.add_argument("--dry-run", action="store_true",
                          help="仅预览，不实际安装")

    # ── status ──
    p_status = sub.add_parser("status", help="显示能力包状态概览")

    # ── search ──
    p_search = sub.add_parser("search", help="搜索能力包")
    p_search.add_argument("term", type=str, help="搜索关键词")

    # ── skill 子命令 ──
    p_skill = sub.add_parser("skill", help="管理能力包中的 skill")
    skill_sub = p_skill.add_subparsers(dest="skill_action", help="skill 操作")

    # skill add
    p_skill_add = skill_sub.add_parser("add", help="向能力包添加 skill")
    p_skill_add.add_argument("pack", type=str, help="能力包名称")
    p_skill_add.add_argument("source_path", type=str, help="源 skill 目录路径")

    # skill remove
    p_skill_remove = skill_sub.add_parser("remove", help="从能力包移除 skill")
    p_skill_remove.add_argument("pack", type=str, help="能力包名称")
    p_skill_remove.add_argument("skill_id", type=str, help="Skill ID")
    p_skill_remove.add_argument("--dry-run", action="store_true",
                               help="仅预览，不实际执行")

    # skill list
    p_skill_list = skill_sub.add_parser("list", help="列出能力包中的 skill")
    p_skill_list.add_argument("pack", type=str, help="能力包名称")

    # skill update
    p_skill_update = skill_sub.add_parser("update", help="更新能力包中的 skill")
    p_skill_update.add_argument("pack", type=str, help="能力包名称")
    p_skill_update.add_argument("skill_id", type=str, help="Skill ID")
    p_skill_update.add_argument("source_path", type=str, nargs="?", default=None,
                               help="源 skill 目录路径（可选）")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if not args.command:
        parser.print_help()
        return 1

    try:
        if args.command == "install":
            return cmd_install(Path(args.pack_dir), dry_run=args.dry_run, target=args.target)
        elif args.command == "remove":
            return cmd_remove(args.pack_name, target=args.target)
        elif args.command == "verify":
            return cmd_verify(args.pack_name, target=args.target)
        elif args.command == "list":
            return cmd_list(target=args.target)
        elif args.command == "inspect":
            return cmd_inspect(Path(args.pack_dir))
        elif args.command == "upgrade":
            return cmd_upgrade(args.name, dry_run=args.dry_run, all_packs=args.all_packs)
        elif args.command == "status":
            return cmd_status()
        elif args.command == "search":
            return cmd_search(args.term)
        elif args.command == "skill":
            if not args.skill_action:
                p_skill = [p for p in parser._subparsers._actions if p.dest == 'command'][0]
                for action in p_skill.choices['skill']._actions:
                    if hasattr(action, 'choices') and action.choices:
                        print("skill 子命令: add, remove, list, update")
                        print("用法: cap-pack skill <add|remove|list|update> ...")
                        return 1
                return 1
            if args.skill_action == "add":
                return cmd_skill_add(args.pack, args.source_path)
            elif args.skill_action == "remove":
                return cmd_skill_remove(args.pack, args.skill_id, dry_run=args.dry_run)
            elif args.skill_action == "list":
                return cmd_skill_list(args.pack)
            elif args.skill_action == "update":
                return cmd_skill_update(args.pack, args.skill_id, args.source_path)
    except Exception as e:
        print(f"❌ 错误: {e}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
