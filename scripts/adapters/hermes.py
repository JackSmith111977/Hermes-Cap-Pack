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
import os
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

    def install(self, pack: CapPack, dry_run: bool = False, skip_deps: bool = False) -> AdapterResult:
        """安装能力包到 Hermes

        Args:
            pack: 要安装的能力包
            dry_run: 仅预览不实际安装
            skip_deps: 跳过依赖检查
        """
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

        # Step 0: 依赖检查（非阻塞，缺失只警告不阻塞）
        if not dry_run:
            missing_deps = self._check_dependencies(pack, skip_deps)
            if missing_deps:
                result.warnings.append(f"缺失依赖包: {', '.join(missing_deps)}")

        # Step 1: 创建快照（用于失败回滚）
        snapshot_id = None
        if not dry_run:
            snapshot_id = SnapshotManager.create(pack.name)
            result.details["snapshot_id"] = snapshot_id

        try:
            # Step 2: 安装 skills
            installed_skills = self._install_skills(pack, dry_run)
            result.details["installed_skills"] = installed_skills

            # Step 3: 安装 scripts（install.scripts → ~/.hermes/scripts/）
            installed_scripts = self._install_scripts(pack, dry_run)
            result.details["installed_scripts"] = installed_scripts

            # Step 4: 复制 references
            installed_refs = self._install_references(pack, dry_run)
            result.details["installed_references"] = installed_refs

            # Step 5: 注入 MCP 配置
            mcp_results = self._install_mcp(pack, dry_run)
            result.details["mcp_injected"] = mcp_results

            # Step 6: 执行 post_install 脚本
            if not dry_run:
                post_install_ok = self._run_post_install(pack)
                if not post_install_ok:
                    result.warnings.append("部分 post_install 命令执行失败")

            # Step 7: 验证门禁（失败 → 自动回滚）
            if not dry_run:
                verify_result = self._verify_installation(pack)
                result.details["verification"] = {
                    "passed": verify_result["passed"],
                    "check_count": len(verify_result["checks"]),
                    "failure_count": len(verify_result["failures"]),
                }
                if not verify_result["passed"]:
                    for f in verify_result["failures"]:
                        result.errors.append(f"验证失败: {f}")
                    # 自动回滚
                    if snapshot_id:
                        ops = SnapshotManager.restore(snapshot_id)
                        result.details["rollback_ops"] = ops
                        result.warnings.append("验证门禁未通过，已自动回滚到安装前状态")
                        snapshot_id = None  # 防止再次清理
                    result.success = False
                    return result

            # Step 8: 记录跟踪
            if not dry_run:
                tracked = _load_tracked()
                # 收集 script target 路径（用于后续 verify 检查）
                script_targets = []
                manifest = pack.manifest
                install_cfg = manifest.get("install", {})
                for entry in install_cfg.get("scripts", []):
                    dst_abs = entry.get("target", "")
                    if dst_abs:
                        script_targets.append(str(Path(dst_abs).expanduser()))
                tracked[pack.name] = {
                    "version": pack.version,
                    "path": str(pack.pack_dir),
                    "installed_at": __import__("datetime").datetime.now().isoformat()[:19],
                    "skills": installed_skills,
                    "skill_count": len(installed_skills),
                    "script_count": len(installed_scripts),
                    "script_targets": script_targets,
                    "experience_count": len(pack.experiences),
                    "mcp_count": mcp_results,
                }
                _save_tracked(tracked)

            # Step 9: 成功 → 清理快照
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

    def _install_scripts(self, pack: CapPack, dry_run: bool) -> list[str]:
        """安装 scripts（install.scripts → ~/.hermes/scripts/）"""
        installed = []
        manifest = pack.manifest
        install_cfg = manifest.get("install", {})
        scripts_cfg = install_cfg.get("scripts", [])

        for entry in scripts_cfg:
            src_rel = entry.get("source", "")
            dst_abs = entry.get("target", "")
            if not src_rel or not dst_abs:
                continue

            src_path = pack.pack_dir / src_rel
            dst_path = Path(dst_abs).expanduser()

            if not src_path.exists():
                continue

            if dry_run:
                installed.append(src_rel)
                continue

            # 确保目标目录存在
            dst_path.parent.mkdir(parents=True, exist_ok=True)

            # 备份已有
            if dst_path.exists():
                bak_path = dst_path.with_suffix(dst_path.suffix + ".bak")
                if bak_path.exists():
                    bak_path.unlink()
                shutil.copy2(dst_path, bak_path)

            # 复制
            shutil.copy2(src_path, dst_path)
            installed.append(src_rel)

        return installed

    def _install_references(self, pack: CapPack, dry_run: bool) -> list[str]:
        """复制 references（install.references）"""
        installed = []
        manifest = pack.manifest
        install_cfg = manifest.get("install", {})
        refs_cfg = install_cfg.get("references", [])

        for entry in refs_cfg:
            src_rel = entry.get("source", "")
            dst_abs = entry.get("target", "")
            if not src_rel or not dst_abs:
                continue

            src_path = pack.pack_dir / src_rel
            dst_path = Path(dst_abs).expanduser()

            if not src_path.exists():
                continue

            if dry_run:
                installed.append(src_rel)
                continue

            # 目录 vs 文件
            if src_path.is_dir():
                dst_path.mkdir(parents=True, exist_ok=True)
                for item in src_path.iterdir():
                    if item.is_file():
                        shutil.copy2(item, dst_path / item.name)
            else:
                dst_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src_path, dst_path)

            installed.append(src_rel)

        return installed

    def _run_post_install(self, pack: CapPack) -> bool:
        """执行 post_install 命令"""
        manifest = pack.manifest
        install_cfg = manifest.get("install", {})
        post_cmds = install_cfg.get("post_install", [])

        all_ok = True
        for cmd in post_cmds:
            try:
                result = __import__("subprocess").run(
                    cmd, shell=True, capture_output=True, text=True, timeout=30
                )
                if result.returncode != 0:
                    print(f"  ⚠️  post_install 命令失败: {cmd}")
                    print(f"     stderr: {result.stderr.strip()}")
                    all_ok = False
            except Exception as e:
                print(f"  ⚠️  post_install 命令异常: {cmd} → {e}")
                all_ok = False

        return all_ok

    # ── 依赖检查 ──

    def _check_dependencies(self, pack: CapPack, skip_deps: bool = False) -> list[str]:
        """检查包级依赖是否已安装，返回缺失依赖列表（非阻塞）"""
        if skip_deps:
            return []

        if not pack.depends_on:
            return []

        tracked = _load_tracked()
        missing = []
        for dep_name, dep_info in pack.depends_on.items():
            if dep_name not in tracked:
                reason = ""
                if isinstance(dep_info, dict):
                    reason = dep_info.get("reason", "")
                msg = dep_name
                if reason:
                    msg += f" ({reason})"
                missing.append(msg)

        return missing

    # ── 验证门禁 ──

    def _verify_installation(self, pack: CapPack) -> dict:
        """安装后验证门禁：检查 skill / 脚本 / YAML 前端

        Returns:
            dict: {"passed": bool, "checks": list[str], "failures": list[str]}
        """
        checks = []
        failures = []

        # 1. 检查每个 skill SKILL.md 是否存在
        for skill in pack.skills:
            src = pack.pack_dir / "SKILLS" / skill.id
            skill_file = src / "SKILL.md"
            if skill_file.exists():
                checks.append(f"skill {skill.id}: SKILL.md 存在")
                # 2. 检查 YAML frontmatter
                content = skill_file.read_text()
                if content.startswith("---"):
                    # 基本 frontmatter 完整性检查
                    try:
                        import yaml
                        parts = content.split("---", 2)
                        if len(parts) >= 3:
                            fm = yaml.safe_load(parts[1])
                            if isinstance(fm, dict):
                                has_id = "id" in fm or "name" in fm or "description" in fm
                                if has_id:
                                    checks.append(f"skill {skill.id}: YAML frontmatter 完整")
                                else:
                                    failures.append(f"skill {skill.id}: YAML frontmatter 缺少 id/name/description")
                            else:
                                failures.append(f"skill {skill.id}: YAML frontmatter 不是对象")
                        else:
                            failures.append(f"skill {skill.id}: frontmatter 未闭合")
                    except Exception as e:
                        failures.append(f"skill {skill.id}: YAML frontmatter 解析失败: {e}")
                else:
                    failures.append(f"skill {skill.id}: 缺少 YAML frontmatter (---)")
            else:
                failures.append(f"skill {skill.id}: SKILL.md 不存在")

        # 3. 检查脚本可执行性
        manifest = pack.manifest
        install_cfg = manifest.get("install", {})
        for entry in install_cfg.get("scripts", []):
            dst_abs = entry.get("target", "")
            if not dst_abs:
                continue
            dst_path = Path(dst_abs).expanduser()
            if dst_path.exists():
                checks.append(f"script {dst_path.name}: 文件存在")
                # 检查可执行权限
                if not os.access(str(dst_path), os.X_OK):
                    failures.append(f"script {dst_path.name}: 缺少可执行权限")
                else:
                    checks.append(f"script {dst_path.name}: 可执行权限正确")
            else:
                failures.append(f"script {dst_path.name}: 文件不存在")

        return {
            "passed": len(failures) == 0,
            "checks": checks,
            "failures": failures,
        }

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
        import yaml
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

        # 1. 检查每个 skill 文件 + YAML frontmatter
        missing_skills = []
        valid_skills = []
        bad_frontmatter_skills = []
        for sid in skill_ids:
            skill_file = HERMES_SKILLS / sid / "SKILL.md"
            if skill_file.exists():
                valid_skills.append(sid)
                # 检查 YAML frontmatter
                content = skill_file.read_text()
                if content.startswith("---"):
                    try:
                        parts = content.split("---", 2)
                        if len(parts) >= 3:
                            fm = yaml.safe_load(parts[1])
                            if isinstance(fm, dict) and ("id" in fm or "name" in fm or "description" in fm):
                                pass  # OK
                            else:
                                bad_frontmatter_skills.append(f"{sid}(不完整YAML)")
                        else:
                            bad_frontmatter_skills.append(f"{sid}(frontmatter未闭合)")
                    except Exception as e:
                        bad_frontmatter_skills.append(f"{sid}(解析失败:{e})")
                else:
                    bad_frontmatter_skills.append(f"{sid}(无frontmatter)")
            else:
                missing_skills.append(sid)

        result.details["total_skills"] = len(skill_ids)
        result.details["valid_skills"] = len(valid_skills)
        result.details["missing_skills"] = missing_skills
        result.details["bad_frontmatter_skills"] = bad_frontmatter_skills

        if missing_skills:
            result.success = False
            for sid in missing_skills:
                result.errors.append(f"缺失 skill: {sid}")

        if bad_frontmatter_skills:
            result.warnings.append(f"YAML frontmatter 问题: {', '.join(bad_frontmatter_skills)}")

        # 2. 检查脚本可执行性
        script_targets = info.get("script_targets", [])
        bad_scripts = []
        for script_path in script_targets:
            sp = Path(script_path)
            if sp.exists():
                if not os.access(str(sp), os.X_OK):
                    bad_scripts.append(f"{sp.name}(不可执行)")
            else:
                bad_scripts.append(f"{sp.name}(文件不存在)")

        result.details["script_count"] = len(script_targets)
        result.details["bad_scripts"] = bad_scripts
        if bad_scripts:
            result.warnings.append(f"脚本问题: {', '.join(bad_scripts)}")

        # 3. 获取包路径检查 MCP
        pack_path = info.get("path", "")
        if pack_path:
            pack_dir = Path(pack_path)
            manifest_file = pack_dir / "cap-pack.yaml"
            if manifest_file.exists():
                manifest = _load_yaml(manifest_file)
                if "mcp_servers" in manifest:
                    result.details["has_mcp_config"] = True
                    if HERMES_CONFIG.exists():
                        config = _load_yaml(HERMES_CONFIG)
                        configured = [m["id"] for m in manifest["mcp_servers"]]
                        actual = list(config.get("mcp_servers", {}).keys())
                        missing_mcp = [m for m in configured if m not in actual]
                        if missing_mcp:
                            result.warnings.append(f"MCP 服务未配置: {missing_mcp}")

        return result
