"""
CLI 命令实现 — 能力包的安装/卸载/验证/列出/检查/升级/状态/搜索/skill管理
使用 HermesAdapter 进行实际操作。
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import yaml

# ── 确保项目根目录在 Python 路径中 ──
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from scripts.uca import PackParser, PackParseError
from scripts.adapters.hermes import HermesAdapter
from scripts.adapters.opencode import OpenCodeAdapter

# ── 路径常量 ──────────────────────────────────────────

PROJECT_ROOT = Path(__file__).parent.parent.parent
SCHEMA_PATH = PROJECT_ROOT / "schemas" / "cap-pack-v1.schema.json"
HERMES_HOME = Path.home() / ".hermes"
INSTALLED_PACKS_PATH = HERMES_HOME / "installed_packs.json"


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


def _get_adapter(target: str | None = None):
    """获取适配器实例，auto-detect 优先 Hermes"""
    if target == "hermes":
        return HermesAdapter()
    elif target == "opencode":
        return OpenCodeAdapter()
    # auto-detect
    hermes = HermesAdapter()
    if hermes.is_available:
        return hermes
    opencode = OpenCodeAdapter()
    if opencode.is_available:
        return opencode
    return hermes  # fallback


def cmd_install(pack_dir: Path, dry_run: bool = False, target: str | None = None) -> int:
    """安装能力包"""
    parser = PackParser(schema_path=SCHEMA_PATH)

    _print_header(f"📦 安装能力包: {pack_dir.name}")

    # Step 1: 解析
    print(f"\n  📖 解析 cap-pack.yaml...")
    pack = parser.parse(pack_dir)
    target_name = target or "auto"
    print(f"     名称:    {pack.name}")
    print(f"     版本:    {pack.version}")
    print(f"     Skills:  {len(pack.skills)}")
    print(f"     经验:    {len(pack.experiences)}")
    print(f"     MCP:     {len(pack.mcp_configs)}")
    print(f"     目标:    {target_name}")

    # Step 2: 获取适配器
    adapter = _get_adapter(target)
    adapter_name = adapter.name
    print(f"     适配器:  {adapter_name}")

    if not adapter.is_available and not dry_run:
        print(f"\n  ⚠️  {adapter_name} 适配器不可用")

    if dry_run:
        print(f"\n  🔍 [DRY RUN] 将安装以下 skill:")
        _print_skill_tree(pack.skills)
        if pack.mcp_configs:
            print(f"\n  🔌 将注入 MCP 服务:")
            for m in pack.mcp_configs:
                print(f"     ⚡ {m.name} ({adapter_name})")
        print(f"\n  ✅ 预览完成，未执行任何操作")
        return 0

    result = adapter.install(pack)

    if result.success:
        installed = result.details.get("installed_skills", [])
        mcp_count = result.details.get("mcp_injected", 0)
        print(f"\n  ✅ 安装完成！共安装 {len(installed)} 个 skill → {adapter_name}")
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


def cmd_remove(pack_name: str, target: str | None = None) -> int:
    """卸载能力包"""
    adapter = _get_adapter(target)
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


def cmd_verify(pack_name: str, target: str | None = None) -> int:
    """验证已安装的能力包"""
    adapter = _get_adapter(target)
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


def cmd_list(target: str | None = None) -> int:
    """列出已安装的能力包"""
    adapter = _get_adapter(target)
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


# ── 新的辅助函数 ──────────────────────────────────────


def _read_installed_packs() -> dict:
    """读取 ~/.hermes/installed_packs.json，返回 {name: info}"""
    if not INSTALLED_PACKS_PATH.exists():
        return {}
    try:
        return json.loads(INSTALLED_PACKS_PATH.read_text())
    except (json.JSONDecodeError, OSError):
        return {}


def _read_yaml_file(path: Path) -> dict | None:
    """安全读取 YAML 文件，出错返回 None"""
    try:
        with open(path) as f:
            return yaml.safe_load(f) or {}
    except Exception:
        return None


def _write_yaml_file(path: Path, data: dict) -> bool:
    """安全写入 YAML 文件，成功返回 True"""
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
        return True
    except Exception:
        return False


def _backup_file(path: Path, suffix: str | None = None) -> Path | None:
    """备份文件，返回备份路径。失败返回 None"""
    if not path.exists():
        return None
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        bak = path.with_suffix(f".{suffix or 'bak'}.{timestamp}")
        shutil.copy2(path, bak)
        return bak
    except Exception:
        return None


def _bump_version(version: str, part: str = "patch") -> str:
    """语义化版本号递增

    Args:
        version: 当前版本号，如 "1.2.3"
        part: "major" | "minor" | "patch"

    Returns:
        递增后的版本号
    """
    try:
        parts = [int(x) for x in str(version).split(".")]
        while len(parts) < 3:
            parts.append(0)
        if part == "major":
            parts[0] += 1
            parts[1] = 0
            parts[2] = 0
        elif part == "minor":
            parts[1] += 1
            parts[2] = 0
        else:  # patch
            parts[2] += 1
        return ".".join(str(p) for p in parts)
    except (ValueError, TypeError):
        return version


def _find_pack_dir(name: str) -> Path | None:
    """在 packs/ 目录下查找能力包目录

    按名称精确匹配子目录名。
    """
    packs_dir = PROJECT_ROOT / "packs"
    if not packs_dir.exists():
        return None
    target = packs_dir / name
    if target.is_dir() and (target / "cap-pack.yaml").exists():
        return target
    # fallback: 尝试 cap-pack.yml
    if target.is_dir() and (target / "cap-pack.yml").exists():
        return target
    return None


def _extract_skill_info(skill_dir: Path) -> dict:
    """从 skill 目录的 SKILL.md 提取基本信息

    Returns:
        {"id": str, "name": str, "description": str, "version": str}
    """
    info = {
        "id": skill_dir.name,
        "name": skill_dir.name,
        "description": "",
        "version": "1.0.0",
    }
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        return info

    try:
        content = skill_md.read_text()
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                fm = yaml.safe_load(parts[1])
                if isinstance(fm, dict):
                    info["name"] = fm.get("name", fm.get("id", info["name"]))
                    info["description"] = fm.get("description", info["description"])
                    info["version"] = str(fm.get("version", "1.0.0"))
    except Exception:
        pass

    return info


# ── upgrade ────────────────────────────────────────────


def cmd_upgrade(name: str, dry_run: bool = False, all_packs: bool = False) -> int:
    """升级能力包

    cap-pack upgrade <name> [--dry-run]
    cap-pack upgrade --all [--dry-run]
    """
    installed = _read_installed_packs()
    if not installed:
        print("📭 没有已安装的能力包")
        return 1 if name else 0

    if all_packs:
        names = list(installed.keys())
        if not names:
            print("📭 没有可升级的已安装能力包")
            return 0
        success = True
        for n in names:
            result = _do_upgrade_one(n, installed.get(n, {}), dry_run)
            if result != 0:
                success = False
        return 0 if success else 1

    if name not in installed:
        print(f"❌ 能力包 '{name}' 未安装")
        return 1

    return _do_upgrade_one(name, installed[name], dry_run)


def _do_upgrade_one(name: str, info: dict, dry_run: bool) -> int:
    """升级单个能力包（内部实现）"""
    stored_version = info.get("version", "0.0.0")

    # 查找包目录
    pack_dir = _find_pack_dir(name)
    if pack_dir is None:
        # fallback: 使用存储的路径
        stored_path = info.get("path", "")
        if stored_path:
            pack_dir = Path(stored_path)
        if not pack_dir or not pack_dir.exists():
            print(f"❌ 找不到能力包目录: {name}")
            return 1

    # 解析当前包
    parser = PackParser(schema_path=SCHEMA_PATH)
    try:
        pack = parser.parse(pack_dir)
    except PackParseError as e:
        print(f"❌ 解析 {name} 失败: {e}")
        return 1

    pack_version = pack.version

    # 版本比较
    if pack_version == stored_version:
        print(f"  ✅ {name} 已是最新版本 ({stored_version})")
        return 0

    _print_header(f"📦 升级能力包: {name}")
    print(f"     当前版本:     v{stored_version}")
    print(f"     可用版本:     v{pack_version}")
    print(f"     Skills:       {len(pack.skills)} 个")

    if dry_run:
        print(f"\n  🔍 [DRY RUN] 将执行升级:")
        print(f"     - 备份 installed_packs.json")
        print(f"     - 安装 {len(pack.skills)} 个 skill")
        print(f"     - 验证安装完整性")
        print(f"  ✅ 预览完成，未执行任何操作")
        return 0

    # 备份 installed_packs.json
    bak = _backup_file(INSTALLED_PACKS_PATH, "pre-upgrade")
    if bak:
        print(f"     📦 已备份: {bak.name}")

    # 执行升级（通过适配器的 update 方法）
    adapter = HermesAdapter()
    result = adapter.update(pack, stored_version)

    if not result.success:
        for err in result.errors:
            print(f"  ❌ {err}")
        if result.warnings:
            for w in result.warnings:
                print(f"  ⚠️  {w}")
        return 1

    print(f"\n  ✅ 升级完成！v{stored_version} → v{pack_version}")
    updated = result.details.get("updated_skills", [])
    if updated:
        print(f"     更新 {len(updated)} 个 skill")

    if result.warnings:
        for w in result.warnings:
            print(f"  ⚠️  {w}")

    # 验证安装
    print(f"\n  🔍 验证安装...")
    verify_result = adapter.verify(name)
    if verify_result.success:
        print(f"     ✅ 验证通过")
    else:
        for err in verify_result.errors:
            print(f"     ❌ {err}")

    return 0


# ── status ─────────────────────────────────────────────


def cmd_status() -> int:
    """显示能力包状态概览"""
    _print_header("📊 能力包状态概览")

    # 已提取的模块数（~/.hermes/skills/ 目录下的 skill 子目录数）
    extracted_count = 0
    if HERMES_HOME.exists():
        skills_dir = HERMES_HOME / "skills"
        if skills_dir.exists():
            extracted_count = sum(1 for d in skills_dir.iterdir() if d.is_dir())
    print(f"  已提取的模块 (Skills): {extracted_count}")

    # 已安装的包
    installed = _read_installed_packs()
    installed_count = len(installed)
    print(f"  已安装的能力包:       {installed_count} 个")

    if installed:
        print()
        print(f"  {'='*56}")
        print(f"  已安装的能力包列表:")
        print(f"  {'='*56}")
        for name, info in sorted(installed.items()):
            ver = info.get("version", "?")
            skills = info.get("skill_count", len(info.get("skills", [])))
            installed_at = info.get("installed_at", "")[:10] if info.get("installed_at") else "?"
            print(f"    📦 {name:<30s} v{ver:<8s}  📄 {skills} skill  🕐 {installed_at}")

    # 可用但未安装的包
    packs_dir = PROJECT_ROOT / "packs"
    available = []
    if packs_dir.exists():
        for d in sorted(packs_dir.iterdir()):
            if d.is_dir() and (d / "cap-pack.yaml").exists():
                name = d.name
                if name not in installed:
                    manifest = _read_yaml_file(d / "cap-pack.yaml")
                    if manifest:
                        ver = manifest.get("version", "?")
                        desc = manifest.get("description", "")
                        skills_count = len(manifest.get("skills", []))
                        available.append((name, ver, desc, skills_count))

    if available:
        print()
        print(f"  {'='*56}")
        print(f"  可用能力包 (未安装):")
        print(f"  {'='*56}")
        for name, ver, desc, sc in available:
            short_desc = desc[:50] + "..." if len(desc) > 50 else desc
            print(f"    📦 {name:<30s} v{ver:<8s}  📄 {sc} skill  {short_desc}")

    # SQS 平均质量
    sqs_script = HERMES_HOME / "scripts" / "skill-quality-score.py"
    if not sqs_script.exists():
        sqs_script = PROJECT_ROOT / "scripts" / "skill-quality-score.py"

    if sqs_script.exists():
        print()
        print(f"  {'='*56}")
        print(f"  质量评分 (SQS):")
        print(f"  {'='*56}")
        try:
            result = subprocess.run(
                [sys.executable, str(sqs_script), "--audit", "--json"],
                capture_output=True, text=True, timeout=30, cwd=PROJECT_ROOT
            )
            if result.returncode == 0 and result.stdout.strip():
                reports = json.loads(result.stdout)
                if reports:
                    scores = [r.get("total", 0) for r in reports if r.get("total") is not None]
                    if scores:
                        avg_sqs = sum(scores) / len(scores)
                        print(f"    📊 平均 SQS: {avg_sqs:.1f}/100  ({len(reports)} skills)")
                        # 等级
                        if avg_sqs >= 90:
                            print(f"    🟢 优秀")
                        elif avg_sqs >= 70:
                            print(f"    🟡 良好")
                        elif avg_sqs >= 50:
                            print(f"    🟠 需改进")
                        else:
                            print(f"    🔴 不合格")
                    else:
                        print(f"    ⚠️  暂无 SQS 数据")
                else:
                    print(f"    ⚠️  暂无 SQS 数据")
            else:
                print(f"    ⚠️  无法获取 SQS 评分")
        except (subprocess.TimeoutExpired, json.JSONDecodeError, OSError) as e:
            print(f"    ⚠️  SQS 评分不可用: {e}")
        except Exception:
            print(f"    ⚠️  SQS 评分不可用")
    else:
        print()
        print(f"  📊 SQS 质量评分脚本未安装")

    print()
    return 0


# ── search ─────────────────────────────────────────────


def cmd_search(term: str) -> int:
    """搜索能力包"""
    packs_dir = PROJECT_ROOT / "packs"
    if not packs_dir.exists():
        print(f"❌ 未找到能力包目录: {packs_dir}")
        return 1

    parser = PackParser(schema_path=SCHEMA_PATH)
    installed = _read_installed_packs()
    term_lower = term.lower()

    matches = []

    for d in sorted(packs_dir.iterdir()):
        if not d.is_dir():
            continue
        yaml_file = d / "cap-pack.yaml"
        yml_file = d / "cap-pack.yml"
        manifest_path = yaml_file if yaml_file.exists() else (yml_file if yml_file.exists() else None)
        if manifest_path is None:
            continue

        try:
            pack = parser.parse(d)
        except (PackParseError, Exception):
            continue

        # 匹配条件
        name_match = term_lower in pack.name.lower()
        desc_match = term_lower in pack.description.lower() if hasattr(pack, "description") and pack.description else False
        skill_match = any(term_lower in s.id.lower() or term_lower in (s.description or "").lower() for s in pack.skills)

        if name_match or desc_match or skill_match:
            is_installed = pack.name in installed
            matches.append({
                "name": pack.name,
                "version": pack.version,
                "description": getattr(pack, "description", "") or pack.manifest.get("description", ""),
                "skill_count": len(pack.skills),
                "installed": is_installed,
            })

    if not matches:
        print(f"🔍 未找到匹配 '{term}' 的能力包")
        return 0

    _print_header(f"🔍 搜索 '{term}' — 找到 {len(matches)} 个匹配包")

    for m in matches:
        status_icon = "✅" if m["installed"] else "📦"
        status_text = "已安装" if m["installed"] else "可用"
        desc_short = m["description"][:60] + "..." if len(m["description"]) > 60 else m["description"]
        print(f"  {status_icon} {m['name']:<30s} v{m['version']:<8s}")
        print(f"     描述:     {desc_short}")
        print(f"     Skills:   {m['skill_count']} 个")
        print(f"     状态:     {status_text}")
        print()

    return 0


# ── skill 子命令 ───────────────────────────────────────


def cmd_skill_add(pack_name: str, source_path_str: str) -> int:
    """向能力包添加 skill

    cap-pack skill add <pack> <source_path>
    """
    pack_dir = _find_pack_dir(pack_name)
    if pack_dir is None:
        print(f"❌ 找不到能力包 '{pack_name}' (在 packs/ 目录下)")
        return 1

    yaml_path = pack_dir / "cap-pack.yaml"
    if not yaml_path.exists():
        yaml_path = pack_dir / "cap-pack.yml"
    if not yaml_path.exists():
        print(f"❌ 找不到 {pack_name} 的 cap-pack.yaml")
        return 1

    # 读取当前 YAML
    data = _read_yaml_file(yaml_path)
    if data is None:
        print(f"❌ 无法读取 {yaml_path}")
        return 1

    # 确定 source 路径
    source_path = Path(source_path_str).resolve()
    if not source_path.exists():
        print(f"❌ 源路径不存在: {source_path}")
        return 1

    # 确保包含 SKILL.md
    if not (source_path / "SKILL.md").exists():
        print(f"❌ 源路径不是有效的 skill 目录 (缺少 SKILL.md): {source_path}")
        return 1

    # 提取 skill 信息
    skill_info = _extract_skill_info(source_path)
    skill_id = skill_info["id"]

    # 检查是否已存在同名 skill
    existing_ids = [s.get("id") for s in data.get("skills", []) if isinstance(s, dict)]
    if skill_id in existing_ids:
        print(f"❌ Skill '{skill_id}' 已存在于 {pack_name} 中")
        return 1

    # 目标目录
    skills_dir = pack_dir / "SKILLS"
    target_dir = skills_dir / skill_id

    if target_dir.exists():
        print(f"❌ 目标目录已存在: {target_dir}")
        return 1

    # 复制 skill 目录
    try:
        shutil.copytree(source_path, target_dir)
    except Exception as e:
        print(f"❌ 复制失败: {e}")
        return 1

    # 构建新的 skill 条目
    new_skill = {
        "id": skill_id,
        "name": skill_info["name"],
        "description": skill_info["description"],
        "version": skill_info["version"],
        "tags": [],
    }
    # 保留 source 字段（如果是相对路径）
    try:
        rel_path = source_path.relative_to(PROJECT_ROOT)
        new_skill["source"] = str(rel_path)
    except ValueError:
        new_skill["source"] = str(source_path)

    # 添加到 skills 列表
    skills = data.get("skills", [])
    if not isinstance(skills, list):
        skills = []
    skills.append(new_skill)
    data["skills"] = skills

    # 版本递增 minor
    data["version"] = _bump_version(data.get("version", "1.0.0"), "minor")

    # 写入 YAML
    if not _write_yaml_file(yaml_path, data):
        # 回滚：删除已复制的目录
        if target_dir.exists():
            shutil.rmtree(target_dir)
        print(f"❌ 写入 {yaml_path} 失败，已回滚")
        return 1

    print(f"  ✅ Skill '{skill_id}' 已添加到 {pack_name}")
    print(f"     名称:    {skill_info['name']}")
    print(f"     版本:    v{data['version']}")
    print(f"     路径:    {target_dir.relative_to(pack_dir)}")
    return 0


def cmd_skill_remove(pack_name: str, skill_id: str, dry_run: bool = False) -> int:
    """从能力包中移除 skill

    cap-pack skill remove <pack> <skill_id> [--dry-run]
    """
    pack_dir = _find_pack_dir(pack_name)
    if pack_dir is None:
        print(f"❌ 找不到能力包 '{pack_name}'")
        return 1

    yaml_path = pack_dir / "cap-pack.yaml"
    if not yaml_path.exists():
        yaml_path = pack_dir / "cap-pack.yml"
    if not yaml_path.exists():
        print(f"❌ 找不到 {pack_name} 的 cap-pack.yaml")
        return 1

    data = _read_yaml_file(yaml_path)
    if data is None:
        print(f"❌ 无法读取 {yaml_path}")
        return 1

    # 查找 skill 索引
    skills = data.get("skills", [])
    if not isinstance(skills, list):
        print(f"❌ skills 列表格式错误")
        return 1

    skill_idx = None
    for i, s in enumerate(skills):
        if isinstance(s, dict) and s.get("id") == skill_id:
            skill_idx = i
            break

    if skill_idx is None:
        print(f"❌ 未找到 skill '{skill_id}'")
        return 1

    skill_entry = skills[skill_idx]
    skill_name = skill_entry.get("name", skill_id)

    # 技能目录
    skill_dir = pack_dir / "SKILLS" / skill_id

    if dry_run:
        print(f"\n  🔍 [DRY RUN] 将移除 skill:")
        print(f"     - 包:      {pack_name}")
        print(f"     - Skill:   {skill_id} ({skill_name})")
        if skill_dir.exists():
            print(f"     - 目录:    {skill_dir}")
            print(f"     - 备份到:  {pack_dir / 'backups' / skill_id}")
        print(f"     - 版本:    {data.get('version', '?')} → {_bump_version(data.get('version', '?'), 'patch')}")
        print(f"  ✅ 预览完成，未执行任何操作")
        return 0

    # 备份 skill 目录
    if skill_dir.exists():
        backups_dir = pack_dir / "backups"
        backups_dir.mkdir(parents=True, exist_ok=True)
        backup_target = backups_dir / skill_id
        if backup_target.exists():
            shutil.rmtree(backup_target)
        try:
            shutil.copytree(skill_dir, backup_target)
            print(f"     📦 已备份: {backup_target}")
        except Exception as e:
            print(f"  ⚠️  备份失败: {e}")

        # 删除原目录
        try:
            shutil.rmtree(skill_dir)
        except Exception as e:
            print(f"  ⚠️  删除失败: {e}")

    # 从 YAML 中移除
    skills.pop(skill_idx)
    data["skills"] = skills

    # 版本递增 patch
    data["version"] = _bump_version(data.get("version", "1.0.0"), "patch")

    if not _write_yaml_file(yaml_path, data):
        print(f"❌ 写入 {yaml_path} 失败")
        return 1

    print(f"  ✅ Skill '{skill_name}' ({skill_id}) 已从 {pack_name} 移除")
    print(f"     版本: v{data['version']}")
    return 0


def cmd_skill_list(pack_name: str) -> int:
    """列出能力包中的 skill

    cap-pack skill list <pack>
    """
    pack_dir = _find_pack_dir(pack_name)
    if pack_dir is None:
        print(f"❌ 找不到能力包 '{pack_name}'")
        return 1

    yaml_path = pack_dir / "cap-pack.yaml"
    if not yaml_path.exists():
        yaml_path = pack_dir / "cap-pack.yml"
    if not yaml_path.exists():
        print(f"❌ 找不到 {pack_name} 的 cap-pack.yaml")
        return 1

    data = _read_yaml_file(yaml_path)
    if data is None:
        print(f"❌ 无法读取 {yaml_path}")
        return 1

    skills = data.get("skills", [])
    if not skills or not isinstance(skills, list):
        print(f"  📭 '{pack_name}' 没有 skill")
        return 0

    ver = data.get("version", "?")
    _print_header(f"📋 {pack_name} (v{ver}) — {len(skills)} 个 skill")

    for s in skills:
        if not isinstance(s, dict):
            continue
        sid = s.get("id", "?")
        name = s.get("name", sid)
        desc = s.get("description", "")
        sver = s.get("version", "")
        tags = s.get("tags", [])
        desc_short = desc[:55] + "..." if len(desc) > 55 else desc
        tags_str = f" [{', '.join(tags[:3])}]" if tags else ""
        ver_str = f" v{sver}" if sver else ""
        print(f"  📄 {sid:<25s}  {ver_str}  {desc_short}{tags_str}")

    return 0


def cmd_skill_update(pack_name: str, skill_id: str, source_path_str: str | None = None) -> int:
    """更新能力包中的 skill

    cap-pack skill update <pack> <skill_id> [source_path]

    相当于 skill remove + skill add 合并执行。
    如果未指定 source_path，尝试从原路径或 Hermes skill 位置读取。
    """
    pack_dir = _find_pack_dir(pack_name)
    if pack_dir is None:
        print(f"❌ 找不到能力包 '{pack_name}'")
        return 1

    yaml_path = pack_dir / "cap-pack.yaml"
    if not yaml_path.exists():
        yaml_path = pack_dir / "cap-pack.yml"
    if not yaml_path.exists():
        print(f"❌ 找不到 {pack_name} 的 cap-pack.yaml")
        return 1

    data = _read_yaml_file(yaml_path)
    if data is None:
        print(f"❌ 无法读取 {yaml_path}")
        return 1

    # 查找 skill 条目
    skills = data.get("skills", [])
    skill_idx = None
    for i, s in enumerate(skills):
        if isinstance(s, dict) and s.get("id") == skill_id:
            skill_idx = i
            break

    if skill_idx is None:
        print(f"❌ 未找到 skill '{skill_id}'")
        return 1

    skill_entry = skills[skill_idx]
    _print_header(f"📦 更新 skill: {skill_id}")

    # 确定 source 路径
    source_path: Path | None = None

    if source_path_str:
        source_path = Path(source_path_str).resolve()
        if not source_path.exists():
            print(f"❌ 源路径不存在: {source_path}")
            return 1
    else:
        # 未指定源路径，尝试自动查找
        # 1. 检查 source 字段
        src_field = skill_entry.get("source", "")
        if src_field:
            candidate = PROJECT_ROOT / src_field
            if candidate.exists() and (candidate / "SKILL.md").exists():
                source_path = candidate
            elif Path(src_field).expanduser().exists():
                source_path = Path(src_field).expanduser()
        # 2. 检查 Hermes skills 目录
        if source_path is None:
            hermes_skill_dir = HERMES_HOME / "skills" / skill_id
            if hermes_skill_dir.exists() and (hermes_skill_dir / "SKILL.md").exists():
                source_path = hermes_skill_dir
        # 3. 使用已有的 SKILLS 目录（原地更新 YAML 条目）
        if source_path is None:
            existing_skill_dir = pack_dir / "SKILLS" / skill_id
            if existing_skill_dir.exists() and (existing_skill_dir / "SKILL.md").exists():
                source_path = existing_skill_dir

    if source_path is None:
        print(f"❌ 无法确定源路径，请指定 <source_path>")
        return 1

    if not (source_path / "SKILL.md").exists():
        print(f"❌ 源路径不是有效的 skill 目录 (缺少 SKILL.md): {source_path}")
        return 1

    # 提取新信息
    new_info = _extract_skill_info(source_path)

    # 复制/更新 skill 目录
    target_dir = pack_dir / "SKILLS" / skill_id

    # 备份旧目录
    if target_dir.exists():
        backups_dir = pack_dir / "backups"
        backups_dir.mkdir(parents=True, exist_ok=True)
        backup_target = backups_dir / f"{skill_id}.pre-update"
        if backup_target.exists():
            shutil.rmtree(backup_target)
        try:
            shutil.copytree(target_dir, backup_target)
            print(f"     📦 已备份旧目录: {backup_target.name}")
        except Exception as e:
            print(f"  ⚠️  备份失败: {e}")

        # 删除旧目录
        shutil.rmtree(target_dir)

    # 复制新内容
    try:
        shutil.copytree(source_path, target_dir)
    except Exception as e:
        print(f"❌ 复制失败: {e}")
        # 尝试恢复备份
        if backup_target.exists():
            try:
                shutil.copytree(backup_target, target_dir)
                print(f"     ♻️  已从备份恢复")
            except Exception:
                pass
        return 1

    # 更新 YAML 条目
    updated_entry = {
        "id": skill_id,
        "name": new_info["name"],
        "description": new_info["description"],
        "version": new_info["version"],
    }
    # 保留原有 tags 和 source
    if "tags" in skill_entry:
        updated_entry["tags"] = skill_entry["tags"]
    if "source" in skill_entry:
        updated_entry["source"] = skill_entry["source"]
    elif source_path_str:
        try:
            rel_path = Path(source_path_str).relative_to(PROJECT_ROOT)
            updated_entry["source"] = str(rel_path)
        except ValueError:
            pass

    # 替换旧的 skill 条目
    skills[skill_idx] = updated_entry
    data["skills"] = skills

    # 版本递增 patch
    data["version"] = _bump_version(data.get("version", "1.0.0"), "patch")

    if not _write_yaml_file(yaml_path, data):
        print(f"❌ 写入 {yaml_path} 失败")
        return 1

    print(f"  ✅ Skill '{skill_id}' 已更新")
    print(f"     名称:    {new_info['name']}")
    print(f"     版本:    v{new_info['version']} (包版本: v{data['version']})")
    return 0
