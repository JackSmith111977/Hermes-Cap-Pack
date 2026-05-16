"""Integration package — pre-flight gates, SRA quality injector, and cron reporter."""

from skill_governance.integration.pre_flight_gate import check_gate, GateResult
from skill_governance.integration.sra_quality_injector import inject_quality_to_sra
from skill_governance.integration.cron_reporter import setup_cron, run_scan, build_report, send_feishu

__all__ = [
    "check_gate",
    "GateResult",
    "inject_quality_to_sra",
    "setup_cron",
    "run_scan",
    "build_report",
    "send_feishu",
]
