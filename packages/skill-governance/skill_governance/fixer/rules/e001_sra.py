"""E001 — SRA metadata enhancement: triggers and description quality.

Story-6-2-2: E001 SRA metadata fix rule.

Analyzes SKILL.md frontmatter for each skill in the pack:
  - ``triggers`` must have at least 3 entries for good SRA discoverability
  - ``description`` must be at least 20 characters and contain trigger-relevant words

When these conditions are not met, the rule uses LLM assistance to generate
optimized triggers and descriptions, falling back to heuristic generation when
the LLM CLI is unavailable.

References:
  - ADR-6-1 (dual-phase fix design)
  - ADR-6-2 (.bak backup convention)
  - Scanner E001 check (compliance.py _check_e001)
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml

from skill_governance.fixer.base import FixAction, FixResult
from skill_governance.fixer.llm_assist import LLMAssistRule

# ─── Constants ──────────────────────────────────────────────────────────────────

_MIN_TRIGGERS = 3
_MIN_DESCRIPTION_LENGTH = 20
_MAX_SKILLS_TO_PROCESS = 10  # safety limit


# ─── Parsing helpers ───────────────────────────────────────────────────────────


def _parse_frontmatter_from_txt(content: str) -> dict[str, Any]:
    """Parse YAML frontmatter from a markdown string."""
    lines = content.split("\n")
    if not lines or lines[0].strip() != "---":
        return {}
    end_idx = -1
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end_idx = i
            break
    if end_idx == -1:
        return {}
    try:
        fm = yaml.safe_load("\n".join(lines[1:end_idx]))
        return fm if isinstance(fm, dict) else {}
    except Exception:
        return {}


def _find_skill_md_files(pack_path: str) -> list[Path]:
    """Find all SKILL.md files under *pack_path*."""
    return sorted(Path(pack_path).rglob("SKILL.md"))


def _load_skill_metadata_from_pack(pack_path: str) -> list[dict[str, Any]]:
    """Extract metadata for all skills from cap-pack.yaml + SKILL.md files.

    Returns a list of dicts with keys:
      ``skill_id``, ``skill_md_path``, ``name``, ``description``, ``tags``,
      ``triggers``, ``frontmatter``, ``body``.
    """
    pack_dir = Path(pack_path)
    cap_yaml = pack_dir / "cap-pack.yaml"
    if not cap_yaml.exists():
        return []

    with open(cap_yaml, "r", encoding="utf-8") as f:
        manifest = yaml.safe_load(f) or {}

    # Build a map: skill_id → manifest entry
    skill_map: dict[str, dict[str, Any]] = {}
    for sk in manifest.get("skills", []):
        sid = sk.get("id", "") or sk.get("name", "")
        if sid:
            skill_map[sid] = sk

    skills_meta: list[dict[str, Any]] = []
    for skill_md_path in _find_skill_md_files(pack_path):
        try:
            content = skill_md_path.read_text(encoding="utf-8")
        except Exception:
            continue

        fm = _parse_frontmatter_from_txt(content)
        sid = str(fm.get("id", skill_md_path.parent.name))

        manifest_entry = skill_map.get(sid, {})
        body_start = content.find("---", content.find("---") + 3) if content.startswith("---") else 0
        body = content[body_start + 3:].strip() if body_start > 0 else content.strip()

        skills_meta.append({
            "skill_id": sid,
            "skill_md_path": str(skill_md_path),
            "name": str(fm.get("name", manifest_entry.get("name", sid))),
            "description": str(fm.get("description", manifest_entry.get("description", ""))),
            "tags": list(fm.get("tags", manifest_entry.get("tags", []))),
            "triggers": list(fm.get("triggers", [])),
            "frontmatter": fm,
            "body": body,
        })

    return skills_meta


# ═══════════════════════════════════════════════════════════════════════════════
# E001SRAMetadataFixRule
# ═══════════════════════════════════════════════════════════════════════════════


class E001SRAMetadataFixRule(LLMAssistRule):
    """Enhance SRA metadata — triggers and description — for each skill.

    Analyzes SKILL.md frontmatter and identifies skills where:

    * ``triggers`` has fewer than ``MIN_TRIGGERS`` (3) entries.
    * ``description`` is shorter than ``MIN_DESCRIPTION_LENGTH`` (20 chars)
      or lacks keywords that appear in the skill tags.

    During ``apply()``, calls the LLM to generate optimized triggers and
    descriptions.  Idempotent — skills that already meet the thresholds are
    never touched.
    """

    rule_id = "E001"
    description = "SRA discoverability — triggers >= 3, description >= 20 chars with relevant keywords"
    severity = "warning"

    # ── idempotency guard ──────────────────────────────────────────────────────

    def _is_already_fixed(self, pack_path: str) -> bool:
        """Return ``True`` when every skill already has good SRA metadata."""
        skills = _load_skill_metadata_from_pack(pack_path)
        for sk in skills:
            triggers = sk.get("triggers", [])
            desc = sk.get("description", "")
            if len(triggers) < _MIN_TRIGGERS:
                return False
            if len(desc) < _MIN_DESCRIPTION_LENGTH:
                return False
            # Check that description covers at least one tag keyword
            tags = sk.get("tags", [])
            if tags and not any(t.lower() in desc.lower() for t in tags if isinstance(t, str)):
                return False
        return True

    # ── analyze (dry-run) ──────────────────────────────────────────────────────

    def analyze(self, pack_path: str, check_details: dict[str, Any]) -> FixResult:
        """Inspect each skill and plan SRA metadata enhancements.

        Args:
            pack_path:      Path to the cap-pack directory.
            check_details:  Details from the failed scan check.

        Returns:
            A ``FixResult`` with ``dry_run=True`` containing one ``FixAction``
            per skill that needs metadata improvement.
        """
        result = FixResult(rule_id=self.rule_id, dry_run=True)

        skills = _load_skill_metadata_from_pack(pack_path)
        if not skills:
            result.errors.append(f"No SKILL.md files found in {pack_path}")
            return result

        for sk in skills:
            issues = self._check_skill_metadata(sk)
            if not issues:
                continue

            action = FixAction(
                rule_id=self.rule_id,
                action_type="modify",
                target_path=sk["skill_md_path"],
                old_content="",  # filled in apply()
                new_content="",
                description=(
                    f"Enhance SRA metadata for skill '{sk['skill_id']}': "
                    f"{' | '.join(issues)}"
                ),
            )
            result.actions.append(action)

        return result

    # ── apply ──────────────────────────────────────────────────────────────────

    def apply(self, pack_path: str, check_details: dict[str, Any]) -> FixResult:
        """Apply SRA metadata enhancements using LLM or fallback generation.

        Idempotent — skills that already meet the thresholds are skipped.

        Args:
            pack_path:      Path to the cap-pack directory.
            check_details:  Details from the failed scan check.

        Returns:
            A ``FixResult`` with ``dry_run=False``.
        """
        result = FixResult(rule_id=self.rule_id, dry_run=False)

        skills = _load_skill_metadata_from_pack(pack_path)
        if not skills:
            result.errors.append(f"No SKILL.md files found in {pack_path}")
            return result

        for sk in skills:
            issues = self._check_skill_metadata(sk)
            if not issues:
                result.skipped += 1
                continue

            skill_md_path = Path(sk["skill_md_path"])
            if not skill_md_path.exists():
                result.errors.append(f"SKILL.md not found: {skill_md_path}")
                continue

            # Read current content
            try:
                content = skill_md_path.read_text(encoding="utf-8")
            except Exception as exc:
                result.errors.append(f"Cannot read {skill_md_path}: {exc}")
                continue

            fm = _parse_frontmatter_from_txt(content)
            if not fm:
                result.errors.append(f"No valid frontmatter in {skill_md_path}")
                continue

            updated = dict(fm)
            changed = False

            # Fix triggers if insufficient
            triggers = list(fm.get("triggers", []))
            if len(triggers) < _MIN_TRIGGERS:
                new_triggers = self._generate_triggers(
                    sk["skill_id"],
                    sk["name"],
                    sk["description"],
                    sk["tags"],
                )
                if new_triggers:
                    updated["triggers"] = new_triggers
                    changed = True

            # Fix description if too short or missing tag keywords
            desc = fm.get("description", "")
            tags = sk.get("tags", [])
            needs_desc = (
                len(desc) < _MIN_DESCRIPTION_LENGTH
                or (tags and not any(t.lower() in desc.lower() for t in tags if isinstance(t, str)))
            )
            if needs_desc:
                new_desc = self._generate_description(
                    sk["skill_id"],
                    sk["name"],
                    tags,
                    desc,
                )
                if new_desc and new_desc != desc:
                    updated["description"] = new_desc
                    changed = True

            if not changed:
                result.skipped += 1
                continue

            # Create .bak backup (ADR-6-2)
            self._backup(skill_md_path)

            # Write updated frontmatter
            new_content = self._rebuild_skill_md(content, fm, updated)

            try:
                skill_md_path.write_text(new_content, encoding="utf-8")
            except Exception as exc:
                result.errors.append(f"Failed to write {skill_md_path}: {exc}")
                continue

            action = FixAction(
                rule_id=self.rule_id,
                action_type="modify",
                target_path=sk["skill_md_path"],
                old_content=content,
                new_content=new_content,
                description=(
                    f"Applied SRA metadata enhancement for skill "
                    f"'{sk['skill_id']}'"
                ),
            )
            result.actions.append(action)
            result.applied += 1

        return result

    # ── internal helpers ───────────────────────────────────────────────────────

    @staticmethod
    def _check_skill_metadata(sk: dict[str, Any]) -> list[str]:
        """Check a single skill's metadata and return a list of issues found.

        Returns an empty list when metadata is adequate.
        """
        issues: list[str] = []
        triggers = sk.get("triggers", [])
        desc = sk.get("description", "")
        tags = sk.get("tags", [])

        if len(triggers) < _MIN_TRIGGERS:
            issues.append(
                f"triggers has {len(triggers)} entries (min {_MIN_TRIGGERS})"
            )

        if len(desc) < _MIN_DESCRIPTION_LENGTH:
            issues.append(
                f"description is {len(desc)} chars (min {_MIN_DESCRIPTION_LENGTH})"
            )
        elif tags:
            missing_tags = [
                t for t in tags if isinstance(t, str) and t.lower() not in desc.lower()
            ]
            if missing_tags:
                issues.append(f"description missing tag keywords: {', '.join(missing_tags[:3])}")

        return issues

    @staticmethod
    def _generate_triggers(
        skill_id: str, name: str, description: str, tags: list[str]
    ) -> list[str]:
        """Generate improved triggers via LLM or fallback.

        Tries LLM first; falls back to heuristic generation.
        """
        # Try LLM
        prompt = LLMAssistRule._build_llm_prompt_triggers(
            skill_id, name, description, tags
        )
        llm_response = LLMAssistRule._call_llm(prompt)
        if llm_response:
            parsed = LLMAssistRule._parse_llm_yaml_list(llm_response, "triggers")
            if parsed and len(parsed) >= _MIN_TRIGGERS:
                return parsed[:5]

        # Fallback
        return LLMAssistRule._fallback_triggers(skill_id, name, description, tags)

    @staticmethod
    def _generate_description(
        skill_id: str, name: str, tags: list[str], current_desc: str
    ) -> str | None:
        """Generate an improved description via LLM or fallback.

        Tries LLM first; falls back to heuristic generation.
        """
        # Try LLM
        prompt = LLMAssistRule._build_llm_prompt_description(
            skill_id, name, tags, current_desc
        )
        llm_response = LLMAssistRule._call_llm(prompt)
        if llm_response:
            parsed = LLMAssistRule._parse_llm_single_line(llm_response)
            if parsed and len(parsed) >= _MIN_DESCRIPTION_LENGTH:
                return parsed

        # Fallback
        if len(current_desc) < _MIN_DESCRIPTION_LENGTH:
            return LLMAssistRule._fallback_description(name, tags)
        return None

    @staticmethod
    def _rebuild_skill_md(
        old_content: str,
        old_frontmatter: dict[str, Any],
        new_frontmatter: dict[str, Any],
    ) -> str:
        """Rebuild a SKILL.md string with updated frontmatter.

        Preserves the body (everything after the closing ``---``).
        """
        # Find the closing --- of frontmatter
        lines = old_content.split("\n")
        end_idx = -1
        for i in range(1, len(lines)):
            if lines[i].strip() == "---":
                end_idx = i
                break

        body = ""
        if end_idx > 0 and end_idx + 1 < len(lines):
            body = "\n".join(lines[end_idx + 1:])

        # Dump new frontmatter
        fm_yaml = yaml.dump(
            new_frontmatter,
            default_flow_style=False,
            allow_unicode=True,
            sort_keys=False,
        )

        return f"---\n{fm_yaml}---\n\n{body}"
