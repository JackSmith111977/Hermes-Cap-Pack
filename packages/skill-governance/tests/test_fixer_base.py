"""Tests for FixRule ABC, FixAction, FixResult, and FixDispatcher."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from skill_governance.fixer.base import FixAction, FixResult, FixRule
from skill_governance.fixer.dispatcher import FixDispatcher


# ── FixAction tests ──────────────────────────────────────────────────────────


class TestFixAction:
    """FixAction data model unit tests."""

    def test_minimal_creation(self):
        """FixAction with only required fields."""
        action = FixAction(
            rule_id="F001", action_type="create", target_path="/tmp/test"
        )
        assert action.rule_id == "F001"
        assert action.action_type == "create"
        assert action.target_path == "/tmp/test"
        assert action.old_content == ""
        assert action.new_content == ""
        assert action.description == ""

    def test_all_fields(self):
        """FixAction with all fields populated."""
        action = FixAction(
            rule_id="F001",
            action_type="modify",
            target_path="/tmp/test.md",
            old_content="old",
            new_content="new",
            description="Test modification",
        )
        assert action.old_content == "old"
        assert action.new_content == "new"
        assert action.description == "Test modification"


# ── FixResult tests ──────────────────────────────────────────────────────────


class TestFixResult:
    """FixResult data model unit tests."""

    def test_default_values(self):
        """FixResult defaults are as expected."""
        result = FixResult(rule_id="F001")
        assert result.rule_id == "F001"
        assert result.dry_run is False
        assert result.applied == 0
        assert result.skipped == 0
        assert result.errors == []
        assert result.actions == []

    def test_total_property(self):
        """total = applied + skipped + len(errors)."""
        result = FixResult(rule_id="F001", applied=3, skipped=2)
        result.errors.append("error-1")
        assert result.total == 6  # 3 + 2 + 1

    def test_success_property_true(self):
        """success is True when errors is empty."""
        result = FixResult(rule_id="F001", applied=1)
        assert result.success is True

    def test_success_property_false(self):
        """success is False when errors is non-empty."""
        result = FixResult(rule_id="F001", applied=1)
        result.errors.append("something went wrong")
        assert result.success is False

    def test_diff_create(self):
        """diff output for a create action."""
        action = FixAction(
            rule_id="F001",
            action_type="create",
            target_path="/tmp/new.md",
            new_content="# Hello\n\nNew file.\n",
        )
        result = FixResult(rule_id="F001", actions=[action])
        diff = result.diff
        assert "--- /dev/null" in diff
        assert "+++ /tmp/new.md" in diff
        assert "+# Hello" in diff
        assert "+New file." in diff

    def test_diff_delete(self):
        """diff output for a delete action."""
        action = FixAction(
            rule_id="F001",
            action_type="delete",
            target_path="/tmp/old.md",
            old_content="# Bye\n",
        )
        result = FixResult(rule_id="F001", actions=[action])
        diff = result.diff
        assert "--- /tmp/old.md" in diff
        assert "+++ /dev/null" in diff
        assert "-# Bye" in diff

    def test_diff_modify(self):
        """diff output for a modify action."""
        action = FixAction(
            rule_id="F001",
            action_type="modify",
            target_path="/tmp/file.md",
            old_content="line1\nline2\n",
            new_content="line1\nmodified\n",
        )
        result = FixResult(rule_id="F001", actions=[action])
        diff = result.diff
        assert "/tmp/file.md" in diff
        assert "-line2" in diff
        assert "+modified" in diff

    def test_to_dict(self):
        """to_dict serialises FixResult to a JSON-compatible dict."""
        action = FixAction(
            rule_id="F001",
            action_type="create",
            target_path="/tmp/new.md",
            description="Create file",
        )
        result = FixResult(
            rule_id="F001",
            dry_run=True,
            applied=1,
            actions=[action],
        )
        d = result.to_dict()
        assert d["rule_id"] == "F001"
        assert d["dry_run"] is True
        assert d["applied"] == 1
        assert d["actions"][0]["action_type"] == "create"
        assert d["actions"][0]["target_path"] == "/tmp/new.md"

    def test_to_dict_skips_content(self):
        """to_dict should not include old/new_content for brevity."""
        action = FixAction(
            rule_id="F001",
            action_type="modify",
            target_path="/tmp/f.md",
            old_content="aaa",
            new_content="bbb",
        )
        result = FixResult(rule_id="F001", actions=[action])
        d = result.to_dict()
        action_dict = d["actions"][0]
        assert "old_content" not in action_dict
        assert "new_content" not in action_dict


# ── FixRule ABC tests ────────────────────────────────────────────────────────


class TestFixRuleABC:
    """FixRule abstract base class tests."""

    def test_cannot_instantiate_abstract(self):
        """FixRule ABC cannot be instantiated directly."""
        with pytest.raises(TypeError):
            FixRule()  # type: ignore[abstract]

    def test_concrete_subclass_works(self):
        """A concrete subclass with rule_id/description/severity works."""

        class ConcreteRule(FixRule):
            rule_id = "TEST"
            description = "Test rule"
            severity = "warning"

            def analyze(
                self, pack_path: str, check_details: dict[str, Any]
            ) -> FixResult:
                return FixResult(rule_id=self.rule_id, dry_run=True)

            def apply(
                self, pack_path: str, check_details: dict[str, Any]
            ) -> FixResult:
                return FixResult(rule_id=self.rule_id, dry_run=False)

        rule = ConcreteRule()
        assert rule.rule_id == "TEST"
        assert rule.description == "Test rule"
        assert rule.severity == "warning"

        # Default _is_already_fixed returns False
        assert rule._is_already_fixed("/tmp") is False

    def test_analyze_and_apply_return_results(self):
        """analyze and apply return correctly typed FixResults."""

        class ConcreteRule(FixRule):
            rule_id = "TEST"
            description = "Test"
            severity = "info"

            def analyze(
                self, pack_path: str, check_details: dict[str, Any]
            ) -> FixResult:
                return FixResult(rule_id=self.rule_id, dry_run=True, applied=1)

            def apply(
                self, pack_path: str, check_details: dict[str, Any]
            ) -> FixResult:
                return FixResult(rule_id=self.rule_id, dry_run=False, applied=1)

        rule = ConcreteRule()
        result_a = rule.analyze("/tmp", {})
        assert result_a.dry_run is True
        assert result_a.applied == 1

        result_b = rule.apply("/tmp", {})
        assert result_b.dry_run is False
        assert result_b.applied == 1

    def test_backup_creates_dot_bak(self, tmp_path):
        """_backup() creates a .bak copy alongside the original."""

        class ConcreteRule(FixRule):
            rule_id = "TEST"
            description = "Test"
            severity = "info"

            def analyze(self, *args, **kwargs):
                return FixResult(rule_id=self.rule_id, dry_run=True)

            def apply(self, *args, **kwargs):
                return FixResult(rule_id=self.rule_id, dry_run=False)

        rule = ConcreteRule()
        test_file = tmp_path / "test.txt"
        test_file.write_text("original content")

        bak_path = rule._backup(str(test_file))
        assert Path(bak_path).name == "test.txt.bak"
        assert Path(bak_path).exists()
        assert Path(bak_path).read_text() == "original content"
        # Original should be unchanged
        assert test_file.read_text() == "original content"

    def test_backup_raises_on_missing_file(self, tmp_path):
        """_backup() raises FileNotFoundError for non-existent paths."""

        class ConcreteRule(FixRule):
            rule_id = "TEST"
            description = "Test"
            severity = "info"

            def analyze(self, *args, **kwargs):
                return FixResult(rule_id=self.rule_id, dry_run=True)

            def apply(self, *args, **kwargs):
                return FixResult(rule_id=self.rule_id, dry_run=False)

        rule = ConcreteRule()
        missing = tmp_path / "does-not-exist.txt"
        with pytest.raises(FileNotFoundError, match="Cannot back up"):
            rule._backup(str(missing))


# ── FixDispatcher tests ──────────────────────────────────────────────────────


class _MockRule(FixRule):
    """Helper: a concrete FixRule with configurable rule_id."""

    rule_id = "MOCK"
    description = "Mock rule for dispatcher testing"
    severity = "info"

    def __init__(self, rule_id: str | None = None) -> None:
        super().__init__()
        if rule_id is not None:
            self.rule_id = rule_id

    def analyze(self, pack_path: str, check_details: dict[str, Any]) -> FixResult:
        return FixResult(rule_id=self.rule_id, dry_run=True, applied=1)

    def apply(self, pack_path: str, check_details: dict[str, Any]) -> FixResult:
        return FixResult(rule_id=self.rule_id, dry_run=False, applied=1)


class TestFixDispatcher:
    """FixDispatcher unit tests."""

    # ── registration ────────────────────────────────────────────────────

    def test_register_and_get_rule(self):
        """Register and retrieve a rule by ID."""
        dispatcher = FixDispatcher()
        rule = _MockRule("MYR")
        dispatcher.register(rule)
        assert dispatcher.get_rule("MYR") is rule
        assert dispatcher.get_rule("NONEXIST") is None

    def test_registered_rules_list(self):
        """registered_rules returns the list of registered rule IDs."""
        dispatcher = FixDispatcher()
        assert dispatcher.registered_rules == []

        dispatcher.register(_MockRule("R1"))
        dispatcher.register(_MockRule("R2"))
        assert "R1" in dispatcher.registered_rules
        assert "R2" in dispatcher.registered_rules

    def test_register_duplicate_raises(self):
        """Registering the same rule_id twice raises ValueError."""
        dispatcher = FixDispatcher()
        rule = _MockRule("DUP")
        dispatcher.register(rule)
        with pytest.raises(ValueError, match="already registered"):
            dispatcher.register(rule)

    def test_register_empty_rule_id_raises(self):
        """Registering a rule with empty rule_id raises ValueError."""
        dispatcher = FixDispatcher()
        rule = _MockRule("")
        with pytest.raises(ValueError, match="empty rule_id"):
            dispatcher.register(rule)

    # ── dispatch ────────────────────────────────────────────────────────

    def test_dispatch_empty_report(self):
        """dispatch with an empty report returns []."""
        dispatcher = FixDispatcher()
        results = dispatcher.dispatch({})
        assert results == []

    def test_dispatch_dry_run(self):
        """dispatch with dry_run=True calls analyze()."""
        dispatcher = FixDispatcher()
        dispatcher.register(_MockRule("MOCK"))

        report = {
            "target_path": "/tmp/pack",
            "layers": {
                "L0": {
                    "checks": [
                        {
                            "rule_id": "MOCK",
                            "passed": False,
                            "details": {},
                        }
                    ]
                }
            },
        }

        results = dispatcher.dispatch(report, dry_run=True)
        assert len(results) == 1
        assert results[0].rule_id == "MOCK"
        assert results[0].dry_run is True

    def test_dispatch_apply(self):
        """dispatch with dry_run=False calls apply()."""
        dispatcher = FixDispatcher()
        dispatcher.register(_MockRule("MOCK"))

        report = {
            "target_path": "/tmp/pack",
            "layers": {
                "L0": {
                    "checks": [
                        {
                            "rule_id": "MOCK",
                            "passed": False,
                            "details": {},
                        }
                    ]
                }
            },
        }

        results = dispatcher.dispatch(report, dry_run=False)
        assert len(results) == 1
        assert results[0].rule_id == "MOCK"
        assert results[0].dry_run is False

    def test_dispatch_only_matching_rules(self):
        """dispatch only invokes rules whose rule_id matches failed checks."""
        dispatcher = FixDispatcher()
        dispatcher.register(_MockRule("R1"))
        dispatcher.register(_MockRule("R2"))

        report = {
            "target_path": "/tmp/pack",
            "layers": {
                "L0": {
                    "checks": [
                        {"rule_id": "R1", "passed": False, "details": {}},
                    ]
                }
            },
        }

        results = dispatcher.dispatch(report)
        assert len(results) == 1
        assert results[0].rule_id == "R1"

    def test_dispatch_filter_by_rules_filter(self):
        """rules_filter restricts which rules are invoked."""
        dispatcher = FixDispatcher()
        dispatcher.register(_MockRule("R1"))
        dispatcher.register(_MockRule("R2"))

        report = {
            "target_path": "/tmp/pack",
            "layers": {
                "L0": {
                    "checks": [
                        {"rule_id": "R1", "passed": False, "details": {}},
                        {"rule_id": "R2", "passed": False, "details": {}},
                    ]
                }
            },
        }

        results = dispatcher.dispatch(report, rules_filter=["R2"])
        assert len(results) == 1
        assert results[0].rule_id == "R2"

    def test_dispatch_passed_checks_ignored(self):
        """Only failed checks (passed=False) are dispatched."""
        dispatcher = FixDispatcher()
        dispatcher.register(_MockRule("R1"))

        report = {
            "target_path": "/tmp/pack",
            "layers": {
                "L0": {
                    "checks": [
                        {"rule_id": "R1", "passed": True, "details": {}},
                    ]
                }
            },
        }

        results = dispatcher.dispatch(report)
        assert results == []

    def test_dispatch_no_matching_rules(self):
        """dispatch returns [] when no registered rule matches."""
        dispatcher = FixDispatcher()
        dispatcher.register(_MockRule("R1"))

        report = {
            "target_path": "/tmp/pack",
            "layers": {
                "L0": {
                    "checks": [
                        {"rule_id": "R2", "passed": False, "details": {}},
                    ]
                }
            },
        }

        results = dispatcher.dispatch(report)
        assert results == []
