"""F001 rule — SKILL.md must exist at the expected path for each skill in the pack.

Creates skeleton SKILL.md files for skills declared in ``cap-pack.yaml`` that
are missing their SKILL.md.  The generated file includes a valid YAML frontmatter
(``name``, ``description``, ``version``, ``tags``, ``triggers``) followed by
basic Markdown section placeholders.

Idempotent — existing SKILL.md files are never overwritten.

References:
    - ADR-6-1 (dual-phase fix design)
    - ADR-6-2 (.bak backup convention)
    - SPEC-6-1 (pack structure specification)
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from skill_governance.adapter.cap_pack_adapter import (
    _extract_skill_tags_and_desc,
    _parse_frontmatter,
)
from skill_governance.fixer.base import FixAction, FixResult, FixRule

# ─── Template ──────────────────────────────────────────────────────────────────

SKILL_MD_TEMPLATE: str = """# {name}

{description}

## Overview

<!-- TODO: Add a brief overview of what this skill does, when it activates,
     and the core problem it solves. -->

## Usage

<!-- TODO: Add usage instructions, example prompts, and typical invocation
     patterns.  Include code blocks where helpful. -->

## Configuration

<!-- TODO: Document environment variables, configuration files, or other
     setup required by this skill. -->

## Dependencies

<!-- TODO: List any cap-pack or skill dependencies. -->

## References

<!-- TODO: Add links to related documentation, external resources, or
     related skills. -->
"""


class F001SkillMDFixRule(FixRule):
    """Verify and create missing SKILL.md files for every skill in a cap-pack.

    ``analyze()`` scans ``cap-pack.yaml`` for skill entries whose SKILL.md
    path does not yet exist and returns planned ``create`` actions.

    ``apply()`` writes the missing SKILL.md files from a skeleton template,
    using metadata extracted from the skill entry in ``cap-pack.yaml``.
    """

    rule_id = "F001"
    description = (
        "SKILL.md must exist at the expected path for each skill in the pack"
    )
    severity = "blocking"

    # ── idempotency guard ──────────────────────────────────────────────────────

    def _is_already_fixed(self, pack_path: str) -> bool:
        """Return ``True`` when every declared skill already has a SKILL.md."""
        return len(self._find_missing_skills(pack_path)) == 0

    # ── analyze (dry-run) ──────────────────────────────────────────────────────

    def analyze(self, pack_path: str, check_details: dict[str, Any]) -> FixResult:
        """Inspect the pack and produce a plan of create actions for missing SKILL.md files.

        Args:
            pack_path:      Path to the cap-pack directory.
            check_details:  Details from the failed scan check.

        Returns:
            A ``FixResult`` with ``dry_run=True`` containing a ``FixAction``
            for each missing SKILL.md.
        """
        result = FixResult(rule_id=self.rule_id, dry_run=True)

        missing = self._find_missing_skills(pack_path)
        for skill in missing:
            action = FixAction(
                rule_id=self.rule_id,
                action_type="create",
                target_path=skill["skill_md_path"],
                new_content=self._render_skill_md(skill),
                description=(
                    f"Create missing SKILL.md for skill "
                    f"'{skill['id']}' at {skill['skill_md_path']}"
                ),
            )
            result.actions.append(action)

        return result

    # ── apply ──────────────────────────────────────────────────────────────────

    def apply(self, pack_path: str, check_details: dict[str, Any]) -> FixResult:
        """Create missing SKILL.md files from the skeleton template.

        Idempotent — existing SKILL.md files are never overwritten.

        Args:
            pack_path:      Path to the cap-pack directory.
            check_details:  Details from the failed scan check.

        Returns:
            A ``FixResult`` with ``dry_run=False`` and counters for
            applied / skipped actions.
        """
        result = FixResult(rule_id=self.rule_id, dry_run=False)

        missing = self._find_missing_skills(pack_path)
        for skill in missing:
            target = Path(skill["skill_md_path"])

            # Idempotency: skip if file already exists
            if target.exists():
                result.skipped += 1
                continue

            # Ensure parent directory exists
            target.parent.mkdir(parents=True, exist_ok=True)

            content = self._render_skill_md(skill)
            target.write_text(content, encoding="utf-8")

            action = FixAction(
                rule_id=self.rule_id,
                action_type="create",
                target_path=str(target),
                new_content=content,
                description=(
                    f"Created missing SKILL.md for skill "
                    f"'{skill['id']}' at {skill['skill_md_path']}"
                ),
            )
            result.actions.append(action)
            result.applied += 1

        return result

    # ── internal helpers ───────────────────────────────────────────────────────

    def _find_missing_skills(self, pack_path: str) -> list[dict[str, Any]]:
        """Parse ``cap-pack.yaml`` and return skill entries whose SKILL.md is missing.

        Returns a list of dicts with keys:
            ``id``, ``name``, ``description``, ``version``, ``tags``,
            ``skill_md_path``.
        """
        pack_dir = Path(pack_path)
        cap_pack_yaml = pack_dir / "cap-pack.yaml"

        if not cap_pack_yaml.exists():
            return []

        with open(cap_pack_yaml, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        missing: list[dict[str, Any]] = []

        for sk in data.get("skills", []):
            skill_id = sk.get("id", "") or sk.get("name", "")
            rel_path = sk.get("path", f"SKILLS/{skill_id}/SKILL.md")
            skill_md_path = (pack_dir / rel_path).resolve()

            if skill_md_path.exists():
                continue

            missing.append({
                "id": skill_id,
                "name": sk.get("name", skill_id),
                "description": sk.get("description", ""),
                "version": str(sk.get("version", "1.0.0")),
                "tags": sk.get("tags", []),
                "skill_md_path": str(skill_md_path),
            })

        return missing

    @staticmethod
    def _render_skill_md(skill: dict[str, Any]) -> str:
        """Render a complete SKILL.md string from the metadata dict.

        The generated file contains:

        1. YAML frontmatter (``name``, ``description``, ``version``,
           ``tags``, ``triggers``)
        2. A level-1 heading with the skill name
        3. The description paragraph
        4. Placeholder sections: Overview, Usage, Configuration, Dependencies,
           References
        """
        name = skill.get("name", skill.get("id", "unknown"))
        description = skill.get("description", "")
        version = skill.get("version", "1.0.0")
        tags: list[str] = skill.get("tags", [])

        # Infer triggers from the skill name and up to 3 tags
        triggers: list[str] = [name.lower().replace("_", "-").replace(" ", "-")]
        for t in tags[:3]:
            if isinstance(t, str) and t not in triggers:
                triggers.append(t)

        frontmatter: dict[str, Any] = {
            "name": name,
            "description": description,
            "version": version,
        }
        if tags:
            frontmatter["tags"] = tags
        frontmatter["triggers"] = triggers

        fm_yaml = yaml.dump(
            frontmatter,
            default_flow_style=False,
            allow_unicode=True,
            sort_keys=False,
        )

        body = SKILL_MD_TEMPLATE.format(name=name, description=description)

        return f"---\n{fm_yaml}---\n\n{body}"
