"""AtomicityScanner — checks SKILL.md line count, topic count, dep count (H004-H005)."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Optional

from skill_governance.models.result import CheckResult
from skill_governance.scanner.base import BaseScanner


class AtomicityScanner(BaseScanner):
    """Layer 2 (Health) scanner for atomicity rules H004 and H005.

    H004: SKILL.md must be < 500 lines (single responsibility principle).
    H005: Topic count per SKILL.md must be <= 3 distinct topics.
    """

    def __init__(self, rule_loader: Any = None) -> None:
        super().__init__(rule_loader)
        self.layer_id = "L2"

    def _scan_impl(self, target: Any, **kwargs: Any) -> list[CheckResult]:
        """Scan for atomicity violations.

        Args:
            target: List of skill dicts, each with at least a "path" key
                    pointing to the skill directory (containing SKILL.md).
        """
        results: list[CheckResult] = []
        skills = target if isinstance(target, list) else kwargs.get("skills", [])

        # H004 — line count check
        h004_result = self._check_line_count(skills)
        results.append(h004_result)

        # H005 — topic count check
        h005_result = self._check_topic_count(skills)
        results.append(h005_result)

        return results

    def _check_line_count(self, skills: list[dict[str, Any]]) -> CheckResult:
        """H004: SKILL.md < 500 lines per skill."""
        max_lines: int = 500
        violations: list[dict[str, Any]] = []
        total_skills = 0

        for skill in skills:
            skill_path = skill.get("path", "")
            if not skill_path:
                continue
            skill_dir = Path(skill_path)
            skill_md = skill_dir / "SKILL.md"
            if not skill_md.exists():
                continue
            total_skills += 1
            try:
                with open(skill_md, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                line_count = len(lines)
                if line_count > max_lines:
                    violations.append(
                        {
                            "skill_path": str(skill_md),
                            "line_count": line_count,
                            "max_allowed": max_lines,
                        }
                    )
            except Exception:
                continue

        passed = len(violations) == 0
        score = 100.0 if passed else max(0, 100.0 - (len(violations) / max(1, total_skills)) * 100)
        suggestions = [
            f"Split {v['skill_path']} ({v['line_count']} lines) into smaller atomic skills"
            for v in violations
        ]

        return self._make_result(
            rule_id="H004",
            passed=passed,
            score=round(score, 2),
            details={
                "max_lines": max_lines,
                "violations": violations,
                "total_skills_checked": total_skills,
            },
            suggestions=suggestions if suggestions else ["All skills within line count limits"],
        )

    def _check_topic_count(self, skills: list[dict[str, Any]]) -> CheckResult:
        """H005: Topic count per SKILL.md <= 3 distinct topics."""
        max_topics: int = 3
        violations: list[dict[str, Any]] = []
        total_skills = 0

        for skill in skills:
            skill_path = skill.get("path", "")
            if not skill_path:
                continue
            skill_dir = Path(skill_path)
            skill_md = skill_dir / "SKILL.md"
            if not skill_md.exists():
                continue
            total_skills += 1
            try:
                with open(skill_md, "r", encoding="utf-8") as f:
                    content = f.read()

                headings = re.findall(r"^#{2,3}\s+(.+)$", content, re.MULTILINE)
                topics = self._extract_topics(headings)

                if len(topics) > max_topics:
                    violations.append(
                        {
                            "skill_path": str(skill_md),
                            "topic_count": len(topics),
                            "topics": topics,
                            "max_allowed": max_topics,
                        }
                    )
            except Exception:
                continue

        passed = len(violations) == 0
        score = 100.0 if passed else max(0, 100.0 - (len(violations) / max(1, total_skills)) * 100)
        suggestions = [
            f"Reduce topic count in {v['skill_path']} from {v['topic_count']} to ≤ {max_topics} — merge or split"
            for v in violations
        ]

        return self._make_result(
            rule_id="H005",
            passed=passed,
            score=round(score, 2),
            details={
                "max_topics": max_topics,
                "violations": violations,
                "total_skills_checked": total_skills,
            },
            suggestions=suggestions if suggestions else ["All skills within topic count limits"],
        )

    @staticmethod
    def _extract_topics(headings: list[str]) -> list[str]:
        """Extract distinct normalized topics from markdown headings."""
        seen: set[str] = set()
        topics: list[str] = []
        stop_words = {"introduction", "overview", "usage", "setup", "installation", "reference", "conclusion", "example", "examples"}

        for h in headings:
            normalized = h.strip().lower()
            normalized = re.sub(r"[^a-z0-9\s]", "", normalized)
            if normalized in stop_words:
                continue
            if normalized not in seen:
                seen.add(normalized)
                topics.append(h.strip())

        return topics
