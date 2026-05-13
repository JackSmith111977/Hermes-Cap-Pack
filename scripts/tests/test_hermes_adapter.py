"""Tests for HermesAdapter"""

import pytest
import json
import yaml
from pathlib import Path

from scripts.adapters.hermes import HermesAdapter, SnapshotManager
from scripts.uca.protocol import CapPack, CapPackSkill, CapPackMCP


@pytest.fixture
def adapter() -> HermesAdapter:
    return HermesAdapter()


@pytest.fixture
def hermes_home(tmp_path: Path) -> Path:
    """模拟 Hermes 家目录"""
    hh = tmp_path / ".hermes"
    hh.mkdir()
    (hh / "skills").mkdir()
    # 创建基础 config.yaml
    config = {"model": {"default": "test-model"}, "mcp_servers": {}}
    with open(hh / "config.yaml", "w") as f:
        yaml.dump(config, f)
    return hh


@pytest.fixture
def sample_pack(tmp_path: Path) -> tuple[CapPack, Path]:
    """创建测试用的能力包"""
    pack_dir = tmp_path / "test-pack"
    pack_dir.mkdir()

    # Skills
    for sid in ["skill-a", "skill-b"]:
        d = pack_dir / "SKILLS" / sid
        d.mkdir(parents=True)
        (d / "SKILL.md").write_text(f"# {sid}\nDescription of {sid}")

    # cap-pack.yaml
    manifest = {
        "name": "test-pack",
        "version": "1.0.0",
        "type": "capability-pack",
        "skills": [
            {"id": "skill-a", "path": "SKILLS/skill-a/SKILL.md", "description": "Skill A"},
            {"id": "skill-b", "path": "SKILLS/skill-b/SKILL.md", "description": "Skill B"},
        ],
        "mcp_servers": [
            {"id": "test-mcp", "command": "npx", "args": ["test-mcp"], "timeout": 30},
        ],
    }
    with open(pack_dir / "cap-pack.yaml", "w") as f:
        yaml.dump(manifest, f)

    pack = CapPack(
        name="test-pack",
        version="1.0.0",
        pack_dir=pack_dir,
        manifest=manifest,
        skills=[
            CapPackSkill(id="skill-a", path="SKILLS/skill-a/SKILL.md", description="Skill A"),
            CapPackSkill(id="skill-b", path="SKILLS/skill-b/SKILL.md", description="Skill B"),
        ],
        mcp_configs=[
            CapPackMCP(name="test-mcp", config={"command": "npx", "args": ["test-mcp"], "timeout": 30}),
        ],
    )
    return pack, pack_dir


class TestHermesAdapterProperties:
    def test_name(self, adapter: HermesAdapter):
        assert adapter.name == "hermes"

    def test_is_available_false(self, adapter: HermesAdapter, tmp_path: Path):
        """在非 Hermes 环境中不可用"""
        import scripts.adapters.hermes as h
        original_config = h.HERMES_CONFIG
        h.HERMES_CONFIG = tmp_path / "nonexistent" / "config.yaml"
        try:
            assert adapter.is_available is False
        finally:
            h.HERMES_CONFIG = original_config


class TestHermesAdapterInstall:
    def test_install_skills(self, adapter: HermesAdapter, hermes_home: Path, sample_pack: tuple):
        """安装 skill 文件"""
        pack, _ = sample_pack
        # 修改路径指向模拟环境
        import scripts.adapters.hermes as h
        original_skills = h.HERMES_SKILLS
        h.HERMES_SKILLS = hermes_home / "skills"

        try:
            result = adapter.install(pack)
            assert result.success is True
            assert len(result.details["installed_skills"]) == 2
            assert (hermes_home / "skills" / "skill-a" / "SKILL.md").exists()
            assert (hermes_home / "skills" / "skill-b" / "SKILL.md").exists()
        finally:
            h.HERMES_SKILLS = original_skills

    def test_install_dry_run(self, adapter: HermesAdapter, hermes_home: Path, sample_pack: tuple):
        """dry-run 不实际安装"""
        pack, _ = sample_pack
        import scripts.adapters.hermes as h
        original_skills = h.HERMES_SKILLS
        h.HERMES_SKILLS = hermes_home / "skills"

        try:
            result = adapter.install(pack, dry_run=True)
            assert result.success is True
            assert not (hermes_home / "skills" / "skill-a").exists()
        finally:
            h.HERMES_SKILLS = original_skills

    def test_install_tracking(self, adapter: HermesAdapter, hermes_home: Path, sample_pack: tuple):
        """安装后记录跟踪信息"""
        pack, _ = sample_pack
        import scripts.adapters.hermes as h
        h.HERMES_SKILLS = hermes_home / "skills"
        h.TRACK_FILE = hermes_home / "installed_packs.json"
        original_track = h.TRACK_FILE
        h.TRACK_FILE = hermes_home / "installed_packs.json"

        try:
            result = adapter.install(pack)
            assert result.success is True

            tracked = json.loads((hermes_home / "installed_packs.json").read_text())
            assert "test-pack" in tracked
            assert tracked["test-pack"]["version"] == "1.0.0"
            assert tracked["test-pack"]["skill_count"] == 2
        finally:
            h.TRACK_FILE = original_track


class TestHermesAdapterUninstall:
    def test_uninstall_nonexistent(self, adapter: HermesAdapter):
        result = adapter.uninstall("nonexistent-pack")
        assert result.success is False
        assert "未安装" in result.errors[0]

    def test_uninstall_success(self, adapter: HermesAdapter, hermes_home: Path, sample_pack: tuple):
        """卸载已安装的包"""
        pack, _ = sample_pack
        import scripts.adapters.hermes as h
        h.HERMES_SKILLS = hermes_home / "skills"
        h.TRACK_FILE = hermes_home / "installed_packs.json"

        # 先安装
        adapter.install(pack)

        # 再卸载
        result = adapter.uninstall("test-pack")
        assert result.success is True
        assert result.details["removed"] == 2

        # 确认跟踪已清除
        tracked = json.loads((hermes_home / "installed_packs.json").read_text())
        assert "test-pack" not in tracked


class TestHermesAdapterVerify:
    def test_verify_nonexistent(self, adapter: HermesAdapter):
        result = adapter.verify("nonexistent")
        assert result.success is False

    def test_verify_success(self, adapter: HermesAdapter, hermes_home: Path, sample_pack: tuple):
        pack, _ = sample_pack
        import scripts.adapters.hermes as h
        h.HERMES_SKILLS = hermes_home / "skills"
        h.TRACK_FILE = hermes_home / "installed_packs.json"

        adapter.install(pack)
        result = adapter.verify("test-pack")
        assert result.success is True
        assert result.details["valid_skills"] == 2

    def test_verify_missing_skill(self, adapter: HermesAdapter, hermes_home: Path, sample_pack: tuple):
        pack, _ = sample_pack
        import scripts.adapters.hermes as h
        h.HERMES_SKILLS = hermes_home / "skills"
        h.TRACK_FILE = hermes_home / "installed_packs.json"

        adapter.install(pack)
        # 删除一个 skill 文件
        import shutil
        shutil.rmtree(hermes_home / "skills" / "skill-a")

        result = adapter.verify("test-pack")
        assert result.success is False
        assert len(result.details["missing_skills"]) == 1


class TestHermesAdapterList:
    def test_list_empty(self, adapter: HermesAdapter, tmp_path: Path):
        import scripts.adapters.hermes as h
        h.TRACK_FILE = tmp_path / "empty_track.json"
        h.TRACK_FILE.write_text("{}")

        packs = adapter.list_installed()
        assert packs == []

    def test_list_with_packs(self, adapter: HermesAdapter, hermes_home: Path, sample_pack: tuple):
        pack, _ = sample_pack
        import scripts.adapters.hermes as h
        h.HERMES_SKILLS = hermes_home / "skills"
        h.TRACK_FILE = hermes_home / "installed_packs.json"

        adapter.install(pack)
        packs = adapter.list_installed()
        assert len(packs) == 1
        assert packs[0]["name"] == "test-pack"


class TestSnapshotManager:
    def test_create_snapshot(self, hermes_home: Path):
        """创建快照"""
        import scripts.adapters.hermes as h
        h.SNAPSHOT_DIR = hermes_home / ".uca-snapshots"
        h.TRACK_FILE = hermes_home / "installed_packs.json"

        # 先创建一些被跟踪的状态
        tracked = {"test-pack": {"version": "1.0.0", "skills": ["skill-a"]}}
        h.TRACK_FILE.write_text(json.dumps(tracked))

        snapshot_id = SnapshotManager.create("test-pack")
        assert snapshot_id is not None
        assert (hermes_home / ".uca-snapshots" / snapshot_id).exists()

    def test_restore_snapshot(self, hermes_home: Path):
        """从快照恢复"""
        import scripts.adapters.hermes as h
        h.SNAPSHOT_DIR = hermes_home / ".uca-snapshots"
        h.TRACK_FILE = hermes_home / "installed_packs.json"

        tracked = {"test-pack": {"version": "1.0.0", "skills": ["skill-a"]}}
        h.TRACK_FILE.write_text(json.dumps(tracked))

        snapshot_id = SnapshotManager.create("test-pack")

        # 修改 tracked
        h.TRACK_FILE.write_text("{}")

        # 恢复
        ops = SnapshotManager.restore(snapshot_id)
        assert len(ops) > 0
        restored = json.loads(h.TRACK_FILE.read_text())
        assert "test-pack" in restored
