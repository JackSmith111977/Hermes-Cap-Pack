"""ComplianceChecker — L1 F001-F007 + L3 E001-E005 rules."""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any, Optional

from skill_governance.models.result import CheckResult
from skill_governance.scanner.base import BaseScanner

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore[assignment]


class ComplianceChecker(BaseScanner):
    """Multi-layer compliance scanner for L1 (Foundation) and L3 (Ecosystem) rules.

    L1 Rules (F001-F007):
      F001: SKILL.md must exist
      F002: YAML frontmatter must contain name and description
      F003: SQS >= 60
      F004: version field must be present and valid semver
      F005: tags field must have at least 2 entries
      F006: classification must be one of: domain, toolset, infrastructure
      F007: triggers array must have at least 1 entry

    L3 Rules (E001-E005):
      E001: SRA discoverability > 80%
      E002: Cross-platform compatibility (>=2 agent_types)
      E003: Cross-pack non-redundancy (<60% overlap)
      E004: At least 1 L2 Experience document exists
      E005: SKILL.md contains no dead/broken links
    """

    def __init__(self, layer_id: str = "L1", rule_loader: Any = None) -> None:
        super().__init__(rule_loader)
        self.layer_id = layer_id
        self._target_skills: list[dict[str, Any]] = []
        self._target_pack_path: str = ""

    def _scan_impl(self, target: Any, **kwargs: Any) -> list[CheckResult]:
        """Run checks for the configured layer.

        Args:
            target: For L1: list of skill dicts with "path" key.
                    For L3: dict with skills, pack_path, other data.
                    Or pass via kwargs.
        """
        if self.layer_id == "L1":
            return self._scan_l1(target, **kwargs)
        elif self.layer_id == "L3":
            return self._scan_l3(target, **kwargs)
        else:
            return []

    # ─── L1: Foundation Checks ───────────────────────────────────────────────

    def _scan_l1(self, target: Any, **kwargs: Any) -> list[CheckResult]:
        data = target if isinstance(target, dict) else kwargs
        skills: list[dict[str, Any]] = data.get("skills", []) if isinstance(data, dict) else (
            target if isinstance(target, list) else kwargs.get("skills", [])
        )
        self._target_skills = skills

        return [
            self._check_f001(skills),
            self._check_f002(skills),
            self._check_f003(skills),
            self._check_f004(skills),
            self._check_f005(skills),
            self._check_f006(skills),
            self._check_f007(skills),
        ]

    def _check_f001(self, skills: list[dict[str, Any]]) -> CheckResult:
        """F001: SKILL.md must exist."""
        missing: list[dict[str, Any]] = []
        for sk in skills:
            skill_path = sk.get("path", "")
            if not skill_path:
                continue
            skill_md = Path(skill_path) / "SKILL.md"
            if not skill_md.exists():
                missing.append({"skill_id": sk.get("id", "") or sk.get("name", ""), "path": str(skill_md)})

        passed = len(missing) == 0
        score = 100.0 if passed else max(0, 100.0 - (len(missing) / max(1, len(skills))) * 100)
        suggestions = [f"Create SKILL.md at '{m['path']}'" for m in missing]

        return self._make_result(
            rule_id="F001",
            passed=passed,
            score=round(score, 2),
            details={"missing_skills": missing, "total_checked": len(skills)},
            suggestions=suggestions or ["All SKILL.md files exist"],
        )

    def _check_f002(self, skills: list[dict[str, Any]]) -> CheckResult:
        """F002: Frontmatter must contain name and description."""
        violations: list[dict[str, Any]] = []
        for sk in skills:
            skill_path = sk.get("path", "")
            if not skill_path:
                continue
            skill_md = Path(skill_path) / "SKILL.md"
            if not skill_md.exists():
                continue
            try:
                content = skill_md.read_text(encoding="utf-8")
                frontmatter = self._parse_frontmatter(content)
                missing_fields = []
                for field in ("name", "description"):
                    if field not in frontmatter or not frontmatter[field]:
                        missing_fields.append(field)
                if missing_fields:
                    violations.append(
                        {
                            "skill_id": sk.get("id", "") or sk.get("name", str(skill_md)),
                            "missing_fields": missing_fields,
                        }
                    )
            except Exception:
                violations.append(
                    {
                        "skill_id": sk.get("id", "") or sk.get("name", str(skill_md)),
                        "missing_fields": ["frontmatter_parse_error"],
                    }
                )

        passed = len(violations) == 0
        score = 100.0 if passed else max(0, 100.0 - (len(violations) / max(1, len(skills))) * 100)
        suggestions = [
            f"Add missing fields {v['missing_fields']} to SKILL.md frontmatter for '{v['skill_id']}'"
            for v in violations
        ]

        return self._make_result(
            rule_id="F002",
            passed=passed,
            score=round(score, 2),
            details={"violations": violations},
            suggestions=suggestions or ["All frontmatter contains required fields"],
        )

    def _check_f003(self, skills: list[dict[str, Any]]) -> CheckResult:
        """F003: SQS >= 60 (simulated from sqs_total in data)."""
        low_sqs: list[dict[str, Any]] = []
        for sk in skills:
            sqs = sk.get("sqs_total") or sk.get("sqs", {}).get("total")
            if sqs is not None and sqs < 60:
                low_sqs.append(
                    {
                        "skill_id": sk.get("id", "") or sk.get("name", ""),
                        "sqs_total": sqs,
                        "minimum": 60,
                    }
                )

        passed = len(low_sqs) == 0
        score = 100.0 if passed else max(0, 100.0 - (len(low_sqs) / max(1, len(skills))) * 100)
        suggestions = [
            f"Skill '{s['skill_id']}' has SQS {s['sqs_total']} — below minimum 60, improve quality"
            for s in low_sqs
        ]

        return self._make_result(
            rule_id="F003",
            passed=passed,
            score=round(score, 2),
            details={"low_sqs_skills": low_sqs, "minimum": 60, "max_score": 100},
            suggestions=suggestions or ["All skills meet minimum SQS threshold"],
        )

    def _check_f004(self, skills: list[dict[str, Any]]) -> CheckResult:
        """F004: version must be valid semver."""
        semver_pattern = re.compile(r"^\d+\.\d+\.\d+$")
        violations: list[dict[str, Any]] = []
        for sk in skills:
            version = sk.get("version", "")
            if not version:
                violations.append(
                    {
                        "skill_id": sk.get("id", "") or sk.get("name", ""),
                        "version": version,
                        "reason": "missing",
                    }
                )
            elif not semver_pattern.match(version):
                violations.append(
                    {
                        "skill_id": sk.get("id", "") or sk.get("name", ""),
                        "version": version,
                        "reason": "invalid_semver",
                    }
                )

        passed = len(violations) == 0
        score = 100.0 if passed else max(0, 100.0 - (len(violations) / max(1, len(skills))) * 100)
        suggestions = [
            f"Skill '{v['skill_id']}': version '{v['version']}' is invalid — use MAJOR.MINOR.PATCH"
            for v in violations
        ]

        return self._make_result(
            rule_id="F004",
            passed=passed,
            score=round(score, 2),
            details={"violations": violations},
            suggestions=suggestions or ["All versions are valid semver"],
        )

    def _check_f005(self, skills: list[dict[str, Any]]) -> CheckResult:
        """F005: tags must have >= 2 entries."""
        violations: list[dict[str, Any]] = []
        for sk in skills:
            tags = sk.get("tags", [])
            if not isinstance(tags, list) or len(tags) < 2:
                violations.append(
                    {
                        "skill_id": sk.get("id", "") or sk.get("name", ""),
                        "tags_count": len(tags) if isinstance(tags, list) else 0,
                        "min_required": 2,
                    }
                )

        passed = len(violations) == 0
        score = 100.0 if passed else max(0, 100.0 - (len(violations) / max(1, len(skills))) * 100)
        suggestions = [
            f"Skill '{v['skill_id']}' has only {v['tags_count']} tag(s) — add at least {v['min_required']}"
            for v in violations
        ]

        return self._make_result(
            rule_id="F005",
            passed=passed,
            score=round(score, 2),
            details={"violations": violations},
            suggestions=suggestions or ["All skills have sufficient tags"],
        )

    def _check_f006(self, skills: list[dict[str, Any]]) -> CheckResult:
        """F006: classification must be one of: domain, toolset, infrastructure."""
        allowed = {"domain", "toolset", "infrastructure"}
        violations: list[dict[str, Any]] = []
        for sk in skills:
            classification = sk.get("classification", "")
            if classification not in allowed:
                violations.append(
                    {
                        "skill_id": sk.get("id", "") or sk.get("name", ""),
                        "classification": classification,
                        "allowed": sorted(allowed),
                    }
                )

        passed = len(violations) == 0
        score = 100.0 if passed else max(0, 100.0 - (len(violations) / max(1, len(skills))) * 100)
        suggestions = [
            f"Skill '{v['skill_id']}': classification '{v['classification']}' invalid — use one of {v['allowed']}"
            for v in violations
        ]

        return self._make_result(
            rule_id="F006",
            passed=passed,
            score=round(score, 2),
            details={"violations": violations},
            suggestions=suggestions or ["All classifications are valid"],
        )

    def _check_f007(self, skills: list[dict[str, Any]]) -> CheckResult:
        """F007: triggers must have >= 1 entry."""
        violations: list[dict[str, Any]] = []
        for sk in skills:
            triggers = sk.get("triggers", [])
            if not isinstance(triggers, list) or len(triggers) < 1:
                violations.append(
                    {
                        "skill_id": sk.get("id", "") or sk.get("name", ""),
                        "triggers_count": len(triggers) if isinstance(triggers, list) else 0,
                        "min_required": 1,
                    }
                )

        passed = len(violations) == 0
        score = 100.0 if passed else max(0, 100.0 - (len(violations) / max(1, len(skills))) * 100)
        suggestions = [
            f"Skill '{v['skill_id']}' has no triggers — add at least {v['min_required']} for SRA discovery"
            for v in violations
        ]

        return self._make_result(
            rule_id="F007",
            passed=passed,
            score=round(score, 2),
            details={"violations": violations},
            suggestions=suggestions or ["All skills have triggers defined"],
        )

    # ─── L3: Ecosystem Checks ────────────────────────────────────────────────

    def _scan_l3(self, target: Any, **kwargs: Any) -> list[CheckResult]:
        data = target if isinstance(target, dict) else kwargs
        skills: list[dict[str, Any]] = data.get("skills", [])
        pack_path: str = str(data.get("pack_path", ""))
        self._target_skills = skills
        self._target_pack_path = pack_path

        return [
            self._check_e001(skills),
            self._check_e002(skills),
            self._check_e003(skills),
            self._check_e004(pack_path),
            self._check_e005(skills),
        ]

    def _check_e001(self, skills: list[dict[str, Any]]) -> CheckResult:
        """E001: SRA discoverability > 80% (simulated from trigger quality)."""
        total = len(skills)
        discoverable = sum(
            1
            for sk in skills
            if sk.get("triggers") and isinstance(sk.get("triggers"), list) and len(sk["triggers"]) >= 1
        )
        hit_rate = discoverable / max(1, total)
        min_rate = 0.80
        passed = hit_rate >= min_rate
        score = round(hit_rate * 100, 2)

        suggestions = []
        if not passed:
            suggestions.append(
                f"SRA hit rate is {hit_rate:.1%} — below {min_rate:.0%}. Add more triggers/descriptions."
            )

        return self._make_result(
            rule_id="E001",
            passed=passed,
            score=score,
            details={
                "hit_rate": round(hit_rate, 4),
                "min_hit_rate": min_rate,
                "discoverable_count": discoverable,
                "total_skills": total,
            },
            suggestions=suggestions or ["SRA discoverability meets threshold"],
        )

    def _check_e002(self, skills: list[dict[str, Any]]) -> CheckResult:
        """E002: Cross-platform compatibility — >=2 agent_types declared."""
        violations: list[dict[str, Any]] = []
        for sk in skills:
            compat = sk.get("compatibility", {})
            if isinstance(compat, dict):
                agent_types = compat.get("agent_types", [])
            elif isinstance(compat, list):
                agent_types = compat
            else:
                agent_types = []
            if not isinstance(agent_types, list) or len(agent_types) < 2:
                violations.append(
                    {
                        "skill_id": sk.get("id", "") or sk.get("name", ""),
                        "agent_types": agent_types,
                        "min_required": 2,
                    }
                )

        passed = len(violations) == 0
        score = 100.0 if passed else max(0, 100.0 - (len(violations) / max(1, len(skills))) * 100)
        suggestions = [
            f"Skill '{v['skill_id']}' declares only {len(v['agent_types'])} agent type(s) — need at least {v['min_required']}"
            for v in violations
        ]

        return self._make_result(
            rule_id="E002",
            passed=passed,
            score=round(score, 2),
            details={"violations": violations},
            suggestions=suggestions or ["All skills declare sufficient agent types"],
        )

    def _check_e003(self, skills: list[dict[str, Any]]) -> CheckResult:
        """E003: Cross-pack non-redundancy (<60% overlap).

        Note: True cross-pack requires access to other packs. This check
        estimates based on skill IDs and names to flag potential duplicates.
        """
        max_overlap = 0.60
        potential_duplicates: list[dict[str, Any]] = []
        seen_names: dict[str, list[str]] = {}

        for sk in skills:
            name = (sk.get("name", "") or sk.get("id", "")).lower().strip()
            if not name:
                continue
            if name in seen_names:
                potential_duplicates.append(
                    {
                        "name": name,
                        "occurrences": seen_names[name] + [sk.get("id", "") or sk.get("name", "")],
                    }
                )
            seen_names.setdefault(name, []).append(sk.get("id", "") or sk.get("name", ""))

        passed = len(potential_duplicates) == 0
        score = 100.0 if passed else max(0, 100.0 - (len(potential_duplicates) / max(1, len(skills))) * 50)

        return self._make_result(
            rule_id="E003",
            passed=passed,
            score=round(score, 2),
            details={
                "max_overlap_ratio": max_overlap,
                "potential_duplicates": potential_duplicates,
            },
            suggestions=[
                f"Potential duplicate skill name '{d['name']}' found — investigate if these should be merged"
                for d in potential_duplicates
            ]
            or ["No cross-pack redundancy detected (limited to intra-pack scan)"],
        )

    def _check_e004(self, pack_path: str) -> CheckResult:
        """E004: At least 1 L2 Experience document exists."""
        experiences_count = 0
        experiences_found: list[str] = []

        if pack_path:
            experiences_dir = Path(pack_path) / "EXPERIENCES"
            if experiences_dir.exists():
                for md_file in experiences_dir.glob("*.md"):
                    experiences_count += 1
                    experiences_found.append(md_file.name)

        passed = experiences_count >= 1
        score = 100.0 if passed else 0.0

        return self._make_result(
            rule_id="E004",
            passed=passed,
            score=score,
            details={
                "experiences_count": experiences_count,
                "min_experiences": 1,
                "experiences_found": experiences_found,
                "pack_path": pack_path,
            },
            suggestions=["Add at least 1 Experience document (pitfall, decision-tree, etc.)"]
            if not passed
            else ["Experience documents present"],
        )

    def _check_e005(self, skills: list[dict[str, Any]]) -> CheckResult:
        """E005: SKILL.md contains no dead/broken links.

        Checks for markdown links and basic URL format validation.
        """
        total_links = 0
        broken_links: list[dict[str, Any]] = []

        link_pattern = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")

        for sk in skills:
            skill_path = sk.get("path", "")
            if not skill_path:
                continue
            skill_md = Path(skill_path) / "SKILL.md"
            if not skill_md.exists():
                continue
            try:
                content = skill_md.read_text(encoding="utf-8")
                for match in link_pattern.finditer(content):
                    total_links += 1
                    url = match.group(2).strip()
                    # Check for obvious broken links
                    if url.startswith("http"):
                        pass  # Would need actual HTTP check in production
                    elif url.startswith("#"):
                        anchor = url[1:]
                        if anchor and anchor not in content:
                            broken_links.append(
                                {
                                    "skill_id": sk.get("id", "") or sk.get("name", ""),
                                    "link_text": match.group(1),
                                    "url": url,
                                    "reason": "anchor_not_found",
                                }
                            )
                    elif url.startswith("mailto:"):
                        pass
                    elif url and not Path(skill_path, url).exists():
                        broken_links.append(
                            {
                                "skill_id": sk.get("id", "") or sk.get("name", ""),
                                "link_text": match.group(1),
                                "url": url,
                                "reason": "file_not_found",
                            }
                        )
            except Exception:
                continue

        passed = len(broken_links) == 0
        score = 100.0 if passed else max(0, 100.0 - (len(broken_links) / max(1, total_links)) * 100)

        return self._make_result(
            rule_id="E005",
            passed=passed,
            score=round(score, 2),
            details={
                "total_links": total_links,
                "broken_links": broken_links,
                "max_fail_ratio": 0.0,
            },
            suggestions=[
                f"Fix broken link '{b['link_text']}' ({b['url']}) in skill '{b['skill_id']}'"
                for b in broken_links
            ]
            or ["No broken links detected"],
        )

    @staticmethod
    def _parse_frontmatter(content: str) -> dict[str, Any]:
        """Extract and parse YAML frontmatter from SKILL.md content."""
        # Try YAML frontmatter (--- delimited)
        fm_match = re.match(r"^---\s*\n(.*?)\n---", content, re.DOTALL)
        if fm_match and yaml:
            try:
                return yaml.safe_load(fm_match.group(1)) or {}
            except Exception:
                pass

        # Fallback: regex-based key: value extraction
        result: dict[str, Any] = {}
        for line in content.split("\n"):
            line = line.strip()
            kv_match = re.match(r"^(\w+)\s*:\s*(.*)", line)
            if kv_match:
                key = kv_match.group(1)
                value = kv_match.group(2).strip().strip('"').strip("'")
                if value and not value.startswith("#"):
                    result[key] = value
        return result
