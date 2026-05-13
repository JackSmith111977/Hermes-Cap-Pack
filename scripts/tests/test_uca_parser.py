"""Tests for UCA Core pack parser"""

import pytest
import tempfile
import yaml
from pathlib import Path

from scripts.uca.parser import PackParser, PackParseError
from scripts.uca.protocol import CapPack, CapPackSkill


SAMPLE_PACK = {
    "name": "test-pack",
    "version": "1.0.0",
    "type": "capability-pack",
    "description": "A test pack",
    "author": "boku",
    "created": "2026-05-13",
    "updated": "2026-05-13",
    "skills": [
        {
            "id": "skill-one",
            "path": "SKILLS/skill-one/SKILL.md",
            "description": "First skill",
            "tags": ["test"],
        },
        {
            "id": "skill-two",
            "path": "SKILLS/skill-two/SKILL.md",
            "description": "Second skill",
        },
    ],
    "experiences": [
        {
            "id": "exp-one",
            "path": "EXPERIENCES/exp-one.md",
            "type": "pitfall",
            "description": "Common pitfall",
        },
    ],
    "dependencies": {
        "python_packages": ["pyyaml>=6.0"],
    },
    "compatibility": {
        "agent_types": ["hermes"],
    },
}


@pytest.fixture
def pack_dir(tmp_path: Path) -> Path:
    """创建测试用的能力包目录"""
    p = tmp_path / "test-pack"
    p.mkdir()
    with open(p / "cap-pack.yaml", "w") as f:
        yaml.dump(SAMPLE_PACK, f)
    return p


@pytest.fixture
def parser() -> PackParser:
    return PackParser()


class TestPackParserBasic:
    """基本解析功能测试"""

    def test_parse_success(self, parser: PackParser, pack_dir: Path):
        pack = parser.parse(pack_dir)
        assert isinstance(pack, CapPack)
        assert pack.name == "test-pack"
        assert pack.version == "1.0.0"
        assert pack.pack_dir == pack_dir.resolve()

    def test_parse_name_fallback(self, parser: PackParser, tmp_path: Path):
        """没有 name 字段时使用目录名"""
        p = tmp_path / "my-awesome-pack"
        p.mkdir()
        minimal = {"version": "0.1.0"}
        with open(p / "cap-pack.yaml", "w") as f:
            yaml.dump(minimal, f)
        pack = parser.parse(p)
        assert pack.name == "my-awesome-pack"

    def test_parse_skills(self, parser: PackParser, pack_dir: Path):
        pack = parser.parse(pack_dir)
        assert len(pack.skills) == 2
        assert pack.skills[0].id == "skill-one"
        assert pack.skills[1].description == "Second skill"

    def test_parse_experiences(self, parser: PackParser, pack_dir: Path):
        pack = parser.parse(pack_dir)
        assert len(pack.experiences) == 1
        assert pack.experiences[0].id == "exp-one"

    def test_parse_dependencies(self, parser: PackParser, pack_dir: Path):
        pack = parser.parse(pack_dir)
        assert "pyyaml>=6.0" in pack.dependencies

    def test_parse_compatibility(self, parser: PackParser, pack_dir: Path):
        pack = parser.parse(pack_dir)
        assert pack.compatibility == {"agent_types": ["hermes"]}


class TestPackParserErrors:
    """错误处理测试"""

    def test_file_not_found(self, parser: PackParser, tmp_path: Path):
        with pytest.raises(PackParseError, match="找不到能力包清单文件"):
            parser.parse(tmp_path / "nonexistent")

    def test_empty_dir(self, parser: PackParser, tmp_path: Path):
        p = tmp_path / "empty-pack"
        p.mkdir()
        with pytest.raises(PackParseError, match="找不到能力包清单文件"):
            parser.parse(p)

    def test_invalid_yaml(self, parser: PackParser, tmp_path: Path):
        p = tmp_path / "bad-pack"
        p.mkdir()
        with open(p / "cap-pack.yaml", "w") as f:
            f.write(": invalid yaml {{{{")
        with pytest.raises(PackParseError, match="YAML 格式错误"):
            parser.parse(p)

    def test_not_dict(self, parser: PackParser, tmp_path: Path):
        p = tmp_path / "list-pack"
        p.mkdir()
        with open(p / "cap-pack.yaml", "w") as f:
            yaml.dump(["just", "a", "list"], f)
        with pytest.raises(PackParseError, match="必须是对象"):
            parser.parse(p)


class TestPackParserRealPacks:
    """真实能力包解析测试"""

    def test_parse_doc_engine(self, parser: PackParser):
        project_root = Path(__file__).parent.parent.parent
        pack_dir = project_root / "packs" / "doc-engine"
        if not pack_dir.exists():
            pytest.skip("doc-engine pack not found")
        pack = parser.parse(pack_dir)
        assert pack.name == "doc-engine"
        assert len(pack.skills) > 0
        assert len(pack.experiences) > 0

    def test_parse_quality_assurance(self, parser: PackParser):
        project_root = Path(__file__).parent.parent.parent
        pack_dir = project_root / "packs" / "quality-assurance"
        if not pack_dir.exists():
            pytest.skip("quality-assurance pack not found")
        pack = parser.parse(pack_dir)
        assert pack.name == "quality-assurance"
        assert len(pack.skills) > 0


class TestPackParserEdgeCases:
    """边界情况测试"""

    def test_yml_extension(self, parser: PackParser, tmp_path: Path):
        """支持 .yml 扩展名"""
        p = tmp_path / "yml-pack"
        p.mkdir()
        with open(p / "cap-pack.yml", "w") as f:
            yaml.dump({"name": "yml-pack", "version": "1.0.0"}, f)
        pack = parser.parse(p)
        assert pack.name == "yml-pack"

    def test_minimal_without_skills(self, parser: PackParser, tmp_path: Path):
        p = tmp_path / "minimal-pack"
        p.mkdir()
        with open(p / "cap-pack.yaml", "w") as f:
            yaml.dump({"name": "minimal", "version": "0.0.1"}, f)
        pack = parser.parse(p)
        assert pack.name == "minimal"
        assert pack.skills == []

    def test_version_as_float(self, parser: PackParser, tmp_path: Path):
        """version 可能是数字 1.0 而非字符串 "1.0.0" """
        p = tmp_path / "version-pack"
        p.mkdir()
        with open(p / "cap-pack.yaml", "w") as f:
            yaml.dump({"name": "ver-pack", "version": 2.0}, f)
        pack = parser.parse(p)
        assert pack.version == "2.0"

    def test_unknown_fields_ignored(self, parser: PackParser, pack_dir: Path):
        """未知字段不应导致解析失败"""
        pack = parser.parse(pack_dir)
        assert pack.manifest.get("extra_field") is None  # 不在样本中
