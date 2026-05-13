"""
HermesAdapter — 将能力包安装到 Hermes Agent

功能:
  - 安装 skill 文件到 ~/.hermes/skills/
  - MCP 配置注入到 ~/.hermes/config.yaml
  - 安装前快照 / 失败回滚
  - 验证安装完整性
"""

from __future__ import annotations

import json
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Optional

# ── 项目根路径 ──
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from scripts.uca.protocol import (
    AgentAdapter,
    CapPack,
    CapPackMCP,
    AdapterResult,
)

# ── 路径常量 ──────────────────────────────────────────

HERMES_HOME = Path.home() / ".hermes"
HERMES_SKILLS = HERMES_HOME / "skills"
HERMES_CONFIG = HERMES_HOME / "config.yaml"
TRACK_FILE = HERMES_HOME / "installed_packs.json"
SNAPSHOT_DIR = HERMES_HOME / ".uca-snapshots"


# ── 文件操作工具 ──────────────────────────────────────


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


def _load_yaml(path: Path) -> dict:
    """安全加载 YAML 文件"""
    import yaml
    with open(path) as f:
        return yaml.safe_load(f) or {}


def _write_yaml(path: Path, data: dict):
    """安全写入 YAML 文件"""
    import yaml
    # 保留原文件注释和格式的策略：直接 dump
    with open(path, "w") as f:
        yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)


# ── Snapshot 管理器 ───────────────────────────────────


class SnapshotManager:
    """安装前快照管理，用于失败回滚"""

    @staticmethod
    def create(pack_name: str) -> str | None:
        """创建当前状态快照，返回快照 ID"""
        snapshot_id = f"{pack_name}-{__import__('datetime').datetime.now().strftime('%Y%m%d%H%M%S')}"
        snap_path = SNAPSHOT_DIR / snapshot_id
        snap_path.mkdir(parents=True, exist_ok=True)

        # 快照 tracked 状态
        tracked = _load_tracked()
        if pack_name in tracked:
            state = dict(tracked[pack_name])
            state["_pack_name"] = pack_name
            (snap_path / "tracked.json").write_text(
                json.dumps(state, indent=2)
            )

        # 快照 skill 目录
        if pack_name in tracked:
            for sid in tracked[pack_name].get("skills", []):
                src = HERMES_SKILLS / sid
                if src.exists():
                    dst = snap_path / "skills" / sid
                    shutil.copytree(src, dst)

        # 快照 config.yaml 的 mcp_servers 部分
        if HERMES_CONFIG.exists():
            config = _load_yaml(HERMES_CONFIG)
            if "mcp_servers" in config:
                (snap_path / "mcp_servers.json").write_text(
                    json.dumps(config["mcp_servers"], indent=2)
                )

        return snapshot_id

    @staticmethod
    def restore(snapshot_id: str) -> list[str]:
        """从快照恢复，返回恢复操作日志"""
        snap_path = SNAPSHOT_DIR / snapshot_id
        if not snap_path.exists():
            return [f"快照不存在: {snapshot_id}"]

        ops = []

        # 恢复 skills
        skills_snap = snap_path / "skills"
        if skills_snap.exists():
            for skill_dir in skills_snap.iterdir():
                if skill_dir.is_dir():
                    dst = HERMES_SKILLS / skill_dir.name
                    if dst.exists():
                        shutil.rmtree(dst)
                    shutil.copytree(skill_dir, dst)
                    ops.append(f"恢复 skill: {skill_dir.name}")

        # 恢复 tracked 状态
        tracked_file = snap_path / "tracked.json"
        if tracked_file.exists():
            old_state = json.loads(tracked_file.read_text())
            tracked = _load_tracked()
            pack_name = old_state.pop("_pack_name", snap_path.name.split("-")[0])
            tracked[pack_name] = old_state
            _save_tracked(tracked)
            ops.append(f"恢复跟踪状态: {pack_name}")

        # 恢复 MCP 配置
        mcp_file = snap_path / "mcp_servers.json"
        if mcp_file.exists() and HERMES_CONFIG.exists():
            mcp_config = json.loads(mcp_file.read_text())
            config = _load_yaml(HERMES_CONFIG)
            config["mcp_servers"] = mcp_config
            _write_yaml(HERMES_CONFIG, config)
            ops.append("恢复 MCP 配置")

        # 清理快照
        shutil.rmtree(snap_path)
        ops.append(f"清理快照: {snapshot_id}")

        return ops

    @staticmethod
    def cleanup(snapshot_id: str):
        """安装成功后清理快照"""
        snap_path = SNAPSHOT_DIR / snapshot_id
        if snap_path.exists():
            shutil.rmtree(snap_path)


# ── HermesAdapter ────────────────────────────────────


class HermesAdapter:
    """Hermes Agent 适配器

    将能力包安装到 Hermes 环境：
    - Skills → ~/.hermes/skills/{name}/
    - MCP → ~/.hermes/config.yaml mcp_servers
    - 追踪 → ~/.hermes/installed_packs.json
    """

    # AgentAdapter Protocol 属性
    @property
    def name(self) -> str:
        return "hermes"

    @property
    def is_available(self) -> bool:
        """检查是否在 Hermes 环境中"""
        return HERMES_HOME.exists() and HERMES_CONFIG.exists()

    # ── 安装 ──

    def install(self, pack: CapPack, dry_run: bool = False) -> AdapterResult:
        """安装能力包到 Hermes"""
        if not dry_run and not self.is_available:
            return AdapterResult(
                success=False,
                pack_name=pack.name,
                action="install",
                errors=["Hermes 环境不可用 (未找到 ~/.hermes/config.yaml)"],
            )

        result = AdapterResult(
            success=True,
            pack_name=pack.name,
            action="install",
        )

        # Step 1: 创建快照（用于失败回滚）
        snapshot_id = None
        if not dry_run:
            snapshot_id = SnapshotManager.create(pack.name)
            result.details["snapshot_id"] = snapshot_id

        try:
            # Step 2: 安装 skills
            installed_skills = self._install_skills(pack, dry_run)
            result.details["installed_skills"] = installed_skills

            # Step 3: 注入 MCP 配置
            mcp_results = self._install_mcp(pack, dry_run)
            result.details["mcp_injected"] = mcp_results

            # Step 4: 记录跟踪
            if not dry_run:
                tracked = _load_tracked()
                tracked[pack.name] = {
                    "version": pack.version,
                    "path": str(pack.pack_dir),
                    "installed_at": __import__("datetime").datetime.now().isoformat()[:19],
                    "skills": installed_skills,
                    "skill_count": len(installed_skills),
                    "experience_count": len(pack.experiences),
                    "mcp_count": mcp_results,
                }
                _save_tracked(tracked)

            # Step 5: 成功 → 清理快照
            if not dry_run and snapshot_id:
                SnapshotManager.cleanup(snapshot_id)
                result.details.pop("snapshot_id", None)

        except Exception as e:
            result.success = False
            result.errors.append(f"安装异常: {e}")
            # 回滚
            if snapshot_id:
                ops = SnapshotManager.restore(snapshot_id)
                result.details["rollback_ops"] = ops
                result.warnings.append("已自动回滚到安装前状态")

        return result

    def _install_skills(self, pack: CapPack, dry_run: bool) -> list[str]:
        """安装 skill 文件，返回已安装的 skill ID 列表"""
        installed = []
        for skill in pack.skills:
            src = pack.pack_dir / "SKILLS" / skill.id
            dst = HERMES_SKILLS / skill.id

            if not src.exists():
                continue

            if dry_run:
                installed.append(skill.id)
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

        return installed

    def _install_mcp(self, pack: CapPack, dry_run: bool) -> int:
        """注入 MCP 配置到 config.yaml，返回注入数"""
        if not pack.mcp_configs:
            return 0

        if dry_run:
            return len(pack.mcp_configs)

        if not HERMES_CONFIG.exists():
            return 0

        config = _load_yaml(HERMES_CONFIG)

        # 确保 mcp_servers 存在
        if "mcp_servers" not in config:
            config["mcp_servers"] = {}

        # 注入每个 MCP 配置
        injected = 0
        for mcp in pack.mcp_configs:
            server_name = mcp.name
            if server_name not in config["mcp_servers"]:
                config["mcp_servers"][server_name] = mcp.config
                injected += 1
            else:
                # 已存在，合并配置
                existing = config["mcp_servers"][server_name]
                for k, v in mcp.config.items():
                    if k not in existing:
                        existing[k] = v
                        injected += 1

        _write_yaml(HERMES_CONFIG, config)
        return injected

    # ── 卸载 ──

    def uninstall(self, pack_name: str) -> AdapterResult:
        """卸载能力包，含备份恢复"""
        result = AdapterResult(
            success=True,
            pack_name=pack_name,
            action="uninstall",
        )

        tracked = _load_tracked()
        if pack_name not in tracked:
            result.success = False
            result.errors.append(f"能力包 '{pack_name}' 未安装")
            return result

        info = tracked[pack_name]
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

        result.details["removed"] = removed
        result.details["restored_from_backup"] = restored
        return result

    # ── 更新 ──

    def update(self, pack: CapPack, old_version: str) -> AdapterResult:
        """更新能力包到新版本"""
        result = AdapterResult(
            success=True,
            pack_name=pack.name,
            action="update",
            details={"old_version": old_version, "new_version": pack.version},
        )

        # 先卸载旧版本（保留备份）
        uninstall_result = self.uninstall(pack.name)
        if not uninstall_result.success:
            return uninstall_result

        # 再安装新版本
        install_result = self.install(pack)
        if not install_result.success:
            # 安装失败，尝试恢复旧版本
            result.warnings.append("新版本安装失败，已保留旧版本备份")
            return install_result

        result.details["updated_skills"] = install_result.details.get("installed_skills", [])
        return result

    # ── 列出已安装 ──

    def list_installed(self) -> list[dict]:
        """列出已安装的能力包"""
        tracked = _load_tracked()
        return [
            {
                "name": name,
                "version": info.get("version", "?"),
                "installed_at": info.get("installed_at", ""),
                "skill_count": info.get("skill_count", len(info.get("skills", []))),
            }
            for name, info in sorted(tracked.items())
        ]

    # ── 验证 ──

    def verify(self, pack_name: str) -> AdapterResult:
        """验证已安装的能力包"""
        result = AdapterResult(
            success=True,
            pack_name=pack_name,
            action="verify",
        )

        tracked = _load_tracked()
        if pack_name not in tracked:
            result.success = False
            result.errors.append(f"能力包 '{pack_name}' 未安装")
            return result

        info = tracked[pack_name]
        skill_ids = info.get("skills", [])

        # 检查每个 skill 文件
        missing_skills = []
        valid_skills = []
        for sid in skill_ids:
            skill_file = HERMES_SKILLS / sid / "SKILL.md"
            if skill_file.exists():
                valid_skills.append(sid)
            else:
                missing_skills.append(sid)

        result.details["total_skills"] = len(skill_ids)
        result.details["valid_skills"] = len(valid_skills)
        result.details["missing_skills"] = missing_skills

        if missing_skills:
            result.success = False
            for sid in missing_skills:
                result.errors.append(f"缺失 skill: {sid}")

        # 获取包路径检查 MCP（如果 manifest 有记录）
        pack_path = info.get("path", "")
        if pack_path:
            pack_dir = Path(pack_path)
            manifest_file = pack_dir / "cap-pack.yaml"
            if manifest_file.exists():
                manifest = _load_yaml(manifest_file)
                if "mcp_servers" in manifest:
                    result.details["has_mcp_config"] = True
                    # 验证 MCP 是否已注入
                    if HERMES_CONFIG.exists():
                        config = _load_yaml(HERMES_CONFIG)
                        configured = [m["id"] for m in manifest["mcp_servers"]]
                        actual = list(config.get("mcp_servers", {}).keys())
                        missing_mcp = [m for m in configured if m not in actual]
                        if missing_mcp:
                            result.warnings.append(f"MCP 服务未配置: {missing_mcp}")

        return result
