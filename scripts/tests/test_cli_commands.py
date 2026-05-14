"""Tests for CLI commands — upgrade, search, status, skill management"""

import pytest
import json
import yaml
import shutil
from pathlib import Path

from scripts.cli.commands import (
    cmd_upgrade,
    cmd_search,
    cmd_status,
    cmd_skill_add,
    cmd_skill_remove,
    cmd_skill_list,
    cmd_skill_update,
    _read_installed_packs,
    _find_pack_dir,
    _bump_version,
)


# ── Fixtures ──────────────────────────────────────────────────────


@pytest.fixture
def project_root(tmp_path: Path, monkeypatch) -> Path:
    """模拟项目根目录，含 schemas/ 和 packs/"""
    root = tmp_path / "hermes-cap-pack"
    root.mkdir()

    # schemas/cap-pack-v1.schema.json
    schema_dir = root / "schemas"
    schema_dir.mkdir()
    schema = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "required": ["name", "version"],
        "properties": {
            "name": {"type": "string"},
            "version": {"type": "string"},
            "skills": {"type": "array"},
        },
    }
    with open(schema_dir / "cap-pack-v1.schema.json", "w") as f:
        json.dump(schema, f)

    # packs/ 目录
    (root / "packs").mkdir()

    # 注入 PROJECT_ROOT
    import scripts.cli.commands as cmds
    monkeypatch.setattr(cmds, "PROJECT_ROOT", root)
    monkeypatch.setattr(cmds, "SCHEMA_PATH", schema_dir / "cap-pack-v1.schema.json")

    return root


@pytest.fixture
def hermes_home(tmp_path: Path, monkeypatch) -> Path:
    """模拟 ~/.hermes/ 目录"""
    hh = tmp_path / ".hermes"
    hh.mkdir()
    (hh / "skills").mkdir()
    (hh / "scripts").mkdir()

    import scripts.cli.commands as cmds
    monkeypatch.setattr(cmds, "HERMES_HOME", hh)
    monkeypatch.setattr(cmds, "INSTALLED_PACKS_PATH", hh / "installed_packs.json")

    return hh


@pytest.fixture
def sample_skill_dir(tmp_path) -> Path:
    """创建一个模拟 skill 目录"""
    d = tmp_path / "skills" / "my-skill"
    d.mkdir(parents=True)
    (d / "SKILL.md").write_text("""---
id: my-skill
name: My Skill
description: A test skill for CLI tests
version: 1.0.0
---
# My Skill
Test content
""")
    return d


@pytest.fixture
def demo_pack(project_root: Path) -> Path:
    """在 packs/ 中创建测试用的能力包"""
    pack_dir = project_root / "packs" / "demo-pack"
    pack_dir.mkdir()

    # cap-pack.yaml
    manifest = {
        "name": "demo-pack",
        "version": "2.0.0",
        "type": "capability-pack",
        "description": "Demo pack for testing CLI commands",
        "author": "boku",
        "created": "2026-05-14",
        "skills": [
            {"id": "skill-a", "path": "SKILLS/skill-a/SKILL.md", "description": "First skill", "tags": ["test"]},
            {"id": "skill-b", "path": "SKILLS/skill-b/SKILL.md", "description": "Second skill"},
        ],
        "experiences": [],
        "compatibility": {"agent_types": ["hermes", "opencode"]},
    }
    with open(pack_dir / "cap-pack.yaml", "w") as f:
        yaml.dump(manifest, f)

    # SKILLS/ 目录
    for sid in ["skill-a", "skill-b"]:
        d = pack_dir / "SKILLS" / sid
        d.mkdir(parents=True)
        (d / "SKILL.md").write_text(f"""---
id: {sid}
name: {sid}
description: Skill {sid}
---
# {sid}
""")

    return pack_dir


# ── Helper Tests ──────────────────────────────────────────────────


class TestHelpers:
    def test_find_pack_dir_found(self, project_root: Path, demo_pack: Path):
        result = _find_pack_dir("demo-pack")
        assert result is not None
        assert result.name == "demo-pack"

    def test_find_pack_dir_not_found(self, project_root: Path):
        result = _find_pack_dir("nonexistent")
        assert result is None

    def test_bump_version_patch(self):
        assert _bump_version("1.0.0", "patch") == "1.0.1"
        assert _bump_version("2.3.4", "patch") == "2.3.5"

    def test_bump_version_minor(self):
        assert _bump_version("1.0.0", "minor") == "1.1.0"
        assert _bump_version("2.3.4", "minor") == "2.4.0"

    def test_bump_version_major(self):
        assert _bump_version("1.0.0", "major") == "2.0.0"
        assert _bump_version("2.3.4", "major") == "3.0.0"

    def test_bump_version_short(self):
        assert _bump_version("1", "minor") == "1.1.0"

    def test_bump_version_invalid(self):
        assert _bump_version("abc", "patch") == "abc"


# ── Status Tests ──────────────────────────────────────────────────


class TestCmdStatus:
    def test_status_empty(self, project_root: Path, hermes_home: Path):
        """没有已安装的包时 status 正常显示"""
        exit_code = cmd_status()
        assert exit_code == 0

    def test_status_with_installed(self, project_root: Path, hermes_home: Path):
        """有已安装的包时也正常"""
        # 模拟已安装包
        installed = {
            "demo-pack": {
                "version": "2.0.0",
                "skill_count": 2,
                "installed_at": "2026-05-14T12:00:00",
            }
        }
        hermes_home.joinpath("installed_packs.json").write_text(json.dumps(installed))
        exit_code = cmd_status()
        assert exit_code == 0


# ── Search Tests ──────────────────────────────────────────────────


class TestCmdSearch:
    def test_search_match_name(self, project_root: Path, demo_pack: Path, capsys):
        exit_code = cmd_search("demo")
        assert exit_code == 0

    def test_search_match_skill(self, project_root: Path, demo_pack: Path, capsys):
        exit_code = cmd_search("skill-a")
        assert exit_code == 0

    def test_search_no_match(self, project_root: Path, capsys):
        exit_code = cmd_search("zzz_nonexistent")
        assert exit_code == 0

    def test_search_empty_packs_dir(self, project_root: Path, capsys):
        """packs/ 目录为空时搜索也能工作"""
        exit_code = cmd_search("anything")
        assert exit_code == 0


# ── Upgrade Tests ─────────────────────────────────────────────────


class TestCmdUpgrade:
    def test_upgrade_no_installed(self, project_root: Path, hermes_home: Path, capsys):
        """没有已安装的包时 upgrade 返回 1"""
        exit_code = cmd_upgrade("demo-pack")
        assert exit_code == 1

    def test_upgrade_dry_run(self, project_root: Path, hermes_home: Path, demo_pack: Path, capsys):
        """--dry-run 不实际修改"""
        installed = {"demo-pack": {"version": "1.0.0"}}
        hermes_home.joinpath("installed_packs.json").write_text(json.dumps(installed))
        exit_code = cmd_upgrade("demo-pack", dry_run=True)
        assert exit_code == 0

    def test_upgrade_not_found(self, project_root: Path, hermes_home: Path, capsys):
        """未安装的包名提示错误"""
        installed = {"other-pack": {"version": "1.0.0"}}
        hermes_home.joinpath("installed_packs.json").write_text(json.dumps(installed))
        exit_code = cmd_upgrade("nonexistent")
        assert exit_code == 1

    def test_upgrade_already_latest(self, project_root: Path, hermes_home: Path, demo_pack: Path, capsys):
        """已是最新版本时提示"""
        installed = {"demo-pack": {"version": "2.0.0"}}
        hermes_home.joinpath("installed_packs.json").write_text(json.dumps(installed))
        exit_code = cmd_upgrade("demo-pack")
        assert exit_code == 0

    def test_upgrade_pack_dir_not_found(self, project_root: Path, hermes_home: Path, capsys):
        """pack 目录不存在时优雅报错"""
        installed = {"ghost-pack": {"version": "1.0.0"}}
        hermes_home.joinpath("installed_packs.json").write_text(json.dumps(installed))
        exit_code = cmd_upgrade("ghost-pack")
        assert exit_code == 1


# ── Skill Add Tests ──────────────────────────────────────────────


class TestCmdSkillAdd:
    def test_skill_add_success(self, project_root: Path, demo_pack: Path, sample_skill_dir: Path, capsys):
        exit_code = cmd_skill_add("demo-pack", str(sample_skill_dir))
        assert exit_code == 0
        # 验证 skill 已添加到目录
        skill_dir = demo_pack / "SKILLS" / "my-skill"
        assert skill_dir.exists()
        assert (skill_dir / "SKILL.md").exists()
        # 验证 cap-pack.yaml 已更新
        manifest = yaml.safe_load((demo_pack / "cap-pack.yaml").read_text())
        skill_ids = [s["id"] for s in manifest.get("skills", [])]
        assert "my-skill" in skill_ids
        # 版本应当增加 minor
        assert manifest["version"] == "2.1.0"

    def test_skill_add_pack_not_found(self, project_root: Path, sample_skill_dir: Path, capsys):
        exit_code = cmd_skill_add("nonexistent", str(sample_skill_dir))
        assert exit_code == 1

    def test_skill_add_source_not_found(self, project_root: Path, demo_pack: Path, capsys):
        exit_code = cmd_skill_add("demo-pack", "/tmp/nonexistent-skill")
        assert exit_code == 1

    def test_skill_add_duplicate(self, project_root: Path, demo_pack: Path, sample_skill_dir: Path, capsys):
        """添加两次相同的 skill 应当失败"""
        cmd_skill_add("demo-pack", str(sample_skill_dir))
        exit_code = cmd_skill_add("demo-pack", str(sample_skill_dir))
        assert exit_code == 1

    def test_skill_add_no_skill_md(self, project_root: Path, demo_pack: Path, tmp_path, capsys):
        """没有 SKILL.md 的目录应当被拒绝"""
        bad_dir = tmp_path / "bad-skill"
        bad_dir.mkdir()
        exit_code = cmd_skill_add("demo-pack", str(bad_dir))
        assert exit_code == 1

    def test_skill_add_rollback_on_write_fail(self, project_root: Path, demo_pack: Path, sample_skill_dir: Path, monkeypatch, capsys):
        """YAML 写入失败时自动回滚"""
        def _broken_write(*args, **kwargs):
            return False
        import scripts.cli.commands as cmds
        monkeypatch.setattr(cmds, "_write_yaml_file", _broken_write)
        exit_code = cmd_skill_add("demo-pack", str(sample_skill_dir))
        assert exit_code == 1
        # 验证没有残留文件
        assert not (demo_pack / "SKILLS" / "my-skill").exists()


# ── Skill Remove Tests ────────────────────────────────────────────


class TestCmdSkillRemove:
    def test_skill_remove_success(self, project_root: Path, demo_pack: Path, capsys):
        exit_code = cmd_skill_remove("demo-pack", "skill-a")
        assert exit_code == 0
        # 验证已从 YAML 移除
        manifest = yaml.safe_load((demo_pack / "cap-pack.yaml").read_text())
        skill_ids = [s["id"] for s in manifest.get("skills", [])]
        assert "skill-a" not in skill_ids
        assert manifest["version"] == "2.0.1"  # patch bump

    def test_skill_remove_all_skills(self, project_root: Path, demo_pack: Path, capsys):
        """移除所有 skill 后列表为空"""
        cmd_skill_remove("demo-pack", "skill-a")
        cmd_skill_remove("demo-pack", "skill-b")
        manifest = yaml.safe_load((demo_pack / "cap-pack.yaml").read_text())
        assert len(manifest.get("skills", [])) == 0

    def test_skill_remove_not_found(self, project_root: Path, demo_pack: Path, capsys):
        exit_code = cmd_skill_remove("demo-pack", "skill-nonexistent")
        assert exit_code == 1

    def test_skill_remove_pack_not_found(self, project_root: Path, capsys):
        exit_code = cmd_skill_remove("nonexistent", "skill-a")
        assert exit_code == 1

    def test_skill_remove_dry_run(self, project_root: Path, demo_pack: Path, capsys):
        """--dry-run 不实际修改"""
        exit_code = cmd_skill_remove("demo-pack", "skill-a", dry_run=True)
        assert exit_code == 0
        # 验证未实际删除
        manifest = yaml.safe_load((demo_pack / "cap-pack.yaml").read_text())
        skill_ids = [s["id"] for s in manifest.get("skills", [])]
        assert "skill-a" in skill_ids
        assert (demo_pack / "SKILLS" / "skill-a").exists()


# ── Skill List Tests ──────────────────────────────────────────────


class TestCmdSkillList:
    def test_skill_list_success(self, project_root: Path, demo_pack: Path, capsys):
        exit_code = cmd_skill_list("demo-pack")
        assert exit_code == 0

    def test_skill_list_empty(self, project_root: Path, demo_pack: Path, capsys):
        """没有 skill 的包也能列出"""
        # 清空 skills 列表
        manifest = yaml.safe_load((demo_pack / "cap-pack.yaml").read_text())
        manifest["skills"] = []
        with open(demo_pack / "cap-pack.yaml", "w") as f:
            yaml.dump(manifest, f)
        exit_code = cmd_skill_list("demo-pack")
        assert exit_code == 0

    def test_skill_list_pack_not_found(self, project_root: Path, capsys):
        exit_code = cmd_skill_list("nonexistent")
        assert exit_code == 1


# ── Skill Update Tests ────────────────────────────────────────────


class TestCmdSkillUpdate:
    def test_skill_update_with_source(self, project_root: Path, demo_pack: Path, sample_skill_dir: Path, capsys):
        """指定 source 路径更新 skill"""
        exit_code = cmd_skill_update("demo-pack", "skill-a", str(sample_skill_dir))
        assert exit_code == 0

    def test_skill_update_auto_source_from_hermes(self, project_root: Path, demo_pack: Path, hermes_home: Path, sample_skill_dir: Path, capsys):
        """不指定 source 时自动从 Hermes skills 查找"""
        # 复制 skill 到 Hermes skills 目录
        hermes_skill = hermes_home / "skills" / "skill-a"
        shutil.copytree(sample_skill_dir, hermes_skill)
        exit_code = cmd_skill_update("demo-pack", "skill-a")
        assert exit_code == 0

    def test_skill_update_not_found(self, project_root: Path, demo_pack: Path, capsys):
        exit_code = cmd_skill_update("demo-pack", "skill-nonexistent")
        assert exit_code == 1

    def test_skill_update_pack_not_found(self, project_root: Path, capsys):
        exit_code = cmd_skill_update("nonexistent", "skill-a")
        assert exit_code == 1

    def test_skill_update_source_not_valid(self, project_root: Path, demo_pack: Path, capsys):
        """无效的 source 路径"""
        exit_code = cmd_skill_update("demo-pack", "skill-a", "/tmp/nonexistent")
        assert exit_code == 1

    def test_skill_update_source_missing_skill_md(self, project_root: Path, demo_pack: Path, tmp_path, capsys):
        """source 路径缺少 SKILL.md"""
        bad_dir = tmp_path / "bad-skill"
        bad_dir.mkdir()
        exit_code = cmd_skill_update("demo-pack", "skill-a", str(bad_dir))
        assert exit_code == 1


# ── End-to-End Workflow Tests ──────────────────────────────────────


class TestEndToEndWorkflow:
    """完整的 skill 管理工作流测试"""

    def test_full_skill_lifecycle(self, project_root: Path, demo_pack: Path, sample_skill_dir: Path, hermes_home: Path, capsys):
        """skill add → list → update → remove 的完整生命周期"""
        # 1. Add
        assert cmd_skill_add("demo-pack", str(sample_skill_dir)) == 0
        manifest = yaml.safe_load((demo_pack / "cap-pack.yaml").read_text())
        assert "my-skill" in [s["id"] for s in manifest.get("skills", [])]
        assert manifest["version"] == "2.1.0"

        # 2. List — 确认有 3 个 skill
        assert cmd_skill_list("demo-pack") == 0

        # 3. Update
        assert cmd_skill_update("demo-pack", "my-skill", str(sample_skill_dir)) == 0

        # 4. Remove
        assert cmd_skill_remove("demo-pack", "my-skill") == 0
        manifest = yaml.safe_load((demo_pack / "cap-pack.yaml").read_text())
        assert "my-skill" not in [s["id"] for s in manifest.get("skills", [])]

    def test_upgrade_search_status_flow(self, project_root: Path, demo_pack: Path, hermes_home: Path, capsys):
        """upgrade → search → status 的查询工作流"""
        # 模拟已安装
        installed = {"demo-pack": {"version": "1.0.0", "path": str(demo_pack)}}
        hermes_home.joinpath("installed_packs.json").write_text(json.dumps(installed))

        # 1. Upgrade (dry-run)
        assert cmd_upgrade("demo-pack", dry_run=True) == 0

        # 2. Search
        assert cmd_search("demo") == 0
        assert cmd_search("skill-a") == 0

        # 3. Status
        assert cmd_status() == 0
