"""Tests for UCA Core pack verifier"""

import pytest
from pathlib import Path

from scripts.uca.verifier import PackVerifier, VerificationResult
from scripts.uca.protocol import CapPack, CapPackSkill, AdapterResult


@pytest.fixture
def verifier() -> PackVerifier:
    return PackVerifier()


@pytest.fixture
def installed_dir(tmp_path: Path) -> Path:
    """创建模拟的已安装 skill 目录"""
    skills_dir = tmp_path / "skills"
    for sid in ["pdf-layout", "html-presentation"]:
        d = skills_dir / sid
        d.mkdir(parents=True)
        (d / "SKILL.md").write_text(f"# {sid}")
    return skills_dir


@pytest.fixture
def sample_pack() -> CapPack:
    return CapPack(
        name="test-pack",
        version="1.0.0",
        pack_dir=Path("/tmp/test-pack"),
        manifest={},
        skills=[
            CapPackSkill(id="pdf-layout", path="SKILLS/pdf-layout/SKILL.md"),
            CapPackSkill(id="html-presentation", path="SKILLS/html-presentation/SKILL.md"),
            CapPackSkill(id="missing-skill", path="SKILLS/missing-skill/SKILL.md"),
        ],
    )


class TestPackVerifierBasic:
    def test_initialization(self, verifier: PackVerifier):
        assert verifier is not None

    def test_verify_skill_files_all_exist(self, verifier: PackVerifier, installed_dir: Path):
        """检查已安装的 skill 文件是否存在"""
        skills = [
            CapPackSkill(id="pdf-layout", path="SKILLS/pdf-layout/SKILL.md"),
            CapPackSkill(id="html-presentation", path="SKILLS/html-presentation/SKILL.md"),
        ]
        results = verifier.verify_skill_files(skills, installed_dir)
        assert len(results) == 2
        assert all(r["exists"] for r in results)

    def test_verify_skill_files_missing(self, verifier: PackVerifier, installed_dir: Path):
        """报告缺失的 skill 文件"""
        skills = [
            CapPackSkill(id="pdf-layout", path="SKILLS/pdf-layout/SKILL.md"),
            CapPackSkill(id="ghost-skill", path="SKILLS/ghost-skill/SKILL.md"),
        ]
        results = verifier.verify_skill_files(skills, installed_dir)
        assert results[0]["exists"] is True
        assert results[1]["exists"] is False
        assert "SKILL.md not found" in results[1].get("error", "")

    def test_verify_full_pass(self, verifier: PackVerifier, installed_dir: Path):
        """完整的 verify 流程"""
        pack = CapPack(
            name="test-pack",
            version="1.0.0",
            pack_dir=Path("/tmp/test-pack"),
            manifest={},
            skills=[
                CapPackSkill(id="pdf-layout", path="SKILLS/pdf-layout/SKILL.md"),
            ],
        )
        result = verifier.verify(pack, installed_dir)
        assert result.success is True
        assert result.pack_name == "test-pack"
        assert result.action == "verify"

    def test_verify_full_fail(self, verifier: PackVerifier, installed_dir: Path):
        """有缺失 skill 时验证失败"""
        pack = CapPack(
            name="test-pack",
            version="1.0.0",
            pack_dir=Path("/tmp/test-pack"),
            manifest={},
            skills=[
                CapPackSkill(id="pdf-layout", path="SKILLS/pdf-layout/SKILL.md"),
                CapPackSkill(id="ghost", path="SKILLS/ghost/SKILL.md"),
            ],
        )
        result = verifier.verify(pack, installed_dir)
        assert result.success is False
        assert len(result.errors) > 0

    def test_verify_empty_skills(self, verifier: PackVerifier, installed_dir: Path):
        """没有 skill 时验证通过但无细节"""
        pack = CapPack(
            name="empty-pack",
            version="1.0.0",
            pack_dir=Path("/tmp/empty"),
            manifest={},
        )
        result = verifier.verify(pack, installed_dir)
        assert result.success is True
