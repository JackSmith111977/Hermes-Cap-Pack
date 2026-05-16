"""JSON reporter — layered L0-L4 output."""

from __future__ import annotations

import json
from typing import Any, Optional

from skill_governance.models.result import ScanReport


class JSONReporter:
    """Produces JSON-formatted scan reports with L0-L4 layered structure."""

    def __init__(self, indent: int = 2) -> None:
        self.indent = indent

    def generate(self, report: ScanReport, output_path: Optional[str] = None) -> str:
        """Generate JSON report string and optionally write to file.

        Args:
            report: The ScanReport to serialize.
            output_path: If provided, write JSON to this file.

        Returns:
            JSON string of the report.
        """
        data = report.to_dict()
        json_str = json.dumps(data, indent=self.indent, ensure_ascii=False)

        if output_path:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(json_str)

        return json_str

    def generate_summary(self, report: ScanReport) -> dict[str, Any]:
        """Generate a compact summary dict."""
        return {
            "target_path": report.target_path,
            "timestamp": report.timestamp,
            "overall_status": report.overall_status,
            "terminated": report.terminated,
            "layers": {
                lid: {
                    "passed": lr.passed,
                    "score": lr.score,
                    "checks_passed": lr.checks_passed,
                    "checks_total": lr.checks_total,
                }
                for lid, lr in sorted(report.layers.items())
            },
        }

    @staticmethod
    def from_file(filepath: str) -> ScanReport:
        """Deserialize a JSON file back into a ScanReport.

        Note: This produces a dict with the same structure. Full ScanReport
        reconstruction requires the full model layer. Returns raw dict for now.
        """
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)  # type: ignore[return-value]
