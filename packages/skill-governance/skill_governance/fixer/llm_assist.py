"""LLMAssistRule — base class for fix rules that leverage LLM assistance.

Provides:
  - ``_call_llm(prompt)`` — tries ``opencode run`` via subprocess, falls back
    to a simple heuristic-based generator when the CLI is not available.
  - Dual-phase ``analyze()`` / ``apply()`` lifecycle inherited from ``FixRule``.

Every concrete subclass sets ``rule_id``, ``description``, and ``severity`` as
class-level attributes and provides its own ``analyze()`` / ``apply()``.

Story-6-2-1: LLM-assisted repair framework + F006 enhancement support.
"""

from __future__ import annotations

import json
import logging
import re
import shutil
import subprocess
import sys
from typing import Any

from skill_governance.fixer.base import FixResult, FixRule

logger = logging.getLogger(__name__)

# ─── Constants ──────────────────────────────────────────────────────────────────

_MAX_LLM_OUTPUT_CHARS = 4096
_LLM_TIMEOUT = 30


# ─── LLM invocation ────────────────────────────────────────────────────────────


def _call_opencode(prompt: str, timeout: int = _LLM_TIMEOUT) -> str | None:
    """Invoke ``opencode run`` with a given *prompt* and return the response.

    Returns ``None`` when the CLI is not available, times out, or returns a
    non-zero exit code.
    """
    if not shutil.which("opencode"):
        logger.debug("opencode CLI not found on PATH")
        return None

    cmd = ["opencode", "run", "--json", prompt]
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except (subprocess.TimeoutExpired, OSError) as exc:
        logger.warning("opencode call failed: %s", exc)
        return None

    if proc.returncode != 0:
        logger.warning(
            "opencode returned %d: %s", proc.returncode, proc.stderr.strip()
        )
        return None

    output = (proc.stdout or "").strip()
    if not output:
        return None

    # Try to extract text/response from various opencode output formats
    return _extract_opencode_response(output)


def _extract_opencode_response(raw: str) -> str:
    """Extract the relevant response text from opencode output.

    Handles JSON-wrapped responses and plain text output.
    """
    # Attempt JSON parse (opencode --json usually wraps in JSON)
    try:
        data = json.loads(raw)
        if isinstance(data, dict):
            for key in ("content", "message", "response", "text", "output"):
                if key in data and isinstance(data[key], str):
                    return data[key][:_MAX_LLM_OUTPUT_CHARS]
        if isinstance(data, str):
            return data[:_MAX_LLM_OUTPUT_CHARS]
    except (json.JSONDecodeError, ValueError):
        pass

    # Plain text fallback
    return raw[:_MAX_LLM_OUTPUT_CHARS]


# ─── Fallback heuristic generators ─────────────────────────────────────────────


def _fallback_generate_triggers(
    skill_id: str,
    skill_name: str,
    description: str,
    tags: list[str],
) -> list[str]:
    """Heuristic fallback when the LLM is unavailable.

    Generates trigger entries from skill metadata:
      - skill name (lowercased, hyphenated)
      - up to 3 tags
      - 1-2 keywords extracted from the description
    """
    triggers: list[str] = []
    seen: set[str] = set()

    # 1. Skill name → trigger
    name_trigger = (skill_name or skill_id).lower()
    name_trigger = re.sub(r"[_\s]+", "-", name_trigger)
    if name_trigger and name_trigger not in seen:
        triggers.append(name_trigger)
        seen.add(name_trigger)

    # 2. Tags (up to 3)
    for tag in tags[:3]:
        t = str(tag).strip().lower()
        if t and t not in seen:
            triggers.append(t)
            seen.add(t)

    # 3. Description keywords (up to 2)
    if description:
        keywords = _extract_keywords(description, seen)
        for kw in keywords[:2]:
            if kw not in seen:
                triggers.append(kw)
                seen.add(kw)

    return triggers[:5]


def _fallback_generate_description(
    skill_name: str, tags: list[str]
) -> str:
    """Generate a fallback description from skill name and tags."""
    tag_str = ", ".join(tag for tag in tags if isinstance(tag, str))
    if tag_str:
        return f"A {skill_name} skill focusing on {tag_str}."
    return f"A skill for {skill_name}."


def _fallback_infer_agent_types(
    skill_name: str, description: str, tags: list[str]
) -> list[str]:
    """Fallback agent_type inference when LLM is unavailable.

    Returns at least 2 agent types based on heuristic keyword matching.
    """
    text = f"{skill_name} {description} {' '.join(tags)}".lower()

    # Heuristic mapping: keywords → likely agent types
    agent_map: dict[str, list[str]] = {
        "opencode": ["opencode", "openclaw"],
        "claude": ["claude", "opencode"],
        "openclaw": ["openclaw", "opencode"],
        "code": ["opencode", "openclaw"],
        "cli": ["opencode", "openclaw"],
        "desktop": ["openclaw", "claude"],
        "web": ["openclaw", "claude"],
        "chat": ["openclaw", "claude"],
        "analysis": ["openclaw", "opencode"],
        "creative": ["openclaw", "claude"],
        "design": ["openclaw", "claude"],
        "workflow": ["opencode", "openclaw"],
        "automation": ["opencode", "openclaw"],
        "quality": ["opencode", "openclaw"],
        "engine": ["opencode", "openclaw"],
        "infra": ["opencode", "openclaw"],
        "pipeline": ["opencode", "openclaw"],
        "process": ["opencode", "openclaw"],
    }

    candidates: list[tuple[str, int]] = {}
    for keyword, types in agent_map.items():
        if keyword in text:
            for t in types:
                candidates[t] = candidates.get(t, 0) + 1

    if not candidates:
        return ["opencode", "openclaw"]

    # Sort by frequency descending, then alphabetically
    sorted_types = sorted(candidates, key=lambda k: (-candidates[k], k))
    return sorted_types[:3] if len(sorted_types) >= 2 else sorted_types + ["opencode"]


def _extract_keywords(text: str, seen: set[str]) -> list[str]:
    """Extract salient keywords from *text*, excluding stopwords and *seen* tokens."""
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
        "的", "了", "在", "是", "我", "有", "和", "就", "不", "人", "都",
        "一", "一个", "上", "也", "很", "到", "说", "要", "去", "你",
        "会", "着", "没有", "看", "好", "自己", "这", "他", "她", "它",
        "们", "那", "什么", "怎么", "如何", "为", "能", "及", "与",
        "但", "而", "或",
        "use", "used", "using", "uses", "generate", "generating",
        "generates", "created", "create", "creates", "creating",
        "build", "building", "builds", "built", "provide", "provides",
        "providing", "support", "supports", "supporting", "supported",
        "include", "includes", "including", "covered",
        "cover", "covers", "covering", "based",
        "complete", "comprehensive", "full", "professional",
    }

    text = text.lower()
    tokens: list[str] = []
    for match in re.finditer(r"[\u4e00-\u9fff]+|[a-z][a-z0-9-]*", text):
        token = match.group(0)
        if token not in stopwords and token not in seen and len(token) >= 2:
            tokens.append(token)

    seen_local: set[str] = set()
    unique: list[str] = []
    for t in tokens:
        if t not in seen_local:
            unique.append(t)
            seen_local.add(t)

    return unique[:3]


# ═══════════════════════════════════════════════════════════════════════════════
# LLMAssistRule
# ═══════════════════════════════════════════════════════════════════════════════


class LLMAssistRule(FixRule):
    """Base class for fix rules that use LLM assistance.

    Provides ``_call_llm()`` which attempts to invoke the local LLM CLI
    (``opencode run``) and falls back to heuristic generators when the CLI
    is unavailable.

    Subclasses must implement:
      - ``rule_id``, ``description``, ``severity`` (class attrs)
      - ``analyze()`` → ``FixResult``
      - ``apply()`` → ``FixResult``
    """

    # ── LLM invocation ─────────────────────────────────────────────────────

    @staticmethod
    def _call_llm(prompt: str) -> str | None:
        """Attempt to get an LLM-generated response for *prompt*.

        Tries:
          1. ``opencode run`` via subprocess
          2. Returns ``None`` on failure (caller should use fallback)

        Args:
            prompt: The prompt to send to the LLM.

        Returns:
            The LLM response text, or ``None`` if unavailable.
        """
        return _call_opencode(prompt)

    # ── Fallback helpers (available to subclasses) ──────────────────────────

    @staticmethod
    def _fallback_triggers(
        skill_id: str,
        skill_name: str,
        description: str,
        tags: list[str],
    ) -> list[str]:
        """Heuristic fallback trigger generation."""
        return _fallback_generate_triggers(skill_id, skill_name, description, tags)

    @staticmethod
    def _fallback_description(skill_name: str, tags: list[str]) -> str:
        """Heuristic fallback description generation."""
        return _fallback_generate_description(skill_name, tags)

    @staticmethod
    def _fallback_agent_types(
        skill_name: str, description: str, tags: list[str]
    ) -> list[str]:
        """Heuristic fallback agent type inference."""
        return _fallback_infer_agent_types(skill_name, description, tags)

    @staticmethod
    def _build_llm_prompt_triggers(
        skill_id: str, skill_name: str, description: str, tags: list[str]
    ) -> str:
        """Build a prompt asking the LLM to generate triggers for a skill.

        Returns a prompt string suitable for ``_call_llm()``.
        """
        return (
            f"Generate a YAML list of 3-5 trigger keywords for a skill package.\n\n"
            f"Skill ID: {skill_id}\n"
            f"Name: {skill_name}\n"
            f"Description: {description}\n"
            f"Tags: {', '.join(tags) if tags else '(none)'}\n\n"
            f"Requirements:\n"
            f"- Triggers must be single words or short phrases (lowercase)\n"
            f"- They should help SRA (Skill Recommendation Agent) discover this skill\n"
            f"- Cover the skill's core functionality, domain, and use cases\n"
            f"- Be specific enough to match relevant user requests\n\n"
            f"Return ONLY a YAML list, no commentary:\n"
            f"triggers:\n  - <trigger1>\n  - <trigger2>"
        )

    @staticmethod
    def _build_llm_prompt_description(
        skill_id: str, skill_name: str, tags: list[str], current_description: str
    ) -> str:
        """Build a prompt asking the LLM to improve a skill description."""
        return (
            f"Improve this skill description for SRA discovery.\n\n"
            f"Skill ID: {skill_id}\n"
            f"Name: {skill_name}\n"
            f"Current description: {current_description or '(missing)'}\n"
            f"Tags: {', '.join(tags) if tags else '(none)'}\n\n"
            f"Requirements:\n"
            f"- 1-2 sentences, concise but informative\n"
            f"- Include keywords that help SRA matching\n"
            f"- Describe what the skill does and when to use it\n\n"
            f"Return ONLY the new description, no YAML wrapper."
        )

    @staticmethod
    def _build_llm_prompt_agent_types(
        skill_id: str, skill_name: str, description: str, tags: list[str]
    ) -> str:
        """Build a prompt asking the LLM to infer compatible agent types."""
        return (
            f"Infer the best agent types for this skill package.\n\n"
            f"Skill ID: {skill_id}\n"
            f"Name: {skill_name}\n"
            f"Description: {description}\n"
            f"Tags: {', '.join(tags) if tags else '(none)'}\n\n"
            f"Available agent types: opencode, openclaw, claude\n\n"
            f"Choose at least 2 agent types that best match this skill's purpose.\n"
            f"- opencode: CLI/code-oriented agents\n"
            f"- openclaw: Desktop/GUI agents\n"
            f"- claude: Chat/conversation agents\n\n"
            f"Return ONLY a YAML list, no commentary:\n"
            f"agent_types:\n  - <type1>\n  - <type2>"
        )

    @staticmethod
    def _build_llm_prompt_replacement_url(
        broken_url: str, link_text: str, skill_context: str
    ) -> str:
        """Build a prompt asking the LLM to find a replacement for a broken URL."""
        return (
            f"Find a working replacement URL for this broken link.\n\n"
            f"Broken URL: {broken_url}\n"
            f"Link text: {link_text}\n"
            f"Skill context: {skill_context[:500]}\n\n"
            f"Requirements:\n"
            f"- Return a single URL that is the most likely correct/replacement URL\n"
            f"- The URL should be relevant to the link text and skill context\n"
            f"- If the original URL looks like a moved resource, try to find the new location\n\n"
            f"Return ONLY the replacement URL, no commentary."
        )

    @staticmethod
    def _parse_llm_yaml_list(raw: str, key: str) -> list[str] | None:
        """Parse a YAML list from an LLM response.

        Looks for ``key:`` followed by a list (either ``- item`` or ``[a, b]``)
        in *raw* output.  Returns ``None`` if parsing fails.
        """
        if not raw:
            return None

        # Try JSON-style list: [a, b, c]
        import json as _json
        try:
            parsed = _json.loads(raw)
            if isinstance(parsed, list):
                return [str(item) for item in parsed if isinstance(item, str)]
            if isinstance(parsed, dict) and key in parsed and isinstance(parsed[key], list):
                return [str(item) for item in parsed[key] if isinstance(item, str)]
        except (_json.JSONDecodeError, ValueError):
            pass

        # Try YAML-like list lines
        in_list = False
        items: list[str] = []
        for line in raw.splitlines():
            stripped = line.strip()
            if stripped.startswith(f"{key}:"):
                # Inline list: key: [a, b]
                rest = stripped[len(key) + 1:].strip()
                if rest.startswith("["):
                    try:
                        parsed = _json.loads(rest)
                        if isinstance(parsed, list):
                            return [str(item) for item in parsed if isinstance(item, str)]
                    except (_json.JSONDecodeError, ValueError):
                        pass
                    continue
                # Block list follows
                in_list = True
                continue
            if in_list:
                if stripped.startswith("- "):
                    items.append(stripped[2:].strip())
                elif stripped == "":
                    # End of list on blank line (usually)
                    break
                elif not stripped.startswith("  ") and not stripped.startswith("-"):
                    # Next top-level key
                    break

        if items:
            return items

        # Fallback: just grab lines starting with "- "
        fallback_items = []
        for line in raw.splitlines():
            s = line.strip()
            if s.startswith("- "):
                fallback_items.append(s[2:].strip())
        return fallback_items if fallback_items else None

    @staticmethod
    def _parse_llm_single_line(raw: str) -> str | None:
        """Extract a single line of text from an LLM response.

        Strips markdown code fences, whitespace, and returns the first
        non-empty line.
        """
        if not raw:
            return None

        # Strip markdown code fences
        cleaned = re.sub(r"```(?:yaml|json|text)?\s*", "", raw).strip()
        # Take first non-empty line
        for line in cleaned.splitlines():
            line = line.strip().strip("\"'")
            if line:
                return line
        return None
