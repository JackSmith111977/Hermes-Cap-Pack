"""FixRule abstract base class with FixAction / FixResult data models.

Implements ADR-6-1 dual-phase design:
  - analyze()  → generate a plan (dry-run capable)
  - apply()    → execute the plan (with .bak backup per ADR-6-2)

Every concrete FixRule subclass must set ``rule_id``, ``description``,
and ``severity`` as class-level attributes.
"""

from __future__ import annotations

import difflib
import shutil
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


# ─── Data models ───────────────────────────────────────────────────────────────


@dataclass
class FixAction:
    """A single atomic fix operation.

    Attributes:
        rule_id:       ID of the rule that produced this action.
        action_type:   One of ``create``, ``modify``, ``delete``.
        target_path:   Absolute path to the file being acted upon.
        old_content:   Original content (empty for ``create``).
        new_content:   Replacement content (empty for ``delete``).
        description:   Human-readable summary of this action.
    """

    rule_id: str
    action_type: str  # create | modify | delete
    target_path: str
    old_content: str = ""
    new_content: str = ""
    description: str = ""


@dataclass
class FixResult:
    """Aggregated result of one FixRule execution (analyze or apply).

    Attributes:
        rule_id:   ID of the rule that produced this result.
        dry_run:   Whether the result is from a dry-run (analyze) phase.
        applied:   Number of actions successfully applied.
        skipped:   Number of actions skipped (e.g. already fixed).
        errors:    List of error messages encountered during apply.
        actions:   The list of FixAction objects that were planned/applied.
    """

    rule_id: str
    dry_run: bool = False
    applied: int = 0
    skipped: int = 0
    errors: list[str] = field(default_factory=list)
    actions: list[FixAction] = field(default_factory=list)

    # ── computed properties ──────────────────────────────────────────────

    @property
    def total(self) -> int:
        """Total number of actions considered."""
        return self.applied + self.skipped + len(self.errors)

    @property
    def success(self) -> bool:
        """True when there are zero errors."""
        return len(self.errors) == 0

    @property
    def diff(self) -> str:
        """Generate a unified-diff string from all actions in this result.

        Each action is rendered as a ``diff --git``-style section so the
        output can be reviewed or piped into ``patch``.
        """
        lines: list[str] = []
        for action in self.actions:
            if action.action_type == "create":
                lines.append(f"--- /dev/null")
                lines.append(f"+++ {action.target_path}")
                for i, line in enumerate(action.new_content.splitlines(keepends=True), 1):
                    lines.append(f"+{line.rstrip()}")
                lines.append("")
            elif action.action_type == "delete":
                lines.append(f"--- {action.target_path}")
                lines.append(f"+++ /dev/null")
                for i, line in enumerate(action.old_content.splitlines(keepends=True), 1):
                    lines.append(f"-{line.rstrip()}")
                lines.append("")
            elif action.action_type == "modify":
                old_lines = action.old_content.splitlines(keepends=True)
                new_lines = action.new_content.splitlines(keepends=True)
                diff_lines = list(
                    difflib.unified_diff(
                        old_lines,
                        new_lines,
                        fromfile=action.target_path,
                        tofile=action.target_path,
                        lineterm="",
                    )
                )
                lines.extend(diff_lines)
                lines.append("")
        return "\n".join(lines)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a JSON-compatible dict."""
        return {
            "rule_id": self.rule_id,
            "dry_run": self.dry_run,
            "applied": self.applied,
            "skipped": self.skipped,
            "errors": list(self.errors),
            "actions": [
                {
                    "rule_id": a.rule_id,
                    "action_type": a.action_type,
                    "target_path": a.target_path,
                    "description": a.description,
                }
                for a in self.actions
            ],
        }


# ─── Abstract base class ───────────────────────────────────────────────────────


class FixRule(ABC):
    """Abstract base class for all fix rules.

    Subclasses **must** define:

    * ``rule_id``     – unique identifier (e.g. ``"FIX-L0-001"``)
    * ``description`` – human-readable description
    * ``severity``    – ``"blocking"`` | ``"warning"`` | ``"info"``

    Lifecycle
    ---------
    1. **analyze** — inspect the pack and return a ``FixResult`` with
       planned actions (dry-run).  No files are changed.
    2. **apply**   — execute the planned modifications and return a
       ``FixResult`` with the actual outcome.

    Backup convention (ADR-6-2)
    ---------------------------
    Before modifying a file the ``_backup()`` helper creates a ``.bak``
    copy alongside the original via ``shutil.copy2``.
    """

    # ── class-level metadata (override in subclasses) ────────────────────
    rule_id: str = ""
    description: str = ""
    severity: str = "warning"

    # ── abstract interface ───────────────────────────────────────────────

    @abstractmethod
    def analyze(self, pack_path: str, check_details: dict[str, Any]) -> FixResult:
        """Inspect the pack and produce a plan of fix actions.

        This is the **dry-run** phase — no files are modified.

        Args:
            pack_path:      Path to the cap-pack directory.
            check_details:  Details from the failed scan check (e.g.
                            ``CheckResult.details``) that triggered this fix.

        Returns:
            A ``FixResult`` with ``dry_run=True`` and a list of planned
            ``FixAction`` objects.
        """
        ...

    @abstractmethod
    def apply(self, pack_path: str, check_details: dict[str, Any]) -> FixResult:
        """Execute the fix plan and modify files.

        This is the **apply** phase — files may be created, modified, or
        deleted.  The ``_backup()`` helper should be called before any
        in-place modification.

        Args:
            pack_path:      Path to the cap-pack directory.
            check_details:  Details from the failed scan check.

        Returns:
            A ``FixResult`` with ``dry_run=False`` and the actual outcome.
        """
        ...

    # ── helpers ──────────────────────────────────────────────────────────

    def _backup(self, path: str | Path) -> str:
        """Create a ``.bak`` copy of *path* using ``shutil.copy2``.

        The backup is placed next to the original file with ``.bak``
        appended to the name.

        Returns:
            The absolute path to the backup file.

        Raises:
            FileNotFoundError: If *path* does not exist.
        """
        src = Path(path).resolve()
        if not src.exists():
            raise FileNotFoundError(f"Cannot back up non-existent file: {src}")
        bak = src.with_name(src.name + ".bak")
        shutil.copy2(str(src), str(bak))
        return str(bak)

    def _is_already_fixed(self, pack_path: str) -> bool:
        """Check whether the issue this rule fixes is already resolved.

        Override in subclasses when the rule can cheaply verify that its
        fix has already been applied (idempotency guard).

        Args:
            pack_path: Path to the cap-pack directory.

        Returns:
            ``True`` if the pack already satisfies this rule; ``False``
            if the fix still needs to be applied.
        """
        # Default: assume not fixed so the rule runs every time.
        return False
