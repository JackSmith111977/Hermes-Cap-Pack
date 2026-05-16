"""WorkflowDetector — DAG cycle detection, deadlock freedom, skill refs, pattern validation (W001-W005)."""

from __future__ import annotations

import re
from collections import deque
from typing import Any, Optional

from skill_governance.models.result import CheckResult
from skill_governance.scanner.base import BaseScanner


class WorkflowDetector(BaseScanner):
    """Layer 4 (Workflow) scanner for W001-W005 rules.

    W001: All skill references in workflow steps resolve to existing skills.
    W002: DAG must have no cyclic dependencies (Kahn's algorithm / topological sort).
    W003: DAG must be deadlock-free — all nodes reachable from at least one root.
    W004: Workflow pattern value must be one of: sequential, parallel, conditional, dag.
    W005: Condition expressions (if present) must have valid syntax.
    """

    ALLOWED_PATTERNS = {"sequential", "parallel", "conditional", "dag"}
    FORBIDDEN_IN_EXPR = {"eval(", "exec(", "__import__"}

    def __init__(self, rule_loader: Any = None) -> None:
        super().__init__(rule_loader)
        self.layer_id = "L4"

    def _scan_impl(self, target: Any, **kwargs: Any) -> list[CheckResult]:
        """Run W001-W005 checks.

        Args:
            target: dict with keys:
                - "workflows": list of workflow definition dicts
                - "skills": list of skill dicts (for reference resolution)
        """
        data = target if isinstance(target, dict) else kwargs
        workflows: list[dict[str, Any]] = data.get("workflows", [])
        skills: list[dict[str, Any]] = data.get("skills", [])
        skill_ids = set()
        for sk in skills:
            sid = sk.get("id", "") or sk.get("name", "")
            if sid:
                skill_ids.add(sid)

        results: list[CheckResult] = []

        results.append(self._check_skill_refs(workflows, skill_ids))
        results.append(self._check_cycles(workflows))
        results.append(self._check_deadlock(workflows))
        results.append(self._check_pattern_valid(workflows))
        results.append(self._check_conditions(workflows))

        return results

    def _get_all_step_skills(self, workflows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Flatten all step/skill references from workflows."""
        refs: list[dict[str, Any]] = []
        for wf in workflows:
            wf_id = wf.get("id", "unknown")
            for step in wf.get("steps", []):
                refs.append(
                    {
                        "workflow_id": wf_id,
                        "step_id": step.get("id", ""),
                        "skill_ref": step.get("skill", ""),
                    }
                )
                # Handle nested steps
                for nested in step.get("steps", []):
                    refs.append(
                        {
                            "workflow_id": wf_id,
                            "step_id": nested.get("id", ""),
                            "skill_ref": nested.get("skill", ""),
                        }
                    )
            # Handle branches (conditional)
            for branch in wf.get("branches", []):
                for step in branch.get("steps", []):
                    refs.append(
                        {
                            "workflow_id": wf_id,
                            "step_id": step.get("id", ""),
                            "skill_ref": step.get("skill", ""),
                        }
                    )
        return refs

    def _check_skill_refs(
        self, workflows: list[dict[str, Any]], skill_ids: set[str]
    ) -> CheckResult:
        """W001: All skill references must resolve."""
        refs = self._get_all_step_skills(workflows)
        unresolved: list[dict[str, Any]] = []
        for ref in refs:
            if ref["skill_ref"] and ref["skill_ref"] not in skill_ids:
                unresolved.append(ref)

        passed = len(unresolved) == 0
        score = 100.0 if passed else max(0, 100.0 - (len(unresolved) / max(1, len(refs))) * 100)
        suggestions = [
            f"Workflow '{u['workflow_id']}' step '{u['step_id']}' references unknown skill '{u['skill_ref']}'"
            for u in unresolved
        ]

        return self._make_result(
            rule_id="W001",
            passed=passed,
            score=round(score, 2),
            details={
                "total_refs": len(refs),
                "unresolved": unresolved,
            },
            suggestions=suggestions if suggestions else ["All skill references resolve correctly"],
        )

    def _build_dag_graph(
        self, wf: dict[str, Any]
    ) -> tuple[dict[str, list[str]], set[str]]:
        """Build adjacency list from a DAG workflow's steps."""
        graph: dict[str, list[str]] = {}
        nodes: set[str] = set()
        for step in wf.get("steps", []):
            sid = step.get("id", "")
            if not sid:
                continue
            nodes.add(sid)
            deps = step.get("depends_on", [])
            if isinstance(deps, list):
                graph.setdefault(sid, []).extend(deps)
            # Handle nested steps
            for nested in step.get("steps", []):
                nsid = nested.get("id", "")
                if not nsid:
                    continue
                nodes.add(nsid)
                ndeps = nested.get("depends_on", [])
                if isinstance(ndeps, list):
                    graph.setdefault(nsid, []).extend(ndeps)
        # Ensure all dependency targets are in the graph
        for node, deps in graph.items():
            for d in deps:
                if d not in nodes:
                    nodes.add(d)
                    graph.setdefault(d, [])
        return graph, nodes

    def _check_cycles(self, workflows: list[dict[str, Any]]) -> CheckResult:
        """W002: DAG cycle detection using Kahn's algorithm (BFS topological sort)."""
        cyclic_workflows: list[dict[str, Any]] = []

        for wf in workflows:
            pattern = wf.get("pattern", "")
            if pattern != "dag":
                continue

            graph, nodes = self._build_dag_graph(wf)
            if not nodes:
                continue

            # Build in-degree map and reverse adjacency
            in_degree: dict[str, int] = {n: 0 for n in nodes}
            adj: dict[str, list[str]] = {n: [] for n in nodes}
            for node, deps in graph.items():
                for dep in deps:
                    if dep in adj:
                        adj[dep].append(node)
                        in_degree[node] = in_degree.get(node, 0) + 1

            # Kahn's algorithm
            queue = deque([n for n in nodes if in_degree.get(n, 0) == 0])
            visited_count = 0
            while queue:
                node = queue.popleft()
                visited_count += 1
                for neighbor in adj.get(node, []):
                    in_degree[neighbor] -= 1
                    if in_degree[neighbor] == 0:
                        queue.append(neighbor)

            if visited_count != len(nodes):
                cyclic_workflows.append(
                    {
                        "workflow_id": wf.get("id", "unknown"),
                        "total_nodes": len(nodes),
                        "reachable_nodes": visited_count,
                        "cycled_nodes": len(nodes) - visited_count,
                    }
                )

        passed = len(cyclic_workflows) == 0
        score = 100.0 if passed else max(0, 100.0 - (len(cyclic_workflows) / max(1, len(workflows))) * 100)
        suggestions = [
            f"Workflow '{w['workflow_id']}' contains {w['cycled_nodes']} node(s) in cycle — remove cyclic dependencies"
            for w in cyclic_workflows
        ]

        return self._make_result(
            rule_id="W002",
            passed=passed,
            score=round(score, 2),
            details={
                "cyclic_workflows": cyclic_workflows,
                "total_workflows": len(workflows),
            },
            suggestions=suggestions if suggestions else ["No cyclic dependencies detected"],
        )

    def _check_deadlock(self, workflows: list[dict[str, Any]]) -> CheckResult:
        """W003: DAG deadlock-free — all nodes reachable from at least one root.

        Uses BFS from root nodes (nodes with no incoming edges).
        """
        deadlock_workflows: list[dict[str, Any]] = []

        for wf in workflows:
            pattern = wf.get("pattern", "")
            if pattern != "dag":
                continue

            graph, nodes = self._build_dag_graph(wf)
            if not nodes:
                continue

            # Build reverse graph to find roots (nodes with no dependencies)
            has_incoming: set[str] = set()
            for node, deps in graph.items():
                for d in deps:
                    if d in nodes:
                        has_incoming.add(node)
                    # Also record that d has an outgoing edge (but this doesn't make d non-root)

            roots = nodes - has_incoming
            if not roots:
                deadlock_workflows.append(
                    {
                        "workflow_id": wf.get("id", "unknown"),
                        "total_nodes": len(nodes),
                        "reason": "No root nodes found — all nodes have dependencies",
                    }
                )
                continue

            # BFS from all roots
            visited: set[str] = set()
            queue = deque(roots)
            while queue:
                node = queue.popleft()
                if node in visited:
                    continue
                visited.add(node)
                # Find all neighbors that depend on this node
                for neighbor, deps in graph.items():
                    if node in deps and neighbor not in visited:
                        queue.append(neighbor)

            unreachable = nodes - visited
            if unreachable:
                deadlock_workflows.append(
                    {
                        "workflow_id": wf.get("id", "unknown"),
                        "total_nodes": len(nodes),
                        "reachable": len(visited),
                        "unreachable_nodes": sorted(unreachable),
                    }
                )

        passed = len(deadlock_workflows) == 0
        score = 100.0 if passed else max(0, 100.0 - (len(deadlock_workflows) / max(1, len(workflows))) * 100)
        suggestions = [
            f"Workflow '{w['workflow_id']}' has {len(w.get('unreachable_nodes', []))} unreachable node(s) — check dependency chains"
            for w in deadlock_workflows
        ]

        return self._make_result(
            rule_id="W003",
            passed=passed,
            score=round(score, 2),
            details={
                "deadlock_workflows": deadlock_workflows,
                "total_workflows": len(workflows),
            },
            suggestions=suggestions if suggestions else ["No deadlock detected"],
        )

    def _check_pattern_valid(self, workflows: list[dict[str, Any]]) -> CheckResult:
        """W004: Workflow pattern must be one of the allowed values."""
        invalid: list[dict[str, Any]] = []
        for wf in workflows:
            pattern = wf.get("pattern", "")
            if pattern not in self.ALLOWED_PATTERNS:
                invalid.append(
                    {
                        "workflow_id": wf.get("id", "unknown"),
                        "pattern": pattern,
                        "allowed": sorted(self.ALLOWED_PATTERNS),
                    }
                )

        passed = len(invalid) == 0
        score = 100.0 if passed else max(0, 100.0 - (len(invalid) / max(1, len(workflows))) * 100)
        suggestions = [
            f"Workflow '{w['workflow_id']}' has invalid pattern '{w['pattern']}' — use one of {w['allowed']}"
            for w in invalid
        ]

        return self._make_result(
            rule_id="W004",
            passed=passed,
            score=round(score, 2),
            details={
                "invalid_patterns": invalid,
                "total_workflows": len(workflows),
            },
            suggestions=suggestions if suggestions else ["All patterns are valid"],
        )

    def _check_conditions(self, workflows: list[dict[str, Any]]) -> CheckResult:
        """W005: Condition expressions must have valid syntax."""
        invalid: list[dict[str, Any]] = []
        max_expr_length: int = 500
        total_conditions = 0

        def check_expr(expr: Any, context: dict[str, Any]) -> None:
            nonlocal total_conditions
            if not expr or not isinstance(expr, str):
                return
            total_conditions += 1
            issues: list[str] = []
            if len(expr) > max_expr_length:
                issues.append(f"Expression exceeds {max_expr_length} chars ({len(expr)})")
            for forbidden in self.FORBIDDEN_IN_EXPR:
                if forbidden in expr:
                    issues.append(f"Contains forbidden pattern '{forbidden}'")
            if issues:
                invalid.append({**context, "expression": expr, "issues": issues})

        for wf in workflows:
            wf_id = wf.get("id", "unknown")
            # Check workflow-level condition
            check_expr(wf.get("condition"), {"workflow_id": wf_id, "location": "workflow"})
            # Check step conditions
            for step in wf.get("steps", []):
                check_expr(
                    step.get("condition"),
                    {"workflow_id": wf_id, "step_id": step.get("id", ""), "location": "step"},
                )
                for nested in step.get("steps", []):
                    check_expr(
                        nested.get("condition"),
                        {"workflow_id": wf_id, "step_id": nested.get("id", ""), "location": "step.nested"},
                    )
            # Check branch conditions
            for branch in wf.get("branches", []):
                check_expr(
                    branch.get("condition"),
                    {"workflow_id": wf_id, "branch_id": branch.get("id", ""), "location": "branch"},
                )

        passed = len(invalid) == 0
        score = 100.0 if passed else max(0, 100.0 - (len(invalid) / max(1, total_conditions)) * 100)
        suggestions = [
            f"Workflow '{w['workflow_id']}' {w['location']}: {', '.join(w['issues'])}"
            for w in invalid
        ]

        return self._make_result(
            rule_id="W005",
            passed=passed,
            score=round(score, 2),
            details={
                "invalid_conditions": invalid,
                "total_conditions": total_conditions,
            },
            suggestions=suggestions if suggestions else ["All condition expressions are valid"],
        )
