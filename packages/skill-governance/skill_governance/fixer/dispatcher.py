"""FixDispatcher — routes scan failures to registered FixRule instances.

Based on ADR-6-4 / STORY-6-0-1 the dispatcher takes a scan report
(``dict``) and a list of candidate rule IDs, matches each check that
failed against registered ``FixRule`` objects, and returns a list of
``FixResult`` objects.

Typical usage::

    dispatcher = FixDispatcher()
    dispatcher.register(MyFixRule())

    report = scan_report.to_dict()          # from a previous scan
    results = dispatcher.dispatch(report)   # list[FixResult]
"""

from __future__ import annotations

from typing import Any

from skill_governance.fixer.base import FixResult, FixRule


class FixDispatcher:
    """Route failed scan checks to registered fix rules.

    The dispatcher owns a registry of ``FixRule`` instances keyed by
    ``rule_id``.  Call ``dispatch()`` with a scan report to apply the
    matching rules to every check that failed.
    """

    def __init__(self) -> None:
        self._rules: dict[str, FixRule] = {}

    # ── registration ─────────────────────────────────────────────────────────

    def register(self, rule: FixRule) -> None:
        """Register a single ``FixRule`` instance.

        Args:
            rule: A concrete subclass of ``FixRule``.  Its ``rule_id``
                  class-attribute is used as the registry key.

        Raises:
            ValueError: If a rule with the same ``rule_id`` is already
                        registered, or if ``rule`` does not define a
                        non-empty ``rule_id``.
        """
        rid = rule.rule_id
        if not rid:
            raise ValueError(f"Cannot register a FixRule with an empty rule_id")
        if rid in self._rules:
            raise ValueError(
                f"A FixRule with rule_id={rid!r} is already registered"
            )
        self._rules[rid] = rule

    def get_rule(self, rule_id: str) -> FixRule | None:
        """Retrieve a registered rule by its ``rule_id``.

        Args:
            rule_id: The unique identifier of the rule.

        Returns:
            The ``FixRule`` instance, or ``None`` if not found.
        """
        return self._rules.get(rule_id)

    @property
    def registered_rules(self) -> list[str]:
        """Return a list of all registered rule IDs."""
        return list(self._rules.keys())

    # ── dispatch ─────────────────────────────────────────────────────────────

    def dispatch(
        self,
        report: dict[str, Any],
        rules_filter: list[str] | None = None,
        dry_run: bool = True,
    ) -> list[FixResult]:
        """Route failed checks from a scan report to matching fix rules.

        The algorithm:

        1. Flatten all ``CheckResult`` objects from every layer in the
           report.
        2. Keep only checks where ``passed == False``.
        3. If *rules_filter* is given, further restrict to checks whose
           ``rule_id`` appears in that list.
        4. For each matching (rule, check) pair, call ``rule.analyze()``
           if *dry_run* is ``True``, otherwise ``rule.apply()``.

        Args:
            report:       A scan report dict — the same shape produced by
                          ``ScanReport.to_dict()``.  Expected to contain a
                          ``"layers"`` key mapping layer IDs to objects
                          that each have a ``"checks"`` list.
            rules_filter: Optional list of rule IDs to restrict dispatch
                          to.  When ``None`` all registered rules whose
                          ``rule_id`` matches a failed check are invoked.
            dry_run:      When ``True`` (default) calls ``analyze()`` on
                          each rule; when ``False`` calls ``apply()``.

        Returns:
            A list of ``FixResult`` objects, one per rule that was
            dispatched.  The list is in registration order.
        """
        # 1. Flatten all checks from the report
        failed_checks = self._collect_failed_checks(report)

        # 2. Filter by rules_filter if provided
        if rules_filter is not None:
            filter_set = set(rules_filter)
            failed_checks = [c for c in failed_checks if c["rule_id"] in filter_set]

        # 3. Group failed checks by rule_id so a rule is only called once
        #    (it receives all matching check details).
        checks_by_rule: dict[str, list[dict[str, Any]]] = {}
        for check in failed_checks:
            rid = check["rule_id"]
            checks_by_rule.setdefault(rid, []).append(check)

        # 4. Dispatch
        results: list[FixResult] = []
        for rid, check_details_list in checks_by_rule.items():
            rule = self._rules.get(rid)
            if rule is None:
                continue

            # Merge details from all matching checks for this rule
            merged_details = self._merge_check_details(check_details_list)

            if dry_run:
                result = rule.analyze(
                    pack_path=report.get("target_path", ""),
                    check_details=merged_details,
                )
                result.dry_run = True
            else:
                result = rule.apply(
                    pack_path=report.get("target_path", ""),
                    check_details=merged_details,
                )
                result.dry_run = False

            results.append(result)

        return results

    # ── internal helpers ──────────────────────────────────────────────────────

    @staticmethod
    def _collect_failed_checks(report: dict[str, Any]) -> list[dict[str, Any]]:
        """Flatten all failed checks from every layer in *report*."""
        failed: list[dict[str, Any]] = []
        layers = report.get("layers", {})
        if isinstance(layers, dict):
            for layer_id, layer_data in layers.items():
                checks = []
                if isinstance(layer_data, dict):
                    checks = layer_data.get("checks", [])
                elif hasattr(layer_data, "checks"):
                    checks = layer_data.checks
                for check in checks:
                    if isinstance(check, dict):
                        passed = check.get("passed", True)
                    else:
                        passed = getattr(check, "passed", True)
                    if not passed:
                        if isinstance(check, dict):
                            failed.append(check)
                        else:
                            # Duck-type CheckResult-like objects
                            failed.append(
                                {
                                    "rule_id": getattr(check, "rule_id", "unknown"),
                                    "layer_id": getattr(check, "layer_id", layer_id),
                                    "description": getattr(check, "description", ""),
                                    "severity": getattr(check, "severity", "info"),
                                    "details": getattr(check, "details", {}),
                                    "suggestions": getattr(check, "suggestions", []),
                                }
                            )
        return failed

    @staticmethod
    def _merge_check_details(
        check_details_list: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Merge multiple check detail dicts into one.

        Uses the first check as the base and overlays subsequent ``details``
        dicts on top.
        """
        if not check_details_list:
            return {}

        base = dict(check_details_list[0])
        details = base.get("details", {})
        if isinstance(details, dict):
            merged_details = dict(details)
        else:
            merged_details = {}

        for check in check_details_list[1:]:
            extra = check.get("details", {})
            if isinstance(extra, dict):
                merged_details.update(extra)

        base["details"] = merged_details
        return base
