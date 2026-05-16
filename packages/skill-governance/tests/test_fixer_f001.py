"""Tests for F001 — missing SKILL.md creation (F001SkillMDFixRule).

Covers the four required scenarios:
  1. Detect   — analyze finds skills without SKILL.md
  2. Dry-run  — analyze returns planned actions without modifying files
  3. Apply    — apply creates the missing SKILL.md files
  4. Idempotent — re-running apply doesn't create duplicates
"""

from __future__ import annotations

from pathlib import Path

from skill_governance.fixer.rules.f001_skill_md import F001SkillMDFixRule


class TestF001SkillMDFixRule:
    """F001: SKILL.md must exist for each skill declared in cap-pack.yaml."""

    # ── detect ───────────────────────────────────────────────────────────────

    def test_detect_missing_skills(self, temp_pack: Path):
        """analyze() should detect skills without SKILL.md."""
        rule = F001SkillMDFixRule()
        result = rule.analyze(str(temp_pack), {})

        assert result.rule_id == "F001"
        assert result.dry_run is True
        assert len(result.actions) > 0

        # skill-a has SKILL.md, so it should NOT be in the actions
        skill_a_md = str(temp_pack / "SKILLS" / "skill-a" / "SKILL.md")
        skill_b_md = str(temp_pack / "SKILLS" / "skill-b" / "SKILL.md")
        skill_c_md = str(temp_pack / "SKILLS" / "skill-c" / "SKILL.md")

        assert skill_a_md not in [a.target_path for a in result.actions]
        assert skill_b_md in [a.target_path for a in result.actions]
        assert skill_c_md in [a.target_path for a in result.actions]

    # ── dry-run ──────────────────────────────────────────────────────────────

    def test_dry_run_does_not_create_files(self, temp_pack: Path):
        """analyze() should NOT create any files (dry-run)."""
        rule = F001SkillMDFixRule()
        result = rule.analyze(str(temp_pack), {})

        # No files should have been created
        skill_b_md = temp_pack / "SKILLS" / "skill-b" / "SKILL.md"
        skill_c_md = temp_pack / "SKILLS" / "skill-c" / "SKILL.md"
        assert not skill_b_md.exists()
        assert not skill_c_md.exists()

        # All actions should be 'create' type
        for action in result.actions:
            assert action.action_type == "create"

    # ── apply ────────────────────────────────────────────────────────────────

    def test_apply_creates_missing_skill_md(self, temp_pack: Path):
        """apply() should create SKILL.md for missing skills."""
        rule = F001SkillMDFixRule()
        result = rule.apply(str(temp_pack), {})

        assert result.rule_id == "F001"
        assert result.dry_run is False
        assert result.applied > 0
        assert len(result.errors) == 0

        # Verify files were created
        skill_b_md = temp_pack / "SKILLS" / "skill-b" / "SKILL.md"
        skill_c_md = temp_pack / "SKILLS" / "skill-c" / "SKILL.md"
        assert skill_b_md.exists()
        assert skill_c_md.exists()

        # Verify content has YAML frontmatter
        content_b = skill_b_md.read_text(encoding="utf-8")
        assert content_b.startswith("---")
        assert "name: Skill B" in content_b
        assert "version: 1.0.0" in content_b

    # ── idempotent ───────────────────────────────────────────────────────────

    def test_idempotent_second_apply_skips(self, temp_pack: Path):
        """Running apply() twice should be idempotent."""
        rule = F001SkillMDFixRule()

        # First apply creates files
        result1 = rule.apply(str(temp_pack), {})
        assert result1.applied > 0

        # Second apply should skip since files now exist
        result2 = rule.apply(str(temp_pack), {})
        assert result2.applied == 0
        assert result2.errors == []

    def test_analyze_after_apply_finds_nothing(self, temp_pack: Path):
        """After apply(), analyze() should find no missing skills."""
        rule = F001SkillMDFixRule()

        # Apply first
        rule.apply(str(temp_pack), {})

        # Then analyze should find nothing
        result = rule.analyze(str(temp_pack), {})
        assert len(result.actions) == 0
        assert result.applied == 0

    def test_is_already_fixed_after_apply(self, temp_pack: Path):
        """_is_already_fixed() returns True after apply()."""
        rule = F001SkillMDFixRule()

        assert rule._is_already_fixed(str(temp_pack)) is False

        rule.apply(str(temp_pack), {})

        assert rule._is_already_fixed(str(temp_pack)) is True
