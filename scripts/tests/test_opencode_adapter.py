"""Tests for OpenCodeAdapter"""

import pytest
import json
import yaml
from pathlib import Path

from scripts.adapters.opencode import OpenCodeAdapter
from scripts.uca.protocol import CapPack, CapPackSkill, CapPackMCP


@pytest.fixture
def adapter() -> OpenCodeAdapter:
    return OpenCodeAdapter()


@pytest.fixture
def opencode_home(tmp_path: Path) -> Path:
    """模拟 OpenCode 配置目录"""
    oc = tmp_path / ".config" / "opencode"
    oc.mkdir(parents=True)
    (oc / "skills").mkdir()
    return oc


@pytest.fixture
def sample_pack(tmp_path: Path) -> tuple[CapPack, Path]:
    """创建测试用的能力包"""
    pack_dir = tmp_path / "test-pack"
    pack_dir.mkdir()

    for sid in ["skill-a", "skill-b"]:
        d = pack_dir / "SKILLS" / sid
        d.mkdir(parents=True)
        content = f"""---
name: {sid}
description: "Description of {sid}"
version: 1.0.0
tags: [test]
---

# {sid}
Body content
"""
        (d / "SKILL.md").write_text(content)

    manifest = {
        "name": "test-pack",
        "version": "1.0.0",
        "type": "capability-pack",
        "skills": [
            {"id": "skill-a", "path": "SKILLS/skill-a/SKILL.md", "description": "Skill A"},
            {"id": "skill-b", "path": "SKILLS/skill-b/SKILL.md", "description": "Skill B"},
        ],
        "mcp_servers": [
            {"id": "test-mcp", "command": "npx -y test-mcp", "timeout": 30},
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
            CapPackMCP(name="test-mcp", config={"command": "npx -y test-mcp", "timeout": 30}),
        ],
    )
    return pack, pack_dir


class TestOpenCodeAdapterProperties:
    def test_name(self, adapter: OpenCodeAdapter):
        assert adapter.name == "opencode"

    def test_is_available(self, adapter: OpenCodeAdapter):
        """OpenCode 已安装在这个环境中"""
        # 只检查是否返回 bool
        assert isinstance(adapter.is_available, bool)


class TestOpenCodeAdapterInstall:
    def test_install_skills(self, adapter: OpenCodeAdapter, opencode_home: Path, sample_pack: tuple):
        """安装 skill 文件到 ~/.config/opencode/skills/"""
        pack, _ = sample_pack
        import scripts.adapters.opencode as oc
        oc.OPENCODE_SKILLS = opencode_home / "skills"

        result = adapter.install(pack)
        assert result.success is True
        assert len(result.details["installed_skills"]) == 2

        # 检查文件是否创建
        skill_a_file = opencode_home / "skills" / "skill-a" / "SKILL.md"
        assert skill_a_file.exists()
        content = skill_a_file.read_text()
        assert "name: skill-a" in content
        assert "compatibility: opencode" in content

    def test_install_dry_run(self, adapter: OpenCodeAdapter, opencode_home: Path, sample_pack: tuple):
        """dry-run 不实际安装"""
        pack, _ = sample_pack
        import scripts.adapters.opencode as oc
        oc.OPENCODE_SKILLS = opencode_home / "skills"

        result = adapter.install(pack, dry_run=True)
        assert result.success is True
        assert not (opencode_home / "skills" / "skill-a").exists()

    def test_install_tracking(self, adapter: OpenCodeAdapter, opencode_home: Path, sample_pack: tuple):
        """安装后记录跟踪信息"""
        pack, _ = sample_pack
        import scripts.adapters.opencode as oc
        oc.OPENCODE_SKILLS = opencode_home / "skills"
        oc.TRACK_FILE = opencode_home / "track.json"

        result = adapter.install(pack)
        assert result.success is True

        tracked = json.loads((opencode_home / "track.json").read_text())
        assert "test-pack" in tracked
        assert tracked["test-pack"]["version"] == "1.0.0"


class TestOpenCodeAdapterUninstall:
    def test_uninstall_nonexistent(self, adapter: OpenCodeAdapter):
        result = adapter.uninstall("nonexistent")
        assert result.success is False

    def test_uninstall_success(self, adapter: OpenCodeAdapter, opencode_home: Path, sample_pack: tuple):
        pack, _ = sample_pack
        import scripts.adapters.opencode as oc
        oc.OPENCODE_SKILLS = opencode_home / "skills"
        oc.TRACK_FILE = opencode_home / "track.json"

        adapter.install(pack)
        result = adapter.uninstall("test-pack")
        assert result.success is True
        assert not (opencode_home / "skills" / "skill-a").exists()


class TestOpenCodeAdapterVerify:
    def test_verify_nonexistent(self, adapter: OpenCodeAdapter):
        result = adapter.verify("nonexistent")
        assert result.success is False

    def test_verify_success(self, adapter: OpenCodeAdapter, opencode_home: Path, sample_pack: tuple):
        pack, _ = sample_pack
        import scripts.adapters.opencode as oc
        oc.OPENCODE_SKILLS = opencode_home / "skills"
        oc.TRACK_FILE = opencode_home / "track.json"

        adapter.install(pack)
        result = adapter.verify("test-pack")
        assert result.success is True
        assert result.details["valid_skills"] == 2
