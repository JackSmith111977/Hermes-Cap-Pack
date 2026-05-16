"""Integration tests for the CLI ``fix`` command (Typer-based).

Tests argument parsing, error handling, and the end-to-end fix pipeline
using ``CliRunner`` with monkeypatched dispatcher and scan report.

The scan pipeline naturally produces failed checks for F001, F006, F007
when skills are missing classification and triggers.  The dispatcher
routes these to the corresponding fix rules.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import yaml
from typer.testing import CliRunner

from skill_governance.cli.main import app
from skill_governance.fixer import FixDispatcher
from skill_governance.fixer.rules import (
    F001SkillMDFixRule,
    F006ClassificationFixRule,
    F007TriggersFixRule,
)


runner = CliRunner()


# ── Helpers ──────────────────────────────────────────────────────────────────


def _create_test_pack(tmp_path: Path) -> Path:
    """Create a minimal pack with issues that trigger F001, F006, F007."""
    pack_dir = tmp_path / "fix-test-pack"
    pack_dir.mkdir()

    skills_dir = pack_dir / "SKILLS"
    skills_dir.mkdir()

    # skill-a has SKILL.md (covered)
    (skills_dir / "skill-a").mkdir()
    (skills_dir / "skill-a" / "SKILL.md").write_text(
        "---\nid: skill-a\nname: Skill A\ndescription: A test skill\n"
        "tags: [creative, design]\nversion: 1.0.0\n---\n# Skill A\n"
    )

    # skill-b and skill-c have no SKILL.md (F001 triggers)
    (skills_dir / "skill-b").mkdir()
    (skills_dir / "skill-c").mkdir()

    manifest: dict[str, Any] = {
        "name": "fix-test-pack",
        "version": "1.0.0",
        "description": "A pack for CLI fix testing",
        # no classification — triggers F006 at skill level in scan
        # empty triggers — triggers F007 at skill level in scan
        "triggers": [],
        "skills": [
            {
                "id": "skill-a",
                "name": "Skill A",
                "path": "SKILLS/skill-a/SKILL.md",
                "tags": ["creative", "design"],
            },
            {
                "id": "skill-b",
                "name": "Skill B",
                "path": "SKILLS/skill-b/SKILL.md",
                "tags": ["workflow", "automation"],
            },
            {
                "id": "skill-c",
                "name": "Skill C",
                "path": "SKILLS/skill-c/SKILL.md",
                "tags": ["quality", "engine"],
            },
        ],
    }

    with open(pack_dir / "cap-pack.yaml", "w", encoding="utf-8") as f:
        yaml.dump(
            manifest, f, default_flow_style=False, sort_keys=False, allow_unicode=True
        )

    return pack_dir


def _patcher_dispatcher() -> FixDispatcher:
    """Return a FixDispatcher with rules that match scan rule IDs."""
    d = FixDispatcher()
    d.register(F001SkillMDFixRule())
    d.register(F006ClassificationFixRule())
    d.register(F007TriggersFixRule())
    return d


# ─── Tests ───────────────────────────────────────────────────────────────────


class TestCliFixCommand:
    """Integration tests for ``skill-governance fix``."""

    def test_fix_help(self):
        """``fix --help`` prints usage information."""
        result = runner.invoke(app, ["fix", "--help"])
        assert result.exit_code == 0
        assert "fix" in result.output.lower()
        assert "pack-path" in result.output.lower() or "pack_path" in result.output.lower()

    def test_fix_missing_path(self):
        """``fix`` without arguments exits with error."""
        result = runner.invoke(app, ["fix"])
        assert result.exit_code != 0
        assert "Provide a pack path" in result.output or "Error" in result.output

    def test_fix_nonexistent_path(self, tmp_path: Path, monkeypatch: Any):
        """``fix`` with a non-existent path shows an error."""
        monkeypatch.setattr(
            "skill_governance.cli.main._setup_fix_dispatcher",
            _patcher_dispatcher,
        )

        bad_path = tmp_path / "does-not-exist"
        result = runner.invoke(app, ["fix", str(bad_path)])
        # The CLI should handle the missing directory gracefully
        # (it prints an error and continues to next pack)
        assert result.exit_code == 0  # fix command doesn't exit on individual pack error
        assert "does not exist" in result.output

    def test_fix_dry_run_shows_plan(self, tmp_path: Path, monkeypatch: Any):
        """``fix --dry-run`` shows the fix plan without modifying files."""
        pack_dir = _create_test_pack(tmp_path)

        monkeypatch.setattr(
            "skill_governance.cli.main._setup_fix_dispatcher",
            _patcher_dispatcher,
        )

        result = runner.invoke(app, ["fix", str(pack_dir), "--dry-run"])
        assert result.exit_code == 0

        # Output should mention the pack name and the fix plan
        output = result.output
        assert "fix-test-pack" in output
        # The dispatcher should generate some fix actions
        # (at minimum F001 for missing SKILL.md files)
        assert "F001" in output

    def test_fix_apply_modifies_pack(self, tmp_path: Path, monkeypatch: Any):
        """``fix --apply`` actually modifies the pack."""
        pack_dir = _create_test_pack(tmp_path)

        monkeypatch.setattr(
            "skill_governance.cli.main._setup_fix_dispatcher",
            _patcher_dispatcher,
        )

        result = runner.invoke(app, ["fix", str(pack_dir), "--apply"])
        assert result.exit_code == 0

        # Verify that some files were created/modified
        # skill-b and skill-c should now have SKILL.md
        assert (pack_dir / "SKILLS" / "skill-b" / "SKILL.md").exists()
        assert (pack_dir / "SKILLS" / "skill-c" / "SKILL.md").exists()

        output = result.output
        assert "F001" in output  # F001 rule should have run
