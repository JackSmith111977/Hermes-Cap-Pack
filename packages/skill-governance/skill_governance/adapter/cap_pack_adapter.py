"""Cap-pack auto-adaptation engine — STORY-5-2-3.

An adapter that automatically maps skills to cap-pack packages by:
  - Scanning a skill for compliance
  - Suggesting the best-matching cap-pack package using tag Jaccard similarity
  - Dry-running proposed changes
  - Applying changes (with user confirmation)

This is a pure algorithmic matcher — no LLM calls.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

import yaml

from skill_governance.models.result import CheckResult, ScanReport, ScanResult
from skill_governance.scanner.base import RuleLoader
from skill_governance.scanner.compliance import ComplianceChecker


# ─── Data types ───────────────────────────────────────────────────────────────


@dataclass
class PackManifest:
    """Parsed cap-pack.yaml manifest from a pack directory."""

    name: str
    path: str
    description: str
    classification: str
    tags: list[str] = field(default_factory=list)
    domain: str = ""
    category: str = ""
    skills: list[dict[str, Any]] = field(default_factory=list)
    triggers: list[str] = field(default_factory=list)
    version: str = ""

    @classmethod
    def from_file(cls, yaml_path: str | os.PathLike[str]) -> PackManifest:
        """Parse a cap-pack.yaml file into a PackManifest."""
        path = Path(yaml_path)
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        # Collect tags from skills and pack-level
        tags: list[str] = []
        skill_tags: list[str] = []
        for sk in data.get("skills", []):
            st = sk.get("tags", [])
            if isinstance(st, list):
                skill_tags.extend(st)
        # Pack-level tags may come from category/domain/triggers
        tags.extend(data.get("triggers", []))
        if data.get("domain"):
            tags.append(data["domain"])
        if data.get("category"):
            tags.append(data["category"])
        tags.extend(skill_tags)

        return cls(
            name=data.get("name", path.parent.name),
            path=str(path.parent.resolve()),
            description=data.get("description", ""),
            classification=data.get("classification", ""),
            tags=list(set(t.lower() for t in tags if isinstance(t, str))),
            domain=data.get("domain", ""),
            category=data.get("category", ""),
            skills=data.get("skills", []),
            triggers=data.get("triggers", []),
            version=str(data.get("version", "")),
        )


@dataclass
class PackSuggestion:
    """A single pack suggestion with relevance score."""

    pack_name: str
    pack_path: str
    score: float
    reasons: list[str] = field(default_factory=list)


@dataclass
class AdaptationResult:
    """Result of a scan/suggest/apply operation."""

    skill_path: str
    compliance_ok: bool
    suggestions: list[PackSuggestion] = field(default_factory=list)
    applied: bool = False
    message: str = ""


# ─── Jaccard similarity ───────────────────────────────────────────────────────


def _jaccard_similarity(set_a: set[str], set_b: set[str]) -> float:
    """Compute Jaccard similarity between two sets of strings.

    Returns a float in [0.0, 1.0], where 1.0 means identical sets.
    """
    if not set_a or not set_b:
        return 0.0
    intersection = set_a & set_b
    union = set_a | set_b
    return len(intersection) / len(union)


def _tokenize(text: str) -> set[str]:
    """Tokenize a text string into a set of lowercase alphanumeric tokens."""
    import re

    return set(re.findall(r"[a-z0-9]+", text.lower()))


def _extract_skill_tags_and_desc(skill_path: str) -> tuple[set[str], str, dict[str, Any]]:
    """Extract tags, description, and frontmatter from a skill directory.

    Args:
        skill_path: Path to the skill directory (containing SKILL.md).

    Returns:
        A tuple of (tags_set, description, frontmatter_dict).
    """
    sp = Path(skill_path).resolve()
    skill_md = sp / "SKILL.md"

    tags: set[str] = set()
    description = ""
    frontmatter: dict[str, Any] = {}

    if skill_md.exists():
        try:
            content = skill_md.read_text(encoding="utf-8")
            frontmatter = _parse_frontmatter(content)
            skill_tags = frontmatter.get("tags", [])
            if isinstance(skill_tags, list):
                tags = set(str(t).lower() for t in skill_tags)
            description = frontmatter.get("description", "") or ""
            # Also add tokens from skill name and classification
            name = frontmatter.get("name", sp.name)
            tags.add(name.lower())
            classification = frontmatter.get("classification", "")
            if classification:
                tags.add(classification.lower())
        except Exception:
            tags.add(sp.name.lower())

    return tags, description, frontmatter


def _parse_frontmatter(content: str) -> dict[str, Any]:
    """Parse YAML frontmatter from markdown content."""
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
        if isinstance(fm, dict):
            return fm
        return {}
    except Exception:
        return {}


# ─── Package index builder ────────────────────────────────────────────────────


def _build_pack_index(packs_root: str) -> list[PackManifest]:
    """Scan packs/ directory and build an index of all cap-pack.yaml manifests.

    Args:
        packs_root: Path to the root directory containing pack subdirectories.

    Returns:
        A list of PackManifest objects for all discovered packs.
    """
    packs_dir = Path(packs_root)
    if not packs_dir.exists():
        return []

    manifests: list[PackManifest] = []
    for pack_dir in sorted(packs_dir.iterdir()):
        if not pack_dir.is_dir():
            continue
        cap_pack_yaml = pack_dir / "cap-pack.yaml"
        if cap_pack_yaml.exists():
            try:
                manifest = PackManifest.from_file(str(cap_pack_yaml))
                manifests.append(manifest)
            except Exception:
                continue

    return manifests


def _score_pack_for_skill(
    manifest: PackManifest,
    skill_tags: set[str],
    skill_desc: str,
    skill_frontmatter: dict[str, Any],
) -> tuple[float, list[str]]:
    """Score a pack's relevance to a skill using multi-factor matching.

    Factors:
      - Tag Jaccard similarity (weight: 0.5)
      - Description keyword overlap (weight: 0.3)
      - Classification match (weight: 0.1)
      - Domain/category match (weight: 0.1)

    Args:
        manifest: The pack manifest.
        skill_tags: Set of tags from the skill.
        skill_desc: Description text from the skill.
        skill_frontmatter: Full frontmatter dict from the skill.

    Returns:
        A tuple of (total_score, list_of_reason_strings).
    """
    reasons: list[str] = []

    # 1. Tag Jaccard similarity (highest weight)
    pack_tag_set = manifest.tags
    tag_jaccard = _jaccard_similarity(skill_tags, set(pack_tag_set))
    tag_score = tag_jaccard * 0.5
    if tag_jaccard > 0.0:
        common_tags = skill_tags & set(pack_tag_set)
        reasons.append(
            f"Tag match (Jaccard={tag_jaccard:.2f}): {sorted(common_tags)[:5]}"
        )

    # 2. Description keyword overlap
    desc_tokens = _tokenize(skill_desc)
    pack_tokens: set[str] = set()
    if manifest.description:
        pack_tokens.update(_tokenize(manifest.description))
    # Also add pack name tokens
    pack_tokens.update(_tokenize(manifest.name))
    # Add trigger tokens
    for t in manifest.triggers:
        pack_tokens.update(_tokenize(str(t)))

    desc_overlap = _jaccard_similarity(desc_tokens, pack_tokens)
    desc_score = desc_overlap * 0.3
    if desc_overlap > 0.0:
        reasons.append(
            f"Description overlap (Jaccard={desc_overlap:.2f}) with pack '{manifest.name}'"
        )

    # 3. Classification match
    skill_classification = skill_frontmatter.get("classification", "")
    pack_classification = manifest.classification
    class_score = 0.0
    if skill_classification and pack_classification:
        if skill_classification == pack_classification:
            class_score = 0.1
            reasons.append(f"Classification match: {skill_classification}")
        elif skill_classification in pack_classification or pack_classification in skill_classification:
            class_score = 0.05
            reasons.append(f"Partial classification overlap: {skill_classification} ↔ {pack_classification}")

    # 4. Domain/category match
    skill_domain = skill_frontmatter.get("domain", "")
    pack_domain = manifest.domain or manifest.category
    domain_score = 0.0
    if skill_domain and pack_domain:
        if skill_domain == pack_domain:
            domain_score = 0.1
            reasons.append(f"Domain match: {skill_domain}")
        elif skill_domain in pack_domain or pack_domain in skill_domain:
            domain_score = 0.05
            reasons.append(f"Partial domain overlap: {skill_domain} ↔ {pack_domain}")

    total = round(tag_score + desc_score + class_score + domain_score, 4)
    return total, reasons


# ─── Main Adapter ─────────────────────────────────────────────────────────────


class CapPackAdapter:
    """Adapter for automatically mapping skills to cap-pack packages.

    Provides scan, suggest, dry_run, and apply operations for integrating
    a skill into the best-matching cap-pack package.
    """

    def __init__(self, packs_root: str | None = None) -> None:
        """Initialize the adapter.

        Args:
            packs_root: Path to the packs/ directory. If None, auto-detected
                        relative to the project root.
        """
        if packs_root:
            self.packs_root = Path(packs_root).resolve()
        else:
            # Auto-detect: look relative to cwd, package root, or home
            candidates = [
                Path.cwd() / "packs",
                Path.cwd().parent / "packs" if Path.cwd().name != "packs" else Path.cwd(),
                Path.home() / "projects" / "hermes-cap-pack" / "packs",
                Path(__file__).resolve().parent.parent.parent.parent.parent / "packs",
            ]
            resolved: Path | None = None
            for c in candidates:
                if c.exists():
                    resolved = c
                    break
            self.packs_root = resolved or (Path.cwd() / "packs")

        self._pack_index: list[PackManifest] = []
        self._refresh_index()

    def _refresh_index(self) -> None:
        """Rebuild the pack index from the packs directory."""
        self._pack_index = _build_pack_index(str(self.packs_root))

    # ── scan ─────────────────────────────────────────────────────────────

    def scan(self, path: str) -> AdaptationResult:
        """Run a compliance check on a skill path.

        Checks L0 (Compatibility) + L1 (Foundation) rules against the skill.

        Args:
            path: Path to the skill directory.

        Returns:
            An AdaptationResult with compliance_ok set based on L0+L1 pass/fail.
        """
        sp = Path(path).resolve()
        if not sp.exists():
            return AdaptationResult(
                skill_path=path,
                compliance_ok=False,
                message=f"Skill path does not exist: {path}",
            )

        skill_md = sp / "SKILL.md"
        if not skill_md.exists():
            return AdaptationResult(
                skill_path=path,
                compliance_ok=False,
                message=f"SKILL.md not found in {path}",
            )

        # Build skill data
        skill_data = self._collect_skill_data(str(sp))
        skills = [skill_data]

        # Run L0 and L1 checks
        failures: list[str] = []
        for layer_id in ("L0", "L1"):
            checker = ComplianceChecker(layer_id=layer_id)
            try:
                checks = checker.scan({"skills": skills})
                for c in checks:
                    if not c.passed and c.severity == "blocking":
                        failures.append(f"[{layer_id}/{c.rule_id}] {c.description}")
            except Exception as exc:
                failures.append(f"[{layer_id}] Scan error: {exc}")

        ok = len(failures) == 0
        msg = "All compliance checks passed." if ok else f"Blocking failures: {'; '.join(failures)}"

        return AdaptationResult(
            skill_path=str(sp),
            compliance_ok=ok,
            message=msg,
        )

    @staticmethod
    def _collect_skill_data(skill_path: str) -> dict[str, Any]:
        """Collect skill metadata for scanning."""
        sp = Path(skill_path).resolve()
        skill_md = sp / "SKILL.md"
        data: dict[str, Any] = {
            "id": sp.name,
            "name": sp.name,
            "path": str(sp),
            "version": "",
            "classification": "",
            "tags": [],
            "triggers": [],
            "sqs_total": None,
            "compatibility": {},
        }
        if skill_md.exists():
            try:
                content = skill_md.read_text(encoding="utf-8")
                fm = _parse_frontmatter(content)
                data["name"] = fm.get("name", sp.name)
                data["description"] = fm.get("description", "")
                data["version"] = fm.get("version", "")
                data["classification"] = fm.get("classification", "")
                data["tags"] = fm.get("tags", [])
                data["triggers"] = fm.get("triggers", [])
                data["compatibility"] = fm.get("compatibility", {})
                sqs = fm.get("sqs", {})
                data["sqs_total"] = (
                    sqs.get("total") if isinstance(sqs, dict)
                    else sqs if isinstance(sqs, (int, float))
                    else fm.get("sqs_total")
                )
            except Exception:
                pass
        return data

    # ── suggest ──────────────────────────────────────────────────────────

    def suggest(self, path: str, top_n: int = 5) -> AdaptationResult:
        """Infer the best-matching cap-pack package for a skill.

        Scores each pack in the index using:
          1. Tag Jaccard similarity (weight 0.5)
          2. Description keyword overlap (weight 0.3)
          3. Classification match (weight 0.1)
          4. Domain/category match (weight 0.1)

        Args:
            path: Path to the skill directory.
            top_n: Number of top suggestions to return.

        Returns:
            An AdaptationResult with suggestions sorted by score descending.
        """
        sp = Path(path).resolve()
        if not sp.exists():
            return AdaptationResult(
                skill_path=path,
                compliance_ok=False,
                message=f"Skill path does not exist: {path}",
            )

        # Extract skill metadata
        skill_tags, skill_desc, skill_fm = _extract_skill_tags_and_desc(str(sp))

        if not self._pack_index:
            self._refresh_index()

        # Score each pack
        scored: list[tuple[float, PackManifest, list[str]]] = []
        for manifest in self._pack_index:
            score, reasons = _score_pack_for_skill(
                manifest, skill_tags, skill_desc, skill_fm
            )
            scored.append((score, manifest, reasons))

        # Sort by score descending
        scored.sort(key=lambda x: x[0], reverse=True)

        suggestions: list[PackSuggestion] = []
        for score, manifest, reasons in scored[:top_n]:
            if score > 0.0:
                suggestions.append(
                    PackSuggestion(
                        pack_name=manifest.name,
                        pack_path=manifest.path,
                        score=score,
                        reasons=reasons,
                    )
                )

        msg = (
            f"Found {len(suggestions)} relevant pack(s) for skill '{sp.name}'."
            if suggestions
            else f"No matching pack found for skill '{sp.name}'."
        )

        return AdaptationResult(
            skill_path=str(sp),
            compliance_ok=True,
            suggestions=suggestions,
            message=msg,
        )

    # ── dry_run ──────────────────────────────────────────────────────────

    def dry_run(self, path: str) -> AdaptationResult:
        """Print proposed changes without modifying any files.

        Runs scan + suggest and returns the result with a human-readable
        message describing what apply() would do.

        Args:
            path: Path to the skill directory.

        Returns:
            An AdaptationResult with compliance info and suggestions.
        """
        # Run scan first
        scan_result = self.scan(path)
        if not scan_result.compliance_ok:
            return scan_result

        # Run suggestion
        suggest_result = self.suggest(path)

        if not suggest_result.suggestions:
            suggest_result.message = (
                f"[DRY RUN] No suitable pack found for skill at '{path}'. "
                "No changes would be made."
            )
            return suggest_result

        top = suggest_result.suggestions[0]
        suggest_result.message = (
            f"[DRY RUN] Would add skill to pack '{top.pack_name}' "
            f"(score: {top.score:.2f}). "
            f"Reasons: {'; '.join(top.reasons)}. "
            "Use apply() to execute."
        )
        return suggest_result

    # ── apply ────────────────────────────────────────────────────────────

    def apply(self, path: str, confirm: bool = True) -> AdaptationResult:
        """Add a skill entry to the best-matching cap-pack.yaml.

        Requires user confirmation (unless confirm=False).

        Args:
            path: Path to the skill directory.
            confirm: If True (default), prompts the user for confirmation
                     before modifying the file. Set to False for automated use.

        Returns:
            An AdaptationResult indicating whether the change was applied.
        """
        sp = Path(path).resolve()
        skill_name = sp.name

        # Check compliance
        scan_result = self.scan(path)
        if not scan_result.compliance_ok:
            return AdaptationResult(
                skill_path=str(sp),
                compliance_ok=False,
                applied=False,
                message=f"Cannot apply: skill fails compliance checks. {scan_result.message}",
            )

        # Find best pack
        suggest_result = self.suggest(path)
        if not suggest_result.suggestions:
            return AdaptationResult(
                skill_path=str(sp),
                compliance_ok=True,
                applied=False,
                message=f"No suitable pack found for skill '{skill_name}'.",
            )

        top = suggest_result.suggestions[0]
        pack_yaml_path = Path(top.pack_path) / "cap-pack.yaml"

        if not pack_yaml_path.exists():
            return AdaptationResult(
                skill_path=str(sp),
                compliance_ok=True,
                applied=False,
                message=f"cap-pack.yaml not found at {pack_yaml_path}",
            )

        # Read existing content
        with open(pack_yaml_path, "r", encoding="utf-8") as f:
            pack_data = yaml.safe_load(f)

        if not isinstance(pack_data, dict):
            return AdaptationResult(
                skill_path=str(sp),
                compliance_ok=True,
                applied=False,
                message=f"Invalid cap-pack.yaml format at {pack_yaml_path}",
            )

        # Check if skill already exists
        existing_ids = {s.get("id", "") for s in pack_data.get("skills", [])}
        existing_names = {s.get("name", "") for s in pack_data.get("skills", [])}
        if skill_name in existing_ids or skill_name in existing_names:
            return AdaptationResult(
                skill_path=str(sp),
                compliance_ok=True,
                applied=False,
                message=f"Skill '{skill_name}' already exists in pack '{top.pack_name}'. No changes made.",
            )

        # Build new skill entry from SKILL.md frontmatter
        _, _, skill_fm = _extract_skill_tags_and_desc(str(sp))
        skill_md_path = sp / "SKILL.md"
        relative_path = None
        if skill_md_path.exists():
            try:
                relative_path = str(skill_md_path.relative_to(Path(top.pack_path)))
            except ValueError:
                relative_path = str(skill_md_path)

        new_entry: dict[str, Any] = {
            "id": skill_name,
            "name": skill_fm.get("name", skill_name),
            "description": skill_fm.get("description", ""),
            "version": skill_fm.get("version", "1.0.0"),
            "tags": skill_fm.get("tags", []),
        }
        if relative_path:
            new_entry["path"] = relative_path

        # User confirmation
        if confirm:
            print(f"\nProposed changes to: {pack_yaml_path}")
            print(f"  Adding skill: {skill_name}")
            print(f"  Pack: {top.pack_name} (score: {top.score:.2f})")
            print(f"  New entry: {json.dumps(new_entry, indent=2, ensure_ascii=False)}")
            try:
                response = input("\nApply these changes? [y/N]: ").strip().lower()
            except (EOFError, KeyboardInterrupt):
                response = "n"
            if response != "y":
                return AdaptationResult(
                    skill_path=str(sp),
                    compliance_ok=True,
                    applied=False,
                    message="User cancelled the operation.",
                )

        # Add the new skill entry
        pack_data.setdefault("skills", []).append(new_entry)

        # Write updated cap-pack.yaml
        with open(pack_yaml_path, "w", encoding="utf-8") as f:
            yaml.dump(pack_data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

        return AdaptationResult(
            skill_path=str(sp),
            compliance_ok=True,
            applied=True,
            message=(
                f"Successfully added skill '{skill_name}' to pack "
                f"'{top.pack_name}' (score: {top.score:.2f})."
            ),
        )
