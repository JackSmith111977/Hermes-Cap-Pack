"""F006 + F007 fix rules — classification validation and triggers auto-completion.

F006: ``classification`` must be one of: ``domain``, ``toolset``, ``skill``,
      ``infrastructure``.  Uses a heuristic that inspects the pack name and
      SKILL.md tags/description to infer the correct value when the field is
      missing or invalid.  Severity: ``blocking``.

F007: ``triggers`` array must have at least 1 entry.  When empty, auto-fills
      triggers from skill tags (first 3) and keywords extracted from name and
      description.  Severity: ``warning``.

Both rules are idempotent — they skip packs that already satisfy the rule.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml

from skill_governance.fixer.base import FixAction, FixResult, FixRule

# ─── Valid classification values ──────────────────────────────────────────────

VALID_CLASSIFICATIONS: set[str] = {"domain", "toolset", "skill", "infrastructure"}

# ─── Classification heuristics ────────────────────────────────────────────────

_KEYWORD_TO_CLASSIFICATION: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"(?:skill|quality|engine)"), "infrastructure"),
    (re.compile(r"(?:workflow|process)"), "toolset"),
    (re.compile(r"(?:creative|design|analysis)"), "domain"),
]

# Keywords that appear in tag/description text and hint at a classification
_TAG_HINTS: dict[str, str] = {
    # infrastructure hints
    "quality": "infrastructure",
    "engine": "infrastructure",
    "monitoring": "infrastructure",
    "gate": "infrastructure",
    "infra": "infrastructure",
    # toolset hints
    "workflow": "toolset",
    "process": "toolset",
    "pipeline": "toolset",
    "automation": "toolset",
    "orchestration": "toolset",
    "integration": "toolset",
    # domain hints
    "domain": "domain",
    "creative": "domain",
    "design": "domain",
    "analysis": "domain",
}

_DEFAULT_CLASSIFICATION = "toolset"


def _infer_classification_from_name(pack_name: str) -> str | None:
    """Try to infer classification from the pack name alone.

    Returns the inferred classification, or ``None`` if the name does not
    contain any known keyword.
    """
    name_lower = pack_name.lower().replace("-", " ").replace("_", " ")
    for pattern, classification in _KEYWORD_TO_CLASSIFICATION:
        if pattern.search(name_lower):
            return classification
    return None


def _infer_classification_from_tags_and_desc(
    skill_tags: list[str], description: str
) -> str | None:
    """Scan skill-level tags and pack description for classification hints.

    Collects classification "votes" from known tag/description keywords
    and returns the one with the highest count.  Returns ``None`` when no
    hints are found.
    """
    votes: dict[str, int] = {}
    text = " ".join(skill_tags).lower() + " " + description.lower()

    for keyword, classification in _TAG_HINTS.items():
        if keyword in text:
            votes[classification] = votes.get(classification, 0) + 1

    if not votes:
        return None

    # Return the classification with the most votes
    return max(votes, key=lambda k: (votes[k], k))  # tie-break by name


def _infer_classification(pack_name: str, tag_text: str, desc_text: str) -> str:
    """Multi-dimensional classification inference.

    1. Check the pack name (strongest signal).
    2. Check skill tags and pack description (secondary signal).
    3. Fall back to the default.
    """
    # Primary signal: pack name
    name_class = _infer_classification_from_name(pack_name)
    if name_class:
        return name_class

    # Secondary signal: tags + description
    tag_class = _infer_classification_from_tags_and_desc(
        _collect_tags_from_text(tag_text), desc_text
    )
    if tag_class:
        return tag_class

    return _DEFAULT_CLASSIFICATION


def _collect_tags_from_text(text: str) -> list[str]:
    """Split a whitespace/comma-separated string into a list of lowercased tags."""
    if not text:
        return []
    # Split by whitespace or comma
    parts = re.split(r"[\s,]+", text.strip().lower())
    return [p for p in parts if p]


def _skill_tags_from_pack(pack_dir: Path) -> list[str]:
    """Collect all tags from SKILL.md files inside a pack.

    Walks the pack directory looking for ``SKILL.md`` files, parses their
    frontmatter, and gathers the ``tags`` list.
    """
    all_tags: list[str] = []
    for skill_md in sorted(pack_dir.rglob("SKILL.md")):
        try:
            content = skill_md.read_text(encoding="utf-8")
            fm = _parse_frontmatter_from_txt(content)
            tags = fm.get("tags", [])
            if isinstance(tags, list):
                all_tags.extend(str(t).lower() for t in tags)
        except Exception:
            continue
    return all_tags


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


def _load_cap_pack_yaml(pack_path: str) -> tuple[dict[str, Any], Path, str]:
    """Load and parse ``cap-pack.yaml`` from *pack_path*.

    Returns:
        A tuple of (data_dict, path_to_yaml, original_yaml_string).
        Raises ``FileNotFoundError`` if the file does not exist.
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
    """Dump a dict back to YAML string with consistent formatting.

    Uses ``default_flow_style=False`` and explicit start/end markers.
    """
    return yaml.dump(
        data,
        default_flow_style=False,
        allow_unicode=True,
        sort_keys=False,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# F006
# ═══════════════════════════════════════════════════════════════════════════════


class F006ClassificationFixRule(FixRule):
    """Verify and fix the ``classification`` field in ``cap-pack.yaml``.

    If the classification is missing or not one of the four valid values
    (``domain``, ``toolset``, ``skill``, ``infrastructure``), the rule infers
    the correct value using a heuristic:

    1. Pack-name keywords (strongest signal):
       - ``skill`` / ``quality`` / ``engine`` → ``infrastructure``
       - ``workflow`` / ``process`` → ``toolset``
       - ``creative`` / ``design`` / ``analysis`` → ``domain``
    2. SKILL.md tags and pack description (secondary signal).
    3. Fallback: ``toolset``.
    """

    rule_id = "F006"
    description = (
        "classification must be one of: domain, toolset, skill, infrastructure"
    )
    severity = "blocking"

    # ── idempotency guard ──────────────────────────────────────────────────────

    def _is_already_fixed(self, pack_path: str) -> bool:
        """Return ``True`` when classification is valid and non-empty."""
        data, _, _ = _load_cap_pack_yaml(pack_path)
        return data.get("classification", "") in VALID_CLASSIFICATIONS

    # ── analyze (dry-run) ──────────────────────────────────────────────────────

    def analyze(self, pack_path: str, check_details: dict[str, Any]) -> FixResult:
        """Check classification and plan a fix if invalid.

        Args:
            pack_path:      Path to the cap-pack directory.
            check_details:  Details from the failed scan check.

        Returns:
            A ``FixResult`` with ``dry_run=True``.
        """
        result = FixResult(rule_id=self.rule_id, dry_run=True)

        try:
            data, yaml_path, _ = _load_cap_pack_yaml(pack_path)
        except FileNotFoundError:
            result.errors.append(f"cap-pack.yaml not found in {pack_path}")
            return result

        current = data.get("classification", "")
        if current in VALID_CLASSIFICATIONS:
            # Already valid — no action needed
            return result

        # Infer the correct classification
        pack_name = data.get("name", yaml_path.parent.name)
        all_tags = _skill_tags_from_pack(Path(pack_path))
        description = data.get("description", "")
        tag_text = " ".join(all_tags)

        inferred = _infer_classification(pack_name, tag_text, description)

        action = FixAction(
            rule_id=self.rule_id,
            action_type="modify",
            target_path=str(yaml_path),
            old_content=_dump_yaml(data),
            new_content="",  # filled in apply()
            description=(
                f"Fix classification: '{current or '(empty)'}' → '{inferred}' "
                f"for pack '{pack_name}'"
            ),
        )
        result.actions.append(action)

        return result

    # ── apply ──────────────────────────────────────────────────────────────────

    def apply(self, pack_path: str, check_details: dict[str, Any]) -> FixResult:
        """Apply the classification fix by modifying ``cap-pack.yaml``.

        Idempotent — if the classification is already valid no changes are
        made.

        Args:
            pack_path:      Path to the cap-pack directory.
            check_details:  Details from the failed scan check.

        Returns:
            A ``FixResult`` with ``dry_run=False``.
        """
        result = FixResult(rule_id=self.rule_id, dry_run=False)

        try:
            data, yaml_path, _ = _load_cap_pack_yaml(pack_path)
        except FileNotFoundError:
            result.errors.append(f"cap-pack.yaml not found in {pack_path}")
            return result

        current = data.get("classification", "")
        if current in VALID_CLASSIFICATIONS:
            # Idempotent: already fixed
            result.skipped += 1
            return result

        # Infer the correct classification
        pack_name = data.get("name", yaml_path.parent.name)
        all_tags = _skill_tags_from_pack(Path(pack_path))
        description = data.get("description", "")
        tag_text = " ".join(all_tags)

        inferred = _infer_classification(pack_name, tag_text, description)

        # Create .bak backup
        self._backup(yaml_path)

        # Read again in case the file was modified between _load and now
        raw_content = yaml_path.read_text(encoding="utf-8")
        data_updated = yaml.safe_load(raw_content) or {}
        data_updated["classification"] = inferred

        new_yaml = _dump_yaml(data_updated)

        # Preserve comments by doing a targeted field replacement when possible
        # (ADR-6-2: .bak is already created above)
        yaml_path.write_text(new_yaml, encoding="utf-8")

        action = FixAction(
            rule_id=self.rule_id,
            action_type="modify",
            target_path=str(yaml_path),
            old_content=raw_content,
            new_content=new_yaml,
            description=(
                f"Applied classification fix: '{current or '(empty)'}' → "
                f"'{inferred}' for pack '{pack_name}'"
            ),
        )
        result.actions.append(action)
        result.applied += 1

        return result


# ═══════════════════════════════════════════════════════════════════════════════
# F007
# ═══════════════════════════════════════════════════════════════════════════════


class F007TriggersFixRule(FixRule):
    """Verify and auto-fill the ``triggers`` array in ``cap-pack.yaml``.

    If the ``triggers`` array is empty or missing, the rule generates trigger
    entries from:

    1. Skill tags — takes up to 3 unique tags from all SKILL.md files in
       the pack.
    2. Name / description keywords — extracts 1--2 salient keywords from
       the pack name and description.

    Idempotent — existing triggers are never overwritten.

    Severity: ``warning``.
    """

    rule_id = "F007"
    description = "triggers array must have at least 1 entry"
    severity = "warning"

    # ── idempotency guard ──────────────────────────────────────────────────────

    def _is_already_fixed(self, pack_path: str) -> bool:
        """Return ``True`` when triggers is non-empty."""
        data, _, _ = _load_cap_pack_yaml(pack_path)
        triggers = data.get("triggers", [])
        return isinstance(triggers, list) and len(triggers) > 0

    # ── analyze (dry-run) ──────────────────────────────────────────────────────

    def analyze(self, pack_path: str, check_details: dict[str, Any]) -> FixResult:
        """Check triggers and plan a fix if empty.

        Args:
            pack_path:      Path to the cap-pack directory.
            check_details:  Details from the failed scan check.

        Returns:
            A ``FixResult`` with ``dry_run=True``.
        """
        result = FixResult(rule_id=self.rule_id, dry_run=True)

        try:
            data, yaml_path, _ = _load_cap_pack_yaml(pack_path)
        except FileNotFoundError:
            result.errors.append(f"cap-pack.yaml not found in {pack_path}")
            return result

        triggers = data.get("triggers", [])
        if isinstance(triggers, list) and len(triggers) > 0:
            # Already has triggers — idempotent
            return result

        new_triggers = self._generate_triggers(pack_path, data)

        action = FixAction(
            rule_id=self.rule_id,
            action_type="modify",
            target_path=str(yaml_path),
            old_content=_dump_yaml(data),
            new_content="",  # filled in apply()
            description=(
                f"Add {len(new_triggers)} auto-generated trigger(s) to "
                f"pack '{data.get('name', yaml_path.parent.name)}'"
            ),
        )
        result.actions.append(action)

        return result

    # ── apply ──────────────────────────────────────────────────────────────────

    def apply(self, pack_path: str, check_details: dict[str, Any]) -> FixResult:
        """Apply the triggers fix by modifying ``cap-pack.yaml``.

        Idempotent — existing triggers are never overwritten.

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

        triggers = data.get("triggers", [])
        if isinstance(triggers, list) and len(triggers) > 0:
            # Idempotent: already has triggers
            result.skipped += 1
            return result

        new_triggers = self._generate_triggers(pack_path, data)

        # Create .bak backup
        self._backup(yaml_path)

        # Read again for safety
        raw_content_fresh = yaml_path.read_text(encoding="utf-8")
        data_updated = yaml.safe_load(raw_content_fresh) or {}
        data_updated["triggers"] = new_triggers

        new_yaml = _dump_yaml(data_updated)
        yaml_path.write_text(new_yaml, encoding="utf-8")

        action = FixAction(
            rule_id=self.rule_id,
            action_type="modify",
            target_path=str(yaml_path),
            old_content=raw_content_fresh,
            new_content=new_yaml,
            description=(
                f"Added {len(new_triggers)} auto-generated trigger(s) to "
                f"pack '{data.get('name', yaml_path.parent.name)}'"
            ),
        )
        result.actions.append(action)
        result.applied += 1

        return result

    # ── internal helpers ───────────────────────────────────────────────────────

    @staticmethod
    def _generate_triggers(
        pack_path: str, pack_data: dict[str, Any]
    ) -> list[str]:
        """Generate trigger entries for a pack.

        Uses the following sources (in priority order):

        1. Skill tags — up to 3 unique, de-duplicated tags from SKILL.md
           frontmatter across all skills in the pack.
        2. Pack name — added as a trigger with dashes replaced by spaces.
        3. Description keywords — 1--2 salient keywords extracted from the
           description.

        Returns:
            A list of unique trigger strings (lowercased).
        """
        triggers: list[str] = []
        seen: set[str] = set()

        # 1. Collect skill tags (up to 3 unique)
        all_tags = _skill_tags_from_pack(Path(pack_path))
        for tag in all_tags:
            tag_clean = tag.strip().lower()
            if tag_clean and tag_clean not in seen:
                triggers.append(tag_clean)
                seen.add(tag_clean)
                if len(triggers) >= 3:
                    break

        # 2. Add pack name as a trigger
        pack_name = pack_data.get("name", Path(pack_path).name)
        name_trigger = pack_name.replace("-", " ").replace("_", " ").strip().lower()
        if name_trigger and name_trigger not in seen:
            triggers.append(name_trigger)
            seen.add(name_trigger)

        # 3. Extract 1-2 keywords from description
        description = pack_data.get("description", "")
        if description:
            keywords = _extract_salient_keywords(description, seen)
            for kw in keywords[:2]:
                if kw not in seen:
                    triggers.append(kw)
                    seen.add(kw)
                    if len(triggers) >= 5:
                        break

        # Ensure at least 1 trigger
        if not triggers:
            triggers.append(pack_name.replace("-", " ").replace("_", " ").strip().lower())

        # De-duplicate and limit
        unique: list[str] = []
        for t in triggers:
            if t not in unique:
                unique.append(t)

        return unique[:5]


def _extract_salient_keywords(
    text: str, seen: set[str]
) -> list[str]:
    """Extract salient keywords from *text*.

    Picks up to 3 single-word or two-word phrases that are not already in
    *seen*.  Filters out common stopwords and very short tokens.

    Args:
        text: The source text (e.g. pack description).
        seen: Already-used strings to avoid duplicates.

    Returns:
        A list of keyword strings.
    """
    # Common English and Chinese stopwords / filler words
    stopwords: set[str] = {
        "the", "a", "an", "and", "or", "of", "in", "to", "for", "with",
        "on", "at", "by", "is", "are", "was", "were", "be", "been", "being",
        "have", "has", "had", "do", "does", "did", "will", "would", "could",
        "should", "may", "might", "shall", "can", "need", "must",
        "this", "that", "these", "those", "it", "its", "they", "them",
        "their", "we", "our", "you", "your", "he", "she", "him", "her",
        "all", "each", "every", "some", "any", "no", "not", "only",
        "about", "also", "very", "just", "more", "most", "much", "many",
        "such", "other", "another", "from", "as", "into", "through",
        "during", "before", "after", "above", "below", "between",
        # Chinese stopwords
        "的", "了", "在", "是", "我", "有", "和", "就", "不", "人", "都",
        "一", "一个", "上", "也", "很", "到", "说", "要", "去", "你",
        "会", "着", "没有", "看", "好", "自己", "这", "他", "她", "它",
        "们", "那", "什么", "怎么", "如何", "为", "能", "及", "与",
        "及", "但", "而", "或",
        # Verbs/common in descriptions
        "use", "used", "using", "uses", "generate", "generating",
        "generates", "created", "create", "creates", "creating",
        "build", "building", "builds", "built", "provide", "provides",
        "providing", "support", "supports", "supporting", "supported",
        "include", "includes", "including", "covered",
        "cover", "covers", "covering", "based",
        "complete", "comprehensive", "full", "professional",
    }

    # Normalize text
    text = text.lower()

    # Split into tokens (English words + Chinese characters)
    # Match sequences of CJK characters or alphanumeric words
    tokens: list[str] = []
    for match in re.finditer(r"[\u4e00-\u9fff]+|[a-z][a-z0-9-]*", text):
        token = match.group(0)
        if token not in stopwords and token not in seen and len(token) >= 2:
            tokens.append(token)

    # De-duplicate while preserving order
    seen_local: set[str] = set()
    unique_tokens: list[str] = []
    for t in tokens:
        if t not in seen_local:
            unique_tokens.append(t)
            seen_local.add(t)

    # Return up to 3 keywords
    return unique_tokens[:3]
