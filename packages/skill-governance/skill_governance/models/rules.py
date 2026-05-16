"""Rule and RuleLayer data models derived from rules.yaml."""

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class Rule:
    """A single machine-checkable rule definition from rules.yaml."""

    id: str
    description: str
    severity: str  # blocking | warning | info
    check_type: str
    target_field: str
    params: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        def _sanitize(v: Any) -> Any:
            if isinstance(v, str):
                return v.replace("\n", " ").replace("\r", " ").strip()
            return v

        return {
            "id": self.id,
            "description": _sanitize(self.description),
            "severity": self.severity,
            "check_type": self.check_type,
            "target_field": self.target_field,
            "params": self.params,
        }


@dataclass
class RuleLayer:
    """A rules.yaml layer containing a group of related rules."""

    id: str  # e.g. "L0", "L1"
    name: str
    description: str
    target: str
    blocking_failure: bool
    rules: list[Rule] = field(default_factory=list)

    @property
    def rule_ids(self) -> list[str]:
        return [r.id for r in self.rules]

    def get_rule(self, rule_id: str) -> Optional[Rule]:
        for r in self.rules:
            if r.id == rule_id:
                return r
        return None

    def to_dict(self) -> dict[str, Any]:
        def _sanitize(v: Any) -> Any:
            if isinstance(v, str):
                return v.replace("\n", " ").replace("\r", " ").strip()
            return v

        return {
            "id": self.id,
            "name": _sanitize(self.name),
            "description": _sanitize(self.description),
            "target": _sanitize(self.target),
            "blocking_failure": self.blocking_failure,
            "rules": [r.to_dict() for r in self.rules],
        }


@dataclass
class RuleCollection:
    """Collection of all layers parsed from rules.yaml."""

    version: str = ""
    standard_ref: str = ""
    schema_ref: str = ""
    layers: dict[str, RuleLayer] = field(default_factory=dict)

    @property
    def layer_ids(self) -> list[str]:
        return sorted(self.layers.keys())

    def get_layer(self, layer_id: str) -> Optional[RuleLayer]:
        return self.layers.get(layer_id)

    def get_rule(self, layer_id: str, rule_id: str) -> Optional[Rule]:
        layer = self.get_layer(layer_id)
        if layer:
            return layer.get_rule(rule_id)
        return None

    def get_all_rules(self) -> list[Rule]:
        rules: list[Rule] = []
        for lid in sorted(self.layers.keys()):
            rules.extend(self.layers[lid].rules)
        return rules

    def to_dict(self) -> dict[str, Any]:
        def _sanitize(v: Any) -> Any:
            if isinstance(v, str):
                return v.replace("\n", " ").replace("\r", " ").strip()
            return v

        return {
            "version": _sanitize(self.version),
            "standard_ref": _sanitize(self.standard_ref),
            "schema_ref": _sanitize(self.schema_ref),
            "layers": {lid: lr.to_dict() for lid, lr in sorted(self.layers.items())},
        }
