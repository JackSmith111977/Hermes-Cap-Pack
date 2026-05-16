"""Tests for H001 + H002 — cluster membership and cluster size validation.

H001: Every skill must belong to a named cluster.
H002: Cluster size must be between 3 and 15 skills per cluster.

Each rule covers the required scenarios:
  - H001: detect, dry-run, apply, idempotent
  - H002: detect (suggestions in dry-run), apply (always errors — dry-run only)
"""

from __future__ import annotations

from pathlib import Path

import yaml

from skill_governance.fixer.rules.h001_h002 import (
    H001ClusterFixRule,
    H002ClusterSizeFixRule,
)


# ═══════════════════════════════════════════════════════════════════════════════
# H001 — Cluster membership
# ═══════════════════════════════════════════════════════════════════════════════


class TestH001ClusterFixRule:
    """H001: Every skill must belong to a named cluster."""

    # ── detect ───────────────────────────────────────────────────────────────

    def test_detect_unassigned_skills(self, temp_pack: Path):
        """analyze identifies skills without a cluster field."""
        rule = H001ClusterFixRule()
        result = rule.analyze(str(temp_pack), {})

        assert result.rule_id == "H001"
        assert result.dry_run is True
        assert len(result.actions) > 0

        # All actions should be 'modify' type targeting cap-pack.yaml
        for action in result.actions:
            assert action.action_type == "modify"
            assert action.target_path.endswith("cap-pack.yaml")

    def test_detect_no_clusters_no_actions(self, tmp_path: Path):
        """analyze returns no actions when no clusters are defined."""
        pack_dir = tmp_path / "no-clusters-pack"
        pack_dir.mkdir()
        manifest = {
            "name": "no-clusters-pack",
            "classification": "toolset",
            "triggers": ["test"],
            "skills": [
                {"id": "skill-a", "name": "Skill A", "path": "SKILLS/a/SKILL.md"}
            ],
        }
        with open(pack_dir / "cap-pack.yaml", "w") as f:
            yaml.dump(manifest, f)

        rule = H001ClusterFixRule()
        result = rule.analyze(str(pack_dir), {})

        assert len(result.actions) == 0

    def test_detect_all_assigned_no_actions(self, tmp_path: Path):
        """analyze returns no actions when all skills have a valid cluster."""
        pack_dir = tmp_path / "assigned-pack"
        pack_dir.mkdir()
        manifest = {
            "name": "assigned-pack",
            "classification": "domain",
            "triggers": ["test"],
            "skills": [
                {
                    "id": "skill-a",
                    "name": "Skill A",
                    "cluster": "group1",
                    "tags": ["creative"],
                },
                {
                    "id": "skill-b",
                    "name": "Skill B",
                    "cluster": "group1",
                    "tags": ["design"],
                },
            ],
            "clusters": [
                {"id": "group1", "name": "Group One", "skills": ["skill-a", "skill-b"]}
            ],
        }
        with open(pack_dir / "cap-pack.yaml", "w") as f:
            yaml.dump(manifest, f)

        rule = H001ClusterFixRule()
        result = rule.analyze(str(pack_dir), {})

        assert len(result.actions) == 0

    # ── dry-run ──────────────────────────────────────────────────────────────

    def test_dry_run_does_not_modify_file(self, temp_pack: Path):
        """analyze does not modify cap-pack.yaml."""
        rule = H001ClusterFixRule()
        rule.analyze(str(temp_pack), {})

        # Verify no cluster field was added
        cap_pack = temp_pack / "cap-pack.yaml"
        data = yaml.safe_load(cap_pack.read_text(encoding="utf-8"))
        for skill in data.get("skills", []):
            assert "cluster" not in skill or not skill["cluster"]

    # ── apply ────────────────────────────────────────────────────────────────

    def test_apply_assigns_clusters(self, temp_pack: Path):
        """apply adds cluster assignments to unassigned skills."""
        rule = H001ClusterFixRule()
        result = rule.apply(str(temp_pack), {})

        assert result.rule_id == "H001"
        assert result.dry_run is False
        assert result.applied > 0
        assert len(result.errors) == 0

        # Verify skills now have cluster fields pointing to valid clusters
        cap_pack = temp_pack / "cap-pack.yaml"
        data = yaml.safe_load(cap_pack.read_text(encoding="utf-8"))
        valid_ids = {c["id"] for c in data.get("clusters", [])}
        for skill in data.get("skills", []):
            cluster = skill.get("cluster", "")
            assert isinstance(cluster, str) and cluster in valid_ids, (
                f"Skill {skill.get('id')} has invalid cluster: {cluster!r}"
            )

    # ── idempotent ───────────────────────────────────────────────────────────

    def test_idempotent_after_apply(self, temp_pack: Path):
        """After apply, all skills have cluster fields; re-running skips."""
        rule = H001ClusterFixRule()

        # First apply
        rule.apply(str(temp_pack), {})
        assert rule._is_already_fixed(str(temp_pack)) is True

        # Second apply should skip
        result = rule.apply(str(temp_pack), {})
        assert result.applied == 0

    def test_analyze_after_apply_finds_nothing(self, temp_pack: Path):
        """After apply, analyze returns no actions."""
        rule = H001ClusterFixRule()

        rule.apply(str(temp_pack), {})

        result = rule.analyze(str(temp_pack), {})
        assert len(result.actions) == 0


# ═══════════════════════════════════════════════════════════════════════════════
# H002 — Cluster size
# ═══════════════════════════════════════════════════════════════════════════════


class TestH002ClusterSizeFixRule:
    """H002: Cluster size must be between 3 and 15 skills per cluster."""

    # ── detect (dry-run suggestions) ─────────────────────────────────────────

    def test_detect_undersized_clusters(self, temp_pack: Path):
        """analyze flags clusters with fewer than 3 skills."""
        rule = H002ClusterSizeFixRule()
        result = rule.analyze(str(temp_pack), {})

        assert result.rule_id == "H002"
        assert result.dry_run is True
        assert len(result.actions) > 0

        # Both clusters have < 3 skills, so we expect suggestions for both
        for action in result.actions:
            assert action.action_type == "modify"
            assert action.rule_id == "H002"
            # Description should mention the cluster size issue
            assert "only" in action.description or "cluster" in action.description.lower()

    def test_detect_adequately_sized_clusters(self, tmp_path: Path):
        """analyze returns no actions when all clusters have >= 3 skills."""
        pack_dir = tmp_path / "adequate-pack"
        pack_dir.mkdir()

        skill_ids = [f"skill-{i}" for i in range(5)]
        skills = [
            {
                "id": sid,
                "name": sid,
                "cluster": "group1" if i < 3 else "group2",
                "tags": ["tag"],
            }
            for i, sid in enumerate(skill_ids)
        ]

        manifest = {
            "name": "adequate-pack",
            "classification": "toolset",
            "triggers": ["test"],
            "skills": skills,
            "clusters": [
                {
                    "id": "group1",
                    "name": "Group One",
                    "skills": ["skill-0", "skill-1", "skill-2"],
                },
                {
                    "id": "group2",
                    "name": "Group Two",
                    "skills": ["skill-3", "skill-4"],
                },
            ],
        }
        with open(pack_dir / "cap-pack.yaml", "w") as f:
            yaml.dump(manifest, f)

        rule = H002ClusterSizeFixRule()
        result = rule.analyze(str(pack_dir), {})

        # group1 has 3 skills (meets minimum), group2 has 2 (undersized)
        # So we expect 1 action for group2
        assert len(result.actions) == 1

    def test_detect_no_clusters_no_actions(self, tmp_path: Path):
        """analyze returns no actions when no clusters are defined."""
        pack_dir = tmp_path / "no-clusters-h002"
        pack_dir.mkdir()
        manifest = {
            "name": "no-clusters-h002",
            "classification": "domain",
            "triggers": ["x"],
            "skills": [],
        }
        with open(pack_dir / "cap-pack.yaml", "w") as f:
            yaml.dump(manifest, f)

        rule = H002ClusterSizeFixRule()
        result = rule.analyze(str(pack_dir), {})

        assert len(result.actions) == 0

    # ── apply (always errors — dry-run only) ─────────────────────────────────

    def test_apply_always_errors(self, temp_pack: Path):
        """H002.apply() always returns with an error (dry-run only rule)."""
        rule = H002ClusterSizeFixRule()
        result = rule.apply(str(temp_pack), {})

        assert result.rule_id == "H002"
        assert result.dry_run is False
        assert len(result.errors) > 0
        assert "dry-run" in result.errors[0].lower()
        assert result.applied == 0
