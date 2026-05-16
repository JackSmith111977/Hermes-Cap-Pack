"""Tests for F006 + F007 — classification validation and triggers auto-completion.

F006: classification must be one of: domain, toolset, skill, infrastructure.
F007: triggers array must have at least 1 entry.

Each rule covers the four required scenarios:
  1. Detect   — analyze identifies the issue
  2. Dry-run  — analyze returns planned actions without modifying files
  3. Apply    — apply modifies cap-pack.yaml to fix the issue
  4. Idempotent — re-running apply finds nothing to fix
"""

from __future__ import annotations

from pathlib import Path

import yaml

from skill_governance.fixer.rules.f006_f007 import (
    F006ClassificationFixRule,
    F007TriggersFixRule,
)


# ═══════════════════════════════════════════════════════════════════════════════
# F006 — Classification
# ═══════════════════════════════════════════════════════════════════════════════


class TestF006ClassificationFixRule:
    """F006: classification must be one of: domain, toolset, skill, infrastructure."""

    # ── detect ───────────────────────────────────────────────────────────────

    def test_detect_missing_classification(self, temp_pack: Path):
        """analyze identifies missing classification field."""
        rule = F006ClassificationFixRule()
        result = rule.analyze(str(temp_pack), {})

        assert result.rule_id == "F006"
        assert result.dry_run is True
        assert len(result.actions) > 0
        assert result.actions[0].action_type == "modify"
        assert "classification" in result.actions[0].description.lower()

    def test_detect_valid_classification_returns_no_actions(self, tmp_path: Path):
        """analyze returns no actions when classification is already valid."""
        pack_dir = tmp_path / "valid-pack"
        pack_dir.mkdir()
        manifest = {
            "name": "valid-pack",
            "classification": "toolset",
            "skills": [],
        }
        with open(pack_dir / "cap-pack.yaml", "w") as f:
            yaml.dump(manifest, f)

        rule = F006ClassificationFixRule()
        result = rule.analyze(str(pack_dir), {})

        assert len(result.actions) == 0

    # ── dry-run ──────────────────────────────────────────────────────────────

    def test_dry_run_does_not_modify_file(self, temp_pack: Path):
        """analyze does not modify cap-pack.yaml."""
        rule = F006ClassificationFixRule()
        rule.analyze(str(temp_pack), {})

        # Read back the YAML and verify no classification was added
        cap_pack = temp_pack / "cap-pack.yaml"
        data = yaml.safe_load(cap_pack.read_text(encoding="utf-8"))
        assert "classification" not in data or not data["classification"]

    # ── apply ────────────────────────────────────────────────────────────────

    def test_apply_adds_classification(self, temp_pack: Path):
        """apply adds a valid classification to cap-pack.yaml."""
        rule = F006ClassificationFixRule()
        result = rule.apply(str(temp_pack), {})

        assert result.rule_id == "F006"
        assert result.dry_run is False
        assert result.applied == 1
        assert len(result.errors) == 0

        # Verify the file now has a valid classification
        cap_pack = temp_pack / "cap-pack.yaml"
        data = yaml.safe_load(cap_pack.read_text(encoding="utf-8"))
        assert data.get("classification") in {
            "domain",
            "toolset",
            "skill",
            "infrastructure",
        }

    # ── idempotent ───────────────────────────────────────────────────────────

    def test_idempotent_second_apply_skips(self, temp_pack: Path):
        """Second apply skips because classification is already valid."""
        rule = F006ClassificationFixRule()

        # First apply
        rule.apply(str(temp_pack), {})
        assert rule._is_already_fixed(str(temp_pack)) is True

        # Second apply should skip
        result = rule.apply(str(temp_pack), {})
        assert result.applied == 0
        assert result.skipped > 0
        assert len(result.errors) == 0

    def test_analyze_after_apply_finds_nothing(self, temp_pack: Path):
        """After apply, analyze returns no actions."""
        rule = F006ClassificationFixRule()

        rule.apply(str(temp_pack), {})

        result = rule.analyze(str(temp_pack), {})
        assert len(result.actions) == 0


# ═══════════════════════════════════════════════════════════════════════════════
# F007 — Triggers
# ═══════════════════════════════════════════════════════════════════════════════


class TestF007TriggersFixRule:
    """F007: triggers array must have at least 1 entry."""

    # ── detect ───────────────────────────────────────────────────────────────

    def test_detect_empty_triggers(self, temp_pack: Path):
        """analyze identifies empty triggers array."""
        rule = F007TriggersFixRule()
        result = rule.analyze(str(temp_pack), {})

        assert result.rule_id == "F007"
        assert result.dry_run is True
        assert len(result.actions) > 0
        assert result.actions[0].action_type == "modify"
        assert "trigger" in result.actions[0].description.lower()

    def test_detect_populated_triggers_returns_no_actions(self, tmp_path: Path):
        """analyze returns no actions when triggers is already populated."""
        pack_dir = tmp_path / "triggers-ok-pack"
        pack_dir.mkdir()
        manifest = {
            "name": "triggers-ok-pack",
            "classification": "domain",
            "triggers": ["creative", "design"],
            "skills": [],
        }
        with open(pack_dir / "cap-pack.yaml", "w") as f:
            yaml.dump(manifest, f)

        rule = F007TriggersFixRule()
        result = rule.analyze(str(pack_dir), {})

        assert len(result.actions) == 0

    # ── dry-run ──────────────────────────────────────────────────────────────

    def test_dry_run_does_not_modify_file(self, temp_pack: Path):
        """analyze does not modify cap-pack.yaml."""
        rule = F007TriggersFixRule()
        rule.analyze(str(temp_pack), {})

        # Verify triggers is still empty
        cap_pack = temp_pack / "cap-pack.yaml"
        data = yaml.safe_load(cap_pack.read_text(encoding="utf-8"))
        assert "triggers" in data
        assert len(data["triggers"]) == 0

    # ── apply ────────────────────────────────────────────────────────────────

    def test_apply_adds_triggers(self, temp_pack: Path):
        """apply adds auto-generated triggers to cap-pack.yaml."""
        rule = F007TriggersFixRule()
        result = rule.apply(str(temp_pack), {})

        assert result.rule_id == "F007"
        assert result.dry_run is False
        assert result.applied == 1
        assert len(result.errors) == 0

        # Verify the file now has non-empty triggers
        cap_pack = temp_pack / "cap-pack.yaml"
        data = yaml.safe_load(cap_pack.read_text(encoding="utf-8"))
        triggers = data.get("triggers", [])
        assert isinstance(triggers, list)
        assert len(triggers) > 0
        assert all(isinstance(t, str) for t in triggers)

    # ── idempotent ───────────────────────────────────────────────────────────

    def test_idempotent_second_apply_skips(self, temp_pack: Path):
        """Second apply skips because triggers are already populated."""
        rule = F007TriggersFixRule()

        # First apply
        rule.apply(str(temp_pack), {})
        assert rule._is_already_fixed(str(temp_pack)) is True

        # Second apply should skip
        result = rule.apply(str(temp_pack), {})
        assert result.applied == 0
        assert result.skipped > 0
        assert len(result.errors) == 0

    def test_analyze_after_apply_finds_nothing(self, temp_pack: Path):
        """After apply, analyze returns no actions."""
        rule = F007TriggersFixRule()

        rule.apply(str(temp_pack), {})

        result = rule.analyze(str(temp_pack), {})
        assert len(result.actions) == 0
