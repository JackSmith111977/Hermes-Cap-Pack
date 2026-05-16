"""OpenClaw adapter — STORY-5-3-3.

:class:`OpenClawAdapter` extends :class:`SkillGovernanceAdapter` to provide
governance‑aware adaptation for the **OpenClaw** agent environment.

The adapter directly imports the governance scanner modules for compliance
checking (L0‑L4) and delegates pack suggestion / application to
:class:`CapPackAdapter`.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from skill_governance.adapter.base import AdapterConfig, SkillGovernanceAdapter
from skill_governance.adapter.cap_pack_adapter import CapPackAdapter
from skill_governance.models.result import ScanReport, ScanResult
from skill_governance.scanner.base import RuleLoader
from skill_governance.scanner.compliance import ComplianceChecker
from skill_governance.scanner.atomicity import AtomicityScanner
from skill_governance.scanner.tree_validator import TreeValidator
from skill_governance.scanner.workflow_detector import WorkflowDetector


class OpenClawAdapter(SkillGovernanceAdapter):
    """Governance adapter for the **OpenClaw** agent.

    *   **scan**       — directly imports and invokes the scanner modules
                        (ComplianceChecker, AtomicityScanner, TreeValidator,
                        WorkflowDetector) for L0‑L4 compliance.
    *   **suggest**    — delegates to :class:`CapPackAdapter.suggest`.
    *   **dry_run**    — delegates to :class:`CapPackAdapter.dry_run`.
    *   **apply**      — delegates to :class:`CapPackAdapter.apply`.
    *   **get_agent_info** — reports OpenClaw as the target agent.
    """

    def __init__(self, config: AdapterConfig | None = None) -> None:
        """Initialise the OpenClaw adapter.

        Args:
            config: Adapter configuration.  When *None*, a default config with
                    ``agent_type='openclaw'`` and ``dry_run=True`` is created.
        """
        self._config = config or AdapterConfig(
            agent_type="openclaw",
            dry_run=True,
        )
        self._cap_pack_adapter = CapPackAdapter()

    # ── Properties ───────────────────────────────────────────────────────

    @property
    def name(self) -> str:
        """Human-readable adapter identifier."""
        return "openclaw"

    @property
    def config(self) -> AdapterConfig:
        """Return the adapter configuration."""
        return self._config

    # ── scan ──────────────────────────────────────────────────────────────

    def scan(self, path: str) -> dict[str, Any]:
        """Run L0‑L4 compliance scan using the governance engine directly.

        Directly imports and invokes the rule checkers — no subprocess
        overhead.

        Args:
            path: Path to a cap‑pack directory (containing ``cap-pack.yaml``)
                  or a skill directory (containing ``SKILL.md``).

        Returns:
            A dictionary with per‑layer results, overall compliance verdict,
            and any blocking failures detected.
        """
        target = Path(path).resolve()
        if not target.exists():
            return {
                "error": f"Path does not exist: {path}",
                "target_path": str(target),
            }

        # If *path* is a skill directory, try to discover its parent pack.
        pack_path = str(target)
        if (target / "SKILL.md").exists() and not (target / "cap-pack.yaml").exists():
            for parent in [target.parent, target.parent.parent]:
                if (parent / "cap-pack.yaml").exists():
                    pack_path = str(parent)
                    break

        # Load skills from the pack manifest.
        skills = self._load_skills(pack_path)
        workflows, clusters = self._load_workflows_and_clusters(pack_path)

        l0_data = {"skills": skills}
        l1_data = {"skills": skills}
        l2_data = {"skills": skills, "clusters": clusters}
        l3_data = {"skills": skills, "pack_path": pack_path}
        l4_data = {"workflows": workflows, "skills": skills}

        report = self._build_report(
            target_path=pack_path,
            l0_data=l0_data,
            l1_data=l1_data,
            l2_data=l2_data,
            l3_data=l3_data,
            l4_data=l4_data,
        )

        return report.to_dict()

    # ── suggest ───────────────────────────────────────────────────────────

    def suggest(self, path: str) -> list[dict[str, Any]]:
        """Recommend cap‑pack packages via CapPackAdapter.

        Args:
            path: Path to the skill directory (must contain ``SKILL.md``).

        Returns:
            A list of suggestion dicts sorted by score descending.
            Each dict contains:
                - ``pack_name`` (str)
                - ``pack_path`` (str)
                - ``score`` (float, 0.0‑1.0)
                - ``reasons`` (list[str])
        """
        result = self._cap_pack_adapter.suggest(path)
        return [
            {
                "pack_name": s.pack_name,
                "pack_path": s.pack_path,
                "score": s.score,
                "reasons": s.reasons,
            }
            for s in result.suggestions
        ]

    # ── dry_run ───────────────────────────────────────────────────────────

    def dry_run(self, path: str) -> str:
        """Preview the changes :meth:`apply` would perform via CapPackAdapter.

        Args:
            path: Path to the skill or pack directory.

        Returns:
            A human‑readable string describing the proposed modifications.
        """
        target = Path(path).resolve()
        if not target.exists():
            return f"Error: path does not exist: {path}"

        result = self._cap_pack_adapter.dry_run(path)
        return result.message

    # ── apply ─────────────────────────────────────────────────────────────

    def apply(self, path: str) -> bool:
        """Execute adaptation via CapPackAdapter.

        Args:
            path: Path to the skill directory.

        Returns:
            ``True`` if changes were applied successfully, ``False`` otherwise.
        """
        target = Path(path).resolve()
        if not target.exists() or not (target / "SKILL.md").exists():
            return False

        if self._config.dry_run:
            print(self.dry_run(path))
            return True

        result = self._cap_pack_adapter.apply(
            path,
            confirm=not self._config.auto_confirm,
        )
        return result.applied

    # ── get_agent_info ────────────────────────────────────────────────────

    def get_agent_info(self) -> dict[str, Any]:
        """Return metadata about the OpenClaw agent environment.

        Returns:
            A dictionary with agent type and version information.
        """
        return {
            "agent_type": "openclaw",
            "version": "unknown",
        }

    # ── Internal helpers ──────────────────────────────────────────────────

    @staticmethod
    def _load_skills(pack_path: str) -> list[dict[str, Any]]:
        """Load skill entries from ``cap-pack.yaml``."""
        import yaml

        pack_dir = Path(pack_path)
        pack_yaml = pack_dir / "cap-pack.yaml"
        if not pack_yaml.exists():
            return []

        with open(pack_yaml, "r", encoding="utf-8") as fh:
            data = yaml.safe_load(fh) or {}

        skills: list[dict[str, Any]] = []
        for sk in data.get("skills", []):
            sid = sk.get("id", "") or sk.get("name", "")
            skill_path_str = sk.get("path", "")
            if not skill_path_str:
                resolved_path = pack_dir / "SKILLS" / sid
            else:
                resolved_path = pack_dir / skill_path_str
            skills.append(
                {
                    "id": sid,
                    "name": sk.get("name", sid),
                    "path": str(resolved_path),
                    "version": sk.get("version", ""),
                    "classification": sk.get("classification", ""),
                    "tags": sk.get("tags", []),
                    "triggers": sk.get("triggers", []),
                    "sqs_total": sk.get("sqs_total", None),
                    "compatibility": sk.get("compatibility", {}),
                }
            )
        return skills

    @staticmethod
    def _load_workflows_and_clusters(
        pack_path: str,
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        """Load workflows and clusters from ``cap-pack.yaml``."""
        import yaml

        pack_dir = Path(pack_path)
        pack_yaml = pack_dir / "cap-pack.yaml"
        if not pack_yaml.exists():
            return [], []

        with open(pack_yaml, "r", encoding="utf-8") as fh:
            data = yaml.safe_load(fh) or {}

        return data.get("workflows", []), data.get("clusters", [])

    @staticmethod
    def _build_report(
        target_path: str,
        l0_data: dict[str, Any] | None = None,
        l1_data: dict[str, Any] | None = None,
        l2_data: dict[str, Any] | None = None,
        l3_data: dict[str, Any] | None = None,
        l4_data: dict[str, Any] | None = None,
    ) -> ScanReport:
        """Build a full L0‑L4 :class:`ScanReport` (mirrors CLI._build_report).

        Args:
            target_path: The pack directory being scanned.
            l0_data:     Data for Layer 0 (Compatibility) checks.
            l1_data:     Data for Layer 1 (Foundation) checks.
            l2_data:     Data for Layer 2 (Health) checks.
            l3_data:     Data for Layer 3 (Ecosystem) checks.
            l4_data:     Data for Layer 4 (Workflow) checks.

        Returns:
            A populated :class:`ScanReport` with per‑layer results.
        """
        report = ScanReport(target_path=target_path)

        # Layer 0 — Compatibility
        l0_checker = ComplianceChecker(layer_id="L0")
        l0_checks = l0_checker.scan(l0_data or {})
        l0_layer = RuleLoader().get_layer("L0")
        report.layers["L0"] = ScanResult(
            layer_id="L0",
            layer_name=l0_layer.name if l0_layer else "Compatibility",
            target=l0_layer.target if l0_layer else "L0 pass",
            blocking_failure=l0_layer.blocking_failure if l0_layer else True,
            checks=l0_checks,
        )

        # Layer 1 — Foundation
        l1_checker = ComplianceChecker(layer_id="L1")
        l1_checks = l1_checker.scan(l1_data or {})
        l1_layer = RuleLoader().get_layer("L1")
        report.layers["L1"] = ScanResult(
            layer_id="L1",
            layer_name=l1_layer.name if l1_layer else "Foundation",
            target=l1_layer.target if l1_layer else "L1 pass",
            blocking_failure=l1_layer.blocking_failure if l1_layer else True,
            checks=l1_checks,
        )

        # Layer 2 — Health
        l2_results: list = []
        if l2_data:
            atomicity = AtomicityScanner()
            l2_results.extend(atomicity.scan(l2_data))
            tree_val = TreeValidator()
            l2_results.extend(tree_val.scan(l2_data))
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
        l3_checks = l3_checker.scan(l3_data or {})
        l3_layer = RuleLoader().get_layer("L3")
        report.layers["L3"] = ScanResult(
            layer_id="L3",
            layer_name=l3_layer.name if l3_layer else "Ecosystem",
            target=l3_layer.target if l3_layer else "L3 pass",
            blocking_failure=l3_layer.blocking_failure if l3_layer else False,
            checks=l3_checks,
        )

        # Layer 4 — Workflow
        l4_results: list = []
        if l4_data:
            wf_detector = WorkflowDetector()
            l4_results.extend(wf_detector.scan(l4_data))
        l4_layer = RuleLoader().get_layer("L4")
        report.layers["L4"] = ScanResult(
            layer_id="L4",
            layer_name=l4_layer.name if l4_layer else "Workflow Orchestration",
            target=l4_layer.target if l4_layer else "L4 pass (Orchestrated)",
            blocking_failure=l4_layer.blocking_failure if l4_layer else False,
            checks=l4_results,
        )

        return report
