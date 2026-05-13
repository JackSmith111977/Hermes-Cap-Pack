"""Tests for UCA Core protocol definitions"""

import pytest
from pathlib import Path
from scripts.uca.protocol import (
    CapPack, CapPackSkill, CapPackExperience, CapPackMCP,
    AdapterResult,
)


class TestCapPackSkill:
    def test_minimal_skill(self):
        skill = CapPackSkill(id="test-skill", path="SKILLS/test/SKILL.md")
        assert skill.id == "test-skill"
        assert skill.category == ""
        assert skill.description == ""

    def test_full_skill(self):
        skill = CapPackSkill(
            id="full-skill",
            path="SKILLS/full/SKILL.md",
            category="doc-engine",
            description="Generate PDF documents",
            source="pdf-layout",
        )
        assert skill.category == "doc-engine"
        assert skill.source == "pdf-layout"


class TestCapPack:
    def test_minimal_pack(self):
        pack = CapPack(
            name="test-pack",
            version="1.0.0",
            pack_dir=Path("/tmp"),
            manifest={"name": "test-pack"},
        )
        assert pack.name == "test-pack"
        assert pack.version == "1.0.0"
        assert pack.skills == []
        assert pack.experiences == []
        assert pack.mcp_configs == []

    def test_pack_with_skills(self):
        pack = CapPack(
            name="doc-engine",
            version="2.0.0",
            pack_dir=Path("/tmp/packs/doc-engine"),
            manifest={"name": "doc-engine", "skills": [{"id": "pdf-layout"}]},
            skills=[CapPackSkill(id="pdf-layout", path="SKILLS/pdf-layout/SKILL.md")],
            dependencies=["pyyaml"],
        )
        assert len(pack.skills) == 1
        assert pack.skills[0].id == "pdf-layout"
        assert "pyyaml" in pack.dependencies


class TestAdapterResult:
    def test_success_result(self):
        result = AdapterResult(
            success=True,
            pack_name="doc-engine",
            action="install",
            details={"skills_installed": 9},
        )
        assert result.success is True
        assert result.pack_name == "doc-engine"

    def test_failure_result(self):
        result = AdapterResult(
            success=False,
            action="install",
            errors=["Pack not found"],
        )
        assert result.success is False
        assert len(result.errors) == 1

    def test_result_with_warnings(self):
        result = AdapterResult(
            success=True,
            action="verify",
            warnings=["MCP config not found"],
        )
        assert len(result.warnings) == 1
        assert result.backup_path == ""
