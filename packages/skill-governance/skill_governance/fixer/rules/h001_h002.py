"""H001 + H002 fix rules — cluster membership and cluster size validation.

H001: Every skill in a pack that defines clusters must be assigned to a named
      cluster.  Skills without a ``cluster`` field are automatically matched
      to the best cluster using tag-based Jaccard similarity.

      Idempotent — skills that already have a valid ``cluster`` field are
      never reassigned.

H002: Clusters with fewer than 3 skills are flagged for potential merging.
      The rule computes Jaccard similarity between the small cluster's skill
      tags and each other cluster's aggregated tags, then recommends the
      best merge target.

      **Dry-run only** — this rule never modifies ``cap-pack.yaml``.
      Users must review the suggestions and act manually.

References:
    - ADR-6-1 (dual-phase fix design)
    - ADR-6-2 (.bak backup convention)
    - SPEC-6-1 (pack structure specification)
    - arxiv 2601.04748 (recommended cluster sizing 3–15)
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml

from skill_governance.adapter.cap_pack_adapter import _jaccard_similarity
from skill_governance.fixer.base import FixAction, FixResult, FixRule
from skill_governance.fixer.rules.f006_f007 import _dump_yaml, _load_cap_pack_yaml


# ── Constants ──────────────────────────────────────────────────────────────────

_H002_MIN_CLUSTER_SIZE = 3

# ── Tokenisation helper ────────────────────────────────────────────────────────


def _tokenize(text: str) -> set[str]:
    """Tokenise *text* into lowercase alphanumeric tokens."""
    return set(re.findall(r"[a-z0-9]+", text.lower()))


# ── Shared helper functions ────────────────────────────────────────────────────


def _collect_skill_tags(skill_entry: dict[str, Any]) -> set[str]:
    """Collect a normalised set of tags from a skill entry in ``cap-pack.yaml``.

    Sources (in order of importance):
      1. The explicit ``tags`` list on the skill entry.
      2. Tokens extracted from the ``name`` field.
      3. Tokens extracted from the ``description`` field.
    """
    tags: set[str] = set()

    raw_tags = skill_entry.get("tags", [])
    if isinstance(raw_tags, list):
        tags.update(str(t).lower() for t in raw_tags)

    name = skill_entry.get("name", "") or ""
    if name:
        tags.update(_tokenize(name))

    desc = skill_entry.get("description", "") or ""
    if desc:
        tags.update(_tokenize(desc))

    return tags


def _validate_cluster_ids(clusters: list[dict[str, Any]]) -> set[str]:
    """Return the set of valid, non-empty cluster IDs from the clusters list."""
    return {
        c["id"]
        for c in clusters
        if isinstance(c, dict) and isinstance(c.get("id"), str) and c["id"]
    }


def _build_cluster_tag_profiles(
    clusters: list[dict[str, Any]],
    skills_by_id: dict[str, dict[str, Any]],
) -> dict[str, set[str]]:
    """Build an aggregated tag profile for each cluster.

    The profile is the **union** of all tags extracted from the skills
    declared in ``clusters[].skills[]``.  If a cluster has no skills in
    its list its profile will be an empty set.
    """
    profiles: dict[str, set[str]] = {}

    for cluster in clusters:
        cid = cluster.get("id", "")
        if not cid:
            continue

        aggregated: set[str] = set()
        skill_ids = cluster.get("skills", [])
        if isinstance(skill_ids, list):
            for sid in skill_ids:
                skill = skills_by_id.get(sid)
                if skill:
                    aggregated.update(_collect_skill_tags(skill))

        profiles[cid] = aggregated

    return profiles


def _find_best_cluster(
    skill_tags: set[str],
    cluster_profiles: dict[str, set[str]],
) -> str | None:
    """Return the cluster ID whose profile best matches *skill_tags*.

    Uses ``_jaccard_similarity``.  Returns ``None`` when no cluster has
    a non-empty tag profile.
    """
    best_cid: str | None = None
    best_score: float = -1.0

    for cid, ctags in cluster_profiles.items():
        if not ctags:
            continue
        score = _jaccard_similarity(skill_tags, ctags)
        if score > best_score:
            best_score = score
            best_cid = cid

    return best_cid


def _get_cluster_name(clusters: list[dict[str, Any]], cid: str) -> str | None:
    """Look up the human-readable ``name`` of a cluster by its ID."""
    for c in clusters:
        if c.get("id") == cid:
            name = c.get("name")
            if isinstance(name, str) and name:
                return name
    return None


def _build_cluster_assignments(
    data: dict[str, Any],
) -> list[tuple[str, str]]:
    """Determine (skill_id, cluster_id) pairs for every unassigned skill.

    A skill is considered unassigned when its ``cluster`` field is missing,
    empty, or does not reference a valid cluster ID.

    Returns:
        A list of ``(skill_id, target_cluster_id)`` tuples.  Empty when
        every skill already has a valid cluster assignment, or when the
        pack does not define any clusters.
    """
    clusters = data.get("clusters", [])
    if not isinstance(clusters, list) or not clusters:
        return []

    valid_ids = _validate_cluster_ids(clusters)
    if not valid_ids:
        return []

    skills = data.get("skills", [])
    if not isinstance(skills, list):
        return []

    # Build a skill ID → entry lookup
    skills_by_id: dict[str, dict[str, Any]] = {
        s["id"]: s for s in skills if isinstance(s, dict) and s.get("id")
    }

    # Build cluster tag profiles from already-assigned skills
    cluster_profiles = _build_cluster_tag_profiles(clusters, skills_by_id)

    assignments: list[tuple[str, str]] = []

    for skill in skills:
        sid = skill.get("id", "")
        if not sid:
            continue

        # Already assigned to a valid cluster
        current = skill.get("cluster")
        if isinstance(current, str) and current in valid_ids:
            continue

        skill_tags = _collect_skill_tags(skill)
        best_cid = _find_best_cluster(skill_tags, cluster_profiles)

        if best_cid is None and cluster_profiles:
            # Fallback: pick the first cluster (no tag basis to decide)
            best_cid = next(iter(cluster_profiles))

        if best_cid is None:
            # No clusters with tags exist — skip
            continue

        assignments.append((sid, best_cid))

    return assignments


def _count_skills_per_cluster(data: dict[str, Any]) -> dict[str, int]:
    """Count skills per cluster using the cluster's declared skill list.

    Uses ``clusters[].skills[]`` as the authoritative source.  This
    method is used by H002 for cluster-size auditing.
    """
    counts: dict[str, int] = {}

    clusters = data.get("clusters", [])
    if isinstance(clusters, list):
        for cluster in clusters:
            cid = cluster.get("id", "")
            if not cid:
                continue
            skill_ids = cluster.get("skills", [])
            if isinstance(skill_ids, list):
                counts[cid] = len(skill_ids)

    return counts


# ═══════════════════════════════════════════════════════════════════════════════
# H001 — Cluster membership
# ═══════════════════════════════════════════════════════════════════════════════


class H001ClusterFixRule(FixRule):
    """Tree-based cluster membership — every skill must belong to a named cluster.

    When a pack defines ``clusters`` in its ``cap-pack.yaml``, every skill
    entry **must** have a ``cluster`` field pointing to one of those
    clusters.

    Skills missing this field are automatically assigned to the cluster
    with the most similar tag profile (using Jaccard similarity on tags,
    name tokens, and description tokens).

    Idempotent — skills that already have a valid ``cluster`` field are
    never reassigned.
    """

    rule_id = "H001"
    description = (
        "Tree-based cluster membership — every skill must belong to a named cluster"
    )
    severity = "warning"

    # ── idempotency guard ──────────────────────────────────────────────────────

    def _is_already_fixed(self, pack_path: str) -> bool:
        """Return ``True`` when every skill has a valid ``cluster`` field."""
        try:
            data, _, _ = _load_cap_pack_yaml(pack_path)
        except FileNotFoundError:
            return True  # nothing to fix

        clusters = data.get("clusters", [])
        if not isinstance(clusters, list) or not clusters:
            return True  # no clusters defined → nothing to assign

        valid_ids = _validate_cluster_ids(clusters)
        if not valid_ids:
            return True

        skills = data.get("skills", [])
        if not isinstance(skills, list):
            return True

        return all(
            isinstance(s.get("cluster"), str) and s["cluster"] in valid_ids
            for s in skills
        )

    # ── analyze (dry-run) ──────────────────────────────────────────────────────

    def analyze(self, pack_path: str, check_details: dict[str, Any]) -> FixResult:
        """Plan cluster assignments for unclustered skills.

        Args:
            pack_path:      Path to the cap-pack directory.
            check_details:  Details from the failed scan check.

        Returns:
            A ``FixResult`` with ``dry_run=True`` containing a ``FixAction``
            for each skill that needs a cluster assignment.
        """
        result = FixResult(rule_id=self.rule_id, dry_run=True)

        try:
            data, yaml_path, _ = _load_cap_pack_yaml(pack_path)
        except FileNotFoundError:
            result.errors.append(f"cap-pack.yaml not found in {pack_path}")
            return result

        assignments = _build_cluster_assignments(data)
        pack_name = yaml_path.parent.name

        for sid, cid in assignments:
            action = FixAction(
                rule_id=self.rule_id,
                action_type="modify",
                target_path=str(yaml_path),
                old_content=_dump_yaml(data),
                new_content="",  # filled in apply()
                description=(
                    f"Assign skill '{sid}' to cluster '{cid}' "
                    f"in pack '{pack_name}'"
                ),
            )
            result.actions.append(action)

        return result

    # ── apply ──────────────────────────────────────────────────────────────────

    def apply(self, pack_path: str, check_details: dict[str, Any]) -> FixResult:
        """Assign unclustered skills to their best-matching cluster.

        Idempotent — skills that already have a valid ``cluster`` field
        are not touched.

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

        assignments = _build_cluster_assignments(data)
        if not assignments:
            result.skipped += 1
            return result

        # Create .bak backup (ADR-6-2)
        self._backup(yaml_path)

        # Re-read to avoid stale data
        fresh_content = yaml_path.read_text(encoding="utf-8")
        data_updated = yaml.safe_load(fresh_content) or {}

        # Build lookup: skill_id → target cluster_id
        sid_to_cid = dict(assignments)

        # Apply cluster assignments
        skills = data_updated.get("skills", [])
        if isinstance(skills, list):
            for skill in skills:
                sid = skill.get("id", "")
                if sid in sid_to_cid:
                    skill["cluster"] = sid_to_cid[sid]

        new_yaml = _dump_yaml(data_updated)
        yaml_path.write_text(new_yaml, encoding="utf-8")

        pack_name = yaml_path.parent.name
        for sid, cid in assignments:
            action = FixAction(
                rule_id=self.rule_id,
                action_type="modify",
                target_path=str(yaml_path),
                old_content=fresh_content,
                new_content=new_yaml,
                description=(
                    f"Assigned skill '{sid}' to cluster '{cid}' "
                    f"in pack '{pack_name}'"
                ),
            )
            result.actions.append(action)
            result.applied += 1

        return result


# ═══════════════════════════════════════════════════════════════════════════════
# H002 — Cluster size
# ═══════════════════════════════════════════════════════════════════════════════


class H002ClusterSizeFixRule(FixRule):
    """Cluster size must be between 3 and 15 skills per cluster.

    Clusters with fewer than 3 skills are flagged.  The rule computes
    tag-based Jaccard similarity between the small cluster's aggregated
    skill tags and every other cluster's profile, then recommends the
    best merge target.

    .. caution::

        This rule is **dry-run only** — it never modifies
        ``cap-pack.yaml``.  Review the suggestions in the ``analyze()``
        output and merge clusters manually.
    """

    rule_id = "H002"
    description = (
        "Cluster size must be between 3 and 15 skills per cluster"
    )
    severity = "warning"

    # ── analyze (dry-run) ──────────────────────────────────────────────────────

    def analyze(self, pack_path: str, check_details: dict[str, Any]) -> FixResult:
        """Flag undersized clusters and suggest merge targets.

        Args:
            pack_path:      Path to the cap-pack directory.
            check_details:  Details from the failed scan check.

        Returns:
            A ``FixResult`` with ``dry_run=True`` containing one
            ``FixAction`` per undersized cluster with the merge
            recommendation in the description.
        """
        result = FixResult(rule_id=self.rule_id, dry_run=True)

        try:
            data, yaml_path, _ = _load_cap_pack_yaml(pack_path)
        except FileNotFoundError:
            result.errors.append(f"cap-pack.yaml not found in {pack_path}")
            return result

        suggestions = self._build_merge_suggestions(data, yaml_path)
        result.actions.extend(suggestions)

        return result

    # ── apply ──────────────────────────────────────────────────────────────────

    def apply(self, pack_path: str, check_details: dict[str, Any]) -> FixResult:
        """H002 is dry-run only — no files are modified.

        This method always returns with an error message explaining that
        the rule does not auto-apply.
        """
        result = FixResult(rule_id=self.rule_id, dry_run=False)
        result.errors.append(
            "H002 is a dry-run-only rule; it does not modify cap-pack.yaml. "
            "Review the analyze() output and merge undersized clusters "
            "manually."
        )
        return result

    # ── internal helpers ───────────────────────────────────────────────────────

    @staticmethod
    def _build_merge_suggestions(
        data: dict[str, Any],
        yaml_path: Path,
    ) -> list[FixAction]:
        """Build merge suggestions for clusters with fewer than 3 skills.

        For each undersized cluster:
        1. Collect its aggregated tag profile.
        2. Compute Jaccard similarity against every other cluster's profile.
        3. Recommend the best-scoring merge target.

        Returns:
            A list of ``FixAction`` objects (all informational —
            ``old_content`` and ``new_content`` are empty).
        """
        clusters = data.get("clusters", [])
        if not isinstance(clusters, list) or not clusters:
            return []

        skills = data.get("skills", [])
        if not isinstance(skills, list):
            return []

        skills_by_id: dict[str, dict[str, Any]] = {
            s["id"]: s for s in skills if isinstance(s, dict) and s.get("id")
        }

        # Count skills per cluster
        cluster_counts = _count_skills_per_cluster(data)

        # Build tag profiles for ALL clusters
        cluster_profiles = _build_cluster_tag_profiles(clusters, skills_by_id)

        actions: list[FixAction] = []
        pack_name = yaml_path.parent.name

        for cluster in clusters:
            cid = cluster.get("id", "")
            if not cid:
                continue

            count = cluster_counts.get(cid, 0)
            if count >= _H002_MIN_CLUSTER_SIZE:
                continue  # cluster is adequately sized

            cname = _get_cluster_name(clusters, cid) or cid

            # Find the best merge target by Jaccard similarity
            small_tags = cluster_profiles.get(cid, set())
            best_target: str | None = None
            best_score: float = -1.0

            for other_cid, other_tags in cluster_profiles.items():
                if other_cid == cid:
                    continue
                if not other_tags:
                    continue
                score = _jaccard_similarity(small_tags, other_tags)
                if score > best_score:
                    best_score = score
                    best_target = other_cid

            if best_target is not None:
                tname = _get_cluster_name(clusters, best_target) or best_target
                description = (
                    f"Cluster '{cid}' ({cname}) has only {count} skill(s) "
                    f"(minimum is {_H002_MIN_CLUSTER_SIZE}).  "
                    f"Suggest merging into '{best_target}' ({tname}) "
                    f"– Jaccard similarity: {best_score:.2f} "
                    f"– in pack '{pack_name}'"
                )
            else:
                description = (
                    f"Cluster '{cid}' ({cname}) has only {count} skill(s) "
                    f"(minimum is {_H002_MIN_CLUSTER_SIZE}).  "
                    f"No suitable merge target found (no tag overlap "
                    f"with other clusters) in pack '{pack_name}'"
                )

            actions.append(
                FixAction(
                    rule_id="H002",
                    action_type="modify",
                    target_path=str(yaml_path),
                    old_content="",
                    new_content="",
                    description=description,
                )
            )

        return actions
