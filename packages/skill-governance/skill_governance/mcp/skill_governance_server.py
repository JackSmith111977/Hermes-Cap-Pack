"""MCP Server exposing governance + orchestration capabilities — STORY-5-3-2.

Exposes five tools and three resources via the FastMCP protocol so that
MCP clients (including Hermes Agent itself) can perform skill compliance
scanning, pack recommendation, adaptation, and workflow-pattern discovery.

Tools
-----
* ``scan_skill(path)``         — L0-L4 compliance inspection
* ``suggest_pack(path)``       — cap-pack recommendation for a skill
* ``apply_adaptation(path, confirm)`` — auto-adapt skill into best pack
* ``check_compliance(path)``   — detailed compliance report (L0-L4)
* ``list_workflow_patterns()`` — available DAG workflow patterns

Resources (skill-governance:// URI scheme)
-------------------------------------------
* ``skill-governance://rules``      — loaded rule definitions (all layers)
* ``skill-governance://standards``  — standard / schema references
* ``skill-governance://patterns``   — recognised workflow patterns

Usage
-----
Run the server with::

    python3 -m skill_governance.mcp.skill_governance_server
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

# ─── FastMCP ──────────────────────────────────────────────────────────────────

from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.resources import FunctionResource

# ─── Skill governance internals ───────────────────────────────────────────────

from skill_governance.adapter.cap_pack_adapter import CapPackAdapter
from skill_governance.scanner.base import RuleLoader
from skill_governance.scanner.compliance import ComplianceChecker
from skill_governance.scanner.workflow_detector import WorkflowDetector

# ─── Server class ─────────────────────────────────────────────────────────────


class SkillGovernanceMCPServer:
    """MCP server that wraps skill governance primitives as tools + resources.

    Attributes:
        app:       The underlying :class:`FastMCP` application instance.
        adapter:   A :class:`CapPackAdapter` instance used for scan/suggest/apply.
        rules:     Pre-loaded rules collection (via :class:`RuleLoader`).
    """

    def __init__(self, name: str = "skill-governance") -> None:
        mcp = FastMCP(
            name=name,
            instructions="Skill Governance MCP Server — compliance scanning, "
            "cap-pack recommendation, adaptation, and workflow-pattern discovery "
            "for Hermes Cap-Pack.",
        )

        self.app: FastMCP = mcp
        self.adapter: CapPackAdapter = CapPackAdapter()
        self._rule_loader: RuleLoader = RuleLoader()
        self._rules = self._rule_loader.load()
        self._register_tools()
        self._register_resources()

    # ── Tools ─────────────────────────────────────────────────────────────

    def _register_tools(self) -> None:
        """Register all five MCP tools on the FastMCP app."""

        # -----------------------------------------------------------------
        # 1. scan_skill
        # -----------------------------------------------------------------
        @self.app.tool(
            name="scan_skill",
            description="Run an L0-L4 compliance scan on the skill directory at *path*.",
        )
        def scan_skill(path: str) -> str:
            """Execute a compliance scan for the skill at *path*.

            Args:
                path: Filesystem path to a skill directory (must contain ``SKILL.md``).

            Returns:
                JSON string with compliance results (per-layer verdicts,
                blocking failures, and overall pass/fail).
            """
            result = self.adapter.scan(path)
            return json.dumps(
                {
                    "skill_path": result.skill_path,
                    "compliance_ok": result.compliance_ok,
                    "message": result.message,
                    "applied": result.applied,
                },
                indent=2,
                ensure_ascii=False,
            )

        # -----------------------------------------------------------------
        # 2. suggest_pack
        # -----------------------------------------------------------------
        @self.app.tool(
            name="suggest_pack",
            description="Recommend the best-matching cap-pack package(s) for a skill.",
        )
        def suggest_pack(path: str) -> str:
            """Find and rank cap-pack packages relevant to the skill at *path*.

            Uses tag-Jaccard similarity, description keyword overlap,
            classification, and domain matching.

            Args:
                path: Path to the skill directory.

            Returns:
                JSON string listing ranked pack suggestions with scores and reasons.
            """
            result = self.adapter.suggest(path)
            output: dict[str, Any] = {
                "skill_path": result.skill_path,
                "compliance_ok": result.compliance_ok,
                "message": result.message,
                "suggestions": [
                    {
                        "pack_name": s.pack_name,
                        "pack_path": s.pack_path,
                        "score": s.score,
                        "reasons": s.reasons,
                    }
                    for s in result.suggestions
                ],
            }
            return json.dumps(output, indent=2, ensure_ascii=False)

        # -----------------------------------------------------------------
        # 3. apply_adaptation
        # -----------------------------------------------------------------
        @self.app.tool(
            name="apply_adaptation",
            description="Add a skill into the best-matching cap-pack package.",
        )
        def apply_adaptation(path: str, confirm: bool = True) -> str:
            """Automatically adapt a skill into its best-matching cap-pack.

            Runs compliance check + suggestion, then (optionally after user
            confirmation) adds the skill entry into the target ``cap-pack.yaml``.

            Args:
                path:    Path to the skill directory.
                confirm: When *True* (default), prompts for confirmation.
                         Set to *False* for unattended operation.

            Returns:
                JSON string describing whether the adaptation was applied.
            """
            result = self.adapter.apply(path, confirm=confirm)
            return json.dumps(
                {
                    "skill_path": result.skill_path,
                    "compliance_ok": result.compliance_ok,
                    "applied": result.applied,
                    "message": result.message,
                },
                indent=2,
                ensure_ascii=False,
            )

        # -----------------------------------------------------------------
        # 4. check_compliance
        # -----------------------------------------------------------------
        @self.app.tool(
            name="check_compliance",
            description="Return a detailed L0-L4 compliance report for the skill at *path*.",
        )
        def check_compliance(path: str) -> str:
            """Run all four governance layers (L0-L4) against a skill directory.

            Args:
                path: Path to the skill directory.

            Returns:
                JSON string with per-check results (rule_id, passed, severity,
                score, details, suggestions) for layers L0–L4.
            """
            sp = Path(path).resolve()
            if not sp.exists():
                return json.dumps(
                    {"error": f"Path does not exist: {path}"},
                    indent=2,
                )

            # Collect skill data via adapter internals
            skill_data = self.adapter._collect_skill_data(str(sp))
            skills = [skill_data]

            all_checks: list[dict[str, Any]] = []

            # L0 — Atomicity / structure checks (via ComplianceChecker)
            try:
                l0_checker = ComplianceChecker(layer_id="L0")
                l0_checks = l0_checker.scan({"skills": skills})
                for c in l0_checks:
                    all_checks.append(
                        {
                            "layer_id": "L0",
                            "rule_id": c.rule_id,
                            "description": c.description,
                            "severity": c.severity,
                            "passed": c.passed,
                            "score": c.score,
                            "details": c.details,
                            "suggestions": c.suggestions,
                        }
                    )
            except Exception as exc:
                all_checks.append(
                    {
                        "layer_id": "L0",
                        "rule_id": "L0_SCAN_ERR",
                        "description": f"L0 scan error: {exc}",
                        "severity": "blocking",
                        "passed": False,
                        "score": 0.0,
                        "details": {},
                        "suggestions": [],
                    }
                )

            # L1 — Foundation checks
            try:
                l1_checker = ComplianceChecker(layer_id="L1")
                l1_checks = l1_checker.scan({"skills": skills})
                for c in l1_checks:
                    all_checks.append(
                        {
                            "layer_id": "L1",
                            "rule_id": c.rule_id,
                            "description": c.description,
                            "severity": c.severity,
                            "passed": c.passed,
                            "score": c.score,
                            "details": c.details,
                            "suggestions": c.suggestions,
                        }
                    )
            except Exception as exc:
                all_checks.append(
                    {
                        "layer_id": "L1",
                        "rule_id": "L1_SCAN_ERR",
                        "description": f"L1 scan error: {exc}",
                        "severity": "blocking",
                        "passed": False,
                        "score": 0.0,
                        "details": {},
                        "suggestions": [],
                    }
                )

            # L3 — Ecosystem checks (L2 is experience-documents, L3 checks those)
            try:
                l3_checker = ComplianceChecker(layer_id="L3")
                l3_checks = l3_checker.scan(
                    {"skills": skills, "pack_path": str(sp.parent)}
                )
                for c in l3_checks:
                    all_checks.append(
                        {
                            "layer_id": "L3",
                            "rule_id": c.rule_id,
                            "description": c.description,
                            "severity": c.severity,
                            "passed": c.passed,
                            "score": c.score,
                            "details": c.details,
                            "suggestions": c.suggestions,
                        }
                    )
            except Exception as exc:
                all_checks.append(
                    {
                        "layer_id": "L3",
                        "rule_id": "L3_SCAN_ERR",
                        "description": f"L3 scan error: {exc}",
                        "severity": "blocking",
                        "passed": False,
                        "score": 0.0,
                        "details": {},
                        "suggestions": [],
                    }
                )

            # L4 — Workflow checks (only if the skill contains workflow data)
            try:
                workflow_data = {}
                if skill_data.get("triggers") or skill_data.get("workflows"):
                    workflow_data = {
                        "workflows": skill_data.get("workflows", []),
                        "skills": skills,
                    }
                if workflow_data.get("workflows"):
                    l4_checker = WorkflowDetector()
                    l4_checks = l4_checker.scan(workflow_data)
                    for c in l4_checks:
                        all_checks.append(
                            {
                                "layer_id": "L4",
                                "rule_id": c.rule_id,
                                "description": c.description,
                                "severity": c.severity,
                                "passed": c.passed,
                                "score": c.score,
                                "details": c.details,
                                "suggestions": c.suggestions,
                            }
                        )
            except Exception as exc:
                all_checks.append(
                    {
                        "layer_id": "L4",
                        "rule_id": "L4_SCAN_ERR",
                        "description": f"L4 scan error: {exc}",
                        "severity": "blocking",
                        "passed": False,
                        "score": 0.0,
                        "details": {},
                        "suggestions": [],
                    }
                )

            overall_pass = all(c["passed"] for c in all_checks if c["severity"] == "blocking")

            return json.dumps(
                {
                    "skill_path": str(sp),
                    "overall_compliance": "PASS" if overall_pass else "FAIL",
                    "total_checks": len(all_checks),
                    "passed": sum(1 for c in all_checks if c["passed"]),
                    "failed": sum(1 for c in all_checks if not c["passed"]),
                    "checks": all_checks,
                },
                indent=2,
                ensure_ascii=False,
            )

        # -----------------------------------------------------------------
        # 5. list_workflow_patterns
        # -----------------------------------------------------------------
        @self.app.tool(
            name="list_workflow_patterns",
            description="List all recognised workflow DAG patterns.",
        )
        def list_workflow_patterns() -> str:
            """Return the set of allowed workflow patterns.

            Also includes a brief description of each pattern.

            Returns:
                JSON string with the allowed patterns and their descriptions.
            """
            patterns = {
                "sequential": "Steps execute in strict sequence (one after another).",
                "parallel": "Steps execute concurrently where possible.",
                "conditional": "Execution branches based on condition expressions.",
                "dag": "Directed Acyclic Graph — arbitrary dependency topology "
                "with cycle detection and deadlock freedom checks.",
            }
            return json.dumps(
                {
                    "allowed_patterns": list(WorkflowDetector.ALLOWED_PATTERNS),
                    "patterns": patterns,
                    "total": len(patterns),
                },
                indent=2,
                ensure_ascii=False,
            )

    # ── Resources ──────────────────────────────────────────────────────────

    def _register_resources(self) -> None:
        """Register three skill-governance resources on the FastMCP app."""

        # -----------------------------------------------------------------
        # skill-governance://rules
        # -----------------------------------------------------------------
        @self.app.resource(
            uri="skill-governance://rules",
            name="Governance Rules",
            description="All loaded governance rule definitions (L0-L4).",
            mime_type="application/json",
        )
        async def get_rules() -> str:
            """Return the full rule collection as a JSON string."""
            rules_data: dict[str, Any] = {
                "version": self._rules.version,
                "standard_ref": self._rules.standard_ref,
                "schema_ref": self._rules.schema_ref,
                "layers": {},
            }
            for lid, layer in self._rules.layers.items():
                rules_data["layers"][lid] = {
                    "id": layer.id,
                    "name": layer.name,
                    "description": layer.description,
                    "target": layer.target,
                    "blocking_failure": layer.blocking_failure,
                    "rules": [
                        {
                            "id": r.id,
                            "description": r.description,
                            "severity": r.severity,
                            "check_type": r.check_type,
                            "target_field": r.target_field,
                            "params": r.params,
                        }
                        for r in layer.rules
                    ],
                }
            return json.dumps(rules_data, indent=2, ensure_ascii=False)

        # -----------------------------------------------------------------
        # skill-governance://standards
        # -----------------------------------------------------------------
        @self.app.resource(
            uri="skill-governance://standards",
            name="Standards Reference",
            description="Standard & schema references for the governance framework.",
            mime_type="application/json",
        )
        async def get_standards() -> str:
            """Return standard/schema metadata from the loaded rules."""
            return json.dumps(
                {
                    "standard_ref": self._rules.standard_ref or "cap-pack-standards-v1",
                    "schema_ref": self._rules.schema_ref or "cap-pack-schema-v1",
                    "version": self._rules.version or "0.1.0",
                    "layers_available": list(self._rules.layers.keys()),
                    "rules_total": sum(
                        len(layer.rules) for layer in self._rules.layers.values()
                    ),
                },
                indent=2,
                ensure_ascii=False,
            )

        # -----------------------------------------------------------------
        # skill-governance://patterns
        # -----------------------------------------------------------------
        @self.app.resource(
            uri="skill-governance://patterns",
            name="Workflow Patterns",
            description="Recognised DAG workflow patterns with descriptions.",
            mime_type="application/json",
        )
        async def get_patterns() -> str:
            """Return the set of allowed workflow patterns and their semantics."""
            patterns = {
                "sequential": "Steps execute in strict sequence.",
                "parallel": "Steps execute concurrently where possible.",
                "conditional": "Execution branches based on condition expressions.",
                "dag": "Directed Acyclic Graph with topology constraints.",
            }
            return json.dumps(
                {
                    "allowed_patterns": sorted(WorkflowDetector.ALLOWED_PATTERNS),
                    "patterns": patterns,
                    "total": len(patterns),
                    "validation_rules": [
                        "W001: All skill references must resolve to existing skills.",
                        "W002: DAG must have no cyclic dependencies.",
                        "W003: DAG must be deadlock-free — all nodes reachable from a root.",
                        "W004: Pattern value must be one of the allowed set.",
                        "W005: Condition expressions must have valid syntax.",
                    ],
                },
                indent=2,
                ensure_ascii=False,
            )

    # ── Runner ─────────────────────────────────────────────────────────────

    def run(self) -> None:
        """Start the MCP server using stdio transport (default for CLI tools)."""
        self.app.run(transport="stdio")


# ─── Module-level entry point ─────────────────────────────────────────────────

def main() -> None:
    """CLI entry point — builds and starts the MCP server."""
    server = SkillGovernanceMCPServer()
    server.run()


if __name__ == "__main__":
    main()
