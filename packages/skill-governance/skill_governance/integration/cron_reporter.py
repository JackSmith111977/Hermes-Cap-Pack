"""Cron reporter — STORY-5-2-4.

Scheduled scan + Feishu report delivery. Supports:
  - setup_cron(): Registers a Hermes cron job (daily 6:00)
  - run_scan(): Executes a full skill-governance scan
  - build_report(): Generates HTML/JSON compliance summary
  - send_feishu(): Sends report via Feishu API
  - Previous result comparison: reads last scan, detects degradation
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from skill_governance.models.result import ScanReport
from skill_governance.reporter.html_reporter import HTMLReporter
from skill_governance.reporter.json_reporter import JSONReporter
from skill_governance.scanner.base import RuleLoader
from skill_governance.scanner.compliance import ComplianceChecker
from skill_governance.scanner.atomicity import AtomicityScanner
from skill_governance.scanner.tree_validator import TreeValidator
from skill_governance.scanner.workflow_detector import WorkflowDetector


# ─── Constants ────────────────────────────────────────────────────────────────

DEFAULT_REPORT_DIR = os.path.expanduser("~/.hermes/reports/skill-governance")
DEFAULT_CRON_NAME = "skill-governance-daily-scan"
DEFAULT_HERMES_CRON_DIR = os.path.expanduser("~/.hermes/cron")
LAST_SCAN_FILE = "last_scan.json"
FEISHU_WEBHOOK_ENV = "FEISHU_GOVERNANCE_WEBHOOK_URL"


# ─── Data types ───────────────────────────────────────────────────────────────


@dataclass
class CronReport:
    """Container for a complete cron report run."""

    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat() + "Z"
    )
    report: Optional[ScanReport] = None
    html_path: str = ""
    json_path: str = ""
    previous_status: str = ""
    current_status: str = ""
    degraded: bool = False
    summary: dict[str, Any] = field(default_factory=dict)
    error: str = ""


# ─── Helpers ──────────────────────────────────────────────────────────────────


def _load_skills_from_pack(pack_path: str) -> list[dict[str, Any]]:
    """Load skill metadata from a cap-pack.yaml."""
    import yaml

    pack_yaml = Path(pack_path) / "cap-pack.yaml"
    if not pack_yaml.exists():
        return []

    with open(pack_yaml, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    skills: list[dict[str, Any]] = []
    pack_dir = Path(pack_path).resolve()
    for sk in data.get("skills", []):
        sid = sk.get("id", "") or sk.get("name", "")
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
                "sqs_total": sk.get("sqs_total")
                or (
                    sk.get("sqs", {}).get("total")
                    if isinstance(sk.get("sqs"), dict)
                    else None
                ),
                "compatibility": sk.get("compatibility", {}),
            }
        )

    return skills


def _load_workflows(pack_path: str) -> list[dict[str, Any]]:
    """Load workflows from cap-pack.yaml."""
    import yaml

    pack_yaml = Path(pack_path) / "cap-pack.yaml"
    if not pack_yaml.exists():
        return []
    with open(pack_yaml, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data.get("workflows", [])


def _load_clusters(pack_path: str) -> list[dict[str, Any]]:
    """Load clusters from cap-pack.yaml."""
    import yaml

    pack_yaml = Path(pack_path) / "cap-pack.yaml"
    if not pack_yaml.exists():
        return []
    with open(pack_yaml, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data.get("clusters", [])


# ─── Report directory management ──────────────────────────────────────────────


def _ensure_report_dir(report_dir: str) -> Path:
    """Create the report directory if it doesn't exist."""
    path = Path(report_dir)
    path.mkdir(parents=True, exist_ok=True)
    return path


def _read_last_scan(report_dir: str) -> dict[str, Any]:
    """Read the last scan result from disk.

    Args:
        report_dir: Directory where scan reports are stored.

    Returns:
        Dict with previous scan data, or empty dict if none found.
    """
    last_path = Path(report_dir) / LAST_SCAN_FILE
    if last_path.exists():
        try:
            with open(last_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def _write_last_scan(report_dir: str, data: dict[str, Any]) -> None:
    """Write the latest scan result to disk."""
    last_path = Path(report_dir) / LAST_SCAN_FILE
    with open(last_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


# ─── Scan execution ───────────────────────────────────────────────────────────


def run_scan(pack_path: str) -> ScanReport:
    """Execute a full L0-L4 skill-governance scan on a pack.

    Args:
        pack_path: Path to the cap-pack directory containing cap-pack.yaml.

    Returns:
        A ScanReport with all layers populated.

    Raises:
        FileNotFoundError: If the pack path or cap-pack.yaml doesn't exist.
    """
    pp = Path(pack_path).resolve()
    if not pp.exists():
        raise FileNotFoundError(f"Pack path does not exist: {pack_path}")

    pack_yaml = pp / "cap-pack.yaml"
    if not pack_yaml.exists():
        raise FileNotFoundError(f"cap-pack.yaml not found in {pack_path}")

    skills = _load_skills_from_pack(str(pp))
    workflows = _load_workflows(str(pp))
    clusters = _load_clusters(str(pp))

    # Build report
    report = ScanReport(target_path=str(pp))

    # Layer 0 — Compatibility
    l0_checker = ComplianceChecker(layer_id="L0")
    l0_checks = l0_checker.scan({"skills": skills})
    l0_layer = RuleLoader().get_layer("L0")
    from skill_governance.models.result import ScanResult

    report.layers["L0"] = ScanResult(
        layer_id="L0",
        layer_name=l0_layer.name if l0_layer else "Compatibility",
        target=l0_layer.target if l0_layer else "L0 pass",
        blocking_failure=l0_layer.blocking_failure if l0_layer else True,
        checks=l0_checks,
    )

    # Layer 1 — Foundation
    l1_checker = ComplianceChecker(layer_id="L1")
    l1_checks = l1_checker.scan({"skills": skills})
    l1_layer = RuleLoader().get_layer("L1")
    report.layers["L1"] = ScanResult(
        layer_id="L1",
        layer_name=l1_layer.name if l1_layer else "Foundation",
        target=l1_layer.target if l1_layer else "L1 pass",
        blocking_failure=l1_layer.blocking_failure if l1_layer else True,
        checks=l1_checks,
    )

    # Layer 2 — Health
    l2_results: list[Any] = []
    atomicity = AtomicityScanner()
    l2_results.extend(atomicity.scan(skills))
    tree_val = TreeValidator()
    l2_results.extend(tree_val.scan({"skills": skills, "clusters": clusters}))
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
    l3_checks = l3_checker.scan({"skills": skills, "pack_path": str(pp)})
    l3_layer = RuleLoader().get_layer("L3")
    report.layers["L3"] = ScanResult(
        layer_id="L3",
        layer_name=l3_layer.name if l3_layer else "Ecosystem",
        target=l3_layer.target if l3_layer else "L3 pass",
        blocking_failure=l3_layer.blocking_failure if l3_layer else False,
        checks=l3_checks,
    )

    # Layer 4 — Workflow
    l4_results: list[Any] = []
    wf_detector = WorkflowDetector()
    l4_results.extend(wf_detector.scan({"workflows": workflows, "skills": skills}))
    l4_layer = RuleLoader().get_layer("L4")
    report.layers["L4"] = ScanResult(
        layer_id="L4",
        layer_name=l4_layer.name if l4_layer else "Workflow Orchestration",
        target=l4_layer.target if l4_layer else "L4 pass (Orchestrated)",
        blocking_failure=l4_layer.blocking_failure if l4_layer else False,
        checks=l4_results,
    )

    return report


# ─── Report generation ────────────────────────────────────────────────────────


def build_report(
    report: ScanReport,
    output_dir: str = DEFAULT_REPORT_DIR,
    pack_name: str = "",
) -> CronReport:
    """Generate HTML and JSON compliance summary files.

    Args:
        report: The ScanReport from run_scan().
        output_dir: Directory to write report files.
        pack_name: Optional name of the pack for file naming.

    Returns:
        A CronReport with file paths, status, and degradation info.
    """
    report_dir = _ensure_report_dir(output_dir)
    sanitized_name = pack_name or Path(report.target_path).name
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    # JSON report
    json_filename = f"governance-{sanitized_name}-{timestamp}.json"
    json_path = str(report_dir / json_filename)
    json_reporter = JSONReporter()
    json_reporter.generate(report, json_path)

    # HTML report
    html_filename = f"governance-{sanitized_name}-{timestamp}.html"
    html_path = str(report_dir / html_filename)
    html_reporter = HTMLReporter()
    html_reporter.generate(report, html_path)

    # Build summary
    summary = json_reporter.generate_summary(report)

    # Compare with previous scan
    last_scan = _read_last_scan(output_dir)
    previous_status = last_scan.get("overall_status", "")
    current_status = report.overall_status

    degraded = False
    if previous_status and current_status:
        status_rank = {
            "orchestrated": 5,
            "excellent": 4,
            "healthy": 3,
            "compliant": 2,
            "needs_improvement": 1,
            "non_compliant": 0,
        }
        prev_rank = status_rank.get(previous_status, -1)
        curr_rank = status_rank.get(current_status, -1)
        degraded = curr_rank < prev_rank

    # Write current scan as last scan
    _write_last_scan(
        output_dir,
        {
            "timestamp": timestamp,
            "target_path": report.target_path,
            "overall_status": current_status,
            "summary": summary,
        },
    )

    return CronReport(
        timestamp=timestamp,
        report=report,
        html_path=html_path,
        json_path=json_path,
        previous_status=previous_status,
        current_status=current_status,
        degraded=degraded,
        summary=summary,
    )


# ─── Feishu integration ───────────────────────────────────────────────────────


def send_feishu(
    report: CronReport,
    webhook_url: str | None = None,
) -> bool:
    """Send a compliance report to a Feishu webhook URL.

    Falls back to the FEISHU_GOVERNANCE_WEBHOOK_URL environment variable
    if no webhook_url is provided.

    The message includes:
      - Overall compliance status
      - Degradation warning (if any)
      - Layer scores
      - Links to detailed reports (if available)

    Args:
        report: The CronReport from build_report().
        webhook_url: Feishu webhook URL. If None, reads from env var.

    Returns:
        True if the message was sent successfully, False otherwise.
    """
    import urllib.request
    import urllib.error

    url = webhook_url or os.environ.get(FEISHU_WEBHOOK_ENV)
    if not url:
        # Silent skip if no webhook configured — this is normal for non-Feishu users
        return False

    status = report.current_status or "unknown"
    status_emoji = {
        "orchestrated": "🔄",
        "excellent": "🏆",
        "healthy": "🟢",
        "needs_improvement": "🟡",
        "compliant": "✅",
        "non_compliant": "❌",
    }.get(status, "❓")

    # Build layer summary
    layer_lines: list[str] = []
    if report.report:
        for lid in ["L0", "L1", "L2", "L3", "L4"]:
            lr = report.report.layers.get(lid)
            if lr:
                icon = "✅" if lr.passed else "❌"
                layer_lines.append(f"  {icon} {lid} ({lr.layer_name}): {lr.score:.1f}% ({lr.checks_passed}/{lr.checks_total})")

    # Build message text
    degradation_warning = ""
    if report.degraded:
        degradation_warning = (
            f"\n⚠️ **Degradation detected**: Status changed from "
            f"'{report.previous_status}' to '{report.current_status}'.\n"
        )

    report_links = ""
    if report.html_path:
        report_links += f"\n📄 HTML Report: {report.html_path}"
    if report.json_path:
        report_links += f"\n📋 JSON Report: {report.json_path}"

    message_text = (
        f"{status_emoji} **Skill-Governance Daily Report**\n"
        f"**Status**: {status}\n"
        f"**Target**: {report.report.target_path if report.report else 'N/A'}\n"
        f"**Time**: {report.timestamp}\n"
        f"{degradation_warning}"
        f"\n**Layer Scores**:\n"
        + "\n".join(layer_lines)
        + f"\n{report_links}"
    )

    payload = {
        "msg_type": "text",
        "content": {"text": message_text},
    }

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            if resp.status == 200:
                return True
            return False
    except (urllib.error.URLError, OSError):
        return False


# ─── Cron setup ───────────────────────────────────────────────────────────────


def setup_cron(
    pack_path: str,
    report_dir: str = DEFAULT_REPORT_DIR,
    time_str: str = "06:00",
    webhook_url: str | None = None,
) -> dict[str, Any]:
    """Register a Hermes cron job for daily governance scans.

    Creates a cron script at ~/.hermes/cron/ that runs the governance scan
    and sends a Feishu report at the specified time daily.

    Args:
        pack_path: Path to the cap-pack directory to scan.
        report_dir: Directory for storing report outputs.
        time_str: Time to run the scan daily (HH:MM format).
        webhook_url: Optional Feishu webhook URL. Falls back to env var.

    Returns:
        Dict with keys: cron_name, cron_path, schedule, success.
    """
    cron_dir = Path(DEFAULT_HERMES_CRON_DIR)
    cron_dir.mkdir(parents=True, exist_ok=True)

    # Validate time format
    try:
        hour, minute = time_str.split(":")
        int(hour)
        int(minute)
    except (ValueError, AttributeError):
        raise ValueError(f"Invalid time format: '{time_str}'. Use HH:MM (24h).")

    cron_script_path = cron_dir / f"{DEFAULT_CRON_NAME}.sh"
    report_dir_resolved = str(Path(report_dir).resolve())
    pack_path_resolved = str(Path(pack_path).resolve())

    # Build the cron script
    script_lines = [
        "#!/usr/bin/env bash",
        "# Hermes cron job: skill-governance daily scan",
        f"# Scheduled: {time_str} daily",
        f"# Pack: {pack_path_resolved}",
        f"# Report dir: {report_dir_resolved}",
        "",
        "set -euo pipefail",
        "",
        f'cd "$(dirname "$0")"',
        "",
        "# Run the scan and build report",
        'echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] Starting skill-governance scan..."',
        "",
        f'python3 -c "\"\"\"\nimport sys, json',
        f'sys.path.insert(0, "{pack_path_resolved}/../..")',
        f'from skill_governance.integration.cron_reporter import run_scan, build_report, send_feishu',
        f'report = run_scan("{pack_path_resolved}")',
        f'cron_report = build_report(report, "{report_dir_resolved}", "{Path(pack_path).name}")',
        f'print(json.dumps({{"status": cron_report.current_status,',
        f'  "degraded": cron_report.degraded,',
        f'  "html": cron_report.html_path,',
        f'  "json": cron_report.json_path}}, indent=2))',
        f'if send_feishu(cron_report):',
        f'  print("Feishu notification sent.")',
        f'else:',
        f'  print("Feishu notification skipped (no webhook configured).")',
        f'\"\"\"',
        "",
        'echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] Scan complete."',
    ]

    cron_script_path.write_text("\n".join(script_lines) + "\n", encoding="utf-8")
    cron_script_path.chmod(0o755)

    # Also write a cron metadata file
    meta = {
        "cron_name": DEFAULT_CRON_NAME,
        "schedule": f"daily at {time_str}",
        "pack_path": pack_path_resolved,
        "report_dir": report_dir_resolved,
        "script_path": str(cron_script_path),
        "webhook_configured": webhook_url is not None
        or os.environ.get(FEISHU_WEBHOOK_ENV) is not None,
    }

    meta_path = cron_dir / f"{DEFAULT_CRON_NAME}.json"
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

    return {
        "cron_name": DEFAULT_CRON_NAME,
        "cron_path": str(cron_script_path),
        "schedule": f"daily at {time_str}",
        "success": True,
    }
