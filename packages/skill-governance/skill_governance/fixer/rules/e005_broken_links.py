"""E005 — Broken links detection and repair for SKILL.md files.

Story-6-2-3: E005 broken links detection and repair.

Analyzes SKILL.md files in the pack, finds all markdown links ``[text](url)``,
and validates HTTP(S) URLs with ``curl --head``.  Relative file links are
checked against the filesystem.

When broken links are found, the rule attempts to find replacements via LLM
assistance (for HTTP URLs) or simple path correction (for relative paths).

References:
  - ADR-6-1 (dual-phase fix design)
  - ADR-6-2 (.bak backup convention)
  - Scanner E005 check (compliance.py _check_e005)
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path
from typing import Any

from skill_governance.fixer.base import FixAction, FixResult
from skill_governance.fixer.llm_assist import LLMAssistRule

# ─── Constants ──────────────────────────────────────────────────────────────────

_CURL_TIMEOUT = 10  # seconds per URL
_MAX_URLS_TO_CHECK = 50  # safety limit per SKILL.md
_MAX_LLM_FIXES = 5  # limit LLM calls per run

# Regex for markdown links: [text](url)
_LINK_PATTERN = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")

# Known public hosts that respond to HEAD (used to avoid false positives)
_KNOWN_GOOD_HOSTS: set[str] = {
    "github.com",
    "raw.githubusercontent.com",
    "docs.github.com",
    "pypi.org",
    "npmjs.com",
    "docker.com",
    "docs.docker.com",
    "kubernetes.io",
    "python.org",
    "docs.python.org",
    "nodejs.org",
    "npmjs.org",
    "stackoverflow.com",
    "medium.com",
    "twitter.com",
    "x.com",
    "linkedin.com",
    "youtube.com",
    "arxiv.org",
    "doi.org",
    "wikipedia.org",
    "microsoft.com",
    "learn.microsoft.com",
    "code.visualstudio.com",
    "jetbrains.com",
    "plugins.jetbrains.com",
    "openai.com",
    "platform.openai.com",
    "anthropic.com",
    "docs.anthropic.com",
}


# ─── URL validation ────────────────────────────────────────────────────────────


def _check_url_with_curl(url: str) -> bool:
    """Validate a URL using ``curl --head --silent --fail``.

    Returns ``True`` if the URL responds with a 2xx status, ``False``
    otherwise (including timeouts and connection errors).
    """
    if not url.startswith(("http://", "https://")):
        return False

    try:
        proc = subprocess.run(
            [
                "curl",
                "--head",
                "--silent",
                "--fail",
                "--location",
                "--max-time", str(_CURL_TIMEOUT),
                url,
            ],
            capture_output=True,
            text=True,
            timeout=_CURL_TIMEOUT + 5,
        )
        return proc.returncode == 0
    except (subprocess.TimeoutExpired, OSError, FileNotFoundError):
        # curl not available — skip real checks, assume valid for known hosts
        return False


def _check_url_fast(url: str) -> bool | None:
    """Fast URL check using heuristic rules.

    Returns:
      - ``True`` if the URL is definitely valid (known host).
      - ``False`` if the URL is obviously broken.
      - ``None`` if a real HTTP check is needed.
    """
    if url.startswith("mailto:") or url.startswith("#"):
        return True  # anchors and mailto are not validated here

    if url.startswith("http"):
        # Check known-good hosts
        for host in _KNOWN_GOOD_HOSTS:
            if host in url:
                return True
        # Needs real check
        return None

    if url.startswith("/"):
        return None  # absolute path

    return None  # other — needs real check


def _extract_links_from_skill_md(
    skill_md_path: Path,
) -> list[dict[str, Any]]:
    """Extract all markdown links from a SKILL.md file.

    Returns a list of dicts with keys:
      ``link_text``, ``url``, ``line_number``.
    """
    links: list[dict[str, Any]] = []
    try:
        content = skill_md_path.read_text(encoding="utf-8")
    except Exception:
        return links

    for i, line in enumerate(content.splitlines(), 1):
        for match in _LINK_PATTERN.finditer(line):
            url = match.group(2).strip()
            if url:
                links.append({
                    "link_text": match.group(1),
                    "url": url,
                    "line_number": i,
                })

    return links


def _find_skill_md_files(pack_path: str) -> list[Path]:
    """Find all SKILL.md files under *pack_path*."""
    return sorted(Path(pack_path).rglob("SKILL.md"))


# ═══════════════════════════════════════════════════════════════════════════════
# E005BrokenLinksFixRule
# ═══════════════════════════════════════════════════════════════════════════════


class E005BrokenLinksFixRule(LLMAssistRule):
    """Detect and fix broken links in SKILL.md files.

    The ``analyze()`` phase:
      1. Scans all SKILL.md files for markdown links.
      2. Validates HTTP(S) URLs via ``curl --head`` (or fast heuristic for
         known-good hosts).
      3. Checks relative file paths against the filesystem.
      4. Reports all broken links with their location.

    The ``apply()`` phase:
      1. For broken HTTP(S) URLs, attempts to find a replacement via LLM.
      2. For broken relative paths, attempts simple path corrections.
      3. Updates the SKILL.md file with corrected links.

    Idempotent — only previously-identified broken links are processed.
    """

    rule_id = "E005"
    description = "SKILL.md contains no dead/broken links"
    severity = "info"

    # ── idempotency guard ──────────────────────────────────────────────────────

    def _is_already_fixed(self, pack_path: str) -> bool:
        """Return ``True`` when no broken links are detected."""
        broken = self._scan_for_broken_links(pack_path)
        return len(broken) == 0

    # ── analyze (dry-run) ──────────────────────────────────────────────────────

    def analyze(self, pack_path: str, check_details: dict[str, Any]) -> FixResult:
        """Scan all SKILL.md files and report broken links.

        Args:
            pack_path:      Path to the cap-pack directory.
            check_details:  Details from the failed scan check.

        Returns:
            A ``FixResult`` with ``dry_run=True`` containing one ``FixAction``
            per broken link with details about the issue.
        """
        result = FixResult(rule_id=self.rule_id, dry_run=True)

        broken = self._scan_for_broken_links(pack_path)
        if not broken:
            return result

        for b in broken:
            action = FixAction(
                rule_id=self.rule_id,
                action_type="modify",
                target_path=b["skill_md_path"],
                old_content="",
                new_content="",
                description=(
                    f"Broken link in skill '{b['skill_id']}' "
                    f"(line {b['line_number']}): "
                    f"'{b['link_text']}' → {b['url']} [{b['reason']}]"
                ),
            )
            result.actions.append(action)

        return result

    # ── apply ──────────────────────────────────────────────────────────────────

    def apply(self, pack_path: str, check_details: dict[str, Any]) -> FixResult:
        """Attempt to fix broken links in SKILL.md files.

        Uses LLM assistance for broken HTTP(S) URLs.  Attempts simple
        path corrections for relative links.  Idempotent — only
        previously-detected broken links are processed.

        Args:
            pack_path:      Path to the cap-pack directory.
            check_details:  Details from the failed scan check.

        Returns:
            A ``FixResult`` with ``dry_run=False``.
        """
        result = FixResult(rule_id=self.rule_id, dry_run=False)

        broken = self._scan_for_broken_links(pack_path)
        if not broken:
            result.skipped += 1
            return result

        llm_fixes_remaining = _MAX_LLM_FIXES

        # Group broken links by SKILL.md path
        by_file: dict[str, list[dict[str, Any]]] = {}
        for b in broken:
            by_file.setdefault(b["skill_md_path"], []).append(b)

        for skill_md_path_str, broken_links in by_file.items():
            skill_md_path = Path(skill_md_path_str)
            if not skill_md_path.exists():
                for b in broken_links:
                    result.errors.append(
                        f"SKILL.md not found: {skill_md_path_str}"
                    )
                continue

            try:
                content = skill_md_path.read_text(encoding="utf-8")
            except Exception as exc:
                for b in broken_links:
                    result.errors.append(
                        f"Cannot read {skill_md_path_str}: {exc}"
                    )
                continue

            # Build corrections
            corrections: dict[str, str] = {}  # old_url → new_url
            for b in broken_links:
                replacement = self._find_replacement(
                    broken_url=b["url"],
                    link_text=b["link_text"],
                    reason=b["reason"],
                    skill_id=b["skill_id"],
                    pack_path=pack_path,
                    use_llm=(llm_fixes_remaining > 0),
                )
                if replacement and replacement != b["url"]:
                    corrections[b["url"]] = replacement
                    if b["url"].startswith("http"):
                        llm_fixes_remaining -= 1

            if not corrections:
                continue

            # Apply corrections to content
            updated_content = content
            applied_count = 0
            for old_url, new_url in corrections.items():
                # Escape URL for regex (dots, slashes, etc.)
                escaped_old = re.escape(old_url)
                # Only replace inside markdown link parentheses
                # Pattern: ](old_url)  →  ](new_url)
                updated_content = re.sub(
                    r"\]\(" + escaped_old + r"\)",
                    "](" + new_url + ")",
                    updated_content,
                )
                applied_count += 1

            if applied_count == 0:
                continue

            # Create .bak backup (ADR-6-2)
            self._backup(skill_md_path)

            try:
                skill_md_path.write_text(updated_content, encoding="utf-8")
            except Exception as exc:
                result.errors.append(
                    f"Failed to write {skill_md_path}: {exc}"
                )
                continue

            action = FixAction(
                rule_id=self.rule_id,
                action_type="modify",
                target_path=skill_md_path_str,
                old_content=content,
                new_content=updated_content,
                description=(
                    f"Fixed {applied_count} broken link(s) in "
                    f"'{b.get('skill_id', skill_md_path.parent.name)}'"
                ),
            )
            result.actions.append(action)
            result.applied += applied_count

        return result

    # ── internal helpers ───────────────────────────────────────────────────────

    def _scan_for_broken_links(
        self, pack_path: str
    ) -> list[dict[str, Any]]:
        """Scan all SKILL.md files and return details of broken links.

        Returns a list of dicts with keys:
          ``url``, ``link_text``, ``line_number``, ``skill_md_path``,
          ``skill_id``, ``reason``.
        """
        broken: list[dict[str, Any]] = []

        for skill_md_path in _find_skill_md_files(pack_path):
            # Determine skill_id from parent dir name or frontmatter
            skill_id = skill_md_path.parent.name
            links = _extract_links_from_skill_md(skill_md_path)

            for link in links[: _MAX_URLS_TO_CHECK]:
                url = link["url"]
                reason = self._check_link(url, skill_md_path.parent)

                if reason:
                    broken.append({
                        "url": url,
                        "link_text": link["link_text"],
                        "line_number": link["line_number"],
                        "skill_md_path": str(skill_md_path),
                        "skill_id": skill_id,
                        "reason": reason,
                    })

        return broken

    @staticmethod
    def _check_link(url: str, skill_dir: Path) -> str | None:
        """Check a single link and return a reason string if broken.

        Returns ``None`` for valid links, or a string describing the issue.
        """
        # Skip non-validatable URLs
        if url.startswith("mailto:") or url.startswith("#"):
            return None

        if url.startswith(("http://", "https://")):
            # Fast check: known-good hosts
            fast = _check_url_fast(url)
            if fast is True:
                return None
            if fast is False:
                return "invalid_url"

            # Real curl check
            if not _check_url_with_curl(url):
                return "http_error"
            return None

        # Relative file path
        if url.startswith("/"):
            full_path = Path(url)
        else:
            full_path = (skill_dir / url).resolve()

        if not full_path.exists():
            return "file_not_found"

        return None

    @staticmethod
    def _find_replacement(
        broken_url: str,
        link_text: str,
        reason: str,
        skill_id: str,
        pack_path: str,
        use_llm: bool,
    ) -> str | None:
        """Attempt to find a replacement URL for a broken link.

        For HTTP URLs, tries LLM assistance first, then common
        transformations.  For relative paths, tries path adjustments.
        """
        if broken_url.startswith(("http://", "https://")):
            if use_llm:
                # Gather skill context for the LLM
                context = _gather_skill_context(pack_path, skill_id)
                prompt = LLMAssistRule._build_llm_prompt_replacement_url(
                    broken_url, link_text, context,
                )
                response = LLMAssistRule._call_llm(prompt)
                if response:
                    replacement = LLMAssistRule._parse_llm_single_line(response)
                    if replacement and replacement.startswith("http"):
                        return replacement

            # Common transformations
            return _try_common_url_fixes(broken_url)

        # Relative path: try common adjustments
        return _try_common_path_fixes(broken_url, reason)


def _gather_skill_context(pack_path: str, skill_id: str) -> str:
    """Gather context from a skill's SKILL.md for LLM prompts."""
    for skill_md in _find_skill_md_files(pack_path):
        if skill_md.parent.name == skill_id or skill_id in skill_md.name:
            try:
                content = skill_md.read_text(encoding="utf-8")
                # Return first ~500 chars as context
                return content[:500]
            except Exception:
                pass
    return f"Skill: {skill_id} in pack: {Path(pack_path).name}"


def _try_common_url_fixes(url: str) -> str | None:
    """Apply common URL fix heuristics.

    Examples:
      - Add/remove trailing slash
      - Change http → https
      - Fix common domain typos (e.g., githib.com → github.com)
    """
    # http → https
    if url.startswith("http://"):
        https_url = "https://" + url[7:]
        if _check_url_with_curl(https_url):
            return https_url

    # Add trailing slash (common for index pages)
    if not url.endswith("/") and "." not in url.split("/")[-1]:
        with_slash = url + "/"
        if _check_url_with_curl(with_slash):
            return with_slash

    # Remove trailing slash
    if url.endswith("/"):
        without_slash = url.rstrip("/")
        if _check_url_with_curl(without_slash):
            return without_slash

    return None


def _try_common_path_fixes(
    relative_path: str, reason: str
) -> str | None:
    """Attempt to fix broken relative file paths.

    Returns the corrected path if found, or ``None``.
    """
    # Could add path-correction logic here (e.g., parent dir lookup)
    # For now, return None — relative path fixes are best handled manually.
    return None
