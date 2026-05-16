"""Fix reporter — terminal and JSON output for fix results (STORY-6-0-3).

Provides:
  - ensure_backups:  create .bak copies before apply
  - FixReport:       aggregated report data model (JSON-serializable)
  - FixReporter:     generates terminal (Rich) and JSON output

Usage::

    from skill_governance.fixer import FixReport, FixReporter, ensure_backups

    # Backup before apply
    ensure_backups(results, console)

    # Build report
    report = FixReport.from_results(results, pack_path, dry_run=False)

    # Terminal output
    FixReporter().print_report(report, results)

    # JSON export
    FixReporter().generate_json(report, "fix-report.json")
"""

from __future__ import annotations

import json
import shutil
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax

from skill_governance.fixer.base import FixResult


# ─── Backup helpers (ADR-6-2 / STORY-6-0-3) ────────────────────────────────


def ensure_backups(
    results: list[FixResult], console: Optional[Console] = None
) -> None:
    """Create ``.bak`` copies for all files referenced in fix results.

    Iterates through all :class:`FixAction` objects across the given
    results and creates a ``.bak`` copy of every non-create action's
    *target_path* using ``shutil.copy2``.  Duplicate paths are skipped so
    each file is backed up only once.

    Args:
        results: List of :class:`FixResult` containing the planned actions.
        console: Optional Rich console for logging backup status.
    """
    backed_up: set[str] = set()
    for result in results:
        for action in result.actions:
            if action.action_type == "create":
                continue  # no existing file to back up
            target = action.target_path
            if target in backed_up:
                continue
            src = Path(target).resolve()
            if src.exists():
                bak = src.with_name(src.name + ".bak")
                shutil.copy2(str(src), str(bak))
                backed_up.add(target)
                if console:
                    console.print(f"  [dim]Backup: {src.name} → {bak.name}[/dim]")


# ─── FixReport data model ──────────────────────────────────────────────────


@dataclass
class FixReport:
    """Aggregated fix report for a single pack.

    JSON shape (STORY-6-0-3)::

        {
            "timestamp": "2024-01-01T00:00:00+00:00",
            "pack_path": "/path/to/pack",
            "mode": "dry-run" | "apply",
            "rules": [
                {
                    "rule_id": "F001",
                    "applied": 1,
                    "skipped": 0,
                    "errors": [],
                    "actions": [
                        {"action_type": "modify", "target_path": "/path/to/file.py"}
                    ]
                }
            ]
        }
    """

    pack_path: str
    mode: str  # "dry-run" | "apply"
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    rules: list[dict[str, Any]] = field(default_factory=list)

    @classmethod
    def from_results(
        cls,
        results: list[FixResult],
        pack_path: str,
        dry_run: bool,
    ) -> "FixReport":
        """Build a :class:`FixReport` from a list of :class:`FixResult` objects.

        Args:
            results:  Fix results returned by the dispatcher.
            pack_path: Path to the cap-pack directory.
            dry_run:  Whether the results are from a dry-run (analyze) phase.

        Returns:
            A new :class:`FixReport` instance.
        """
        mode = "dry-run" if dry_run else "apply"
        rules = []
        for r in results:
            d = r.to_dict()
            rules.append(
                {
                    "rule_id": d["rule_id"],
                    "applied": d["applied"],
                    "skipped": d["skipped"],
                    "errors": list(d["errors"]),
                    "actions": [
                        {
                            "action_type": a["action_type"],
                            "target_path": a["target_path"],
                        }
                        for a in d["actions"]
                    ],
                }
            )
        return cls(pack_path=pack_path, mode=mode, rules=rules)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a JSON-compatible dict."""
        return {
            "timestamp": self.timestamp,
            "pack_path": self.pack_path,
            "mode": self.mode,
            "rules": self.rules,
        }

    def to_json(self, indent: int = 2) -> str:
        """Serialize to a JSON string."""
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)


# ─── Terminal helpers ──────────────────────────────────────────────────────


def _action_color(action_type: str) -> str:
    """Return a Rich color name for the given action type."""
    return {"create": "green", "modify": "yellow", "delete": "red"}.get(
        action_type, "white"
    )


def _print_single_pack_report(
    report: FixReport, results: list[FixResult], console: Console
) -> None:
    """Print a fix report for a single pack to the terminal."""
    pack_name = Path(report.pack_path).name
    has_results = any(r.actions for r in results)

    if not has_results:
        console.print(f"[dim]  {pack_name}: no issues to fix[/dim]")
        return

    header_style = "bold cyan" if report.mode == "dry-run" else "bold green"
    mode_label = (
        "Fix Plan (dry-run)" if report.mode == "dry-run" else "Applying Fixes"
    )
    console.print()
    console.print(
        f"[{header_style}]── {pack_name} — {mode_label} ──[/{header_style}]"
    )

    total_applied = 0
    total_skipped = 0
    total_errors = 0

    for result in results:
        if not result.actions:
            continue

        total_applied += result.applied
        total_skipped += result.skipped
        total_errors += len(result.errors)

        if report.mode == "dry-run":
            # ── Dry-run: show planned actions + unified diff ──────────────
            console.print(
                f"\n  [cyan bold]{result.rule_id}[/cyan bold] — "
                f"planned {len(result.actions)} action(s)"
            )
            for action in result.actions:
                atype = action.action_type.upper()
                console.print(
                    f"    [{_action_color(action.action_type)}]{atype}"
                    f"[/{_action_color(action.action_type)}] {action.target_path}"
                )
                if action.description:
                    console.print(f"      [dim]{action.description}[/dim]")

            diff_text = result.diff
            if diff_text.strip():
                syntax = Syntax(
                    diff_text, "diff", theme="ansi_dark", line_numbers=False
                )
                console.print(Panel(syntax, border_style="dim", padding=(0, 2)))
        else:
            # ── Apply mode: show outcome per rule ─────────────────────────
            console.print(f"\n  [green bold]{result.rule_id}[/green bold]")

            for action in result.actions:
                atype = action.action_type.upper()
                mark = "[green]✓[/green]"
                console.print(
                    f"    {mark} [{_action_color(action.action_type)}]{atype}"
                    f"[/{_action_color(action.action_type)}] {action.target_path}"
                )

            if result.errors:
                for err in result.errors:
                    console.print(f"    [red]✗ Error: {err}[/red]")

            console.print(
                f"    [dim]Applied: {result.applied}, "
                f"Skipped: {result.skipped}, "
                f"Errors: {len(result.errors)}[/dim]"
            )

    # ── Summary ───────────────────────────────────────────────────────────
    console.print()
    summary_style = "green" if total_errors == 0 else "yellow"
    console.print(f"[bold {summary_style}]Summary:[/bold {summary_style}]")
    if report.mode == "dry-run":
        console.print(f"  Planned actions: {total_applied}")
    else:
        console.print(
            f"  Applied: {total_applied} | "
            f"Skipped: {total_skipped} | "
            f"Errors: {total_errors}"
        )
        if total_errors == 0:
            console.print("[green]  ✓ All fixes applied successfully[/green]")
        else:
            console.print(
                "[yellow]  ⚠ Some fixes failed — review errors above[/yellow]"
            )
    console.print()


# ─── FixReporter ───────────────────────────────────────────────────────────


class FixReporter:
    """Generate fix reports in terminal (Rich) or JSON format.

    Examples::

        # Single pack
        report = FixReport.from_results(results, pack_path, dry_run=True)
        FixReporter().print_report(report, results)
        json_str = FixReporter().generate_json(report, "fix-report.json")

        # Multi-pack
        FixReporter().print_multi_pack_report(all_results, dry_run=True)
    """

    def __init__(self, console: Optional[Console] = None):
        self.console = console or Console()

    def print_report(self, report: FixReport, results: list[FixResult]) -> None:
        """Print a human-readable fix report for a single pack.

        Args:
            report:  The :class:`FixReport` to display.
            results: The original :class:`FixResult` objects (needed for
                     diff generation).
        """
        _print_single_pack_report(report, results, self.console)

    def print_multi_pack_report(
        self, all_results: dict[str, list[FixResult]], dry_run: bool
    ) -> None:
        """Print fix results for one or more packs.

        Args:
            all_results: Mapping of ``pack_path → list[FixResult]``.
            dry_run:     Whether the results are from a dry-run phase.
        """
        if not all_results:
            self.console.print("[yellow]No packs were processed.[/yellow]")
            return

        for pack_path, results in all_results.items():
            report = FixReport.from_results(results, pack_path, dry_run)
            self.print_report(report, results)

    def generate_json(
        self, report: FixReport, output_path: Optional[str] = None
    ) -> str:
        """Generate JSON string and optionally write to file.

        Args:
            report:      The :class:`FixReport` to serialize.
            output_path: If provided, write JSON to this file.

        Returns:
            JSON string of the report.
        """
        json_str = report.to_json()
        if output_path:
            Path(output_path).write_text(json_str, encoding="utf-8")
        return json_str

    @staticmethod
    def generate_multi_pack_json(
        all_results: dict[str, list[FixResult]],
        dry_run: bool,
        output_path: Optional[str] = None,
    ) -> str:
        """Generate a multi-pack JSON report.

        The output wraps individual pack reports in a ``\"packs\"`` key::

            {
                "mode": "dry-run" | "apply",
                "timestamp": "...",
                "packs": {
                    "/path/to/pack": { FixReport.to_dict() },
                    ...
                }
            }

        Args:
            all_results: Mapping of ``pack_path → list[FixResult]``.
            dry_run:     Whether the results are from a dry-run phase.
            output_path: If provided, write JSON to this file.

        Returns:
            JSON string of the multi-pack report.
        """
        mode = "dry-run" if dry_run else "apply"
        timestamp = datetime.now(timezone.utc).isoformat()
        packs = {}
        for pack_path, results in all_results.items():
            report = FixReport.from_results(results, pack_path, dry_run)
            packs[pack_path] = report.to_dict()

        data = {
            "mode": mode,
            "timestamp": timestamp,
            "packs": packs,
        }
        json_str = json.dumps(data, indent=2, ensure_ascii=False)
        if output_path:
            Path(output_path).write_text(json_str, encoding="utf-8")
        return json_str
