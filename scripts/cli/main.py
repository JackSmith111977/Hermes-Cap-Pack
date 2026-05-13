"""
cap-pack CLI — 能力包管理命令行工具

用法:
    cap-pack install <pack-dir>     安装能力包
    cap-pack remove <pack-name>     卸载能力包
    cap-pack verify <pack-name>     验证已安装的能力包
    cap-pack list                   列出已安装的能力包
    cap-pack inspect <pack-dir>     检查能力包内容（不安装）
    cap-pack --help                 显示帮助
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
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="cap-pack",
        description="能力包管理工具 — 安装/卸载/验证/列出 Hermes 能力包",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
    cap-pack install packs/doc-engine        安装 doc-engine 能力包
    cap-pack install packs/doc-engine --dry-run  预览安装
    cap-pack remove doc-engine               卸载 doc-engine
    cap-pack verify doc-engine               验证 doc-engine
    cap-pack list                            列出所有已安装
    cap-pack inspect packs/doc-engine        查看包内容
        """,
    )

    sub = parser.add_subparsers(dest="command", help="可用命令")

    # install
    p_install = sub.add_parser("install", help="安装能力包")
    p_install.add_argument("pack_dir", type=str, help="能力包目录路径")
    p_install.add_argument("--dry-run", action="store_true", help="仅预览，不实际安装")

    # remove
    p_remove = sub.add_parser("remove", help="卸载能力包")
    p_remove.add_argument("pack_name", type=str, help="能力包名称")

    # verify
    p_verify = sub.add_parser("verify", help="验证已安装的能力包")
    p_verify.add_argument("pack_name", type=str, help="能力包名称")

    # list
    sub.add_parser("list", help="列出已安装的能力包")

    # inspect
    p_inspect = sub.add_parser("inspect", help="检查能力包内容（不安装）")
    p_inspect.add_argument("pack_dir", type=str, help="能力包目录路径")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if not args.command:
        parser.print_help()
        return 1

    try:
        if args.command == "install":
            return cmd_install(Path(args.pack_dir), dry_run=args.dry_run)
        elif args.command == "remove":
            return cmd_remove(args.pack_name)
        elif args.command == "verify":
            return cmd_verify(args.pack_name)
        elif args.command == "list":
            return cmd_list()
        elif args.command == "inspect":
            return cmd_inspect(Path(args.pack_dir))
    except Exception as e:
        print(f"❌ 错误: {e}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
