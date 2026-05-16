"""SRA quality injector — STORY-5-2-2.

Injects SQS (Skill Quality Score) scores into SRA recommendation weights.
Reads from the local SQS database (~/.hermes/data/skill-quality.db), detects
workflow declarations from skill frontmatter, and produces a weight mapping
compatible with SRA's weight JSON format.
"""

from __future__ import annotations

import json
import os
import sqlite3
from pathlib import Path
from typing import Any, Optional

import yaml


# ─── Constants ────────────────────────────────────────────────────────────────

DEFAULT_SQS_DB = os.path.expanduser("~/.hermes/data/skill-quality.db")

# Weight mapping: SQS score ranges to base weights
SQS_WEIGHT_MAP: list[tuple[float, float]] = [
    (80.0, 1.0),  # SQS >= 80 → fully weighted
    (60.0, 0.85),  # SQS >= 60 → moderately weighted
    (0.0, 0.5),  # SQS < 60 → low weight
]

WORKFLOW_BONUS: float = 1.2  # ×1.2 multiplier if skill has workflow declarations


# ─── Database helpers ─────────────────────────────────────────────────────────


def _read_sqs_from_db(db_path: str) -> dict[str, float]:
    """Read SQS scores from the local SQLite database.

    Expected schema (created by the Hermes SQS engine):
      CREATE TABLE skill_quality (
          skill_name TEXT PRIMARY KEY,
          sqs_total REAL,
          ...
      );

    Args:
        db_path: Path to the SQLite database file.

    Returns:
        A mapping of skill_name → sqs_total score.
    """
    scores: dict[str, float] = {}
    db = Path(db_path)
    if not db.exists():
        return scores

    try:
        conn = sqlite3.connect(str(db))
        cursor = conn.cursor()

        # Explore the available tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall()]

        # Try common table names
        table_candidates = ["skill_quality", "sqs_scores", "skills", "quality_scores"]
        target_table: str | None = None
        for t in table_candidates:
            if t in tables:
                target_table = t
                break

        if target_table is None and tables:
            # Use the first available table
            target_table = tables[0]

        if target_table:
            # Determine column names
            cursor.execute(f"PRAGMA table_info({target_table});")
            columns = [row[1] for row in cursor.fetchall()]

            name_col = None
            score_col = None
            for col in columns:
                lower = col.lower()
                if lower in ("skill_name", "name", "skill", "id"):
                    name_col = col
                if lower in ("sqs_total", "sqs", "score", "total", "quality_score"):
                    score_col = col

            if name_col and score_col:
                cursor.execute(f"SELECT {name_col}, {score_col} FROM {target_table};")
                for row in cursor.fetchall():
                    name = str(row[0])
                    try:
                        score = float(row[1]) if row[1] is not None else 0.0
                    except (ValueError, TypeError):
                        score = 0.0
                    scores[name] = score

        conn.close()
    except (sqlite3.Error, Exception):
        pass

    return scores


def _detect_workflow_declarations(skill_name: str, skill_path: Optional[str] = None) -> bool:
    """Detect if a skill has workflow declarations in its SKILL.md frontmatter.

    Workflow declarations can appear as:
      - ``workflow`` key in frontmatter
      - ``workflows`` key in frontmatter
      - References to ``steps:`` or ``triggers:`` with workflow-like structure

    Args:
        skill_name: Name of the skill (used to find the path if not provided).
        skill_path: Optional explicit path to the skill directory.

    Returns:
        True if the skill has workflow-related declarations.
    """
    # If no path given, try common locations
    candidates: list[Path] = []
    if skill_path:
        candidates.append(Path(skill_path) / "SKILL.md")
    # Also check common pack skill directories
    base_dirs = [
        Path(os.path.expanduser("~/.hermes/skills")),
        Path.cwd(),
    ]
    for base in base_dirs:
        candidates.append(base / skill_name / "SKILL.md")

    for skill_md in candidates:
        if skill_md.exists():
            try:
                content = skill_md.read_text(encoding="utf-8")
                frontmatter = _parse_frontmatter(content)
                # Check for workflow declarations in frontmatter
                if "workflow" in frontmatter or "workflows" in frontmatter:
                    return True
                # Check if triggers match workflow patterns
                triggers = frontmatter.get("triggers", [])
                if isinstance(triggers, list):
                    wf_keywords = {"workflow", "orchestrate", "pipeline", "step", "dag", "sequential", "parallel"}
                    for t in triggers:
                        if isinstance(t, str) and any(kw in t.lower() for kw in wf_keywords):
                            return True
                # Check for steps key
                if "steps" in frontmatter:
                    return True
            except Exception:
                continue

    return False


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


def _get_base_weight(sqs_score: float) -> float:
    """Map an SQS score to a base weight using the configured thresholds.

    Args:
        sqs_score: The SQS total score (0-100).

    Returns:
        A float weight between 0.5 and 1.0.
    """
    for threshold, weight in sorted(SQS_WEIGHT_MAP, reverse=True):
        if sqs_score >= threshold:
            return weight
    return 0.5


# ─── Main injection function ──────────────────────────────────────────────────


def inject_quality_to_sra(sqs_scores: dict[str, float] | None = None) -> dict[str, float]:
    """Generate SQA-weighted skill recommendation weights.

    Reads SQS scores (from DB or provided dict), detects workflow declarations,
    and returns a weight mapping compatible with SRA's weight JSON format.

    The weight mapping:
      - SQS >= 80  → base weight 1.0
      - SQS >= 60  → base weight 0.85
      - SQS < 60   → base weight 0.5
      - Workflow bonus: ×1.2 if the skill has workflow declarations

    Args:
        sqs_scores: Optional dict of skill_name → sqs_total. If None, scores
                    are read from the local SQS database at
                    ``~/.hermes/data/skill-quality.db``.

    Returns:
        A dict mapping skill_name → final_weight, where final_weight is the
        product of the base weight and any applicable workflow bonus.
    """
    # Load SQS scores if not provided
    if sqs_scores is None:
        sqs_scores = _read_sqs_from_db(DEFAULT_SQS_DB)

    if not sqs_scores:
        return {}

    weights: dict[str, float] = {}

    for skill_name, sqs_score in sqs_scores.items():
        base_weight = _get_base_weight(sqs_score)

        # Detect workflow declarations
        has_workflow = _detect_workflow_declarations(skill_name)

        final_weight = base_weight
        if has_workflow:
            final_weight = round(base_weight * WORKFLOW_BONUS, 4)

        weights[skill_name] = final_weight

    return weights


# ─── Utility ──────────────────────────────────────────────────────────────────


def inject_quality_to_sra_from_db(db_path: str = DEFAULT_SQS_DB) -> dict[str, float]:
    """Convenience wrapper that reads from a specific DB path."""
    scores = _read_sqs_from_db(db_path)
    return inject_quality_to_sra(sqs_scores=scores)


def save_weights_to_json(weights: dict[str, float], output_path: str | os.PathLike[str]) -> None:
    """Save weight mapping to a JSON file compatible with SRA format.

    Args:
        weights: The weight dict from inject_quality_to_sra().
        output_path: Path to write the JSON file.
    """
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(weights, f, indent=2, ensure_ascii=False)
