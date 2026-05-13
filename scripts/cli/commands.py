"""
CLI 命令实现 — 能力包的安装/卸载/验证/列出/检查
"""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

# ── 确保项目根目录在 Python 路径中 ──
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from scripts.uca import (
    PackParser,
    PackParseError,
    DependencyChecker,
    PackVerifier,
    CapPack,
)

# ── 路径常量 ──────────────────────────────────────────

HERMES_SKILLS = Path.home() / ".hermes" / "skills"
TRACK_FILE = Path.home() / ".hermes" / "installed_packs.json"
PROJECT_ROOT = Path(__file__).parent.parent.parent
SCHEMA_PATH = PROJECT_ROOT / "schemas" / "cap-pack-v1.schema.json"


# ── 跟踪文件操作 ──────────────────────────────────────


def _load_tracked() -> dict:
    if TRACK_FILE.exists():
        try:
            return json.loads(TRACK_FILE.read_text())
        except (json.JSONDecodeError, OSError):
            return {}
    return {}


def _save_tracked(tracked: dict):
    TRACK_FILE.parent.mkdir(parents=True, exist_ok=True)
    TRACK_FILE.write_text(json.dumps(tracked, indent=2, ensure_ascii=False) + "\n")


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
    checker = DependencyChecker()

    _print_header(f"📦 安装能力包: {pack_dir.name}")

    # Step 1: 解析
    print(f"\n  📖 解析 cap-pack.yaml...")
    pack = parser.parse(pack_dir)
    print(f"     名称:    {pack.name}")
    print(f"     版本:    {pack.version}")
    print(f"     Skills:  {len(pack.skills)}")
    print(f"     经验:    {len(pack.experiences)}")
    print(f"     MCP:     {len(pack.mcp_configs)}")

    # Step 2: 依赖检查
    if pack.dependencies:
        print(f"\n  🔍 检查依赖...")
        dep_result = checker.check(pack)
        if dep_result["missing_packages"]:
            for pkg in dep_result["missing_packages"]:
                print(f"     ⚠️  缺少 Python 包: {pkg}")
            if not dry_run:
                print("\n  ⚠️  依赖不满足，继续安装（请在安装后手动安装缺失包）")
        else:
            print(f"     ✅ 所有 Python 依赖已满足")

    # Step 3: 检查已安装
    tracked = _load_tracked()
    if pack.name in tracked:
        old_info = tracked[pack.name]
        print(f"\n  🔄 已安装版本: v{old_info.get('version', '?')}")
        print(f"     将更新到:   v{pack.version}")

    if dry_run:
        print(f"\n  🔍 [DRY RUN] 将安装以下 skill:")
        _print_skill_tree(pack.skills)
        print(f"\n  ✅ 预览完成，未执行任何操作")
        return 0

    # Step 4: 实际安装
    print(f"\n  📂 安装 skill 文件...")
    installed = []
    for skill in pack.skills:
        # 源: SKILLS/{id}/ 目录（在 pack_dir 下）
        src = pack.pack_dir / "SKILLS" / skill.id
        dst = HERMES_SKILLS / skill.id

        if not src.exists():
            print(f"     ⚠️  {skill.id}: 源目录不存在，跳过")
            continue

        # 备份已有
        if dst.exists():
            bak = dst.parent / f"{skill.id}.bak"
            if bak.exists():
                shutil.rmtree(bak)
            shutil.copytree(dst, bak)
            shutil.rmtree(dst)

        # 安装
        shutil.copytree(src, dst)
        installed.append(skill.id)
        print(f"     ✅ {skill.id}")

    # Step 5: 记录跟踪
    tracked[pack.name] = {
        "version": pack.version,
        "path": str(pack.pack_dir),
        "installed_at": __import__("datetime").datetime.now().isoformat()[:19],
        "skills": installed,
        "skill_count": len(installed),
        "experience_count": len(pack.experiences),
    }
    _save_tracked(tracked)

    print(f"\n  ✅ 安装完成！共安装 {len(installed)} 个 skill")
    return 0


def cmd_remove(pack_name: str) -> int:
    """卸载能力包"""
    tracked = _load_tracked()

    if pack_name not in tracked:
        print(f"❌ 能力包 '{pack_name}' 未安装")
        return 1

    info = tracked[pack_name]
    _print_header(f"🗑️  卸载能力包: {pack_name}")
    print(f"     当前版本: v{info.get('version', '?')}")
    print(f"     安装时间: {info.get('installed_at', '?')}")

    removed = 0
    restored = 0
    for sid in info.get("skills", []):
        skill_dir = HERMES_SKILLS / sid
        bak_dir = HERMES_SKILLS / f"{sid}.bak"

        if skill_dir.exists():
            shutil.rmtree(skill_dir)
            removed += 1

        if bak_dir.exists():
            shutil.copytree(bak_dir, skill_dir)
            shutil.rmtree(bak_dir)
            restored += 1

    del tracked[pack_name]
    _save_tracked(tracked)

    print(f"\n  ✅ 卸载完成")
    if restored > 0:
        print(f"     ♻️  从备份恢复了 {restored} 个 skill")
    print(f"     🗑️  移除了 {removed} 个 skill")
    return 0


def cmd_verify(pack_name: str) -> int:
    """验证已安装的能力包"""
    tracked = _load_tracked()

    if pack_name not in tracked:
        print(f"❌ 能力包 '{pack_name}' 未安装")
        return 1

    info = tracked[pack_name]
    _print_header(f"🔍 验证能力包: {pack_name}")

    print(f"     版本:     v{info.get('version', '?')}")
    print(f"     Skills:   {info.get('skill_count', 0)} 个")
    print(f"     经验:     {info.get('experience_count', 0)} 个")

    # 使用 verifier 检查
    skill_ids = info.get("skills", [])
    verifier = PackVerifier(skills_base=HERMES_SKILLS)

    # 构造一个轻量的 CapPack 用于验证
    from scripts.uca.protocol import CapPack as CP, CapPackSkill as CPS
    pack = CP(
        name=pack_name,
        version=info.get("version", "?"),
        pack_dir=Path(info.get("path", ".")),
        manifest={},
        skills=[CPS(id=sid, path=f"SKILLS/{sid}/SKILL.md") for sid in skill_ids],
    )

    result = verifier.verify(pack, HERMES_SKILLS)

    print()
    if result.success:
        print(f"  ✅ 验证通过！所有 {len(skill_ids)} 个 skill 文件完好")
    else:
        print(f"  ❌ 验证失败：")
        for err in result.errors:
            print(f"     {err}")
        return 1

    return 0


def cmd_list() -> int:
    """列出已安装的能力包"""
    tracked = _load_tracked()

    if not tracked:
        print("📭 (无已安装的能力包)")
        return 0

    _print_header(f"📋 已安装的能力包 ({len(tracked)} 个)")

    for name, info in sorted(tracked.items()):
        version = info.get("version", "?")
        skills = info.get("skills", [])
        installed_at = info.get("installed_at", "")[:19]
        print(f"\n  📦 {name}  v{version}")
        print(f"     安装时间: {installed_at}")
        print(f"     Skills({len(skills)}): {', '.join(skills[:5])}{'...' if len(skills) > 5 else ''}")

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
