"""Shared fixtures for skill-governance fixer tests."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import yaml

from skill_governance.fixer import FixDispatcher
from skill_governance.fixer.rules import (
    F001SkillMDFixRule,
    F006ClassificationFixRule,
    F007TriggersFixRule,
    H001ClusterFixRule,
    H002ClusterSizeFixRule,
)


@pytest.fixture
def temp_pack(tmp_path: Path) -> Path:
    """Create a temporary cap-pack with known fixable issues.

    The pack has:
    - skill-a with SKILL.md (already covered)
    - skill-b and skill-c without SKILL.md (F001 triggers)
    - No ``classification`` field (F006 triggers)
    - Empty ``triggers`` (F007 triggers)
    - Clusters defined but skills lack ``cluster`` field (H001 triggers)
    - Clusters with < 3 skills (H002 triggers)
    """
    pack_dir = tmp_path / "my-test-pack"
    pack_dir.mkdir()

    # Create SKILL.md for skill-a only
    skills_dir = pack_dir / "SKILLS"
    skills_dir.mkdir()

    skill_a_dir = skills_dir / "skill-a"
    skill_a_dir.mkdir()
    (skill_a_dir / "SKILL.md").write_text(
        """\
---
id: skill-a
name: Skill A
description: A creative design skill
tags: [creative, design]
version: 1.0.0
---

# Skill A

Creative and design skill for testing.
"""
    )

    # skill-b directory exists but no SKILL.md
    (skills_dir / "skill-b").mkdir()
    # skill-c directory exists but no SKILL.md
    (skills_dir / "skill-c").mkdir()

    # cap-pack.yaml with issues
    manifest: dict[str, Any] = {
        "name": "my-test-pack",
        "version": "1.0.0",
        "description": "A test pack with multiple issues for fix rule testing",
        # no "classification" key — F006 will trigger
        "triggers": [],  # empty — F007 will trigger
        "skills": [
            {
                "id": "skill-a",
                "name": "Skill A",
                "path": "SKILLS/skill-a/SKILL.md",
                "tags": ["creative", "design"],
                # no cluster — H001 will trigger
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
        "clusters": [
            {
                "id": "infra",
                "name": "Infrastructure Cluster",
                "skills": ["skill-a"],
            },
            {
                "id": "tools",
                "name": "Tools Cluster",
                "skills": ["skill-b", "skill-c"],
            },
        ],
    }

    cap_pack = pack_dir / "cap-pack.yaml"
    with open(cap_pack, "w", encoding="utf-8") as f:
        yaml.dump(
            manifest, f, default_flow_style=False, sort_keys=False, allow_unicode=True
        )

    return pack_dir


@pytest.fixture
def fix_dispatcher() -> FixDispatcher:
    """Pre-configured FixDispatcher with all known fix rules registered."""
    dispatcher = FixDispatcher()
    dispatcher.register(F001SkillMDFixRule())
    dispatcher.register(F006ClassificationFixRule())
    dispatcher.register(F007TriggersFixRule())
    dispatcher.register(H001ClusterFixRule())
    dispatcher.register(H002ClusterSizeFixRule())
    return dispatcher
