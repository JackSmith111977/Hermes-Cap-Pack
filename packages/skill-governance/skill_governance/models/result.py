"""Data models for scan results and reports."""

from dataclasses import dataclass, field, asdict
from typing import Any, Optional
from datetime import datetime


@dataclass
class CheckResult:
    """Result of a single rule check execution."""

    rule_id: str
    layer_id: str
    description: str
    severity: str  # blocking | warning | info
    passed: bool
    score: float = 0.0
    details: dict[str, Any] = field(default_factory=dict)
    suggestions: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ScanResult:
    """Aggregated result for one layer of rules."""

    layer_id: str
    layer_name: str
    target: str
    blocking_failure: bool
    checks: list[CheckResult] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        if not self.checks:
            return True
        return all(
            c.passed for c in self.checks
        )

    @property
    def score(self) -> float:
        if not self.checks:
            return 100.0
        return sum(c.score for c in self.checks) / len(self.checks)

    @property
    def checks_passed(self) -> int:
        return sum(1 for c in self.checks if c.passed)

    @property
    def checks_total(self) -> int:
        return len(self.checks)

    def to_dict(self) -> dict[str, Any]:
        return {
            "layer_id": self.layer_id,
            "layer_name": self.layer_name,
            "target": self.target,
            "blocking_failure": self.blocking_failure,
            "passed": self.passed,
            "score": round(self.score, 2),
            "checks_passed": self.checks_passed,
            "checks_total": self.checks_total,
            "checks": [c.to_dict() for c in self.checks],
        }

    def has_blocking_failures(self) -> bool:
        return any(
            not c.passed and c.severity == "blocking" for c in self.checks
        )


@dataclass
class ScanReport:
    """Complete scan report covering all L0-L4 layers."""

    target_path: str
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    layers: dict[str, ScanResult] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def overall_status(self) -> str:
        """Determine overall compliance status per CAP-PACK-STANDARD v1.0."""
        l0 = self.layers.get("L0")
        l1 = self.layers.get("L1")
        l2 = self.layers.get("L2")
        l3 = self.layers.get("L3")
        l4 = self.layers.get("L4")

        if l0 and l0.has_blocking_failures():
            return "non_compliant"
        if l1 and l1.has_blocking_failures():
            return "non_compliant"

        if not l0 or not l0.passed:
            return "non_compliant"
        if not l1 or not l1.passed:
            return "non_compliant"

        l2_ok = l2 is not None and l2.passed
        l3_ok = l3 is not None and l3.passed
        l4_ok = l4 is not None and l4.passed

        if l2_ok and l3_ok and l4_ok and l4.checks:
            return "orchestrated"
        if l2_ok and l3_ok:
            return "excellent"
        if l2_ok:
            return "healthy"
        if l2 is not None:
            return "needs_improvement"

        return "compliant"

    @property
    def terminated(self) -> bool:
        """Check if scan terminated early due to blocking failure."""
        if self.layers.get("L0") and self.layers["L0"].has_blocking_failures():
            return False
        if self.layers.get("L1") and self.layers["L1"].has_blocking_failures():
            return False
        return True

    def to_dict(self) -> dict[str, Any]:
        return {
            "target_path": self.target_path,
            "timestamp": self.timestamp,
            "overall_status": self.overall_status,
            "metadata": self.metadata,
            "layers": {
                lid: lr.to_dict() for lid, lr in sorted(self.layers.items())
            },
        }
