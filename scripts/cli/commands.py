"""
CLI 命令实现 — 能力包的安装/卸载/验证/列出/检查
使用 HermesAdapter 进行实际操作。
"""

from __future__ import annotations

import sys
from pathlib import Path

# ── 确保项目根目录在 Python 路径中 ──
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from scripts.uca import PackParser, PackParseError
from scripts.adapters.hermes import HermesAdapter

# ── 路径常量 ──────────────────────────────────────────

PROJECT_ROOT = Path(__file__).parent.parent.parent
SCHEMA_PATH = PROJECT_ROOT / "schemas" / "cap-pack-v1.schema.json"


# ── 工具函数 ──────────────────────────────────────────


def _print_header(title: str):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


def _print_skill_tree(skills: list, indent: str = "    "):
    for s in skills:
        sid = s.id if hasattr(s, "id") else s.get("id", "?")
        desc = s.description if hasattr(s, "description") else s.get("description", "")
        print(f"{indent}📄 {sid}  —  {desc[:60]}")


# ── 命令实现 ──────────────────────────────────────────


def cmd_install(pack_dir: Path, dry_run: bool = False) -> int:
    """安装能力包"""
    parser = PackParser(schema_path=SCHEMA_PATH)

    _print_header(f"📦 安装能力包: {pack_dir.name}")

    # Step 1: 解析
    print(f"\n  📖 解析 cap-pack.yaml...")
    pack = parser.parse(pack_dir)
    print(f"     名称:    {pack.name}")
    print(f"     版本:    {pack.version}")
    print(f"     Skills:  {len(pack.skills)}")
    print(f"     经验:    {len(pack.experiences)}")
    print(f"     MCP:     {len(pack.mcp_configs)}")

    # Step 2: 使用 HermesAdapter 安装
    adapter = HermesAdapter()

    if not adapter.is_available:
        print(f"\n  ⚠️  Hermes 环境不可用，将执行离线安装")
        print(f"     (仅复制 skill 文件，不注入 MCP 配置)")

    if dry_run:
        print(f"\n  🔍 [DRY RUN] 将安装以下 skill:")
        _print_skill_tree(pack.skills)
        if pack.mcp_configs:
            print(f"\n  🔌 将注入 MCP 服务:")
            for m in pack.mcp_configs:
                print(f"     ⚡ {m.name}")
        print(f"\n  ✅ 预览完成，未执行任何操作")
        return 0

    result = adapter.install(pack)

    if result.success:
        installed = result.details.get("installed_skills", [])
        mcp_count = result.details.get("mcp_injected", 0)
        print(f"\n  ✅ 安装完成！共安装 {len(installed)} 个 skill")
        if mcp_count > 0:
            print(f"  🔌 注入 {mcp_count} 个 MCP 配置")
        if result.warnings:
            for w in result.warnings:
                print(f"  ⚠️  {w}")
        return 0
    else:
        for err in result.errors:
            print(f"\n  ❌ {err}")
        return 1


def cmd_remove(pack_name: str) -> int:
    """卸载能力包"""
    adapter = HermesAdapter()
    result = adapter.uninstall(pack_name)

    if not result.success:
        print(f"❌ {result.errors[0]}")
        return 1

    _print_header(f"🗑️  卸载能力包: {pack_name}")
    removed = result.details.get("removed", 0)
    restored = result.details.get("restored_from_backup", 0)

    print(f"\n  ✅ 卸载完成")
    if restored > 0:
        print(f"     ♻️  从备份恢复了 {restored} 个 skill")
    print(f"     🗑️  移除了 {removed} 个 skill")
    return 0


def cmd_verify(pack_name: str) -> int:
    """验证已安装的能力包"""
    adapter = HermesAdapter()
    result = adapter.verify(pack_name)

    if not result.success:
        print(f"❌ {'; '.join(result.errors)}")
        return 1

    _print_header(f"🔍 验证能力包: {pack_name}")
    print(f"     版本:        v{result.details.get('total_skills', 0)}")
    print(f"     Skills 完好: {result.details.get('valid_skills', 0)}/{result.details.get('total_skills', 0)}")

    if result.warnings:
        for w in result.warnings:
            print(f"  ⚠️  {w}")

    print(f"\n  ✅ 验证通过！")
    return 0


def cmd_list() -> int:
    """列出已安装的能力包"""
    adapter = HermesAdapter()
    packs = adapter.list_installed()

    if not packs:
        print("📭 (无已安装的能力包)")
        return 0

    _print_header(f"📋 已安装的能力包 ({len(packs)} 个)")

    for p in packs:
        print(f"\n  📦 {p['name']}  v{p['version']}")
        print(f"     安装时间: {p.get('installed_at', '')[:19]}")
        print(f"     Skills:   {p['skill_count']} 个")
    print()
    return 0


def cmd_inspect(pack_dir: Path) -> int:
    """检查能力包内容（不安装）"""
    parser = PackParser(schema_path=SCHEMA_PATH)

    _print_header(f"🔎 检查能力包: {pack_dir.name}")

    try:
        pack = parser.parse(pack_dir)
    except PackParseError as e:
        print(f"\n  ❌ {e}")
        return 1

    print(f"\n  名称:       {pack.name}")
    print(f"  版本:       {pack.version}")
    print(f"  目录:       {pack.pack_dir}")
    print(f"  兼容 Agent: {pack.compatibility.get('agent_types', ['未指定'])}")
    print()

    if pack.skills:
        print(f"  📄 Skills ({len(pack.skills)}):")
        _print_skill_tree(pack.skills)
        print()

    if pack.experiences:
        print(f"  📝 经验 ({len(pack.experiences)}):")
        for e in pack.experiences:
            print(f"     📋 {e.id}  —  {e.description[:60]}")
        print()

    if pack.mcp_configs:
        print(f"  🔌 MCP 服务 ({len(pack.mcp_configs)}):")
        for m in pack.mcp_configs:
            print(f"     ⚡ {m.name}")
        print()

    if pack.dependencies:
        print(f"  📎 Python 依赖: {', '.join(pack.dependencies)}")
        print()

    return 0
