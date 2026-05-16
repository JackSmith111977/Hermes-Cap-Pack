"""E002 — Cross-platform compatibility: agent_types enrichment.

Story-6-2-2: E002 cross-platform fix rule.

Analyzes each skill entry in ``cap-pack.yaml`` and checks the
``compatibility.agent_types`` list.  When fewer than 2 agent types are
declared, the rule uses LLM assistance to infer the best platform list
from the skill's name, description, and tags.

Idempotent — skills that already declare >= 2 agent types are never touched.

References:
  - ADR-6-1 (dual-phase fix design)
  - ADR-6-2 (.bak backup convention)
  - Scanner E002 check (compliance.py _check_e002)
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from skill_governance.fixer.base import FixAction, FixResult
from skill_governance.fixer.llm_assist import LLMAssistRule

# ─── Constants ──────────────────────────────────────────────────────────────────

_MIN_AGENT_TYPES = 2
_VALID_AGENT_TYPES = {"opencode", "openclaw", "claude"}
_DEFAULT_AGENT_TYPES = ["opencode", "openclaw"]


# ─── YAML helpers ──────────────────────────────────────────────────────────────


def _load_cap_pack_yaml(
    pack_path: str,
) -> tuple[dict[str, Any], Path, str]:
    """Load and parse ``cap-pack.yaml`` from *pack_path*.

    Returns ``(data, path, raw_string)``.  Raises ``FileNotFoundError``
    if the file does not exist.
    """
    pack_dir = Path(pack_path).resolve()
    yaml_path = pack_dir / "cap-pack.yaml"

    if not yaml_path.exists():
        raise FileNotFoundError(f"cap-pack.yaml not found in {pack_path}")

    content = yaml_path.read_text(encoding="utf-8")
    data = yaml.safe_load(content)
    if not isinstance(data, dict):
        data = {}

    return data, yaml_path, content


def _dump_yaml(data: dict[str, Any]) -> str:
    """Dump a dict to a YAML string with consistent formatting."""
    return yaml.dump(
        data,
        default_flow_style=False,
        allow_unicode=True,
        sort_keys=False,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# E002CrossPlatformFixRule
# ═══════════════════════════════════════════════════════════════════════════════


class E002CrossPlatformFixRule(LLMAssistRule):
    """Verify and fix cross-platform compatibility (>= 2 agent_types).

    Analyzes each skill entry in ``cap-pack.yaml``.  When
    ``compatibility.agent_types`` has fewer than 2 entries, the rule infers
    the most appropriate agent types using:

    1. LLM assistance (via ``opencode run``) — best quality.
    2. Heuristic fallback — keyword-based mapping when LLM is unavailable.

    The fix updates the skill entry's ``compatibility.agent_types`` list.

    Idempotent — skills that already declare >= 2 agent types are never
    modified.
    """

    rule_id = "E002"
    description = (
        "Cross-platform compatibility — >=2 agent_types declared per skill"
    )
    severity = "warning"

    # ── idempotency guard ──────────────────────────────────────────────────────

    def _is_already_fixed(self, pack_path: str) -> bool:
        """Return ``True`` when every skill has >= 2 agent_types."""
        try:
            data, _, _ = _load_cap_pack_yaml(pack_path)
        except FileNotFoundError:
            return True

        for sk in data.get("skills", []):
            if not isinstance(sk, dict):
                continue
            agent_types = self._get_agent_types(sk)
            if len(agent_types) < _MIN_AGENT_TYPES:
                return False
        return True

    # ── analyze (dry-run) ──────────────────────────────────────────────────────

    def analyze(self, pack_path: str, check_details: dict[str, Any]) -> FixResult:
        """Inspect each skill and plan agent_types fixes.

        Args:
            pack_path:      Path to the cap-pack directory.
            check_details:  Details from the failed scan check.

        Returns:
            A ``FixResult`` with ``dry_run=True`` containing one ``FixAction``
            per skill that needs agent_types enrichment.
        """
        result = FixResult(rule_id=self.rule_id, dry_run=True)

        try:
            data, yaml_path, _ = _load_cap_pack_yaml(pack_path)
        except FileNotFoundError:
            result.errors.append(f"cap-pack.yaml not found in {pack_path}")
            return result

        pack_name = data.get("name", yaml_path.parent.name)
        violations = self._find_violations(data)

        for skill_id, agent_types in violations:
            action = FixAction(
                rule_id=self.rule_id,
                action_type="modify",
                target_path=str(yaml_path),
                old_content="",
                new_content="",
                description=(
                    f"Skill '{skill_id}' has {len(agent_types)} agent type(s) "
                    f"— need at least {_MIN_AGENT_TYPES}. "
                    f"In pack '{pack_name}'"
                ),
            )
            result.actions.append(action)

        return result

    # ── apply ──────────────────────────────────────────────────────────────────

    def apply(self, pack_path: str, check_details: dict[str, Any]) -> FixResult:
        """Apply agent_types fixes using LLM or fallback inference.

        Idempotent — skills that already have >= 2 agent_types are skipped.

        Args:
            pack_path:      Path to the cap-pack directory.
            check_details:  Details from the failed scan check.

        Returns:
            A ``FixResult`` with ``dry_run=False``.
        """
        result = FixResult(rule_id=self.rule_id, dry_run=False)

        try:
            data, yaml_path, raw_content = _load_cap_pack_yaml(pack_path)
        except FileNotFoundError:
            result.errors.append(f"cap-pack.yaml not found in {pack_path}")
            return result

        violations = self._find_violations(data)
        if not violations:
            result.skipped += 1
            return result

        # Create .bak backup (ADR-6-2)
        self._backup(yaml_path)

        # Re-read to avoid stale data
        fresh_content = yaml_path.read_text(encoding="utf-8")
        data_updated = yaml.safe_load(fresh_content) or {}

        # Build a map: skill_id → entry for fast lookup
        skills_map: dict[str, dict[str, Any]] = {}
        for sk in data_updated.get("skills", []):
            if isinstance(sk, dict):
                sid = sk.get("id", "") or sk.get("name", "")
                if sid:
                    skills_map[sid] = sk

        for skill_id, current_types in violations:
            sk_entry = skills_map.get(skill_id)
            if sk_entry is None:
                result.errors.append(f"Skill '{skill_id}' not found in updated data")
                continue

            # Infer new agent types
            new_types = self._infer_agent_types(
                skill_id=skill_id,
                skill_name=str(sk_entry.get("name", skill_id)),
                description=str(sk_entry.get("description", "")),
                tags=list(sk_entry.get("tags", [])),
                current_types=current_types,
            )

            # Update compatibility section
            if "compatibility" not in sk_entry or not isinstance(sk_entry["compatibility"], dict):
                sk_entry["compatibility"] = {"agent_types": new_types}
            else:
                sk_entry["compatibility"]["agent_types"] = new_types

            action = FixAction(
                rule_id=self.rule_id,
                action_type="modify",
                target_path=str(yaml_path),
                old_content=fresh_content,
                new_content="",  # Will rebuild after all updates
                description=(
                    f"Updated agent_types for skill '{skill_id}': "
                    f"{current_types} → {new_types}"
                ),
            )
            result.actions.append(action)
            result.applied += 1

        # Write updated YAML
        if result.applied > 0:
            new_yaml = _dump_yaml(data_updated)
            yaml_path.write_text(new_yaml, encoding="utf-8")

            # Update old_content / new_content in actions
            for action in result.actions:
                action.old_content = fresh_content
                action.new_content = new_yaml

        return result

    # ── internal helpers ───────────────────────────────────────────────────────

    @staticmethod
    def _get_agent_types(skill_entry: dict[str, Any]) -> list[str]:
        """Extract agent_types from a skill entry, handling various formats.

        Supports both ``compatibility.agent_types`` nested format and
        flat ``compatibility`` as a list.
        """
        compat = skill_entry.get("compatibility", {})
        if isinstance(compat, dict):
            agent_types = compat.get("agent_types", [])
        elif isinstance(compat, list):
            agent_types = compat
        else:
            agent_types = []

        if not isinstance(agent_types, list):
            agent_types = []

        return [str(t).strip().lower() for t in agent_types if t]

    @staticmethod
    def _find_violations(data: dict[str, Any]) -> list[tuple[str, list[str]]]:
        """Find skills with fewer than ``MIN_AGENT_TYPES`` agent types.

        Returns a list of ``(skill_id, current_agent_types)`` tuples.
        """
        violations: list[tuple[str, list[str]]] = []
        for sk in data.get("skills", []):
            if not isinstance(sk, dict):
                continue
            skill_id = sk.get("id", "") or sk.get("name", "")
            if not skill_id:
                continue
            agent_types = E002CrossPlatformFixRule._get_agent_types(sk)
            if len(agent_types) < _MIN_AGENT_TYPES:
                violations.append((skill_id, agent_types))
        return violations

    @staticmethod
    def _infer_agent_types(
        skill_id: str,
        skill_name: str,
        description: str,
        tags: list[str],
        current_types: list[str],
    ) -> list[str]:
        """Infer the best agent types for a skill.

        Tries LLM first; falls back to heuristic keyword-based inference.
        Always returns at least 2 agent types.
        """
        # Try LLM
        prompt = LLMAssistRule._build_llm_prompt_agent_types(
            skill_id, skill_name, description, tags,
        )
        llm_response = LLMAssistRule._call_llm(prompt)
        if llm_response:
            parsed = LLMAssistRule._parse_llm_yaml_list(llm_response, "agent_types")
            if parsed:
                # Validate against known types
                valid = [t for t in parsed if t.lower() in _VALID_AGENT_TYPES]
                if len(valid) >= _MIN_AGENT_TYPES:
                    return valid[:3]

        # Fallback: heuristic
        return LLMAssistRule._fallback_agent_types(
            skill_name, description, tags,
        )
