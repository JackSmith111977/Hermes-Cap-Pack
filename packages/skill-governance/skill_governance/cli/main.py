"""CLI main — typer-based `scan` and `watcher` subcommands with Rich console output."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any, Optional

import typer
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel

from skill_governance.models.result import CheckResult, ScanReport, ScanResult
from skill_governance.scanner.base import RuleLoader
from skill_governance.scanner.compliance import ComplianceChecker
from skill_governance.scanner.atomicity import AtomicityScanner
from skill_governance.scanner.tree_validator import TreeValidator
from skill_governance.scanner.workflow_detector import WorkflowDetector
from skill_governance.reporter.json_reporter import JSONReporter
from skill_governance.reporter.html_reporter import HTMLReporter
from skill_governance.watcher.fingerprint import FingerprintWatcher
from skill_governance.fixer import (
    FixDispatcher,
    FixResult,
    FixAction,
    FixReport,
    FixReporter,
    FixRule,
    ensure_backups,
)


app = typer.Typer(
    name="skill-governance",
    help="L0-L4 compliance governance engine for cap-pack skills.",
    add_completion=False,
)
console = Console()


# ─── Shared helpers ───────────────────────────────────────────────────────────


def _load_skills_from_pack(pack_path: str) -> list[dict[str, Any]]:
    """Load skills from a cap-pack.yaml file."""
    pack_yaml = Path(pack_path) / "cap-pack.yaml"
    if not pack_yaml.exists():
        console.print(f"[red]Error:[/red] cap-pack.yaml not found in {pack_path}")
        sys.exit(1)
    try:
        import yaml
        with open(pack_yaml, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except Exception as e:
        console.print(f"[red]Error reading cap-pack.yaml:[/red] {e}")
        sys.exit(1)

    skills: list[dict[str, Any]] = []
    pack_dir = Path(pack_path).resolve()
    for sk in data.get("skills", []):
        sid = sk.get("id", "") or sk.get("name", "")
        # Resolve skill path
        skill_path = sk.get("path", "")
        if not skill_path:
            skill_path = pack_dir / "SKILLS" / sid
        else:
            skill_path = pack_dir / skill_path
        skills.append(
            {
                "id": sid,
                "name": sk.get("name", sid),
                "path": str(skill_path),
                "version": sk.get("version", ""),
                "classification": sk.get("classification", ""),
                "tags": sk.get("tags", []),
                "triggers": sk.get("triggers", []),
                "sqs_total": sk.get("sqs_total") or (sk.get("sqs", {}) if isinstance(sk.get("sqs"), dict) else {}).get("total"),
                "compatibility": sk.get("compatibility", {}),
            }
        )

    return skills


def _build_report(
    target_path: str,
    l0_data: Optional[dict[str, Any]] = None,
    l1_data: Optional[dict[str, Any]] = None,
    l2_data: Optional[dict[str, Any]] = None,
    l3_data: Optional[dict[str, Any]] = None,
    l4_data: Optional[dict[str, Any]] = None,
) -> ScanReport:
    report = ScanReport(target_path=target_path)

    # Layer 0 — Compatibility
    l0_checker = ComplianceChecker(layer_id="L0")
    l0_checks = l0_checker.scan(l0_data or {})
    l0_layer = RuleLoader().get_layer("L0")
    report.layers["L0"] = ScanResult(
        layer_id="L0",
        layer_name=l0_layer.name if l0_layer else "Compatibility",
        target=l0_layer.target if l0_layer else "L0 pass",
        blocking_failure=l0_layer.blocking_failure if l0_layer else True,
        checks=l0_checks,
    )

    # Layer 1 — Foundation
    l1_checker = ComplianceChecker(layer_id="L1")
    l1_checks = l1_checker.scan(l1_data or {})
    l1_layer = RuleLoader().get_layer("L1")
    report.layers["L1"] = ScanResult(
        layer_id="L1",
        layer_name=l1_layer.name if l1_layer else "Foundation",
        target=l1_layer.target if l1_layer else "L1 pass",
        blocking_failure=l1_layer.blocking_failure if l1_layer else True,
        checks=l1_checks,
    )

    # Layer 2 — Health
    l2_results = []
    if l2_data:
        atomicity = AtomicityScanner()
        l2_results.extend(atomicity.scan(l2_data))
        tree_val = TreeValidator()
        l2_results.extend(tree_val.scan(l2_data))
    l2_layer = RuleLoader().get_layer("L2")
    report.layers["L2"] = ScanResult(
        layer_id="L2",
        layer_name=l2_layer.name if l2_layer else "Health",
        target=l2_layer.target if l2_layer else "L2 pass (Healthy)",
        blocking_failure=l2_layer.blocking_failure if l2_layer else False,
        checks=l2_results,
    )

    # Layer 3 — Ecosystem
    l3_checker = ComplianceChecker(layer_id="L3")
    l3_checks = l3_checker.scan(l3_data or {})
    l3_layer = RuleLoader().get_layer("L3")
    report.layers["L3"] = ScanResult(
        layer_id="L3",
        layer_name=l3_layer.name if l3_layer else "Ecosystem",
        target=l3_layer.target if l3_layer else "L3 pass",
        blocking_failure=l3_layer.blocking_failure if l3_layer else False,
        checks=l3_checks,
    )

    # Layer 4 — Workflow
    l4_results = []
    if l4_data:
        wf_detector = WorkflowDetector()
        l4_results.extend(wf_detector.scan(l4_data))
    l4_layer = RuleLoader().get_layer("L4")
    report.layers["L4"] = ScanResult(
        layer_id="L4",
        layer_name=l4_layer.name if l4_layer else "Workflow Orchestration",
        target=l4_layer.target if l4_layer else "L4 pass (Orchestrated)",
        blocking_failure=l4_layer.blocking_failure if l4_layer else False,
        checks=l4_results,
    )

    return report


def _print_rich_report(report: ScanReport) -> None:
    """Print a formatted summary using Rich."""
    status_colors = {
        "orchestrated": "green",
        "excellent": "blue",
        "healthy": "green",
        "needs_improvement": "yellow",
        "compliant": "green",
        "non_compliant": "red",
    }
    status = report.overall_status
    color = status_colors.get(status, "white")

    console.print()
    status_panel = Panel(
        f"[bold {color}]{status.upper()}[/bold {color}] — {report.target_path}",
        title="[bold]Governance Scan Complete[/bold]",
        border_style=color,
    )
    console.print(status_panel)
    console.print(f"  Timestamp: {report.timestamp}")
    console.print(f"  {'Terminated early (blocking failure)' if not report.terminated else 'Full scan'}")
    console.print()

    table = Table(title="L0-L4 Layer Results", show_header=True, header_style="bold")
    table.add_column("Layer", style="cyan", width=6)
    table.add_column("Name", style="white", width=22)
    table.add_column("Status", width=10)
    table.add_column("Score", justify="right", width=8)
    table.add_column("Checks", justify="center", width=12)

    for lid in ["L0", "L1", "L2", "L3", "L4"]:
        lr = report.layers.get(lid)
        if not lr:
            continue
        status_str = "[green]✅ PASS[/green]" if lr.passed else "[red]❌ FAIL[/red]"
        if lr.has_blocking_failures():
            status_str = "[red]🔴 BLOCKING[/red]"
        score_color = "green" if lr.score >= 80 else "yellow" if lr.score >= 50 else "red"
        table.add_row(
            lid,
            lr.layer_name,
            status_str,
            f"[{score_color}]{lr.score:.1f}%[/{score_color}]",
            f"{lr.checks_passed}/{lr.checks_total}",
        )

    console.print(table)
    console.print()

    # Print detailed failures
    for lid in ["L0", "L1", "L2", "L3", "L4"]:
        lr = report.layers.get(lid)
        if not lr:
            continue
        failures = [c for c in lr.checks if not c.passed]
        if failures:
            console.print(f"\n[bold yellow]{lid} — Failed Checks:[/bold yellow]")
            for c in failures:
                sev_style = "red" if c.severity == "blocking" else "yellow"
                console.print(f"  [bold]{c.rule_id}[/bold] ({c.description})")
                console.print(f"    Severity: [{sev_style}]{c.severity}[/{sev_style}] | Score: {c.score:.1f}%")
                if c.suggestions:
                    for s in c.suggestions[:2]:
                        console.print(f"    [dim]→ {s}[/dim]")
            console.print()


# ─── CLI Commands ─────────────────────────────────────────────────────────────


@app.command()
def scan(
    pack_path: str = typer.Argument(
        ..., help="Path to the cap-pack directory (containing cap-pack.yaml)"
    ),
    output: Optional[str] = typer.Option(
        None, "--output", "-o", help="Output file path (JSON or .html extension)"
    ),
    format: str = typer.Option(
        "rich", "--format", "-f", help="Output format: rich, json, html"
    ),
    workflows_file: Optional[str] = typer.Option(
        None, "--workflows", "-w", help="Path to workflows YAML file"
    ),
    clusters_file: Optional[str] = typer.Option(
        None, "--clusters", "-c", help="Path to clusters YAML file"
    ),
) -> None:
    """Run L0-L4 compliance scan on a cap-pack."""
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Loading pack data...", total=None)

        pack_dir = Path(pack_path).resolve()
        if not pack_dir.exists():
            console.print(f"[red]Error:[/red] Path does not exist: {pack_path}")
            raise typer.Exit(code=1)

        skills = _load_skills_from_pack(str(pack_dir))

        # Load workflow data
        workflows: list[dict[str, Any]] = []
        if workflows_file:
            wf_path = Path(workflows_file)
            if wf_path.exists():
                import yaml
                with open(wf_path, "r", encoding="utf-8") as f:
                    wf_data = yaml.safe_load(f)
                workflows = wf_data.get("workflows", [])
        else:
            # Try loading from cap-pack.yaml
            pack_yaml = pack_dir / "cap-pack.yaml"
            if pack_yaml.exists():
                import yaml
                with open(pack_yaml, "r", encoding="utf-8") as f:
                    pack_data = yaml.safe_load(f)
                workflows = pack_data.get("workflows", [])

        # Load cluster data
        clusters: list[dict[str, Any]] = []
        if clusters_file:
            cl_path = Path(clusters_file)
            if cl_path.exists():
                import yaml
                with open(cl_path, "r", encoding="utf-8") as f:
                    cl_data = yaml.safe_load(f)
                clusters = cl_data.get("clusters", [])
        else:
            # Try loading from cap-pack.yaml
            pack_yaml = pack_dir / "cap-pack.yaml"
            if pack_yaml.exists():
                import yaml
                with open(pack_yaml, "r", encoding="utf-8") as f:
                    pack_data = yaml.safe_load(f)
                clusters = pack_data.get("clusters", [])

        progress.update(task, description="Running governance checks...")

        l0_data = {"skills": skills}
        l1_data = {"skills": skills}
        l2_data = {"skills": skills, "clusters": clusters}
        l3_data = {"skills": skills, "pack_path": str(pack_dir)}
        l4_data = {"workflows": workflows, "skills": skills}

        report = _build_report(
            target_path=str(pack_dir),
            l0_data=l0_data,
            l1_data=l1_data,
            l2_data=l2_data,
            l3_data=l3_data,
            l4_data=l4_data,
        )

        progress.update(task, description="Generating output...")

    # Output
    if format == "json" or (output and output.endswith(".json")):
        json_str = JSONReporter().generate(report, output)
        if not output:
            console.print(json_str)
    elif format == "html" or (output and output.endswith(".html")):
        HTMLReporter().generate(report, output)
        if output:
            console.print(f"[green]HTML report written to:[/green] {output}")
        else:
            console.print("[yellow]No output path specified for HTML — use --output[/yellow]")
    else:
        _print_rich_report(report)
        if output:
            JSONReporter().generate(report, output)
            console.print(f"[green]JSON report written to:[/green] {output}")


@app.command()
def watcher(
    pack_path: str = typer.Argument(
        ..., help="Path to the cap-pack directory"
    ),
    action: str = typer.Option(
        "check", "--action", "-a", help="Action: init, check, auto"
    ),
    state_file: Optional[str] = typer.Option(
        None, "--state", "-s", help="Fingerprint state file path"
    ),
) -> None:
    """Initialize or check file fingerprints for change detection."""
    pack_dir = Path(pack_path).resolve()
    if not pack_dir.exists():
        console.print(f"[red]Error:[/red] Path does not exist: {pack_path}")
        raise typer.Exit(code=1)

    skills = _load_skills_from_pack(str(pack_dir))
    fw = FingerprintWatcher(Path(state_file) if state_file else None)

    if action == "init":
        fingerprints = fw.init(skills)
        console.print(f"[green]Initialized fingerprints for {len(fingerprints)} files:[/green]")
        table = Table(show_header=True, header_style="bold")
        table.add_column("File", style="cyan")
        table.add_column("SHA-256 Hash", style="dim")
        for fpath, fhash in fingerprints.items():
            table.add_row(fpath, fhash[:16] + "...")
        console.print(table)

    elif action == "check":
        changed = fw.check(skills)
        if changed:
            console.print(f"[yellow]Found {len(changed)} changed file(s):[/yellow]")
            for fpath, new_hash in changed.items():
                status = "[red]DELETED[/red]" if not new_hash else "[yellow]MODIFIED[/yellow]"
                console.print(f"  {status} {fpath}")
        else:
            console.print("[green]No changes detected — all fingerprints match.[/green]")

    elif action == "auto":
        has_changes, changed = fw.auto_scan(skills)
        if has_changes:
            console.print(f"[yellow]Detected and recorded {len(changed)} change(s):[/yellow]")
            for fpath, new_hash in changed.items():
                status = "[red]DELETED[/red]" if not new_hash else "[yellow]MODIFIED[/yellow]"
                console.print(f"  {status} {fpath}")
        else:
            console.print("[green]No changes detected. Fingerprints are current.[/green]")

    else:
        console.print(f"[red]Unknown action: {action}[/red] (use: init, check, auto)")
        raise typer.Exit(code=1)


@app.command()
def rules(
    layer: Optional[str] = typer.Argument(
        None, help="Layer ID to show (e.g. L0, L1). Shows all if omitted."
    ),
    json_output: bool = typer.Option(
        False, "--json", "-j", help="Output in JSON format"
    ),
) -> None:
    """List loaded rules from rules.yaml."""
    loader = RuleLoader()
    collection = loader.load()

    if json_output:
        sanitized = json.loads(json.dumps(collection.to_dict(), ensure_ascii=False, default=str))
        if layer and layer in collection.layers:
            print(json.dumps(sanitized["layers"][layer], indent=2, ensure_ascii=False))
        else:
            print(json.dumps(sanitized, indent=2, ensure_ascii=False))
        return

    if layer:
        lr = collection.get_layer(layer)
        if not lr:
            console.print(f"[red]Layer {layer} not found[/red]")
            raise typer.Exit(code=1)
        console.print(f"\n[bold]{lr.id}: {lr.name}[/bold]")
        console.print(f"  {lr.description}")
        table = Table(show_header=True, header_style="bold")
        table.add_column("Rule ID", style="cyan")
        table.add_column("Description")
        table.add_column("Severity", width=10)
        table.add_column("Check Type", width=20)
        for r in lr.rules:
            table.add_row(r.id, r.description, r.severity, r.check_type)
        console.print(table)
    else:
        console.print(f"[bold]Rule Collection v{collection.version}[/bold]")
        console.print(f"  Standard: {collection.standard_ref}")
        console.print(f"  Schema: {collection.schema_ref}")
        console.print()
        for lid in collection.layer_ids:
            lr = collection.layers[lid]
            console.print(f"[bold cyan]{lr.id}: {lr.name}[/bold cyan] ({len(lr.rules)} rules)")
            for r in lr.rules:
                sev_style = "red" if r.severity == "blocking" else "yellow" if r.severity == "warning" else "dim"
                console.print(f"  [{sev_style}]{r.id}[/{sev_style}] {r.description}")
            console.print()


# ─── Fix helpers ──────────────────────────────────────────────────────────────


def _find_packs_root() -> Path | None:
    """Locate the ``packs/`` directory relative to the project root.

    Walks up from the CLI script location looking for a ``packs/``
    directory that contains ``cap-pack.yaml`` files.
    """
    cli_path = Path(__file__).resolve()
    for parent in cli_path.parents:
        candidate = parent / "packs"
        if candidate.is_dir():
            # Verify it looks like a packs directory
            subdirs = [d for d in candidate.iterdir() if d.is_dir()]
            if any((d / "cap-pack.yaml").exists() for d in subdirs):
                return candidate
    return None


def _setup_fix_dispatcher() -> FixDispatcher:
    """Create and populate a :class:`FixDispatcher` with available fix rules.

    Auto-discovers concrete ``FixRule`` subclasses from the
    ``skill_governance.fixer.rules`` package via ``importlib`` + ``inspect``,
    instantiates each one, and registers it with the dispatcher.
    """
    import importlib
    import inspect
    import pkgutil

    dispatcher = FixDispatcher()
    rules_pkg = importlib.import_module("skill_governance.fixer.rules")

    for importer, modname, ispkg in pkgutil.walk_packages(
        rules_pkg.__path__, rules_pkg.__name__ + "."
    ):
        try:
            mod = importlib.import_module(modname)
        except Exception:
            continue
        for name, obj in inspect.getmembers(mod):
            if (
                inspect.isclass(obj)
                and issubclass(obj, FixRule)
                and obj is not FixRule
            ):
                try:
                    instance = obj()
                    dispatcher.register(instance)
                except Exception as e:
                    print(f"  ⚠️  Failed to register {name}: {e}")

    return dispatcher


def _print_fix_results(
    all_results: dict[str, list[FixResult]],
    dry_run: bool,
) -> None:
    """Print fix results for one or more packs using Rich formatting.

    Delegates to :class:`FixReporter` for consistent output (STORY-6-0-3).
    """
    FixReporter(console=console).print_multi_pack_report(all_results, dry_run)


# ─── CLI Commands ─────────────────────────────────────────────────────────────


@app.command("fix")
def fix(
    pack_path: Optional[str] = typer.Argument(
        None, help="Path to the cap-pack directory (containing cap-pack.yaml)"
    ),
    rules: Optional[str] = typer.Option(
        None, "--rules", "-r",
        help="Comma-separated rule IDs to dispatch (e.g. F001,F007)",
    ),
    dry_run: bool = typer.Option(
        True, "--dry-run/--apply",
        help="Show fix plan without applying (default: dry-run)",
    ),
    all_packs: bool = typer.Option(
        False, "--all", "-a",
        help="Process all packs in the project's packs/ directory",
    ),
    output: Optional[str] = typer.Option(
        None, "--output", "-o",
        help="Output file for fix report (JSON)",
    ),
) -> None:
    """Scan and auto-fix compliance issues in cap-pack skills.

    Reuses the same scan pipeline as the ``scan`` command, then routes
    any failed checks to registered fix rules for automatic remediation.
    """
    # ── Validate arguments ────────────────────────────────────────────────
    if not all_packs and not pack_path:
        console.print("[red]Error:[/red] Provide a pack path or use --all to process all packs.")
        raise typer.Exit(code=1)

    # ── Resolve pack paths ────────────────────────────────────────────────
    pack_paths: list[str] = []
    if all_packs:
        packs_root = _find_packs_root()
        if not packs_root:
            console.print("[red]Error:[/red] Cannot locate the packs/ directory. "
                           "Run this command from within the project tree.")
            raise typer.Exit(code=1)
        for entry in sorted(packs_root.iterdir()):
            if entry.is_dir() and (entry / "cap-pack.yaml").exists():
                pack_paths.append(str(entry))
        if not pack_paths:
            console.print("[red]Error:[/red] No packs with cap-pack.yaml found.")
            raise typer.Exit(code=1)
        console.print(f"[dim]Found {len(pack_paths)} pack(s) to process[/dim]")
    else:
        pack_paths = [pack_path]  # type: ignore[assignment]

    # ── Parse rules filter ────────────────────────────────────────────────
    rules_filter: list[str] | None = None
    if rules:
        rules_filter = [r.strip() for r in rules.split(",") if r.strip()]
        if not rules_filter:
            console.print("[red]Error:[/red] No valid rule IDs in --rules value.")
            raise typer.Exit(code=1)

    # ── Setup dispatcher ──────────────────────────────────────────────────
    dispatcher = _setup_fix_dispatcher()
    if not dispatcher.registered_rules:
        console.print("[yellow]Warning:[/yellow] No fix rules are registered yet. "
                       "Results will be empty until fix rules are implemented.")

    # ── Process each pack ─────────────────────────────────────────────────
    all_results: dict[str, list[FixResult]] = {}

    for pp in pack_paths:
        pack_dir = Path(pp).resolve()
        pack_name = pack_dir.name

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task(f"Scanning {pack_name}...", total=None)

            if not pack_dir.exists():
                console.print(f"[red]Error:[/red] Path does not exist: {pp}")
                continue

            # Load skills from cap-pack.yaml
            skills = _load_skills_from_pack(str(pack_dir))

            # Load workflows & clusters from cap-pack.yaml (same as scan)
            pack_yaml = pack_dir / "cap-pack.yaml"
            workflows: list[dict[str, Any]] = []
            clusters: list[dict[str, Any]] = []
            if pack_yaml.exists():
                import yaml
                with open(pack_yaml, "r", encoding="utf-8") as f:
                    pack_data = yaml.safe_load(f)
                workflows = pack_data.get("workflows", [])
                clusters = pack_data.get("clusters", [])

            progress.update(task, description=f"Running checks for {pack_name}...")

            l0_data = {"skills": skills}
            l1_data = {"skills": skills}
            l2_data = {"skills": skills, "clusters": clusters}
            l3_data = {"skills": skills, "pack_path": str(pack_dir)}
            l4_data = {"workflows": workflows, "skills": skills}

            report = _build_report(
                target_path=str(pack_dir),
                l0_data=l0_data,
                l1_data=l1_data,
                l2_data=l2_data,
                l3_data=l3_data,
                l4_data=l4_data,
            )

            progress.update(task, description=f"Dispatching fixes for {pack_name}...")

            # ═══ Core: dispatch fix rules ═══════════════════════════════════
            results = dispatcher.dispatch(
                report=report.to_dict(),
                rules_filter=rules_filter,
                dry_run=dry_run,
            )

            all_results[str(pack_dir)] = results

    # ═══ Backup before apply (ADR-6-2 / STORY-6-0-3) ════════════════════════
    if not dry_run:
        for pack_path, results in all_results.items():
            if any(r.actions for r in results):
                console.print(f"[dim]Creating backups for {Path(pack_path).name}...[/dim]")
                ensure_backups(results, console=console)

    # ── Output ────────────────────────────────────────────────────────────
    _print_fix_results(all_results, dry_run=dry_run)

    if output:
        FixReporter.generate_multi_pack_json(
            all_results=all_results,
            dry_run=dry_run,
            output_path=output,
        )
        console.print(f"[green]Fix report written to:[/green] {Path(output).resolve()}")


def main() -> None:
    """Entry point for the CLI."""
    app()


if __name__ == "__main__":
    main()
