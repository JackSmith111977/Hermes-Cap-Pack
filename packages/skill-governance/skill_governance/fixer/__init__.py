"""Fixer package — FixRule abstract layer, dispatcher, and reporter.

Provides:
  - ``FixRule``        — abstract base class for fix rules.
  - ``FixAction``      — data model for a single atomic fix operation.
  - ``FixResult``      — aggregated result of a fix rule execution.
  - ``FixDispatcher``  — routes failed scan checks to registered fix rules.
  - ``FixReport``      — aggregated fix report data model (JSON-serializable).
  - ``FixReporter``    — terminal (Rich) and JSON output for fix results.
  - ``ensure_backups`` — create ``.bak`` copies before applying fixes.

See ADR-6-1 (dual-phase design), ADR-6-2 (.bak backup mode),
and STORY-6-0-3 (report format).
"""

from skill_governance.fixer.base import FixAction, FixResult, FixRule
from skill_governance.fixer.dispatcher import FixDispatcher
from skill_governance.fixer.reporter import FixReport, FixReporter, ensure_backups

__all__ = [
    "FixAction",
    "FixResult",
    "FixRule",
    "FixDispatcher",
    "FixReport",
    "FixReporter",
    "ensure_backups",
]
