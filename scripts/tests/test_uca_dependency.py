"""Tests for UCA Core dependency checker"""

import pytest
from pathlib import Path

from scripts.uca.dependency import DependencyChecker, DependencyError
from scripts.uca.protocol import CapPack


@pytest.fixture
def checker() -> DependencyChecker:
    return DependencyChecker()


@pytest.fixture
def sample_pack() -> CapPack:
    return CapPack(
        name="test-pack",
        version="1.0.0",
        pack_dir=Path("/tmp/test-pack"),
        manifest={},
        dependencies=["pyyaml"],
    )


class TestDependencyChecker:
    def test_initialization(self, checker: DependencyChecker):
        assert checker is not None

    def test_check_python_packages_found(self, checker: DependencyChecker):
        """pyyaml 应该已安装"""
        missing = checker.check_python_packages(["pyyaml"])
        assert missing == []

    def test_check_python_packages_missing(self, checker: DependencyChecker):
        """一个不存在的包应该被报告为缺失"""
        missing = checker.check_python_packages(["this-package-does-not-exist-xyz-999"])
        assert len(missing) > 0
        assert "this-package-does-not-exist-xyz-999" in missing

    def test_check_python_packages_with_version(self, checker: DependencyChecker):
        """带版本约束的包名"""
        missing = checker.check_python_packages(["pyyaml>=6.0"])
        assert missing == []  # pyyaml 已安装

    def test_check_with_satisfied_deps(self, checker: DependencyChecker, sample_pack: CapPack):
        """依赖全部满足时 all_satisfied = True"""
        result = checker.check(sample_pack)
        assert result["all_satisfied"] is True

    def test_check_skills_exist(self, checker: DependencyChecker, tmp_path: Path):
        """检查 skill 是否存在"""
        skills_dir = tmp_path / "skills"
        (skills_dir / "existing-skill").mkdir(parents=True)
        (skills_dir / "existing-skill" / "SKILL.md").write_text("# Existing")

        missing = checker.check_skills_exist(
            ["existing-skill", "non-existent-skill"],
            skills_dir,
        )
        assert missing == ["non-existent-skill"]


class TestDependencyEdgeCases:
    def test_empty_requirements(self, checker: DependencyChecker):
        assert checker.check_python_packages([]) == []

    def test_no_dependencies(self, checker: DependencyChecker):
        pack = CapPack(
            name="no-deps",
            version="1.0.0",
            pack_dir=Path("/tmp"),
            manifest={},
        )
        result = checker.check(pack)
        assert result["all_satisfied"] is True
        assert result["missing_packages"] == []
