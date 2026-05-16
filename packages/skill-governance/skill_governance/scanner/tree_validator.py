"""TreeValidator — cluster membership, cluster size, overlap (H001-H003)."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Optional

from skill_governance.models.result import CheckResult
from skill_governance.scanner.base import BaseScanner


class TreeValidator(BaseScanner):
    """Layer 2 (Health) scanner for tree/cluster rules H001-H003.

    H001: Tree-based cluster membership — every skill must belong to at least one cluster.
    H002: Cluster size must be between 3 and 15 skills per cluster.
    H003: Intra-pack semantic overlap between skills must be < 60%.
    """

    def __init__(self, rule_loader: Any = None) -> None:
        super().__init__(rule_loader)
        self.layer_id = "L2"

    def _scan_impl(self, target: Any, **kwargs: Any) -> list[CheckResult]:
        """Run H001, H002, H003 checks.

        Args:
            target: dict with keys:
                - "skills": list of skill dicts (may have "cluster" or "category")
                - "clusters": list of cluster dicts (each has "name" and "skills")
              OR pass keyword args.
        """
        data = target if isinstance(target, dict) else kwargs
        skills = data.get("skills", [])
        clusters = data.get("clusters", [])
        cluster_map = data.get("cluster_map", {})

        results: list[CheckResult] = []

        h001 = self._check_cluster_membership(skills, clusters, cluster_map)
        results.append(h001)

        h002 = self._check_cluster_size(clusters)
        results.append(h002)

        h003 = self._check_overlap(skills)
        results.append(h003)

        return results

    def _check_cluster_membership(
        self,
        skills: list[dict[str, Any]],
        clusters: list[dict[str, Any]],
        cluster_map: dict[str, Any],
    ) -> CheckResult:
        """H001: Every skill must belong to at least one cluster."""
        clustered_skills: set[str] = set()

        # Collect skill IDs from clusters
        for cluster in clusters:
            for sk in cluster.get("skills", []):
                if isinstance(sk, dict):
                    clustered_skills.add(sk.get("id", "") or sk.get("name", ""))
                else:
                    clustered_skills.add(str(sk))

        # Also check cluster_map if provided
        for cid, members in cluster_map.items():
            for m in members:
                if isinstance(m, dict):
                    clustered_skills.add(m.get("id", "") or m.get("name", ""))
                else:
                    clustered_skills.add(str(m))

        unclustered: list[dict[str, Any]] = []
        for skill in skills:
            sid = skill.get("id", "") or skill.get("name", "")
            if sid and sid not in clustered_skills:
                unclustered.append({"skill_id": sid, "skill_path": skill.get("path", "")})

        passed = len(unclustered) == 0
        score = 100.0 if passed else max(0, 100.0 - (len(unclustered) / max(1, len(skills))) * 100)
        suggestions = [
            f"Skill '{u['skill_id']}' is not a member of any cluster — assign it to an existing cluster or create one"
            for u in unclustered
        ]

        return self._make_result(
            rule_id="H001",
            passed=passed,
            score=round(score, 2),
            details={
                "total_skills": len(skills),
                "clustered_count": len(clustered_skills),
                "unclustered": unclustered,
            },
            suggestions=suggestions if suggestions else ["All skills belong to a cluster"],
        )

    def _check_cluster_size(self, clusters: list[dict[str, Any]]) -> CheckResult:
        """H002: Cluster size 3-15 skills."""
        min_size: int = 3
        max_size: int = 15
        violations: list[dict[str, Any]] = []

        for cluster in clusters:
            members = cluster.get("skills", [])
            size = len(members)
            if size < min_size or size > max_size:
                violations.append(
                    {
                        "cluster_id": cluster.get("id", "") or cluster.get("name", "unnamed"),
                        "size": size,
                        "min_allowed": min_size,
                        "max_allowed": max_size,
                    }
                )

        passed = len(violations) == 0
        score = 100.0 if passed else max(0, 100.0 - (len(violations) / max(1, len(clusters))) * 100)
        suggestions = []
        for v in violations:
            if v["size"] < v["min_allowed"]:
                suggestions.append(
                    f"Cluster '{v['cluster_id']}' has {v['size']} skills — too small, merge with another cluster"
                )
            else:
                suggestions.append(
                    f"Cluster '{v['cluster_id']}' has {v['size']} skills — too large, split into sub-clusters"
                )

        return self._make_result(
            rule_id="H002",
            passed=passed,
            score=round(score, 2),
            details={
                "min_size": min_size,
                "max_size": max_size,
                "violations": violations,
                "total_clusters": len(clusters),
            },
            suggestions=suggestions if suggestions else ["All clusters within size limits"],
        )

    def _check_overlap(self, skills: list[dict[str, Any]]) -> CheckResult:
        """H003: Intra-pack semantic overlap < 60%.

        Uses TF-IDF approximation via word-set overlap ratio.
        """
        max_overlap: float = 0.60
        skills_with_content: list[dict[str, Any]] = []

        for skill in skills:
            skill_path = skill.get("path", "")
            if not skill_path:
                continue
            skill_md_path = Path(skill_path) / "SKILL.md"
            if not skill_md_path.exists():
                continue
            try:
                with open(skill_md_path, "r", encoding="utf-8") as f:
                    content = f.read()
                tokens = set(re.findall(r"\b[a-zA-Z]{3,}\b", content.lower()))
                if tokens:
                    skills_with_content.append(
                        {
                            "skill_id": skill.get("id", "") or skill.get("name", str(skill_md_path)),
                            "skill_path": str(skill_md_path),
                            "tokens": tokens,
                        }
                    )
            except Exception:
                continue

        high_overlap_pairs: list[dict[str, Any]] = []
        for i in range(len(skills_with_content)):
            for j in range(i + 1, len(skills_with_content)):
                a = skills_with_content[i]
                b = skills_with_content[j]
                intersection = len(a["tokens"] & b["tokens"])
                union = len(a["tokens"] | b["tokens"])
                if union == 0:
                    continue
                jaccard = intersection / union
                if jaccard > max_overlap:
                    high_overlap_pairs.append(
                        {
                            "skill_a": a["skill_id"],
                            "skill_b": b["skill_id"],
                            "overlap_ratio": round(jaccard, 4),
                            "threshold": max_overlap,
                        }
                    )

        passed = len(high_overlap_pairs) == 0
        score = 100.0 if passed else max(0, 100.0 - (len(high_overlap_pairs) / max(1, len(skills_with_content))) * 50)
        suggestions = [
            f"High overlap ({p['overlap_ratio']:.1%}) between '{p['skill_a']}' and '{p['skill_b']}' — consider merging"
            for p in high_overlap_pairs
        ]

        return self._make_result(
            rule_id="H003",
            passed=passed,
            score=round(score, 2),
            details={
                "max_overlap_ratio": max_overlap,
                "high_overlap_pairs": high_overlap_pairs,
                "skills_analyzed": len(skills_with_content),
            },
            suggestions=suggestions if suggestions else ["No excessive overlap detected"],
        )
