"""Base scanner module: RuleLoader and BaseScanner abstract class."""

from __future__ import annotations

import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Optional

import yaml

from skill_governance.models.result import CheckResult
from skill_governance.models.rules import Rule, RuleLayer, RuleCollection


# ─── RuleLoader ───────────────────────────────────────────────────────────────


def _find_rules_yaml() -> Path:
    """Search for standards/rules.yaml walking up from the package location."""
    # Check relative to this file first
    here = Path(__file__).resolve().parent
    for parent in [here, *here.parents]:
        candidate = parent / "standards" / "rules.yaml"
        if candidate.exists():
            return candidate
        # Also check parent's parent (for nested package structure)
        candidate2 = parent / ".." / "standards" / "rules.yaml"
        if candidate2.resolve().exists():
            return candidate2.resolve()

    # Search from current working directory upward
    cwd = Path.cwd().resolve()
    for parent in [cwd, *cwd.parents]:
        candidate = parent / "standards" / "rules.yaml"
        if candidate.exists():
            return candidate

    # Last resort: env var or default guess
    env_path = os.environ.get("CAP_PACK_STANDARDS_DIR")
    if env_path:
        candidate = Path(env_path) / "rules.yaml"
        if candidate.exists():
            return candidate

    return here / "standards" / "rules.yaml"


DEFAULT_RULES_PATH: Path = _find_rules_yaml()


class RuleLoader:
    """Loads rules.yaml by layer and group rules."""

    def __init__(self, rules_path: Optional[os.PathLike[str]] = None) -> None:
        self.rules_path = Path(rules_path) if rules_path else DEFAULT_RULES_PATH
        self._collection: Optional[RuleCollection] = None

    def load(self) -> RuleCollection:
        """Parse rules.yaml into a RuleCollection."""
        if self._collection is not None:
            return self._collection

        if not self.rules_path.exists():
            raise FileNotFoundError(f"rules.yaml not found at {self.rules_path}")

        with open(self.rules_path, "r", encoding="utf-8") as f:
            raw = yaml.safe_load(f)

        collection = RuleCollection(
            version=raw.get("version", ""),
            standard_ref=raw.get("standard_ref", ""),
            schema_ref=raw.get("schema_ref", ""),
        )

        for layer_raw in raw.get("layers", []):
            rules = [
                Rule(
                    id=r["id"],
                    description=r["description"],
                    severity=r["severity"],
                    check_type=r["check_type"],
                    target_field=r["target_field"],
                    params=r.get("params", {}),
                )
                for r in layer_raw.get("rules", [])
            ]
            layer = RuleLayer(
                id=layer_raw["id"],
                name=layer_raw["name"],
                description=layer_raw.get("description", ""),
                target=layer_raw.get("target", ""),
                blocking_failure=layer_raw.get("blocking_failure", False),
                rules=rules,
            )
            collection.layers[layer.id] = layer

        self._collection = collection
        return collection

    def get_layer(self, layer_id: str) -> Optional[RuleLayer]:
        """Get a single layer by ID (e.g. 'L0')."""
        return self.load().get_layer(layer_id)

    def get_rule(self, layer_id: str, rule_id: str) -> Optional[Rule]:
        """Get a specific rule by layer and rule IDs."""
        return self.load().get_rule(layer_id, rule_id)

    def reload(self) -> RuleCollection:
        """Force re-read rules.yaml."""
        self._collection = None
        return self.load()


# ─── BaseScanner ──────────────────────────────────────────────────────────────


class BaseScanner(ABC):
    """Abstract base class for all governance scanners.

    Provides a common interface: scan() returns a list of CheckResult objects.
    Subclasses set self.layer_id and implement _scan_impl().
    """

    def __init__(self, rule_loader: Optional[RuleLoader] = None) -> None:
        self.rule_loader = rule_loader or RuleLoader()
        self.layer_id: str = ""

    @abstractmethod
    def _scan_impl(self, target: Any, **kwargs: Any) -> list[CheckResult]:
        """Subclass-specific scan logic. Must return list of CheckResult."""

    def scan(self, target: Any, **kwargs: Any) -> list[CheckResult]:
        """Run scan, return list of CheckResults."""
        return self._scan_impl(target, **kwargs)

    def _make_result(
        self,
        rule_id: str,
        passed: bool,
        score: float = 0.0,
        details: Optional[dict[str, Any]] = None,
        suggestions: Optional[list[str]] = None,
    ) -> CheckResult:
        """Helper to build a CheckResult from a rule definition."""
        rule = self.rule_loader.get_rule(self.layer_id, rule_id)
        return CheckResult(
            rule_id=rule_id,
            layer_id=self.layer_id,
            description=rule.description if rule else rule_id,
            severity=rule.severity if rule else "info",
            passed=passed,
            score=score,
            details=details or {},
            suggestions=suggestions or [],
        )
