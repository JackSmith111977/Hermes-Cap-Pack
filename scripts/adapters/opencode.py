"""
OpenCodeAdapter — 将能力包安装到 OpenCode CLI Agent

OpenCode 原生支持 SKILL.md 标准，并兼容 ~/.claude/skills/ 路径。
适配器将能力包安装到 ~/.config/opencode/skills/。

参考文档:
  - https://opencode.ai/docs/skills/
  - https://dev.opencode.ai/docs/rules/
  - https://open-code.ai/en/docs/config
"""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path
from typing import Optional

# ── 项目根路径 ──
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from scripts.uca.protocol import AgentAdapter, CapPack, AdapterResult

# ── 路径常量 ──────────────────────────────────────────

OPENCODE_CONFIG = Path.home() / ".config" / "opencode"
OPENCODE_SKILLS = OPENCODE_CONFIG / "skills"
OPENCODE_CONFIG_FILE = OPENCODE_CONFIG / "opencode.json"

# 也兼容 Claude 路径（OpenCode 原生读取）
CLAUDE_SKILLS = Path.home() / ".claude" / "skills"

TRACK_FILE = Path.home() / ".hermes" / "installed_opencode_packs.json"


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


def _load_json(path: Path) -> dict:
    if path.exists():
        try:
            return json.loads(path.read_text())
        except (json.JSONDecodeError, OSError):
            return {}
    return {}


def _write_json(path: Path, data: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")


def _rewrite_skill_for_opencode(skill_id: str, src_dir: Path, dst_dir: Path) -> bool:
    """将 Hermes 格式的 SKILL.md 转换为 OpenCode 兼容格式

    OpenCode 只识别以下 frontmatter 字段:
    - name (required)
    - description (required)
    - license (optional)
    - compatibility (optional)
    - metadata (optional, string-to-string map)
    """
    src_file = src_dir / "SKILL.md"
    if not src_file.exists():
        return False

    content = src_file.read_text()

    # 解析 frontmatter（如果有的话）
    frontmatter = {}
    body = content
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            try:
                import yaml
                frontmatter = yaml.safe_load(parts[1]) or {}
            except Exception:
                frontmatter = {}
            body = parts[2].strip() if len(parts) > 2 else ""

    # 构建 OpenCode 兼容的 frontmatter
    oc_frontmatter = {
        "name": skill_id,
        "description": frontmatter.get("description", f"Skill: {skill_id}"),
    }
    # OpenCode 只识别这些字段
    if frontmatter.get("license"):
        oc_frontmatter["license"] = frontmatter["license"]
    oc_frontmatter["compatibility"] = "opencode"
    oc_frontmatter["metadata"] = {
        "source": "hermes-cap-pack",
        "original_name": frontmatter.get("name", skill_id),
    }

    # 写入新文件
    dst_dir.mkdir(parents=True, exist_ok=True)
    import yaml
    new_content = "---\n"
    new_content += yaml.dump(oc_frontmatter, default_flow_style=False, allow_unicode=True)
    new_content += "---\n\n"
    new_content += body
    (dst_dir / "SKILL.md").write_text(new_content)
    return True


# ── OpenCodeAdapter ──────────────────────────────────


class OpenCodeAdapter:
    """OpenCode CLI Agent 适配器"""

    @property
    def name(self) -> str:
        return "opencode"

    @property
    def is_available(self) -> bool:
        """检查 OpenCode 是否已安装"""
        return shutil.which("opencode") is not None

    # ── 安装 ──

    def install(self, pack: CapPack, dry_run: bool = False, skip_deps: bool = False) -> AdapterResult:
        """安装能力包到 OpenCode"""
        if not dry_run and not self.is_available:
            return AdapterResult(
                success=False,
                pack_name=pack.name,
                action="install",
                errors=["OpenCode CLI 未安装"],
            )

        result = AdapterResult(
            success=True,
            pack_name=pack.name,
            action="install",
        )

        try:
            # Step 1: 安装 skills
            installed_skills = self._install_skills(pack, dry_run)
            result.details["installed_skills"] = installed_skills

            # Step 2: 注入 MCP 配置
            mcp_count = self._install_mcp(pack, dry_run)
            result.details["mcp_injected"] = mcp_count

            # Step 3: 记录跟踪（OpenCode 自动发现，但我们需要记录卸载信息）
            if not dry_run:
                tracked = _load_tracked()
                tracked[pack.name] = {
                    "version": pack.version,
                    "path": str(pack.pack_dir),
                    "installed_at": __import__("datetime").datetime.now().isoformat()[:19],
                    "skills": installed_skills,
                    "skill_count": len(installed_skills),
                    "mcp_count": mcp_count,
                }
                _save_tracked(tracked)

        except Exception as e:
            result.success = False
            result.errors.append(f"安装异常: {e}")

        return result

    def _install_skills(self, pack: CapPack, dry_run: bool) -> list[str]:
        """安装 skill 到 ~/.config/opencode/skills/{id}/"""
        installed = []
        for skill in pack.skills:
            src = pack.pack_dir / "SKILLS" / skill.id
            dst = OPENCODE_SKILLS / skill.id

            if not src.exists():
                continue

            if dry_run:
                installed.append(skill.id)
                continue

            # 转换并写入 OpenCode 格式的 SKILL.md
            success = _rewrite_skill_for_opencode(skill.id, src, dst)
            if success:
                installed.append(skill.id)

            # 如果有 references/scripts 等子目录，也复制
            for subdir in ["references", "scripts", "templates", "assets"]:
                sub_src = src / subdir
                if sub_src.exists() and sub_src.is_dir():
                    sub_dst = dst / subdir
                    if sub_dst.exists():
                        shutil.rmtree(sub_dst)
                    shutil.copytree(sub_src, sub_dst)

        return installed

    def _install_mcp(self, pack: CapPack, dry_run: bool) -> int:
        """注入 MCP 配置到 ~/.config/opencode/opencode.json

        OpenCode 的 MCP 配置格式:
        {
          "mcp": {
            "server-name": {
              "type": "local",
              "command": ["npx", "-y", "@package"],
              "environment": { "KEY": "value" }
            }
          }
        }
        """
        if not pack.mcp_configs:
            return 0

        if dry_run:
            return len(pack.mcp_configs)

        config = _load_json(OPENCODE_CONFIG_FILE)

        # 确保 mcp 字段存在
        if "mcp" not in config:
            config["mcp"] = {}

        injected = 0
        for mcp in pack.mcp_configs:
            server_name = mcp.name
            mcp_cfg = dict(mcp.config)

            # 转换格式：OpenCode 的 MCP 格式略有不同
            opencode_mcp = {
                "type": mcp_cfg.get("type", "local"),
            }
            if "command" in mcp_cfg:
                opencode_mcp["command"] = mcp_cfg["command"]
                if isinstance(opencode_mcp["command"], str):
                    opencode_mcp["command"] = ["bash", "-c", opencode_mcp["command"]]
            if "url" in mcp_cfg:
                opencode_mcp["url"] = mcp_cfg["url"]
            if "env" in mcp_cfg:
                opencode_mcp["environment"] = mcp_cfg["env"]

            if server_name not in config["mcp"]:
                config["mcp"][server_name] = opencode_mcp
                injected += 1

        _write_json(OPENCODE_CONFIG_FILE, config)
        return injected

    # ── 卸载 ──

    def uninstall(self, pack_name: str) -> AdapterResult:
        """卸载能力包"""
        result = AdapterResult(
            success=True,
            pack_name=pack_name,
            action="uninstall",
        )

        tracked = _load_tracked()
        if pack_name not in tracked:
            result.success = False
            result.errors.append(f"能力包 '{pack_name}' 未安装到 OpenCode")
            return result

        info = tracked[pack_name]
        removed = 0

        for sid in info.get("skills", []):
            skill_dir = OPENCODE_SKILLS / sid
            if skill_dir.exists():
                shutil.rmtree(skill_dir)
                removed += 1

        del tracked[pack_name]
        _save_tracked(tracked)

        result.details["removed"] = removed
        return result

    # ── 更新 ──

    def update(self, pack: CapPack, old_version: str) -> AdapterResult:
        result = AdapterResult(
            success=True,
            pack_name=pack.name,
            action="update",
            details={"old_version": old_version, "new_version": pack.version},
        )
        uninstall_result = self.uninstall(pack.name)
        if not uninstall_result.success:
            return uninstall_result
        return self.install(pack)

    # ── 列出已安装 ──

    def list_installed(self) -> list[dict]:
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

    # ── 验证（检查 OpenCode 实际是否发现了 skill）──

    def verify(self, pack_name: str) -> AdapterResult:
        """验证已安装的能力包（检查文件 + OpenCode 识别）"""
        result = AdapterResult(
            success=True,
            pack_name=pack_name,
            action="verify",
        )

        tracked = _load_tracked()
        if pack_name not in tracked:
            result.success = False
            result.errors.append(f"能力包 '{pack_name}' 未安装到 OpenCode")
            return result

        info = tracked[pack_name]
        skill_ids = info.get("skills", [])

        missing_skills = []
        valid_skills = []
        for sid in skill_ids:
            skill_file = OPENCODE_SKILLS / sid / "SKILL.md"
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

        # 额外检查：opencode debug skill 能否看到
        if valid_skills:
            result.warnings.append(
                f"已安装 {len(valid_skills)} 个 skill 到 {OPENCODE_SKILLS}\n"
                f"  运行 'opencode debug skill' 确认 OpenCode 已发现它们"
            )

        return result
