"""Pre-flight gate checker — STORY-5-2-1.

Runs a skill-governance scan on a given skill path, checks L0+L1 blocking
rules, and returns a GateResult. Integrates with pre_flight.py via rich output.
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from skill_governance.models.result import CheckResult, ScanResult, ScanReport
from skill_governance.scanner.base import RuleLoader
from skill_governance.scanner.compliance import ComplianceChecker

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
except ImportError:  # pragma: no cover
    Console = None  # type: ignore[assignment]
    Panel = None  # type: ignore[assignment]
    Table = None  # type: ignore[assignment]


# ─── GateResult ───────────────────────────────────────────────────────────────


@dataclass
class GateResult:
    """Result of a pre-flight gate check on a skill path.

    Attributes:
        status: One of PASS, WARN, or BLOCKED.
        message: Human-readable summary of the gate result.
        details: List of detailed messages about individual check outcomes.
        passed: True if status is PASS or WARN; False if BLOCKED.
    """

    status: str  # PASS | WARN | BLOCKED
    message: str
    details: list[str] = field(default_factory=list)
    passed: bool = True

    def __post_init__(self) -> None:
        self.passed = self.status in ("PASS", "WARN")


# ─── Helpers ──────────────────────────────────────────────────────────────────


def _parse_frontmatter(content: str) -> dict[str, Any]:
    """Parse YAML frontmatter from a SKILL.md file."""
    import yaml

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
        frontmatter = yaml.safe_load("\n".join(lines[1:end_idx]))
        if isinstance(frontmatter, dict):
            return frontmatter
        return {}
    except Exception:
        return {}


def _collect_skill_data(skill_path: str) -> dict[str, Any]:
    """Collect skill metadata from a single skill path for scanning.

    Reads SKILL.md frontmatter and builds a skill dict compatible with
    the governance scanner's expected input format.

    Args:
        skill_path: Path to the skill directory containing SKILL.md.

    Returns:
        A skill dict with keys: id, name, path, version, classification,
        tags, triggers, sqs_total, compatibility.
    """
    sp = Path(skill_path).resolve()
    skill_md = sp / "SKILL.md"

    skill_data: dict[str, Any] = {
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
            skill_data["name"] = fm.get("name", sp.name)
            skill_data["description"] = fm.get("description", "")
            skill_data["version"] = fm.get("version", "")
            skill_data["classification"] = fm.get("classification", "")
            skill_data["tags"] = fm.get("tags", [])
            skill_data["triggers"] = fm.get("triggers", [])
            skill_data["compatibility"] = fm.get("compatibility", {})
            # SQS can be embedded in frontmatter or passed separately
            sqs = fm.get("sqs", {})
            if isinstance(sqs, dict):
                skill_data["sqs_total"] = sqs.get("total")
            elif isinstance(sqs, (int, float)):
                skill_data["sqs_total"] = sqs
            # Also check for sqs_total directly
            skill_data["sqs_total"] = skill_data["sqs_total"] or fm.get("sqs_total")
        except Exception:
            pass

    return skill_data


# ─── Main gate check ──────────────────────────────────────────────────────────


def _check_l0_compatibility(skill_data: dict[str, Any]) -> list[CheckResult]:
    """Run L0 Compatibility checks (C001–C005) inline.

    The ComplianceChecker does not natively handle L0, so we implement
    basic inline checks here.
    """
    import re

    results: list[CheckResult] = []
    name = skill_data.get("name", "")
    desc = skill_data.get("description", "")
    tags = skill_data.get("tags", [])

    # C001: name field validation (1-64 chars, lowercase+hyphens)
    name_ok = bool(name) and len(name) <= 64 and bool(re.match(r"^[a-z][a-z0-9-]{0,62}[a-z0-9]$", name))
    results.append(CheckResult(
        rule_id="C001", layer_id="L0",
        description="name field: 1-64 chars, lowercase+hyphens, matches SKILL directory name",
        severity="blocking", passed=name_ok,
        score=100.0 if name_ok else 0.0,
        details={"name": name, "valid": name_ok},
        suggestions=[] if name_ok else [f"Rename to lowercase-hyphen format, 1-64 chars (got '{name}')"],
    ))

    # C002: description present
    desc_ok = bool(desc) and len(desc) >= 1 and len(desc) <= 1024
    results.append(CheckResult(
        rule_id="C002", layer_id="L0",
        description="description field: 1-1024 chars, contains trigger words for SRA discovery",
        severity="blocking", passed=desc_ok,
        score=100.0 if desc_ok else 0.0,
        details={"description_length": len(desc) if desc else 0, "present": bool(desc)},
        suggestions=[] if desc_ok else ["Add a description (1-1024 chars) to SKILL.md frontmatter"],
    ))

    # C003: directory structure — only scripts/references/assets allowed
    sp = Path(skill_data.get("path", ""))
    allowed_dirs = {"scripts", "references", "assets"}
    disallowed: list[str] = []
    if sp.exists():
        for child in sp.iterdir():
            if child.is_dir() and child.name not in allowed_dirs and not child.name.startswith("."):
                disallowed.append(child.name)
    dir_ok = len(disallowed) == 0
    results.append(CheckResult(
        rule_id="C003", layer_id="L0",
        description="Directory structure: only scripts/references/assets allowed as subdirectories",
        severity="blocking", passed=dir_ok,
        score=100.0 if dir_ok else 50.0,
        details={"disallowed_dirs": disallowed, "allowed": sorted(allowed_dirs)},
        suggestions=[] if dir_ok else [f"Remove or rename disallowed directories: {disallowed}"],
    ))

    # C004: SKILL.md line count < 500 (warning)
    skill_md = sp / "SKILL.md"
    line_count = 0
    if skill_md.exists():
        try:
            line_count = len(skill_md.read_text(encoding="utf-8").split("\n"))
        except Exception:
            pass
    line_ok = line_count < 500
    results.append(CheckResult(
        rule_id="C004", layer_id="L0",
        description="SKILL.md line count < 500 (recommended by Agent Skills Spec §4.3)",
        severity="warning", passed=line_ok,
        score=100.0 if line_ok else max(0, 100.0 - (line_count / 500) * 100),
        details={"line_count": line_count, "max_lines": 500},
        suggestions=[] if line_ok else [f"Reduce SKILL.md from {line_count} to under 500 lines"],
    ))

    # C005: Progressive disclosure — required headings present (info)
    has_name = "name" in skill_data and bool(skill_data["name"])
    has_desc = "description" in skill_data and bool(skill_data["description"])
    prog_ok = has_name and has_desc
    results.append(CheckResult(
        rule_id="C005", layer_id="L0",
        description="Progressive disclosure: three-level loading — metadata → instructions → resources",
        severity="info", passed=prog_ok,
        score=100.0 if prog_ok else 50.0,
        details={"has_name": has_name, "has_description": has_desc},
        suggestions=[] if prog_ok else ["Ensure name and description are present for progressive loading"],
    ))

    return results


def check_gate(skill_path: str) -> GateResult:
    """Run the pre-flight gate on a skill directory.

    Checks:
      - L0 (Compatibility) blocking rules: C001–C005
      - L1 (Foundation) blocking rules: F001–F007

    Args:
        skill_path: Filesystem path to the skill directory containing SKILL.md.

    Returns:
        A GateResult with status PASS/WARN/BLOCKED, a summary message,
        and a list of detail messages.

    Raises:
        FileNotFoundError: If the skill path or SKILL.md does not exist.
    """
    sp = Path(skill_path).resolve()
    if not sp.exists():
        raise FileNotFoundError(f"Skill path does not exist: {skill_path}")

    skill_md = sp / "SKILL.md"
    if not skill_md.exists():
        raise FileNotFoundError(f"SKILL.md not found in {skill_path}")

    details: list[str] = []
    blocking_failures: list[str] = []
    warnings: list[str] = []

    # ── Collect skill data ───────────────────────────────────────────────
    skill_data = _collect_skill_data(str(sp))
    skills = [skill_data]

    # ── Layer 0: Compatibility (blocking) ────────────────────────────────
    l0_checks = _check_l0_compatibility(skill_data)

    for check in l0_checks:
        check_detail = (
            f"[L0/{check.rule_id}] {check.description} — "
            f"{'PASS' if check.passed else 'FAIL'} (score: {check.score:.1f}%)"
        )
        details.append(check_detail)
        if not check.passed and check.severity == "blocking":
            blocking_failures.append(f"L0/{check.rule_id}: {check.description}")
        elif not check.passed:
            warnings.append(f"L0/{check.rule_id}: {check.description}")

    # ── Layer 1: Foundation (blocking) ───────────────────────────────────
    l1_checker = ComplianceChecker(layer_id="L1")
    l1_checks: list[CheckResult] = []
    try:
        l1_checks = l1_checker.scan({"skills": skills})
    except Exception as exc:
        details.append(f"L1 scan error: {exc}")

    for check in l1_checks:
        check_detail = (
            f"[L1/{check.rule_id}] {check.description} — "
            f"{'PASS' if check.passed else 'FAIL'} (score: {check.score:.1f}%)"
        )
        details.append(check_detail)
        if not check.passed and check.severity == "blocking":
            blocking_failures.append(f"L1/{check.rule_id}: {check.description}")
        elif not check.passed:
            warnings.append(f"L1/{check.rule_id}: {check.description}")

    # ── Determine gate status ────────────────────────────────────────────
    if blocking_failures:
        status = "BLOCKED"
        message = (
            f"Gate BLOCKED: {len(blocking_failures)} blocking failure(s) detected "
            f"for skill '{sp.name}'."
        )
    elif warnings:
        status = "WARN"
        message = (
            f"Gate WARN: {len(warnings)} warning(s) found for skill '{sp.name}', "
            f"but no blocking failures."
        )
    else:
        status = "PASS"
        message = f"Gate PASS: skill '{sp.name}' passes all L0+L1 checks."

    return GateResult(
        status=status,
        message=message,
        details=details,
    )


# ─── Rich formatted output (for pre_flight.py integration) ────────────────────


def print_gate_result(result: GateResult, *, console: Any = None) -> None:
    """Print a GateResult using Rich formatting.

    Args:
        result: The GateResult to display.
        console: A rich.Console instance. If None, a default one is created.
    """
    if Console is None:
        # Fallback to plain print if rich not available
        print(f"Gate Status: {result.status}")
        print(result.message)
        for d in result.details:
            print(f"  • {d}")
        return

    _console = console or Console()

    status_style = {
        "PASS": "bold green",
        "WARN": "bold yellow",
        "BLOCKED": "bold red",
    }.get(result.status, "bold white")

    panel = Panel(
        f"[{status_style}]{result.status}[/{status_style}] — {result.message}",
        title="Pre-Flight Gate Result",
        border_style=result.status.lower() if result.status in ("PASS", "WARN", "BLOCKED") else "white",
    )
    _console.print()
    _console.print(panel)
    _console.print()

    if result.details:
        table = Table(title="Detailed Check Results", show_header=True, header_style="bold")
        table.add_column("Check", style="cyan", no_wrap=True)
        table.add_column("Outcome", width=10)

        for d in result.details:
            if "PASS" in d:
                outcome = "[green]PASS[/green]"
            elif "FAIL" in d:
                outcome = "[red]FAIL[/red]"
            else:
                outcome = "[dim]INFO[/dim]"
            table.add_row(d, outcome)

        _console.print(table)
        _console.print()
